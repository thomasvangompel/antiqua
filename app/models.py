from . import db
from flask_login import UserMixin
from . import login_manager
from datetime import datetime
from flask import url_for
from sqlalchemy import Numeric

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Tussenliggende tabel voor Many-to-Many tussen boeken en tags
book_tags = db.Table(
    'book_tags',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=False, nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)
    image_file = db.Column(db.String(100), nullable=False, default='default.png')

    # Gesplitst adres
    street = db.Column(db.String(100), nullable=True)
    house_number = db.Column(db.String(10), nullable=True)
    postal_code = db.Column(db.String(10), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    show_on_map = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    business_name = db.Column(db.String(100), unique=True, nullable=True)

    # Relaties
    books = db.relationship('Book', back_populates='user', cascade='all, delete-orphan', passive_deletes=True, foreign_keys='Book.user_id')
    bought_books = db.relationship('Book', back_populates='buyer', passive_deletes=True, foreign_keys='Book.buyer_id')

    given_reviews = db.relationship('Review', back_populates='reviewer', cascade='all, delete-orphan', passive_deletes=True, foreign_keys='Review.user_id')
    received_reviews = db.relationship('Review', back_populates='seller', cascade='all, delete-orphan', passive_deletes=True, foreign_keys='Review.seller_id')

    sent_messages = db.relationship('Message', back_populates='sender', cascade='all, delete-orphan', passive_deletes=True, foreign_keys='Message.sender_id')
    received_messages = db.relationship('Message', back_populates='receiver', cascade='all, delete-orphan', passive_deletes=True, foreign_keys='Message.receiver_id')

    bids = db.relationship('Bid', back_populates='bidder', cascade='all, delete-orphan', passive_deletes=True, foreign_keys='Bid.bidder_id')

    # MFA en status
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_method = db.Column(db.String(20))
    mfa_secret = db.Column(db.String(32))
    mfa_code = db.Column(db.String(10), nullable=True)
    mfa_code_expiry = db.Column(db.DateTime, nullable=True)

    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column('is_active', db.Boolean, default=True, nullable=False)

    # Verzendinstellingen
    allow_shipping = db.Column(db.Boolean, default=False)
    shipping_cost = db.Column(db.Numeric(6, 2), nullable=True)
    pickup_only = db.Column(db.Boolean, default=False)
    platform_payment_only = db.Column(db.Boolean, default=True)
    cash_payment_only = db.Column(db.Boolean, default=True)

    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    author_description = db.Column(db.Text, nullable=True)
    genre = db.Column(db.String(100), nullable=True)

    price = db.Column(db.Numeric(10, 2))
    is_auction = db.Column(db.Boolean, default=False)
    auction_min_price = db.Column(db.Numeric(10, 2), nullable=True)
    auction_end = db.Column(db.DateTime, nullable=True)

    sold_count = db.Column(db.Integer, default=0)
    sold = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='books', foreign_keys=[user_id], passive_deletes=True)

    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    buyer = db.relationship('User', back_populates='bought_books', foreign_keys=[buyer_id], passive_deletes=True)

    tags = db.relationship('Tag', secondary='book_tags', back_populates='books', lazy='subquery')

    bids = db.relationship('Bid', back_populates='book', cascade='all, delete-orphan', passive_deletes=True)

    front_image = db.Column(db.String(150), nullable=True)
    side_image = db.Column(db.String(150), nullable=True)
    back_image = db.Column(db.String(150), nullable=True)

    @property
    def front_image_url(self):
        return url_for('static', filename=f'uploads/{self.front_image}') if self.front_image else None

    @property
    def side_image_url(self):
        return url_for('static', filename=f'uploads/{self.side_image}') if self.side_image else None

    @property
    def back_image_url(self):
        return url_for('static', filename=f'uploads/{self.back_image}') if self.back_image else None

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    books = db.relationship('Book', secondary='book_tags', back_populates='tags')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    reviewer = db.relationship('User', back_populates='given_reviews', foreign_keys=[user_id])
    seller = db.relationship('User', back_populates='received_reviews', foreign_keys=[seller_id])

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    is_favorite = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', back_populates='sent_messages', foreign_keys=[sender_id])
    receiver = db.relationship('User', back_populates='received_messages', foreign_keys=[receiver_id])

class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    bidder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

    bidder = db.relationship('User', back_populates='bids', foreign_keys=[bidder_id])
    book = db.relationship('Book', back_populates='bids')