def send_appointment_email(recipient, buyer_name, buyer_email, book_title, date, time, message_url):
    subject = f'Nieuwe afspraak voor {book_title}'
    body = f"{buyer_name} ({buyer_email}) wil een afspraak maken voor '{book_title}' op {date} om {time}. Bekijk het bericht: {message_url}"
    html = f"""
    <html>
      <body style='font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 20px;'>
        <div style='max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px;'>
          <h2 style='color: #2c3e50;'>Nieuwe afspraakverzoek</h2>
          <p><strong>Koper:</strong> {buyer_name} ({buyer_email})</p>
          <p><strong>Boek:</strong> {book_title}</p>
          <p><strong>Datum:</strong> {date}</p>
          <p><strong>Tijd:</strong> {time}</p>
          <p><a href='{message_url}' style='color: #060680; font-weight: bold;'>Bekijk het bericht in je dashboard</a></p>
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
