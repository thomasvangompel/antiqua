from app import create_app, db
from app.models import AppointmentSlot

app = create_app()

with app.app_context():
    slots = AppointmentSlot.query.all()
    count = len(slots)
    for slot in slots:
        db.session.delete(slot)
    db.session.commit()
    print(f"Verwijderd: {count} tijdslots.")