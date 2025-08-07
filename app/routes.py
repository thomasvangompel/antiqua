import os
import secrets
from PIL import Image
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    current_app, session, abort
)
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from geopy.geocoders import Nominatim

from . import db
from .forms import RegisterForm, LoginForm, BookForm, UpdateProfileForm,MessageForm
from .models import User, Book, Tag, Message,BookView
from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from .utils import send_email 
from flask import session
import google_auth_oauthlib.flow
import requests
import json
from flask import jsonify
from datetime import timedelta
from app.forms import ShippingForm  # pas 'app' aan naar jouw projectnaam indien nodig
from app.forms import PostcardForm
from app.models import Postcard




client_secrets = os.getenv("GOOGLE_OAUTH_SECRETS")


main = Blueprint('main', __name__)
geolocator = Nominatim(user_agent="boekenzot")


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@main.app_context_processor
def inject_new_message_count():
    new_message_count = 0
    if current_user.is_authenticated:
        new_message_count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
    return dict(new_message_count=new_message_count)


@main.route('/')
def home():
    verkopers_met_boeken_of_postkaarten = (
        User.query
        .filter(
            or_(User.books.any(), User.postcards.any()),  # minstens één boek OF postkaart
            User.latitude.isnot(None),
            User.longitude.isnot(None),
            User.business_name.isnot(None),
            User.show_on_map == True
        )
        .all()
    )

    return render_template("home.html", verkopers=verkopers_met_boeken_of_postkaarten)




