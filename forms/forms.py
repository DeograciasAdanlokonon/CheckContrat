from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, HiddenField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired


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


# ToDo: ContractForm
class ContractForm(FlaskForm):
  contract_file = FileField("Contrat de travail", validators=[
        FileRequired(message='Sélectionner un fichier.'),
        FileAllowed(['docx', 'pdf'], 'Documents !')
    ])
  submit = SubmitField('Lancer analyse')


# ToDo: FicheContract
class FicheContract(FlaskForm):
  fiche_file = FileField("Fiche de paie", validators=[
        FileRequired(message='Sélectionner un fichier.'),
        FileAllowed(['pdf'], 'Seulement des Documents PDF/DOCX !')
    ])
  contract_file = FileField("Contrat de travail", validators=[
        FileRequired(message='Sélectionner un fichier.'),
        FileAllowed(['docx', 'pdf'], 'Seulement des Documents PDF/DOCX !')
    ])
  nombre_heure = IntegerField("Nombre d'heure de travail", validators=[DataRequired()])
  submit = SubmitField("Lancer analyse")