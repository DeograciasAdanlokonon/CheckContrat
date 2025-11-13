from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from flask import current_app, url_for
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

APP_EMAIL = os.getenv('APP_MAIL')
APP_EMAIL_PASSWORD = os.getenv('APP_MAIL_PASSWORD')

def generate_confirmation_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
    except Exception:
        return None
    return email

def send_confirmation_email(user):
    token = generate_confirmation_token(user.email)
    confirm_url = url_for('confirm_email', token=token, _external=True)

    # Email content
    subject = "Confirmez votre email - CheckTonContrat"
    sender_email = APP_EMAIL
    receiver_email = user.email

    # Create the HTML version of your message
    html = f"""
    <html>
      <body>
        <p>Bonjour <strong>{user.username}</strong>,</p>
        <p>Merci pour votre inscription sur <strong>CheckTonContrat</strong> !<br>
        Veuillez confirmer votre adresse email en cliquant sur le lien ci-dessous :</p><br>
        <p><a href="{confirm_url}" style="background-color:#4CAF50;color:white;padding:10px 15px;text-decoration:none;border-radius:5px;">
          Confirmer mon email
        </a></p>
        <p>Ce lien expire dans 1 heure.</p>
        <hr>
        <p style="font-size:12px;color:#999;">Ceci est un email automatique — ne pas répondre.</p>
      </body>
    </html>
    """

    # Create a MIME message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # Attach the HTML part
    msg.attach(MIMEText(html, "html"))

    # Send email securely
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, APP_EMAIL_PASSWORD)
        server.send_message(msg)

    print(f"✅ Confirmation email sent to {receiver_email}")


def send_reset_email(to_email: str, token: str):
    """
    Send the password reset email to `to_email` including the reset link.
    Uses smtplib and the MAIL_* config values from Flask app config.
    """
     # Email content
    subject = "Confirmez votre email - CheckTonContrat"
    sender_email = APP_EMAIL
    receiver_email = to_email

    # Build reset URL (absolute)
    reset_url = url_for('reset_password', token=token, _external=True)

    subject = "Réinitialisation de votre mot de passe — CheckTonContrat"
    html = f"""
    <p>Bonjour,</p>
    <p>Nous avons reçu une demande de réinitialisation de mot de passe pour votre compte.</p>
    <p>Cliquez sur ce lien pour définir un nouveau mot de passe (valide 1 heure):</p>
    <p><a href="{reset_url}">Réinitialiser</a></p>
    <p>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>
    <p>L'équipe CheckTonContrat</p>
    """

    # Create a MIME message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # Attach the HTML part
    msg.attach(MIMEText(html, "html"))

    # Send email securely
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, APP_EMAIL_PASSWORD)
        server.send_message(msg)

    print(f"✅ Confirmation email sent to {receiver_email}")


def send_payment_success_email(user, module_type):
    """
    Envoie un email à l'utilisateur après un paiement Stripe réussi,
    l'informant que l'analyse est terminée et disponible sur son tableau de bord.
    """

    # Génère un lien vers le tableau de bord
    dashboard_url = url_for('dashboard', _external=True)

    # Sélection du texte selon le type d'analyse
    if module_type == 'contrat':
        analyse_type = "contrat de travail"
    elif module_type == 'fiche':
        analyse_type = "fiche"
    else:
        analyse_type = "document"

    # Sujet et contenu
    subject = f"Paiement confirmé - Votre analyse de {analyse_type} est prête"
    sender_email = APP_EMAIL
    receiver_email = user.email

    html = f"""
    <html>
      <body style="font-family:Arial,sans-serif;color:#333;">
        <p>Bonjour <strong>{user.username}</strong>,</p>
        <p>Nous vous confirmons que votre paiement Stripe a été effectué avec succès 🎉.</p>
        <p>Votre analyse de <strong>{analyse_type}</strong> est maintenant terminée et disponible sur votre tableau de bord.</p>
        <p>
          <a href="{dashboard_url}" 
             style="display:inline-block;background-color:#4CAF50;color:white;
                    padding:10px 18px;text-decoration:none;border-radius:6px;">
            Accéder à mon tableau de bord
          </a>
        </p>
        <p>Merci d’avoir utilisé <strong>CheckTonContrat</strong> !</p>
        <hr>
        <p style="font-size:12px;color:#888;">Ceci est un email automatique — merci de ne pas y répondre.</p>
      </body>
    </html>
    """

    # Création du message MIME
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.attach(MIMEText(html, "html"))

    # Envoi sécurisé via Gmail (ou ton SMTP)
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, APP_EMAIL_PASSWORD)
        server.send_message(msg)

    print(f"✅ Email de confirmation de paiement envoyé à {receiver_email}")


def send_contact_email(email, message):
    """
    Envoie un email à l'admin un message de contact envoyer 
    par un visiteur.
    """

    # Sujet et contenu
    subject = f"Un nouveau message de contact"
    sender_email = APP_EMAIL
    receiver_email = 'contact@checktoncontrat.fr'

    html = f"""
    <html>
      <body style="font-family:Arial,sans-serif;color:#333;">
        <h2>Un nouveau message de contact par un visiteur de votre site</h2>
        <p><strong>Email :</strong>{email}</p>
        <p><strong>Message : </strong>{message}</p>
        <hr>
        <p style="font-size:12px;color:#888;">Ceci est un email suite au remplissage du formulaire de contact</p>
      </body>
    </html>
    """

    # Création du message MIME
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.attach(MIMEText(html, "html"))

    # Envoi sécurisé via Gmail (ou ton SMTP)
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, APP_EMAIL_PASSWORD)
        server.send_message(msg)

    print("✅ Email de contact envoyé avec succès ! ")