from flask import session

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'POST':
        print("POST ontvangen")
        print("Form data:", request.form)

        if form.validate_on_submit():
            print("Form validatie geslaagd")

            # Check of email al bestaat
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash('Dit e-mailadres is al geregistreerd.', 'danger')
                return redirect(url_for('main.register'))

            # Maak gebruiker aan zonder username, city, business_name
            user = User(
                email=form.email.data,
                is_active=False
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            import random
            code = str(random.randint(100000, 999999))
            session['verification_code'] = code
            session['user_id'] = user.id

            send_email('Je verificatiecode', user.email, code)

            flash('Registratie gelukt! Check je mail voor de verificatiecode.')
            return redirect(url_for('main.verify'))
        else:
            print("Form validatie gefaald")
            print("Fouten:", form.errors)
            flash('Er zijn fouten in het formulier, controleer aub.')

    else:
        print("GET request ontvangen")

    return render_template('register.html', form=form)






from urllib.parse import urlparse, urljoin
def is_safe_url(target):
    """
    Controleer of de URL veilig is voor redirects.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    next_page = request.args.get('next')

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.password and check_password_hash(user.password, form.password.data):
            login_user(user)

            # Admin check
            if user.is_admin:
                return redirect(url_for('main.admin_dashboard'))

            # Redirect naar veilige next pagina of dashboard
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))

        flash('Inloggegevens onjuist', 'danger')

    return render_template('login.html', form=form)




@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Je bent succesvol uitgelogd.', 'success')
    return redirect(url_for('main.home'))



@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        # Redirect admin naar admin_dashboard
        return redirect(url_for('main.admin_dashboard'))
    
    # Voor gewone gebruikers: toon hun boeken, postkaarten en ongelezen berichten
    boeken = Book.query.filter_by(user_id=current_user.id).all()
    postkaarten = Postcard.query.filter_by(user_id=current_user.id).all()
    new_message_count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
    
    return render_template(
        'dashboard.html', 
        user=current_user, 
        boeken=boeken, 
        postkaarten=postkaarten, 
        new_message_count=new_message_count
    )



@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()

    if form.validate_on_submit():
        # Check business_name uniqueness als die gewijzigd is
        if form.business_name.data != current_user.business_name:
            existing_business = User.query.filter_by(business_name=form.business_name.data).first()
            if existing_business:
                flash('Deze winkelnaam is al in gebruik. Kies een andere.', 'danger')
                return redirect(url_for('main.profile'))

        if form.image.data:
            old_image = current_user.image_file
            if old_image != 'default.jpg':
                old_path = os.path.join(current_app.root_path, 'static/profile_pics', old_image)
                if os.path.exists(old_path):
                    os.remove(old_path)

            picture_file = save_picture(form.image.data)
            current_user.image_file = picture_file

        # Update overige velden
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.business_name = form.business_name.data
        current_user.street = form.street.data
        current_user.house_number = form.house_number.data
        current_user.postal_code = form.postal_code.data
        current_user.city = form.city.data
        current_user.show_on_map = form.show_on_map.data

        # Geocode adres
        full_address = f"{form.street.data} {form.house_number.data}, {form.postal_code.data} {form.city.data}, België"
        location = geolocator.geocode(full_address)

        if not location:
            flash('Adres niet gevonden. Controleer je invoer.', 'danger')
            return redirect(url_for('main.profile'))

        current_user.latitude = location.latitude
        current_user.longitude = location.longitude

        db.session.commit()
        flash('Je profiel is bijgewerkt!', 'success')
        return redirect(url_for('main.profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.business_name.data = current_user.business_name
        form.street.data = current_user.street
        form.house_number.data = current_user.house_number
        form.postal_code.data = current_user.postal_code
        form.city.data = current_user.city
        form.show_on_map.data = current_user.show_on_map

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html', title='Profiel', image_file=image_file, form=form)






# Eventueel blijven staan:
def parse_tags(tag_string):
    tags_raw = [tag.strip().lower() for tag in tag_string.split(',') if tag.strip()]
    return list(set(tags_raw[:5]))  # max 5 unieke tags


from genereer_beschrijving import generate_description
from genereer_auteur_beschrijving import generate_author_description


def parse_tags(tag_string):
    tags_raw = [tag.strip().lower() for tag in tag_string.split(',') if tag.strip()]
    return list(set(tags_raw[:5]))  # max 5 unieke tags

from genereer_beschrijving import generate_description
from genereer_genre_en_tags import generate_genre_and_tags
from genereer_auteur_beschrijving import generate_author_description



@main.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Toegang geweigerd.', 'danger')
        return redirect(url_for('main.dashboard'))

    page_users = request.args.get('page_users', 1, type=int)
    page_books = request.args.get('page_books', 1, type=int)

    users = User.query.filter_by(is_admin=False).order_by(User.id).paginate(page=page_users, per_page=10)
    books = Book.query.order_by(Book.id).paginate(page=page_books, per_page=10)

    return render_template('admin_dashboard.html', users=users, books=books)




@main.route('/admin/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_book_admin(book_id):
    boek = Book.query.get_or_404(book_id)
    db.session.delete(boek)
    db.session.commit()
    flash("Boek succesvol verwijderd.", "success")
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Alleen admins mogen dit
    if not current_user.is_admin:
        abort(403)  # Geen toegang

    user = User.query.get_or_404(user_id)

    # Extra beveiliging: Admin mag zichzelf niet verwijderen
    if user.id == current_user.id:
        flash('Je kunt jezelf niet verwijderen.', 'warning')
        return redirect(url_for('main.admin_dashboard'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Gebruiker "{user.username}" is verwijderd.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/books/new', methods=['GET', 'POST'])
@login_required
def new_book():
    # Controle: eerst winkelnaam ingevuld?
    if not current_user.business_name:
        flash('Je moet eerst je profiel bijwerken en een winkelnaam invoeren voordat je een boek kunt toevoegen.', 'warning')
        return redirect(url_for('main.profile'))  # Pas aan naar jouw profiel bewerken route

    form = BookForm()

    if form.validate_on_submit():
        # Upload-map aanmaken als die nog niet bestaat
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)

        def save_image(image_field):
            if image_field.data:
                filename = secure_filename(image_field.data.filename)
                image_path = os.path.join(upload_folder, filename)
                image_field.data.save(image_path)
                return filename
            return None

        # Afbeeldingen opslaan
        front_filename = save_image(form.front_image)
        side_filename = save_image(form.side_image)
        back_filename = save_image(form.back_image)

        # Beschrijving, genre en tags via AI genereren
        description = generate_description(form.title.data, form.genre.data)
        genre, tag_list = generate_genre_and_tags(form.title.data, form.author.data)

        # AI auteur-beschrijving genereren
        author_description = generate_author_description(form.author.data)

        # Veiling-einddatum berekenen als veiling actief is
        auction_end = (
            datetime.utcnow() + timedelta(days=form.auction_days.data)
            if form.is_auction.data and form.auction_days.data
            else None
        )

        # Boekobject aanmaken
        book = Book(
            title=form.title.data,
            author=form.author.data,
            description=description,
            genre=genre,
            price=form.price.data if not form.is_auction.data else None,
            is_auction=form.is_auction.data,
            auction_min_price=form.auction_min.data if form.is_auction.data else None,
            auction_end=auction_end,
            user_id=current_user.id,
            front_image=front_filename,
            side_image=side_filename,
            back_image=back_filename,
            author_description=author_description
        )

        # Tags verwerken op basis van AI-output
        for name in tag_list:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.flush()  # Zorgt dat ID direct beschikbaar is
            if tag not in book.tags:
                book.tags.append(tag)

        db.session.add(book)
        db.session.commit()

        flash('Boek succesvol toegevoegd!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('new_book.html', form=form)



@main.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.user_id != current_user.id:
        flash('Je hebt geen toestemming om dit boek te bewerken.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = BookForm(obj=book)

    if form.validate_on_submit():
        book.title = form.title.data
        book.author = form.author.data
        book.description = form.description.data
        book.genre = form.genre.data
        book.price = form.price.data
        book.author_description = form.author_description.data   # <--- toevoegen

        book.tags.clear()
        tag_names = parse_tags(form.tags.data)
        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)
            book.tags.append(tag)

        db.session.commit()
        flash('Boek succesvol bijgewerkt!', 'success')
        return redirect(url_for('main.dashboard'))

    elif request.method == 'GET':
        form.tags.data = ', '.join([tag.name for tag in book.tags])
        form.price.data = book.price
        form.author_description.data = book.author_description    # <--- toevoegen

    return render_template('edit_book.html', form=form, book=book)



@main.route('/books/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.user_id != current_user.id:
        flash('Je hebt geen toestemming om dit boek te verwijderen.', 'danger')
        return redirect(url_for('main.dashboard'))

    db.session.delete(book)
    db.session.commit()
    flash('Boek verwijderd!', 'success')
    return redirect(url_for('main.dashboard'))


@main.route('/view_books/<int:user_id>')
@login_required
def view_books(user_id):
    session[f'allowed_to_view_books_{user_id}'] = True
    return redirect(url_for('main.user_books', user_id=user_id))


@main.route('/user/<int:user_id>/books')
@login_required
def user_books(user_id):
    if not session.pop(f'allowed_to_view_books_{user_id}', False):
        abort(403)

    page = request.args.get('page', 1, type=int)
    user = User.query.get_or_404(user_id)
    books_paginated = Book.query.filter_by(user_id=user.id).paginate(page=page, per_page=12)

    return render_template('user_books.html', user=user, books=books_paginated)



from datetime import datetime
from .models import Book, Bid
from .forms import BidForm


from flask import request

from flask import request

@main.route('/books/<int:book_id>', methods=['GET', 'POST'])
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    
    # NIEUWE BOOKVIEW TOEVOEGEN
    new_view = BookView(book_id=book.id)
    db.session.add(new_view)
    
    # UPDATE view_count (optioneel, voor snelle access)
    book.view_count = (book.view_count or 0) + 1
    
    db.session.commit()

    auction_open = book.is_auction and book.auction_end and book.auction_end > datetime.utcnow()
    seller = book.user  # verkoper van het boek

    highest_bid = max(book.bids, key=lambda b: b.amount) if book.bids else None

    user_bids = [b for b in book.bids if b.bidder_id == current_user.id]
    user_highest_bid = max(user_bids, key=lambda b: b.amount) if user_bids else None

    base_minimum = float(book.auction_min_price or 0)
    
    if user_highest_bid and highest_bid and user_highest_bid.amount == highest_bid.amount:
        min_bid = float(user_highest_bid.amount) + 1
    elif highest_bid:
        min_bid = float(highest_bid.amount) + 5
    else:
        min_bid = base_minimum

    bid_form = BidForm()

    page = request.args.get('page', 1, type=int)
    bids = Bid.query.filter_by(book_id=book.id).order_by(Bid.amount.desc()).paginate(page=page, per_page=5)

    if bid_form.validate_on_submit():
        if not auction_open:
            flash('De veiling is gesloten.', 'warning')
            return redirect(url_for('main.book_detail', book_id=book.id))

        nieuwe_bod = float(bid_form.amount.data)

        if nieuwe_bod < min_bid:
            flash(f'Je bod moet minimaal €{min_bid:.2f} zijn.', 'danger')
            return redirect(url_for('main.book_detail', book_id=book.id))

        andere_bods = [b.amount for b in book.bids if b.bidder_id != current_user.id]
        hoogste_andere_bod = max(andere_bods) if andere_bods else 0

        if user_highest_bid and highest_bid and user_highest_bid.amount == highest_bid.amount:
            flash('Je hebt al het hoogste bod en kunt niet nog een hoger bod plaatsen.', 'danger')
            return redirect(url_for('main.book_detail', book_id=book.id))

        if hoogste_andere_bod > 0 and nieuwe_bod < hoogste_andere_bod + 5:
            flash(f'Je bod moet minimaal €{hoogste_andere_bod + 5:.2f} zijn.', 'danger')
            return redirect(url_for('main.book_detail', book_id=book.id))

        bid = Bid(amount=nieuwe_bod, bidder_id=current_user.id, book_id=book.id)
        db.session.add(bid)
        db.session.commit()

        flash('Je bod is geplaatst!', 'success')
        return redirect(url_for('main.book_detail', book_id=book.id))

    return render_template(
        'book_detail.html',
        book=book,
        auction_open=auction_open,
        highest_bid=highest_bid,
        bid_form=bid_form,
        bids=bids,
        min_bid=min_bid,
        seller=seller
    )

from sqlalchemy import func, extract
from datetime import datetime, timedelta

@main.route('/books/<int:book_id>/analytics')
def book_analytics(book_id):
    book = Book.query.get_or_404(book_id)

    # Views per dag voor de afgelopen 7 dagen
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    views_per_day = (
        db.session.query(
            func.date(BookView.timestamp).label('day'),
            func.count(BookView.id).label('count')
        )
        .filter(BookView.book_id == book.id)
        .filter(BookView.timestamp >= seven_days_ago)
        .group_by(func.date(BookView.timestamp))
        .order_by(func.date(BookView.timestamp))
        .all()
    )
    
    # Views per uur vandaag (middernacht tot nu)
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    views_per_hour = (
        db.session.query(
            extract('hour', BookView.timestamp).label('hour'),
            func.count(BookView.id).label('count')
        )
        .filter(BookView.book_id == book.id)
        .filter(BookView.timestamp >= today)
        .filter(BookView.timestamp < tomorrow)
        .group_by(extract('hour', BookView.timestamp))
        .order_by(extract('hour', BookView.timestamp))
        .all()
    )
    
    # Omzetten naar dict voor makkelijker gebruik in JS/templates
    views_per_day_dict = {str(day): count for day, count in views_per_day}
    views_per_hour_dict = {int(hour): count for hour, count in views_per_hour}

    return render_template('book_analytics.html',
                           book=book,
                           views_per_day=views_per_day_dict,
                           views_per_hour=views_per_hour_dict)



import mollie.api.client
mollie_client = mollie.api.client.Client()
from mollie.api.client import Client
from flask import current_app, url_for, redirect

@main.route('/books/<int:book_id>/buy')
@login_required
def buy_book(book_id):
    book = Book.query.get_or_404(book_id)

    if book.is_auction:
        flash('Dit boek is alleen via veiling te koop.', 'warning')
        return redirect(url_for('main.book_detail', book_id=book_id))

    mollie_client = Client()
    mollie_client.set_api_key(current_app.config['MOLLIE_API_KEY'])

    base_url = current_app.config['BASE_URL']

    payment = mollie_client.payments.create({
        'amount': {
            'currency': 'EUR',
            'value': f'{book.price:.2f}',
        },
        'description': f'Aankoop van boek: {book.title}',
        'redirectUrl': f'{base_url}{url_for("main.payment_done", book_id=book.id)}',
        'webhookUrl': f'{base_url}{url_for("main.payment_webhook")}',
        'metadata': {
            'book_id': book.id,
            'seller_id': book.user_id
        }
    })

    return redirect(payment.checkout_url)




@main.route('/payment/done')
@login_required
def payment_done():
    
    book_id = request.args.get('book_id')
    # Hier kun je bv. een bedankpagina tonen of bestelling afronden
    flash('Bedankt voor je aankoop!', 'success')
    return redirect(url_for('main.book_detail', book_id=book_id,just_paid=1))

from flask import request, current_app
from mollie.api.client import Client
from app import db  # Pas dit eventueel aan naar je echte app-import
from app.models import Book  # Pas dit aan naar je projectstructuur

@main.route('/payment/webhook', methods=['POST'])
def payment_webhook():
    mollie_client = Client()
    mollie_client.set_api_key(current_app.config['MOLLIE_API_KEY'])

    payment_id = request.form.get('id')
    if not payment_id:
        return 'No payment ID provided', 400

    try:
        payment = mollie_client.payments.get(payment_id)
    except Exception:
        return 'Payment not found or API error', 400

    if payment.is_paid():
        metadata = payment.metadata
        book_id = metadata.get('book_id')
        buyer_id = metadata.get('user_id')

        if not book_id or not buyer_id:
            return 'Missing metadata', 400

        book = Book.query.get(book_id)
        if not book:
            return 'Book not found', 404

        if not book.buyer_id:
            book.sold = True
            book.buyer_id = buyer_id
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                return 'Database error', 500

    return '', 200






from sqlalchemy import or_

@main.route('/search')
def search():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)

    users = []
    books = []
    postkaarten = []

    if query:
        # Zoek gebruikers
        users = User.query.filter(
            or_(
                User.city.ilike(f'%{query}%'),
                User.username.ilike(f'%{query}%'),
                User.business_name.ilike(f'%{query}%')
            )
        ).all()

        # Zoek boeken met join op tags en user
        books = Book.query \
            .join(Book.tags, isouter=True) \
            .join(User, Book.user_id == User.id) \
            .filter(
                or_(
                    Book.title.ilike(f'%{query}%'),
                    Book.author.ilike(f'%{query}%'),
                    Book.description.ilike(f'%{query}%'),
                    Book.genre.ilike(f'%{query}%'),
                    Tag.name.ilike(f'%{query}%'),
                    User.username.ilike(f'%{query}%'),
                    User.business_name.ilike(f'%{query}%')
                )
            ) \
            .distinct() \
            .paginate(page=page, per_page=12)

        # Zoek postkaarten ook met paginatie
        postkaarten = Postcard.query.filter(
            or_(
                Postcard.title.ilike(f'%{query}%'),
                Postcard.publisher.ilike(f'%{query}%'),
                Postcard.description.ilike(f'%{query}%'),
            )
        ).paginate(page=page, per_page=12)

    return render_template('search_results.html', query=query, users=users, books=books, postcards=postkaarten)



@main.route('/<business_name>')
def books_by_business_name(business_name):
    user = User.query.filter_by(business_name=business_name).first_or_404()
    page = request.args.get('page', 1, type=int)
    books = Book.query.filter_by(user_id=user.id).paginate(page=page, per_page=12)
    return render_template('user_books.html', user=user, books=books)


@main.route('/verkoper_id/<int:user_id>')
def redirect_seller_by_id(user_id):
    seller = User.query.get_or_404(user_id)
    return redirect(url_for('main.public_seller_profile',
                            business_name=seller.business_name or seller.username))


from sqlalchemy.sql import func

@main.route('/verkoper/<business_name>')
def public_seller_profile(business_name):
    page = request.args.get('page', 1, type=int)
    seller = User.query.filter_by(business_name=business_name).first_or_404()

    books_pagination = Book.query.filter_by(user_id=seller.id).paginate(page=page, per_page=10)
    books = books_pagination.items

    # Hoogste bod per boek ophalen
    highest_bids = {
        book.id: db.session.query(func.max(Bid.amount))
                           .filter(Bid.book_id == book.id)
                           .scalar()
        for book in books
    }

    total_sold = sum(book.sold_count or 0 for book in Book.query.filter_by(user_id=seller.id).all())
    genres = list({book.genre for book in Book.query.filter_by(user_id=seller.id).all() if book.genre})

    tag_set = set()
    for book in Book.query.filter_by(user_id=seller.id).all():
        tag_set.update(book.tags)
    tags = list(tag_set)

    return render_template(
        'public_seller_profile.html',
        seller=seller,
        total_sold=total_sold,
        genres=genres,
        tags=tags,
        books=books,
        highest_bids=highest_bids,
        pagination=books_pagination
    )



@main.route('/verkoper/<business_name>/genre/<genre>')
def seller_books_by_genre(business_name, genre):
    seller = User.query.filter_by(business_name=business_name).first_or_404()
    books = Book.query.filter_by(user_id=seller.id, genre=genre).all()
    return render_template('seller_books_by_filter.html', seller=seller, books=books, filter_type='Genre', filter_value=genre)


@main.route('/verkoper/<business_name>/tag/<tag_name>')
def seller_books_by_tag(business_name, tag_name):
    seller = User.query.filter_by(business_name=business_name).first_or_404()
    books = Book.query.filter(Book.user_id == seller.id).join(Book.tags).filter(Tag.name == tag_name).all()
    return render_template('seller_books_by_filter.html', seller=seller, books=books, filter_type='Tag', filter_value=tag_name)


# Bericht sturen naar verkoper
@main.route('/verkoper/<business_name>/contact', methods=['GET', 'POST'])
@login_required
def contact_seller(business_name):
    seller = User.query.filter_by(business_name=business_name).first_or_404()

    if seller.id == current_user.id:
        flash("Je kunt jezelf geen bericht sturen.", "warning")
        return redirect(url_for('main.public_seller_profile', business_name=business_name))

    form = MessageForm()
    if form.validate_on_submit():
        nieuw_bericht = Message(
            sender_id=current_user.id,
            receiver_id=seller.id,
            content=form.content.data,
            read=False,
            timestamp=datetime.utcnow()
        )
        db.session.add(nieuw_bericht)
        db.session.commit()
        flash('Bericht succesvol verstuurd!', 'success')
        return redirect(url_for('main.public_seller_profile', business_name=business_name))

    return render_template('contact_seller.html', seller=seller, form=form)


@main.route('/messages')
@login_required
def messages():
    ontvangen = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    verzonden = Message.query.filter_by(sender_id=current_user.id).order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', ontvangen=ontvangen, verzonden=verzonden)


@main.route('/messages/<int:message_id>/read', methods=['GET'])
@login_required
def read_message(message_id):
    bericht = Message.query.get_or_404(message_id)
    if bericht.receiver_id != current_user.id:
        abort(403)
    bericht.read = True
    db.session.commit()
    flash('Bericht gemarkeerd als gelezen.', 'success')
    return redirect(url_for('main.messages'))


@main.route('/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.receiver_id != current_user.id and message.sender_id != current_user.id:
        abort(403)
    db.session.delete(message)
    db.session.commit()
    flash('Bericht verwijderd.', 'success')
    return redirect(url_for('main.messages'))


class ReplyForm(FlaskForm):
    reply = TextAreaField('Antwoord', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Verstuur')


@main.route('/messages/<int:message_id>/reply', methods=['GET', 'POST'])
@login_required
def reply_message(message_id):
    original = Message.query.get_or_404(message_id)
    if original.receiver_id != current_user.id and original.sender_id != current_user.id:
        abort(403)

    form = ReplyForm()
    if form.validate_on_submit():
        # Bepaal wie de ontvanger is voor het antwoord
        if original.receiver_id == current_user.id:
            ontvanger_id = original.sender_id
        else:
            ontvanger_id = original.receiver_id

        new_msg = Message(
            sender_id=current_user.id,
            receiver_id=ontvanger_id,
            content=form.reply.data,
            read=False,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_msg)
        db.session.commit()
        flash('Je antwoord is verstuurd.', 'success')
        return redirect(url_for('main.messages'))

    return render_template('reply_message.html', original=original, form=form)


@main.route('/messages/<int:message_id>/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.receiver_id != current_user.id and message.sender_id != current_user.id:
        abort(403)

    message.is_favorite = not message.is_favorite
    db.session.commit()

    return redirect(url_for('main.messages'))





from flask import request, flash

@main.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        code_input = request.form.get('code')
        if code_input == session.get('verification_code'):
            user = User.query.get(session.get('user_id'))
            if user:
                user.is_active = True
                db.session.commit()
                flash('Account geverifieerd! Je kunt nu inloggen.', 'success')
                return redirect(url_for('main.login'))
            else:
                flash('Gebruiker niet gevonden.', 'danger')
        else:
            flash('Verificatiecode is incorrect.', 'danger')

    return render_template('verify.html')




from flask import render_template
from app.models import User

@main.route('/map')
def map_view():
    # Bijvoorbeeld alle users met een business_name en lat/lon
    verkopers = User.query.filter(
        User.latitude.isnot(None),
        User.longitude.isnot(None),
        User.business_name.isnot(None)
    ).all()

    return render_template('map.html', verkopers=verkopers)




oauth_config = json.loads(client_secrets)
@main.route('/signin')
def signin():
    next_page = request.args.get('next')
    if next_page:
        session['next'] = next_page  # Bewaar waar we naartoe willen

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        oauth_config,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]
    )
    flow.redirect_uri = url_for('main.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)


from urllib.parse import urlparse

@main.route('/oauth2callback')
def oauth2callback():
    if session.get('state') != request.args.get('state'):
        flash('Ongeldige login state', 'danger')
        return redirect(url_for('main.login'))

    oauth_config = json.loads(os.getenv('GOOGLE_OAUTH_SECRETS'))
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        oauth_config,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        state=session['state']
    )
    flow.redirect_uri = url_for('main.oauth2callback', _external=True)
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    access_token = credentials.token

    response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if response.status_code != 200:
        flash('Google login mislukt', 'danger')
        return redirect(url_for('main.login'))

    user_info = response.json()
    email = user_info.get("email")
    name = user_info.get("given_name", "Gebruiker")

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, password=None)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash(f"Ingelogd als {email}", "success")

    next_page = session.pop('next', None)
    if next_page and urlparse(next_page).netloc == '':
        return redirect(next_page)

    return redirect(url_for('main.dashboard'))


def get_mollie_client():
    client = mollie.api.client.Client()
    client.set_api_key(current_app.config["MOLLIE_API_KEY"])
    return client

@main.route('/checkout/<string:item_type>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def checkout(item_type, item_id):
    mollie_client = get_mollie_client()

    if item_type == 'book':
        item = Book.query.get_or_404(item_id)
        description = f"Aankoop van boek: {item.title}"
    elif item_type == 'postcard':
        item = Postcard.query.get_or_404(item_id)
        description = f"Aankoop van postkaart: {item.title}"
    else:
        abort(404)

    seller = item.user

    if request.method == 'POST':
        selected_method = request.form.get("method")
        comment = request.form.get("comment")

        payment = mollie_client.payments.create({
            "amount": {
                "currency": "EUR",
                "value": f"{item.price:.2f}"
            },
            "description": description,
            "redirectUrl": url_for("main.payment_done", item_type=item_type, item_id=item.id, _external=True),
            "webhookUrl": "https://e8dc1f0c0d05.ngrok-free.app/payment/webhook",
            "metadata": {
                "item_type": item_type,
                "item_id": item.id,
                "user_id": current_user.id,
                "comment": comment
            },
            "method": selected_method or None
        })

        return redirect(payment.checkout_url)

    return render_template("checkout.html", item=item, seller=seller, item_type=item_type)


@main.route('/verzendgegevens', methods=['GET', 'POST'])
@login_required
def verzendgegevens():
    form = ShippingForm()

    if form.validate_on_submit():
        current_user.allow_shipping = form.allow_shipping.data
        current_user.shipping_cost = form.shipping_cost.data
        current_user.pickup_only = form.pickup_only.data
        current_user.platform_payment_only = form.platform_payment_only.data
        # Let op: in je model is er geen 'cash_payment_allowed', dus die mag je weghalen of toevoegen aan het model als je die nodig hebt

        db.session.commit()

        flash("Verzendgegevens succesvol opgeslagen.", "success")
        return redirect(url_for('main.dashboard'))

    if request.method == 'GET':
        form.allow_shipping.data = current_user.allow_shipping
        form.shipping_cost.data = current_user.shipping_cost
        form.pickup_only.data = current_user.pickup_only
        form.platform_payment_only.data = current_user.platform_payment_only

    return render_template('verzendgegevens.html', form=form)




import os
from flask import current_app
from werkzeug.utils import secure_filename
from datetime import datetime

@main.route('/postcards/add', methods=['GET', 'POST'])
@login_required
def add_postcard():
    form = PostcardForm()
    if form.validate_on_submit():
        postcard = Postcard(
            title=form.title.data,
            publisher=form.publisher.data,
            auction_end=form.auction_end.data,
            condition=form.condition.data,
            description=form.description.data,
            price=form.price.data,
            is_auction=form.is_auction.data,
            auction_min_price=form.auction_min_price.data,
            sold=form.sold.data,
            user_id=current_user.id
        )
        
        # Afbeelding uploaden en opslaan
        if form.front_image.data:
            front_filename = secure_filename(form.front_image.data.filename)
            front_path = os.path.join(current_app.root_path, 'static/uploads', front_filename)
            form.front_image.data.save(front_path)
            postcard.front_image_url = 'uploads/' + front_filename

        if form.back_image.data:
            back_filename = secure_filename(form.back_image.data.filename)
            back_path = os.path.join(current_app.root_path, 'static/uploads', back_filename)
            form.back_image.data.save(back_path)
            postcard.back_image_url = 'uploads/' + back_filename

        db.session.add(postcard)
        db.session.commit()
        flash('Postkaart succesvol toegevoegd!', 'success')
        return redirect(url_for('main.dashboard'))

    
    return render_template('add_postcard.html', form=form)




@main.route('/postcards/edit/<int:postcard_id>', methods=['GET', 'POST'])
@login_required
def edit_postcard(postcard_id):
    postcard = Postcard.query.get_or_404(postcard_id)
    # Voeg hier je formulier en logica toe om postkaart te bewerken
    form = PostcardForm(obj=postcard)
    if form.validate_on_submit():
        postcard.title = form.title.data
        postcard.description = form.description.data
        postcard.condition = form.condition.data
        # enzovoorts
        db.session.commit()
        flash('Postkaart bijgewerkt!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('edit_postcard.html', form=form, postcard=postcard)



@main.route('/postcards/<int:postcard_id>/delete', methods=['POST'])
@login_required
def delete_postcard(postcard_id):
    postcard = Postcard.query.get_or_404(postcard_id)
    if postcard.user_id != current_user.id:
        abort(403)  # Niet toegestaan
    db.session.delete(postcard)
    db.session.commit()
    flash('Postkaart is verwijderd.', 'success')
    return redirect(url_for('main.dashboard'))



@main.route('/postcard/<int:postcard_id>')
def postcard_detail(postcard_id):
    postcard = Postcard.query.get_or_404(postcard_id)
    return render_template('postcard_detail.html', postcard=postcard)

