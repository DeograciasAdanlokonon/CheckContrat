from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, HiddenField, BooleanField, IntegerField, SelectField
from wtforms.validators import InputRequired, DataRequired, Email, Length, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed, FileRequired

def validate_specific_choice(form, field):
    if field.data == 'select':
        raise ValidationError('Veuillez sélectionnez un type')
    
# ToDo: Registration Form
class RegisterForm(FlaskForm):
  username = StringField("", validators=[DataRequired(), Length(4, 80)])
  email = EmailField("", validators=[DataRequired(), Length(4, 120)])
  password = PasswordField("", validators=[DataRequired(), Length(8, 12)])
  confirm_password = PasswordField("", validators=[DataRequired(), Length(8, 12)])
  agree_terms = BooleanField("", validators=[DataRequired()])
  submit = SubmitField("S'inscrire")


# ToDo: Login Form
class LoginForm(FlaskForm):
  email = EmailField("", validators=[DataRequired(), Length(4, 120)])
  password = PasswordField("", validators=[DataRequired(), Length(8, 12)])
  remember_me = BooleanField("", validators=[DataRequired()])
  submit = SubmitField("Se connecter")

# ToDo: Profile Form
class ProfileForm(FlaskForm):
  username = StringField("Votre nom d'utilisateur", validators=[DataRequired(), Length(4, 80)])
  email = EmailField("Votre email", validators=[DataRequired(), Length(4, 120)])
  new_password = PasswordField("Nouveau mot de passe")
  submit = SubmitField("Sauvegarder")


class RequestPasswordForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Length(4, 120)])
    submit = SubmitField("Envoyer")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("Nouveau mot de passe", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField("Confirmez le mot de passe", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Réinitialiser le mot de passe")


# ToDo: ContractForm
class ContractForm(FlaskForm):
  contract_file = FileField("Contrat", validators=[
        FileRequired(message='Sélectionner un fichier.'),
        FileAllowed(['docx', 'pdf'], 'Seul les documents pdf/docx sont autorisés !')
    ])
  
  choices_data = [
     ('select', '- Seléctionner le type de contrat -'),
     ('cdd', 'CDD'),
     ('cdi', 'CDI'),
     ("d'alternance", 'Alternance (Apprentissage / Professionnalisation)'),
     ('de stage', 'Stage (Convention de stage)'),
     ('professionnel/partenariat entre entreprises', 'Contrat professionnel / Partenariat entre entreprises')
  ]

  alternance_choices = [
     ('select', "- Seléctionner votre année d'alternance -"),
     ('1', '1er année'),
     ('2', '2e année'),
     ("3", '3e année'),
     ('4', 'Plus de 3 ans'),
  ]
  
  type_contract = SelectField('Type de contrat', choices=choices_data, validators=[DataRequired(message='Aucune séléction'), validate_specific_choice])
  alternance = SelectField("Année d'alternance (Obligatoire)", choices=alternance_choices, validators=[DataRequired(message='Aucune séléction')])
  submit = SubmitField('Lancer analyse')


# ToDo: FicheContract
class FicheContract(FlaskForm):
  fiche_file = FileField("Fiche de paie", validators=[
        FileRequired(message='Sélectionner un fichier.'),
        FileAllowed(['pdf'], 'Seulement des Documents PDF/DOCX sont autorisés !')
    ])
  contract_file = FileField("Contrat de travail", validators=[
        FileRequired(message='Sélectionner un fichier.'),
        FileAllowed(['docx', 'pdf'], 'Seulement des Documents PDF/DOCX sont autorisés !')
    ])
  nombre_heure = IntegerField("Nombre d'heure de travail", validators=[DataRequired()])
  submit = SubmitField("Lancer analyse")