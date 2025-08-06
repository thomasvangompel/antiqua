from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Vul hier je admingegevens in
    username = "admin"
    email = "admin@example.com"
    wachtwoord = "supergeheim123"  # pas aan naar iets sterks
    gehashed_wachtwoord = generate_password_hash(wachtwoord)

    # Check of admin al bestaat
    bestaande_user = User.query.filter_by(email=email).first()
    if bestaande_user:
        print("❌ Admin bestaat al.")
    else:
        admin = User(
            username=username,
            email=email,
            password=gehashed_wachtwoord,
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin aangemaakt.")
