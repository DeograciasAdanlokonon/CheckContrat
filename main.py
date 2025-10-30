from flask import Flask, abort, render_template, redirect, url_for, flash, request, send_from_directory, session
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, LoginManager, current_user, logout_user
import stripe
from models.models import db, User, Check
from models.config import CheckDataBase
from forms.forms import RegisterForm, LoginForm, ProfileForm, ContractForm, FicheContract, RequestPasswordForm, ResetPasswordForm
from core.upload import UploadError, save_upload
from core.openai_engine import OpenaiAnalyse
from emails.email_utils import confirm_token, send_confirmation_email, generate_confirmation_token, send_reset_email, send_payment_success_email
import os
import threading
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('APP_SECRET_KEY')
SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SECURITY_PASSWORD_SALT'] = SECURITY_PASSWORD_SALT
Bootstrap(app=app)

# Flask Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

# user loader callback
@login_manager.user_loader
def load_user(user_id):
  return db.get_or_404(User, user_id)

# DataBase configuration
database = CheckDataBase(app=app)

# Openai engine
engine = OpenaiAnalyse()

# Stripe module
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# current year
current_year = datetime.now().year
current_date = date.today()

# Stripe checkout methode
def stripe_checkout(endpoint):
   """Implements stripe choukout"""

   price_id = 'price_1SNWSaDlaxMT86N3tTdU28Be'  
   price_obj = stripe.Price.retrieve(price_id)
   unit_amount = price_obj.unit_amount

   checkout_session = stripe.checkout.Session.create(
      line_items= [
         {
            'price': price_id,
            'quantity': 1
         }
      ],
      mode= 'payment',
      success_url = url_for(endpoint, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
      cancel_url= url_for('cancel', _external=True)
   )

   return checkout_session
   

# ToDo: Index Route
@app.route('/', methods=['GET'])
def index():
  return render_template('index.html', current_year=current_year)

# ToDo: Dashboard Home Route
@app.route('/dashboard', methods = ['GET', 'POST'])
def dashboard():
  """Retuns all the record in the db"""

  if not current_user.is_authenticated:
    return redirect(url_for('login'))  # send user to login page

  result = db.session.execute(db.select(Check).where(Check.user_id == current_user.id))
  checks = result.scalars().all()

  # Get statistic
  total_conforme = sum(1 for c in checks if c.result and c.result.lower() == "conforme")
  total_non_conforme = sum(1 for c in checks if c.result and c.result.lower() == "non conforme")

  return render_template(
    'dashboard/index.html', 
    current_year=current_year, 
    current_date=current_date, 
    current_user=current_user, 
    checks=checks,
    total_conforme=total_conforme,
    total_non_conforme=total_non_conforme
  )

# ToDo: CheckContract Route
@app.route('/contrat-de-travail', methods=['GET', 'POST'])
@login_required
def module_contract():
  # Initialize Contract form
  contract_form = ContractForm()

  if contract_form.validate_on_submit():
    if current_user.is_authenticated:
      uploaded = contract_form.contract_file.data
      type_contract = contract_form.type_contract.data

      try:
        type
        filename = save_upload(uploaded, current_user.id)
        
        data = {
           'type_contract': type_contract,
           'filename': filename
        }
        session['contrat_data'] = data  # store in session

        # Run Stripe checkout
        if filename:
          checkout_session = stripe_checkout(endpoint='analyse_contract')
          return redirect(checkout_session.url, code=303)
        else:
          flash("Aucun fichier sélectionné !", "info")

      except UploadError as e:
        flash(str(e), "danger")
        return redirect(url_for("module_contrat"))

      flash("Fichier uploadé avec succès.", "success")
      # return redirect(url_for("dashboard.index"))

  # GET -> render template with form
  return render_template('dashboard/module_contrat.html', contract_form=contract_form, current_year=current_year)

# ToDo: Analyse Contract route
@app.route('/analyse-contrat', methods=['GET', 'POST'])
@login_required
def analyse_contract():
   session_id = request.args.get('session_id')
   stripe_session = stripe.checkout.Session.retrieve(session_id)

   # Run Openai engine if payment is success
   if stripe_session.payment_status == 'paid':
      try:
         data = session.get('contrat_data')

         prompt = f"Analyse ce contrat {data['type_contract']} et indique s'il est conforme au droit du travail français."
         
         result = engine.analyse_contract(file=data['filename'], prompt=prompt) # Openai engine
         
         # create new check
         new_check = Check(
            module='contrat',
            input_files=data['filename'],
            output_files=result['report_file'],
            result=result['result'],
            detail=result['detail'],
            has_paid=True,
            user_id=current_user.id,
          )
         
         # insert new_check in db
         db.session.add(new_check)
         db.session.flush()
         db.session.commit()

         print(prompt)

         # Send payment email
         send_payment_success_email(user=current_user, module_type='contrat')

         session.pop('contrat_data', None)  # clean up
         
         # head user to view detail route
         return redirect(url_for('view', id=new_check.id))
      except Exception as e:
         flash(f'Une erreure est survenue', 'info')
         return redirect(url_for('module_contract'))
   else:
      return redirect(url_for('cancel'))


# ToDo: FicheContract Route
@app.route('/fiche-de-paie', methods=['GET', 'POST'])
@login_required
def module_fiche():
  # Initialize Contract form
  fiche_form = FicheContract()

  if fiche_form.validate_on_submit():
    if current_user.is_authenticated:
      fiche_uploaded = fiche_form.fiche_file.data
      contract_uploaded = fiche_form.contract_file.data
      if fiche_form.nombre_heure.data:
         hours = fiche_form.nombre_heure.data

    try:
      fiche_name = save_upload(fiche_uploaded, current_user.id)
      contract_name = save_upload(contract_uploaded, current_user.id)

      # Run Stripe checkout
      if fiche_name and contract_name:
        data = {
           'fiche_name': fiche_name,
           'contract_name': contract_name,
           'hours': hours
        }
        # Store data in session for later use
        session['fiche_data'] = data

        checkout_session = stripe_checkout(endpoint='analyse_fiche')
        return redirect(checkout_session.url, code=303)

      else:
        flash('Aucun fichier sélectionné !', 'info')
    except UploadError as e:
      flash(str(e), "danger")
      return redirect(url_for("module_fiche"))

    flash("Fichier uploadé avec succès.", "success")
    # return redirect(url_for("dashboard.index"))

  return render_template('dashboard/module_fiche.html', fiche_form=fiche_form, current_year=current_year)

# ToDo: Analyse Fiche Route
@app.route('/analyse-fiche', methods=['GET', 'POST'])
@login_required
def analyse_fiche():
   session_id = request.args.get('session_id')
   stripe_session = stripe.checkout.Session.retrieve(session_id)

   if stripe_session.payment_status == 'paid':
      try:
        data = session.get('fiche_data')
        if not data:
            flash("Aucune donnée d'analyse trouvée.", "danger")
            return redirect(url_for("module_fiche"))
        
        prompt = "Vérifie si la fiche de paie correspond bien au contrat et identifie toute anomalie, conformement au droit du travail français."
        
        result = engine.analyse_fiche(fiche_file=data['fiche_name'], contrat_file=data['contract_name'], hours=data['hours'], prompt=prompt)
        
        # create new check
        new_check = Check(
            module='fiche',
            input_files=f"{data['fiche_name']};{data['contract_name']}",
            output_files=result['report_file'],
            result=result['result'],
            detail=result['detail'],
            has_paid=True,
            user_id=current_user.id,
          )
        
        # insert new_check
        db.session.add(new_check)
        db.session.flush()
        db.session.commit()

        # Send payment email
        send_payment_success_email(user=current_user, module_type='fiche')
        threading.Thread(target=send_payment_success_email, args=(current_user, 'fiche')).start()

        # clean saved session fiche_data
        session.pop('fiche_data', None)
        
        # head user to view detail route
        return redirect(url_for('view', id=new_check.id))
      except Exception as e:
         flash(f'Une erreur est survenue: {e}', 'info')
         return redirect(url_for('module_fiche'))
   else:
      return redirect(url_for('cancel'))
   

# ToDo: View Check Result Route
@app.route('/check-result/<int:id>', methods=['GET', 'POST'])
@login_required
def view(id):
  check = db.get_or_404(Check, id)
  return render_template('dashboard/view.html', check=check)

# ToDo: Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
  register_form = RegisterForm()

  try:
   # On submit
   if register_form.validate_on_submit():
     username = register_form.username.data
     email = register_form.email.data

     # Check password equal
     if register_form.password.data == register_form.confirm_password.data:
       password = generate_password_hash(register_form.password.data, salt_length=8)

       # Check if user already exist
       result = db.session.execute(db.select(User).where(User.email == email))
       user = result.scalar()

       if not user:
         # create new user
          new_user = User(
            username=username,
            email=email,
            password_hash = password
          )

          # insert new user in db
          db.session.add(new_user)
          db.session.commit()

          # Send confirmation email
          send_confirmation_email(new_user)

          flash("Un lien de confirmation a été envoyé. Veuillez vérifiez votre boîte mail.", "info")

       else:
         flash('Vous aviez déja un compte avec cet email. Veuillez vous connecter !', 'warning')
         
         # head user to login page
         return redirect(url_for('login'))
     else:
       flash('Vos mots de passe doivent être égaux', 'error')
  except Exception as e:
    flash(f'Something went wrong: {e}', 'error')
  
  return render_template('register.html', register_form=register_form)

# ToDo: Login Route
@app.route('/login', methods = ['GET', 'POST'])
def login():
  # Initialize login form
  login_form = LoginForm()

  try:
    # if form submitted
    if login_form.validate_on_submit():
      email = login_form.email.data
      password = login_form.password.data

      # check if user exits in db
      result = db.session.execute(db.select(User).where(User.email == email))
      user = result.scalar()

      if user and user.confirmed_email:
        # check password is correct
        if check_password_hash(user.password_hash, password=password):
          # then let user log in
          login_user(user=user)

          # head user to dashboard page
          return redirect(url_for('dashboard', logged_in=current_user.is_authenticated))
        else:
          flash('Mot de passe incorrect ! Veuillez réessayer.', 'warning')
      else:
        flash("Cet adresse email n'existe pas ou non confirmé. Veuillez réessayer !", 'danger')
  except Exception as e:
    flash(f'Quelque chose à mal fonctionné : {e}', 'danger')
  
  return render_template('login.html', login_form=login_form)


# ToDo: Confirm Email Route
@app.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('Le lien de confirmation est invalide ou déja expiré.', 'danger')
        return redirect(url_for('register'))

    user = User.query.filter_by(email=email).first_or_404()

    if user.confirmed_email:
        flash('Compte déja vérifiéé. Veuillez vous connecter.', 'info')
    else:
        user.confirmed_email = True
        db.session.commit()
        flash('Votre email a été confirmé ! Veuillez vous connecter.', 'success')

    return redirect(url_for('login'))

# Define absolute paths
CORE_DIR = Path(__file__).resolve().parent / "core"
INPUT_DIR = CORE_DIR / "input-files"
OUTPUT_DIR = CORE_DIR / "output-files"

@app.route("/download/<path:filename>")
@login_required
def download_file(filename):
  """
  Allow a logged-in user to download one of their input or output files.
  The filename must exist in either input-files or output-files.
  """
  # Normalize filename
  safe_filename = Path(filename).name  # removes any path traversal like ../../

  # Check both directories
  input_path = INPUT_DIR / safe_filename
  output_path = OUTPUT_DIR / safe_filename

  if input_path.exists():
      directory = INPUT_DIR
  elif output_path.exists():
      directory = OUTPUT_DIR
  else:
      abort(404, description="File not found")

  # Optionally, verify the file belongs to current_user
  # (if filenames start with user_id, like '12_abC123.pdf')
  if not safe_filename.startswith(f"{current_user.id}_") and not safe_filename.startswith("report_"):
      abort(403, description="Accèss non autorisé a ce fichier")

  # Serve file
  return send_from_directory(directory, safe_filename, as_attachment=True)

# Todo: Logout Route
@app.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('index'))

