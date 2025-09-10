from app import create_app, db
from app.models import User, Book, Tag, Bid, Message

app = create_app()

with app.app_context():
    for user in User.query.all():
        db.session.delete(user)
    db.session.commit()
    print("Alle users verwijderd.")