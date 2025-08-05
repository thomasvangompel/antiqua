from app import create_app, db
from app.models import User, Book, Tag, Bid, Message

app = create_app()

with app.app_context():
    User.query.delete()
    db.session.commit()  # <-- commit is noodzakelijk
    print("Alle users verwijderd.")
