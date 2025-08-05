from flask_mail import Message
from flask import current_app
from app import mail  # jouw app package

def send_email(subject, recipient, code):
    # Plain text fallback
    body = f"Je verificatiecode is: {code}"
    
    # HTML content met een simpele stijl
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px;">
          <h2 style="color: #2c3e50;">Je verificatiecode</h2>
          <p>Gebruik onderstaande code om je account te verifiëren:</p>
          <p style="font-size: 24px; font-weight: bold; background-color: #ecf0f1; padding: 10px; border-radius: 5px; display: inline-block;">{code}</p>
          <p>Bedankt voor het gebruiken van onze service!</p>
        </div>
      </body>
    </html>
    """

    msg = Message(
        subject=subject,
        recipients=[recipient],
        body=body,
        html=html,
        sender=current_app.config['MAIL_USERNAME']
    )
    mail.send(msg)