#ToDo: Profile Route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
  user = current_user
  profile_form = ProfileForm()

  if profile_form.validate_on_submit():
    try:
      user.username = profile_form.username.data
      user.email = profile_form.email.data

      if profile_form.new_password.data:
        if len(profile_form.new_password.data) < 8:
          flash('Le mot de passe doit contenir au moins 8 caractères.', 'danger')
          return redirect(url_for('profile'))
        user.password_hash = generate_password_hash(profile_form.new_password.data, salt_length=8)

      db.session.commit()
      flash('Modification sauvegardée avec succèss !', 'success')
      return redirect(url_for('profile'))

    except Exception as e:
      flash(f'Une erreur est survenue: {e}', 'danger')

  return render_template('dashboard/profile.html', form=profile_form, current_user=current_user, current_year=current_year)

# ToDo: Request Password Route
@app.route('/request-password', methods=['GET', 'POST'])
def request_password():
    form = RequestPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_confirmation_token(user.email)
            send_reset_email(user.email, token)
            flash("Un lien de réinitialisation a été envoyé à votre adresse e-mail.", "success")
        else:
            flash("Aucun compte trouvé avec cette adresse e-mail.", "danger")
    return render_template('auth/request_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    email = confirm_token(token)
    if not email:
        flash("Le lien de réinitialisation est invalide ou expiré.", "danger")
        return redirect(url_for('request_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for('request_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            user.password_hash = generate_password_hash(form.password.data, salt_length=8)
            db.session.commit()
            flash("Votre mot de passe a été réinitialisé avec succès. Vous pouvez vous connecter.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.exception("Error resetting password: %s", e)
            flash("Une erreur est survenue. Réessayez plus tard.", "danger")
            return redirect(url_for('request_password'))

    return render_template('auth/reset_password.html', form=form)

# ToDo Cancel Payment Route
@app.route('/cancel')
@login_required
def cancel():
    flash('Payement annulé. Veuillez réessayer !', 'info')
    return redirect(url_for('dashboard'))

# ToDo: Mention Legales Route
@app.route('/mentions-legales', methods=['GET'])
def legal_mention():
  return render_template('mention-legales.html')

# ToDo: Politque Confidentiel Route
@app.route('/politique-de-confidentialite', methods=['GET'])
def confidential_policies():
  return render_template('confidential-policies.html')

# ToDo: CGU Route
@app.route('/cgu')
def cgu():
  return render_template('cgu.html')


if __name__ == "__main__":
  app.run(debug=True, port=5002)