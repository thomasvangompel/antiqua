


from app.forms import ArtForm

from app.forms import ShopProfileForm

import os
from app.models import AppointmentSlot, User, Message, Book
from flask_mail import Message as MailMessage
from app import mail
from app.utils import send_appointment_email
import secrets
from PIL import Image

from flask_login import login_required, current_user


import os
from app.models import AppointmentSlot, User, Message, Book
from flask_mail import Message as MailMessage
from app import mail
from app.utils import send_appointment_email
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
from .forms import RegisterForm, LoginForm, BookForm, UpdateProfileForm,MessageForm,PosterForm
from .models import User, Book, Tag, Message, BookView, Postcard, Poster, CartItem

from .forms import RekForm
from .models import Rek, RekVerdieping


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


main = Blueprint('main', __name__)

client_secrets = os.getenv("GOOGLE_OAUTH_SECRETS")


@main.route('/art/<int:art_id>/delete', methods=['POST'])
@login_required
def delete_art(art_id):
    from app.models import Art
    art = Art.query.get_or_404(art_id)
    if art.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    from . import db
    db.session.delete(art)
    db.session.commit()
    flash('Kunstwerk verwijderd!', 'success')
    return redirect(url_for('main.dashboard'))


@main.route('/art/<int:art_id>/analytics')
@login_required
def art_analytics(art_id):
    from app.models import Art
    art = Art.query.get_or_404(art_id)
    if art.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    # Hier kun je analytics-data toevoegen, bijvoorbeeld views, biedingen, etc.
    # Voor nu tonen we alleen de basisinformatie
    return render_template('art_analytics.html', art=art)

@main.route('/art/<int:art_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_art(art_id):
    from app.models import Art
    art = Art.query.get_or_404(art_id)
    if art.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    from app.forms import ArtForm
    form = ArtForm(obj=art)
    if form.validate_on_submit():
        import bleach
        art.title = form.title.data
        art.artist = form.artist.data
        art.description = bleach.clean(form.description.data, tags=['b', 'i', 'u', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'span', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'], attributes={'a': ['href', 'target', 'rel'], 'span': ['style'], '*': ['style']}, strip=True)
        art.condition = form.condition.data
        if form.image.data:
            image_file = form.image.data
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', image_filename)
            image_file.save(image_path)
            art.image_url = image_filename
        art.price = form.price.data
        art.allow_shipping = form.allow_shipping.data
        art.shipping_cost = form.shipping_cost.data
        art.pickup_only = form.pickup_only.data
        art.platform_payment_only = form.platform_payment_only.data
        art.cash_payment_only = form.cash_payment_only.data
        art.is_auction = form.is_auction.data
        art.auction_min_price = form.auction_min_price.data if form.is_auction.data else None
        auction_end_value = None
        if form.is_auction.data and form.auction_end.data:
            try:
                from datetime import datetime
                auction_end_value = datetime.strptime(form.auction_end.data, "%Y-%m-%d %H:%M")
            except Exception:
                auction_end_value = None
        art.auction_end = auction_end_value
        from . import db
        db.session.commit()
        flash('Kunstwerk bijgewerkt!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_art.html', form=form, edit=True, art=art)




@main.route('/art/add', methods=['GET', 'POST'])
@login_required
def add_art():
    from app.models import Art
    form = ArtForm()
    if form.validate_on_submit():
        import bleach
        image_filename = None
        if form.image.data:
            image_file = form.image.data
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', image_filename)
            image_file.save(image_path)
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'span', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attrs = {'a': ['href', 'target', 'rel'], 'span': ['style'], '*': ['style']}
        # Auction end: alleen als veiling actief is en veld ingevuld
        auction_end_value = None
        if form.is_auction.data and form.auction_end.data:
            try:
                from datetime import datetime
                auction_end_value = datetime.strptime(form.auction_end.data, "%Y-%m-%d %H:%M")
            except Exception:
                auction_end_value = None
        art = Art(
            title=form.title.data,
            artist=form.artist.data,
            description=bleach.clean(form.description.data, tags=allowed_tags, attributes=allowed_attrs, strip=True),
            condition=form.condition.data,
            image_url=image_filename,
            price=form.price.data,
            allow_shipping=form.allow_shipping.data,
            shipping_cost=form.shipping_cost.data,
            pickup_only=form.pickup_only.data,
            platform_payment_only=form.platform_payment_only.data,
            cash_payment_only=form.cash_payment_only.data,
            is_auction=form.is_auction.data,
            auction_min_price=form.auction_min_price.data if form.is_auction.data else None,
            auction_end=auction_end_value,
            user_id=current_user.id
        )
        db.session.add(art)
        db.session.commit()
        flash('Kunstwerk toegevoegd!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_art.html', form=form)


@main.route('/verkoper/winkelprofiel/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_winkelprofiel(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id and not current_user.is_admin:
        abort(403)
    form = ShopProfileForm(obj=user)
    if form.validate_on_submit():
        import bleach
        user.hero_section_enabled = form.enable_hero.data
        if form.hero_image.data:
            image_file = form.hero_image.data
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            image_file.save(image_path)
            user.hero_section_image = filename
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'span', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attrs = {'a': ['href', 'target', 'rel'], 'span': ['style'], '*': ['style']}
        user.about_shop = bleach.clean(form.about_shop.data, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        user.contact_info = bleach.clean(form.contact_info.data, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        db.session.commit()
        flash('Winkelprofiel bijgewerkt!', 'success')
        return redirect(url_for('main.edit_winkelprofiel', user_id=user.id))
    return render_template('winkelprofiel.html', form=form, user=user)
from flask import Blueprint



# ... bestaande code ...
@main.route('/api/appointments/delete_all', methods=['POST'])
@login_required
def delete_all_appointments():
    from app.models import AppointmentSlot
    slots = AppointmentSlot.query.filter_by(user_id=current_user.id).all()
    count = len(slots)
    for slot in slots:
        db.session.delete(slot)
    db.session.commit()
    return jsonify({'status': 'success', 'deleted': count})

@main.route('/api/appointments/available/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_appointments_for_month(year, month):
    from app.models import AppointmentSlot
    # month is 1-based
    slots = AppointmentSlot.query.filter_by(user_id=current_user.id, month=month, year=year).all()
    result = [
        {
            'year': s.year,
            'month': s.month,
            'day': s.day,
            'time': s.time
        } for s in slots
    ]
    return jsonify(result)



@main.route('/new_category', methods=['GET', 'POST'])
@login_required
def new_category():
    form = CategoryForm()
    if form.validate_on_submit():
        from app.models import Category, db
        category = Category(name=form.name.data, user_id=current_user.id)
        db.session.add(category)
        db.session.commit()
        flash('Categorie toegevoegd!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('new_category.html', form=form)



# Afspraak wijzigen route
@main.route('/change_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def change_appointment(appointment_id):
    slot = AppointmentSlot.query.get_or_404(appointment_id)
    if slot.user_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        # Hier kun je logica toevoegen om het tijdslot te wijzigen
        # Bijvoorbeeld: slot.time = request.form['new_time']
        db.session.commit()
        flash('Afspraak succesvol gewijzigd.', 'success')
        return redirect(url_for('main.dashboard_basic'))
    return render_template('change_appointment.html', slot=slot)

# Verwijder afspraak route
@main.route('/delete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    slot = AppointmentSlot.query.get_or_404(appointment_id)
    if slot.user_id != current_user.id and slot.reserved_by_id != current_user.id:
        abort(403)
    db.session.delete(slot)
    db.session.commit()
    flash('Afspraak succesvol verwijderd.', 'success')
    return redirect(url_for('main.dashboard_basic'))




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
    from flask import Blueprint
    main = Blueprint('main', __name__)
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




# Functie om te checken of profiel compleet is
def profiel_is_ingevuld(user):
    def is_filled(val):
        if isinstance(val, str):
            return val is not None and val.strip() != ''
        if isinstance(val, (float, int)):
            return val is not None and val != 0
        return val is not None

    required_fields = [
        user.street,
        user.house_number,
        user.postal_code,
        user.city,
        user.latitude,
        user.longitude
    ]
    if user.account_type == 'pro':
        required_fields.append(user.business_name)
    return all(is_filled(f) for f in required_fields)

# Route voor de start met zoeken knop
@main.route('/start_search')
@login_required
def start_search():
    if profiel_is_ingevuld(current_user):
        return redirect(url_for('main.home'))
    else:
        # Debug: toon welke velden niet gevuld zijn
        missing = []
        def is_filled(val):
            if isinstance(val, str):
                return val is not None and val.strip() != ''
            if isinstance(val, (float, int)):
                return val is not None and val != 0
            return val is not None
        fields = {
            'street': current_user.street,
            'house_number': current_user.house_number,
            'postal_code': current_user.postal_code,
            'city': current_user.city,
            'latitude': current_user.latitude,
            'longitude': current_user.longitude
        }
        if current_user.account_type == 'pro':
            fields['business_name'] = current_user.business_name
        for k, v in fields.items():
            if not is_filled(v):
                missing.append(k)
        flash(f'Vul eerst je profiel volledig in voordat je kunt zoeken! Ontbrekende velden: {", ".join(missing)}', 'warning')
        return redirect(url_for('main.profile'))










@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Je bent succesvol uitgelogd.', 'success')
    return redirect(url_for('main.home'))



from flask import redirect, url_for, render_template
from flask_login import login_required, current_user
from .models import Book, Postcard, Poster, Message

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        # Redirect admin naar admin_dashboard
        return redirect(url_for('main.admin_dashboard'))
    
    # Voor gewone gebruikers: haal hun boeken, postkaarten en posters op
    boeken = Book.query.filter_by(user_id=current_user.id).all()
    postkaarten = Postcard.query.filter_by(user_id=current_user.id).all()
    posters = Poster.query.filter_by(user_id=current_user.id).all()
    from .models import Art
    kunst = Art.query.filter_by(user_id=current_user.id).all()
   
    new_message_count = Message.query.filter_by(receiver_id=current_user.id, read=False).count()
    
    # Kies template op basis van account_type
    if current_user.account_type == 'pro':
        template = 'dashboard_pro.html'
    else:
        template = 'dashboard_basic.html'
    
    from .models import AppointmentSlot
    afspraken = AppointmentSlot.query.filter_by(reserved_by_id=current_user.id).order_by(
        AppointmentSlot.year, AppointmentSlot.month, AppointmentSlot.day, AppointmentSlot.time.asc()
    ).all()
    return render_template(
        template, 
        user=current_user, 
        boeken=boeken, 
        postkaarten=postkaarten,
        posters=posters,
        kunst=kunst,
        new_message_count=new_message_count,
        afspraken=afspraken
    )



from flask import render_template, url_for, flash, redirect, request, current_app
from flask_login import login_required, current_user
from PIL import Image, ExifTags
import os
import secrets

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
            # Verwijder oude afbeelding als die niet default is
            old_image = current_user.image_file
            if old_image != 'default.jpg':
                old_path = os.path.join(current_app.root_path, 'static/profile_pics', old_image)
                if os.path.exists(old_path):
                    os.remove(old_path)

            # Sla nieuwe profielfoto op met oriëntatie-fix
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
        return redirect(url_for('main.dashboard'))

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


def save_picture(form_picture):
    """Slaat een profielfoto op en corrigeert EXIF oriëntatie."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    img = Image.open(form_picture)

    # Fix EXIF oriëntatie
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        exif = img._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation, None)

            if orientation_value == 3:
                img = img.rotate(180, expand=True)
            elif orientation_value == 6:
                img = img.rotate(270, expand=True)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass  # Geen EXIF-oriëntatie aanwezig

    # Optioneel: resize naar max breedte/hoogte
    output_size = (400, 400)
    img.thumbnail(output_size)

    img.save(picture_path)
    return picture_fn


@main.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Toegang geweigerd.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Pagina parameters met fallback naar 1
    page_users = request.args.get('page_users', 1, type=int)
    page_books = request.args.get('page_books', 1, type=int)
    page_posters = request.args.get('page_posters', 1, type=int)
    page_postcards = request.args.get('page_postcards', 1, type=int)

    # Query's met filter en paginatie
    users = User.query.filter_by(is_admin=False).order_by(User.id.asc()).paginate(page=page_users, per_page=10, error_out=False)
    books = Book.query.order_by(Book.id.asc()).paginate(page=page_books, per_page=10, error_out=False)

    # Voor posters en postcards (vergeet niet de modellen te importeren!)
    posters = Poster.query.order_by(Poster.id.asc()).paginate(page=page_posters, per_page=10, error_out=False)
    postcards = Postcard.query.order_by(Postcard.id.asc()).paginate(page=page_postcards, per_page=10, error_out=False)

    pro_users = User.query.filter_by(account_type='pro').order_by(User.id.asc()).all()
    return render_template(
        'admin_dashboard.html',
        users=users,
        books=books,
        posters=posters,
        postcards=postcards,
        pro_users=pro_users
    )


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

from genereer_beschrijving import generate_description
from genereer_genre_en_tags import generate_genre_and_tags
from genereer_auteur_beschrijving import generate_author_description


@main.route('/books/new', methods=['GET', 'POST'])
@login_required
def new_book():
    # Controle: eerst winkelnaam ingevuld?
    if not current_user.business_name:
        flash('Je moet eerst je profiel bijwerken en een winkelnaam invoeren voordat je een boek kunt toevoegen.', 'warning')
        return redirect(url_for('main.profile'))  # Pas aan naar jouw profiel bewerken route

    form = BookForm()
    # Vul rek dropdown
    reks = Rek.query.all()
    form.rek.choices = [(rek.id, rek.naam) for rek in reks]
    # Vul verdieping dropdown
    form.verdieping.choices = []
    verdiepingen = []
    if form.rek.data:
        verdiepingen = RekVerdieping.query.filter_by(rek_id=form.rek.data).all()
        form.verdieping.choices = [(v.id, f"{v.nummer} ({v.rek.naam})") for v in verdiepingen]
    elif reks:
        eerste_rek_id = reks[0].id
        verdiepingen = RekVerdieping.query.filter_by(rek_id=eerste_rek_id).all()
        form.verdieping.choices = [(v.id, f"Verdieping {v.nummer}") for v in verdiepingen]

    # Vul positie dropdown met letter van verdieping
    positie_choices = []
    gekozen_verdieping = None
    if form.verdieping.data:
        gekozen_verdieping = next((v for v in verdiepingen if v.id == form.verdieping.data), None)
    elif verdiepingen:
        gekozen_verdieping = verdiepingen[0]
    if gekozen_verdieping:
        if gekozen_verdieping.links:
            positie_choices.append(('links', f'Links ({gekozen_verdieping.links})'))
        if gekozen_verdieping.midden:
            positie_choices.append(('midden', f'Midden ({gekozen_verdieping.midden})'))
        if gekozen_verdieping.rechts:
            positie_choices.append(('rechts', f'Rechts ({gekozen_verdieping.rechts})'))
    else:
        positie_choices = [('links','Links'),('midden','Midden'),('rechts','Rechts')]
    form.positie.choices = positie_choices

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

        # Boekobject aanmaken met verzend- en betalingsopties
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
            author_description=author_description,
            allow_shipping=form.allow_shipping.data,
            shipping_cost=form.shipping_cost.data if form.allow_shipping.data else None,
            pickup_only=form.pickup_only.data,
            platform_payment_only=form.platform_payment_only.data,
            cash_payment_only=form.cash_payment_only.data,
            rek_id=form.rek.data if form.rek.data else None,
            verdieping_id=form.verdieping.data if form.verdieping.data else None,
            positie=form.positie.data if form.positie.data else None
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
    form.rek.choices = [(rek.id, rek.naam) for rek in Rek.query.all()]
    form.verdieping.choices = []
    if form.rek.data:
        verdiepingen = RekVerdieping.query.filter_by(rek_id=form.rek.data).all()
        form.verdieping.choices = [(v.id, f"{v.nummer} ({v.rek.naam})") for v in verdiepingen]
    elif request.method == 'GET' and book.rek_id:
        verdiepingen = RekVerdieping.query.filter_by(rek_id=book.rek_id).all()
        form.verdieping.choices = [(v.id, f"Verdieping {v.nummer}") for v in verdiepingen]

    if form.validate_on_submit():
        book.title = form.title.data
        book.author = form.author.data
        book.description = form.description.data
        book.genre = form.genre.data
        book.price = form.price.data
        book.author_description = form.author_description.data
        # Afbeeldingen verwerken
        upload_folder = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        from werkzeug.datastructures import FileStorage
        def save_image(image_field):
            if image_field.data and isinstance(image_field.data, FileStorage):
                filename = secure_filename(image_field.data.filename)
                image_path = os.path.join(upload_folder, filename)
                image_field.data.save(image_path)
                return filename
            return None
        if form.front_image.data and isinstance(form.front_image.data, FileStorage):
            book.front_image = save_image(form.front_image)
        if form.side_image.data and isinstance(form.side_image.data, FileStorage):
            book.side_image = save_image(form.side_image)
        if form.back_image.data and isinstance(form.back_image.data, FileStorage):
            book.back_image = save_image(form.back_image)
        # Locatie verwerken
        book.rek_id = form.rek.data if form.rek.data else None
        book.verdieping_id = form.verdieping.data if form.verdieping.data else None
        book.positie = form.positie.data if form.positie.data else None
        # Tags
        book.tags.clear()
        tag_names = form.tags.data.split(',') if form.tags.data else []
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
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

    # Boekweergave vastleggen
    new_view = BookView(book_id=book.id)
    db.session.add(new_view)
    book.view_count = (book.view_count or 0) + 1
    db.session.commit()

    # Informatie voor veiling
    auction_open = book.is_auction and book.auction_end and book.auction_end > datetime.utcnow()
    seller = book.user
    highest_bid = max(book.bids, key=lambda b: b.amount) if book.bids else None

    user_bids = [b for b in book.bids if current_user.is_authenticated and b.bidder_id == current_user.id]
    user_highest_bid = max(user_bids, key=lambda b: b.amount) if user_bids else None

    base_minimum = float(book.auction_min_price or 0)

    if user_highest_bid and highest_bid and user_highest_bid.amount == highest_bid.amount:
        min_bid = float(user_highest_bid.amount) + 1
    elif highest_bid:
        min_bid = float(highest_bid.amount) + 5
    else:
        min_bid = base_minimum

    bid_form = BidForm()

    # Paginate biedingen
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

        # Extra controle of gebruiker al hoogste bod heeft
        if user_highest_bid and highest_bid and user_highest_bid.amount == highest_bid.amount:
            flash('Je hebt al het hoogste bod en kunt niet nog een hoger bod plaatsen.', 'danger')
            return redirect(url_for('main.book_detail', book_id=book.id))

        # Bieddrempel: moet €5 hoger zijn dan hoogste bod van anderen
        andere_bods = [b.amount for b in book.bids if b.bidder_id != current_user.id]
        hoogste_andere_bod = max(andere_bods) if andere_bods else 0

        if hoogste_andere_bod > 0 and nieuwe_bod < hoogste_andere_bod + 5:
            flash(f'Je bod moet minimaal €{hoogste_andere_bod + 5:.2f} zijn.', 'danger')
            return redirect(url_for('main.book_detail', book_id=book.id))

        # Bod opslaan
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







from sqlalchemy import or_

@main.route('/search')
def search():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)

    users = []
    books = []
    postkaarten = []
    posters = []
    kunstwerken = []

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

        # Zoek posters
        posters = Poster.query.filter(
            or_(
                Poster.title.ilike(f'%{query}%'),
                Poster.description.ilike(f'%{query}%'),
                Poster.publisher.ilike(f'%{query}%'),
                # voeg velden toe waar je op wil zoeken in posters
            )
        ).paginate(page=page, per_page=12)

        # Zoek kunstwerken
        from app.models import Art
        kunstwerken = Art.query.filter(
            or_(
                Art.title.ilike(f'%{query}%'),
                Art.artist.ilike(f'%{query}%'),
                Art.description.ilike(f'%{query}%'),
                Art.condition.ilike(f'%{query}%')
            )
        ).paginate(page=page, per_page=12)

    return render_template('search_results.html', query=query, users=users, books=books, postcards=postkaarten, posters=posters, kunstwerken=kunstwerken)

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

    import bleach
    form = MessageForm()
    if request.method == 'POST':
        raw_content = request.form.get('content', '')
        clean_content = bleach.clean(raw_content, tags=["b", "i", "u", "a", "p", "br", "ul", "ol", "li", "strong", "em"], attributes={"a": ["href", "target"]}, strip=True)
        form.content.data = clean_content
        if form.validate():
            nieuw_bericht = Message(
                sender_id=current_user.id,
                receiver_id=seller.id,
                content=clean_content,
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
    page = request.args.get('page', 1, type=int)
    ontvangen_pagination = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).paginate(page=page, per_page=3)
    ontvangen = ontvangen_pagination.items
    verzonden = Message.query.filter_by(sender_id=current_user.id).order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', ontvangen=ontvangen, verzonden=verzonden, ontvangen_pagination=ontvangen_pagination)


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
    reks = Rek.query.all()
    form.rek.choices = [(rek.id, rek.naam) for rek in reks]
    form.verdieping.choices = []
    if form.rek.data:
        verdiepingen = RekVerdieping.query.filter_by(rek_id=form.rek.data).all()
        form.verdieping.choices = [(v.id, f"Verdieping {v.nummer}") for v in verdiepingen]
    elif reks:
        eerste_rek_id = reks[0].id
        verdiepingen = RekVerdieping.query.filter_by(rek_id=eerste_rek_id).all()
        form.verdieping.choices = [(v.id, f"Verdieping {v.nummer}") for v in verdiepingen]
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
            user_id=current_user.id,
            allow_shipping = form.allow_shipping.data,  
            shipping_cost = form.shipping_cost.data,       
            pickup_only = form.pickup_only.data,         
            platform_payment_only = form.platform_payment_only.data, 
            cash_payment_only = form.cash_payment_only.data,   
            rek_id=form.rek.data if form.rek.data else None,
            verdieping_id=form.verdieping.data if form.verdieping.data else None,
            positie=form.positie.data if form.positie.data else None
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


@main.route('/poster/add', methods=['GET', 'POST'])
@login_required
def add_poster():
    form = PosterForm()
    reks = Rek.query.all()
    form.rek.choices = [(rek.id, rek.naam) for rek in reks]
    form.verdieping.choices = []
    if form.rek.data:
        verdiepingen = RekVerdieping.query.filter_by(rek_id=form.rek.data).all()
        form.verdieping.choices = [(v.id, f"Verdieping {v.nummer}") for v in verdiepingen]
    elif reks:
        eerste_rek_id = reks[0].id
        verdiepingen = RekVerdieping.query.filter_by(rek_id=eerste_rek_id).all()
        form.verdieping.choices = [(v.id, f"Verdieping {v.nummer}") for v in verdiepingen]
    if form.validate_on_submit():
        poster = Poster(
            title=form.title.data,
            publisher=form.publisher.data,
            auction_end=form.auction_end.data,
            condition=form.condition.data,
            description=form.description.data,
            price=form.price.data,
            is_auction=form.is_auction.data,
            auction_min_price=form.auction_min_price.data,
            user_id=current_user.id,
            allow_shipping = form.allow_shipping.data,  
            shipping_cost = form.shipping_cost.data,       
            pickup_only = form.pickup_only.data,         
            platform_payment_only = form.platform_payment_only.data, 
            cash_payment_only = form.cash_payment_only.data,   
            rek_id=form.rek.data if form.rek.data else None,
            verdieping_id=form.verdieping.data if form.verdieping.data else None,
            positie=form.positie.data if form.positie.data else None
        )
        
        # Afbeelding uploaden en opslaan
        if form.front_image.data:
            front_filename = secure_filename(form.front_image.data.filename)
            front_path = os.path.join(current_app.root_path, 'static/uploads', front_filename)
            form.front_image.data.save(front_path)
            poster.front_image_url = 'uploads/' + front_filename

        if form.back_image.data:
            back_filename = secure_filename(form.back_image.data.filename)
            back_path = os.path.join(current_app.root_path, 'static/uploads', back_filename)
            form.back_image.data.save(back_path)
            poster.back_image_url = 'uploads/' + back_filename

        db.session.add(poster)
        db.session.commit()
        flash('Poster succesvol toegevoegd!', 'success')
        return redirect(url_for('main.dashboard'))

    
    return render_template('add_poster.html', form=form)




@main.route('/postcards/edit/<int:postcard_id>', methods=['GET', 'POST'])
@login_required
def edit_postcard(postcard_id):
    postcard = Postcard.query.get_or_404(postcard_id)
    form = PostcardForm(obj=postcard)
    form.rek.choices = [(rek.id, rek.naam) for rek in Rek.query.all()]
    form.verdieping.choices = []
    if form.rek.data:
        verdiepingen = RekVerdieping.query.filter_by(rek_id=form.rek.data).all()
        form.verdieping.choices = [(v.id, f"Verdieping {v.nummer}") for v in verdiepingen]
    if form.validate_on_submit():
        postcard.title = form.title.data
        postcard.description = form.description.data
        postcard.condition = form.condition.data
        postcard.publisher = form.publisher.data
        # Voeg meer velden toe als je die hebt

        # Upload nieuwe afbeelding als er een is geüpload
        if form.front_image.data:
            # Oude afbeelding verwijderen als die er is
            if postcard.front_image_url:
                old_image_path = os.path.join(current_app.root_path, 'static', postcard.front_image_url)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

            # Nieuwe afbeelding opslaan
            filename = save_image(form.front_image.data)
            postcard.front_image_url = f'uploads/{filename}'

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

#-------------------------------------------------------------------------------------------------


@main.route('/posters/edit/<int:poster_id>', methods=['GET', 'POST'])
@login_required
def edit_poster(poster_id):
    book = Book.query.get_or_404(book_id)
    # Boekweergave vastleggen
    new_view = BookView(book_id=book.id)
    db.session.add(new_view)
    book.view_count = (book.view_count or 0) + 1
    db.session.commit()
    # Informatie voor veiling
    auction_open = book.is_auction and book.auction_end and book.auction_end > datetime.utcnow()
    seller = book.user
    highest_bid = max(book.bids, key=lambda b: b.amount) if book.bids else None
    user_bids = [b for b in book.bids if current_user.is_authenticated and b.bidder_id == current_user.id]
    user_highest_bid = max(user_bids, key=lambda b: b.amount) if user_bids else None
    base_minimum = float(book.auction_min_price or 0)
    if user_highest_bid and highest_bid and user_highest_bid.amount == highest_bid.amount:
        min_bid = float(user_highest_bid.amount) + 1
    elif highest_bid:
        min_bid = float(highest_bid.amount) + 5
    else:
        min_bid = base_minimum
    bid_form = BidForm()
    # Paginate biedingen
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
        # Extra controle of gebruiker al hoogste bod heeft
        if user_highest_bid and highest_bid and user_highest_bid.amount == highest_bid.amount:
            flash('Je hebt al het hoogste bod en kunt niet nog een hoger bod plaatsen.', 'danger')
            return redirect(url_for('main.book_detail', book_id=book.id))
        # Bieddrempel: moet €5 hoger zijn dan hoogste bod van anderen
        andere_bods = [b.amount for b in book.bids if b.bidder_id != current_user.id]
        hoogste_andere_bod = max(andere_bods) if andere_bods else 0
        if hoogste_andere_bod > 0 and nieuwe_bod < hoogste_andere_bod + 5:
            flash(f'Je bod moet minimaal €{hoogste_andere_bod + 5:.2f} zijn.', 'danger')
            return redirect(url_for('main.book_detail', book_id=book.id))
        # Bod opslaan
        bid = Bid(amount=nieuwe_bod, bidder_id=current_user.id, book_id=book.id)
        db.session.add(bid)
        db.session.commit()
        flash('Je bod is geplaatst!', 'success')
        return redirect(url_for('main.book_detail', book_id=book.id))
    output_size = (500, 500)
    i = Image.open(form_image)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@main.route('/posters/<int:poster_id>/delete', methods=['POST'])
@login_required
def delete_poster(poster_id):
    poster = Poster.query.get_or_404(poster_id)
    if poster.user_id != current_user.id:
        abort(403)
    db.session.delete(poster)
    db.session.commit()
    flash('Poster is verwijderd.', 'success')
    return redirect(url_for('main.dashboard'))


@main.route('/poster/<int:poster_id>')
def poster_detail(poster_id):
    poster = Poster.query.get_or_404(poster_id)
    return render_template('poster_detail.html', poster=poster)





#-------------------filter--------------------------------

from flask import request, render_template, flash, redirect, url_for
from .models import Postcard, Poster, Book, User
from . import db

import requests
from math import radians, cos, sin, asin, sqrt

def geocode(postcode, stad):
    query = f"{postcode} {stad}, België"
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "be",
        "accept-language": "nl"
    }
    headers = {
        "User-Agent": "AntiquaApp/1.0 (email@example.com)"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
            else:
                print(f"Geen geocode resultaat voor: {query}")
        else:
            print(f"Nominatim error status: {resp.status_code}")
    except Exception as e:
        print(f"Fout bij geocoding: {e}")
    return None, None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

@main.route('/filter/<category>')
def filter_items(category):
    page = request.args.get('page', 1, type=int)
    per_page = 9

    sort_by = request.args.get('sort_by', 'relevant')
    postcode = request.args.get('postcode', '').strip()
    stad = request.args.get('stad', '').strip()

    try:
        radius = int(request.args.get('radius', 20))
    except (TypeError, ValueError):
        radius = 20

    search_term = request.args.get('search_term', '').strip()

    if category == 'postcards':
        model = Postcard
        query = model.query.filter_by(sold=False).join(User)
    elif category == 'posters':
        model = Poster
        query = model.query.filter_by(sold=False).join(User)
    elif category == 'books':
        model = Book
        query = model.query.filter_by(sold=False).join(User, Book.user_id == User.id)
    elif category == 'art':
        from app.models import Art
        model = Art
        query = model.query.filter_by(sold=False).join(User)
    else:
        flash("Categorie bestaat niet.", "warning")
        return redirect(url_for('main.home'))

    if search_term:
        like_pattern = f"%{search_term}%"
        if category == 'books':
            query = query.filter(
                db.or_(
                    Book.title.ilike(like_pattern),
                    Book.author.ilike(like_pattern)
                )
            )
        elif category == 'art':
            query = query.filter(
                db.or_(
                    model.title.ilike(like_pattern),
                    model.artist.ilike(like_pattern),
                    model.description.ilike(like_pattern),
                    model.condition.ilike(like_pattern)
                )
            )
        else:
            query = query.filter(model.title.ilike(like_pattern))

    if sort_by == 'cheap':
        query = query.order_by(model.price.asc())
    elif sort_by == 'expensive':
        query = query.order_by(model.price.desc())
    else:
        if hasattr(model, 'created_at'):
            query = query.order_by(model.created_at.desc())
        else:
            query = query.order_by(model.id.desc())

    # Filter op afstand
    if postcode and stad:
        user_lat, user_lon = geocode(postcode, stad)
        if user_lat is not None and user_lon is not None:
            filtered_items = []
            all_items = query.all()
            for item in all_items:
                if (
                    item.user and
                    item.user.latitude is not None and
                    item.user.longitude is not None
                ):
                    try:
                        lat = float(item.user.latitude)
                        lon = float(item.user.longitude)
                        dist = haversine(user_lat, user_lon, lat, lon)
                    except (TypeError, ValueError):
                        continue
                    if dist <= radius:
                        filtered_items.append(item)

            total = len(filtered_items)
            start = (page - 1) * per_page
            end = start + per_page
            items = filtered_items[start:end]

            class SimplePagination:
                def __init__(self, items, page, per_page, total):
                    self.items = items
                    self.page = page
                    self.per_page = per_page
                    self.total = total
                    self.pages = (total + per_page - 1) // per_page
                    self.has_prev = page > 1
                    self.has_next = page < self.pages

                def prev_num(self):
                    return self.page - 1

                def next_num(self):
                    return self.page + 1

            pagination = SimplePagination(items, page, per_page, total)

        else:
            flash("Locatie niet gevonden, geen filtering op afstand toegepast.", "warning")
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            items = pagination.items
    else:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = pagination.items

    return render_template(
        'filter.html',
        items=items,
        category=category,
        selected_postcode=postcode,
        selected_stad=stad,
        selected_radius=radius,
        selected_search_term=search_term,
        pagination=pagination,
        selected_sort=sort_by
    )



#-----------------------winkelwagen------------------------------------


from flask import session, render_template
from flask_login import current_user

def add_to_cart(item_type, item_id):
    # Check: mag niet eigen item kopen
    owner_id = None
    if item_type == 'book':
        item = Book.query.get(item_id)
        if item:
            owner_id = item.user_id
    elif item_type == 'postcard':
        item = Postcard.query.get(item_id)
        if item:
            owner_id = item.user_id
    elif item_type == 'poster':
        item = Poster.query.get(item_id)
        if item:
            owner_id = item.user_id

    if current_user.is_authenticated:
        if owner_id == current_user.id:
            flash('Je kunt je eigen item niet kopen!', 'warning')
            return
        # In database opslaan
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id,
            item_type=item_type,
            item_id=item_id
        ).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(
                user_id=current_user.id,
                item_type=item_type,
                item_id=item_id,
                quantity=1
            )
            db.session.add(cart_item)
        db.session.commit()
    else:
        # In session opslaan
        if owner_id is not None and 'user_id' in session and owner_id == session['user_id']:
            flash('Je kunt je eigen item niet kopen!', 'warning')
            return
        cart = session.get('cart', [])
        for item in cart:
            if item['type'] == item_type and item['id'] == item_id:
                item['quantity'] += 1
                break
        else:
            cart.append({'type': item_type, 'id': item_id, 'quantity': 1})
        session['cart'] = cart



def get_items_in_cart(only_available=False):
    """
    Haalt alle items op uit de cart. 
    only_available=True => filtert items die verkocht zijn.
    """
    items_in_cart = []

    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        for entry in cart_items:
            item = None
            if entry.item_type == 'book':
                item = Book.query.get(entry.item_id)
            elif entry.item_type == 'postcard':
                item = Postcard.query.get(entry.item_id)
            elif entry.item_type == 'poster':
                item = Poster.query.get(entry.item_id)

            if item and (not only_available or not item.sold):
                items_in_cart.append({
                    'item': item,
                    'type': entry.item_type,
                    'quantity': entry.quantity
                })
    else:
        cart_data = session.get('cart', [])
        for entry in cart_data:
            item = None
            if entry['type'] == 'book':
                item = Book.query.get(entry['id'])
            elif entry['type'] == 'postcard':
                item = Postcard.query.get(entry['id'])
            elif entry['type'] == 'poster':
                item = Poster.query.get(entry['id'])

            if item and (not only_available or not item.sold):
                items_in_cart.append({
                    'item': item,
                    'type': entry['type'],
                    'quantity': entry['quantity']
                })

    return items_in_cart

@main.route('/cart')
def cart():
    """
    Route voor de winkelwagenpagina.
    Toont alleen beschikbare items.
    """
    available_items = get_items_in_cart(only_available=True)
    total_items_in_cart = sum(item['quantity'] for item in get_items_in_cart(only_available=False))  # totaal ongeacht sold

    return render_template(
        'cart.html',
        items_in_cart=available_items,
        cart_item_count=total_items_in_cart  # gebruik dit als badge of voor info
    )


@main.context_processor
def inject_cart_count():
    """
    Context processor voor de badge in de navbar.
    Telt totaal items minus de verkochte items.
    """
    all_items = get_items_in_cart(only_available=False)
    cart_count = sum(item['quantity'] for item in all_items)  # totaal items
    sold_count = sum(item['quantity'] for item in all_items if item['item'].sold)  # verkochte items

    return {'cart_count': cart_count - sold_count}


@main.route('/api/add_to_cart/<item_type>/<int:item_id>', methods=['POST'])
def api_add_to_cart(item_type, item_id):
    add_to_cart(item_type, item_id)
    
    # Haal alle items op, maar filter sold items voor de badge
    items_in_cart = get_items_in_cart(only_available=False)
    cart_count = sum(i['quantity'] for i in items_in_cart if not i['item'].sold)
    
    return jsonify({
        'success': True,
        'cart_count': cart_count
    })


#---------------------------verwijderen cart---------------------------


from flask import Flask, render_template, request, redirect, url_for, session

@main.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    item_type = request.form.get("item_type")
    item_id = int(request.form.get("item_id"))

    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id,
            item_type=item_type,
            item_id=item_id
        ).first()

        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                db.session.delete(cart_item)
            db.session.commit()

    else:
        cart = session.get("cart", [])
        for entry in cart:
            if entry["type"] == item_type and entry["id"] == item_id:
                if entry["quantity"] > 1:
                    entry["quantity"] -= 1
                else:
                    cart.remove(entry)
                break
        session["cart"] = cart

    return redirect(url_for("main.cart"))


#--------------------------mollie---------------------------------------

@main.route("/checkout/<item_type>/<int:item_id>")
def checkout_item(item_type, item_id):
    if item_type == 'book':
        item = Book.query.get_or_404(item_id)
    elif item_type == 'postcard':
        item = Postcard.query.get_or_404(item_id)
    elif item_type == 'poster':
        item = Poster.query.get_or_404(item_id)
    else:
        abort(404)

    # Hier kan je checkoutlogica doen, zoals betaalpagina of reservering
    return render_template("checkout.html", item=item, item_type=item_type)

#---------------appointment------------------------



@main.route('/make_appointment/<int:item_id>', methods=['GET', 'POST'])
@login_required
def make_appointment(item_id):
    item = Book.query.get_or_404(item_id)
    from app.models import AppointmentSlot
    verkoper = item.user
    tijdsloten = AppointmentSlot.query.filter_by(user_id=verkoper.id, book_id=None, reserved_by_id=None).order_by(
        AppointmentSlot.year, AppointmentSlot.month, AppointmentSlot.day, AppointmentSlot.time.asc()
    ).all()
    if request.method == 'POST':
        tijdslot_str = request.form.get('tijdslot')
        gekozen_datum = gekozen_tijd = None
        if tijdslot_str:
            import re
            m = re.match(r"(\d+)-(\d+)-(\d+) (\d{2}:\d{2})", tijdslot_str)
            if m:
                year, month, day, time = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
                slot = AppointmentSlot.query.filter_by(user_id=verkoper.id, book_id=None, year=year, month=month, day=day, time=time, reserved_by_id=None).first()
                if slot:
                    slot.reserved_by_id = current_user.id
                    from app import db
                    import datetime
                    slot.reserved_at = datetime.datetime.now()
                    # Boek op sold zetten
                    item.sold = True
                    db.session.commit()
                gekozen_datum = f"{day}-{month}-{year}"
                gekozen_tijd = time
        if not gekozen_datum or not gekozen_tijd:
            flash('Geen geldig tijdslot gekozen.', 'danger')
            return render_template('make_appointment.html', item=item, tijdsloten=tijdsloten)
        # Stuur een bericht naar de verkoper
        from app.models import Message
        verkoper = item.user
        content = (
            f'Nieuwe afspraakverzoek:\n'
            f'- Boek: {item.title}\n'
            f'- Datum: {gekozen_datum}\n'
            f'- Tijd: {gekozen_tijd}\n'
            f'- Koper: {current_user.username} ({current_user.email})\n'
        )

        # Bericht naar verkoper
        msg = Message(sender_id=current_user.id, receiver_id=verkoper.id, content=content)
        # Bericht naar koper (bevestiging)
        bevestiging_content = (
            f'Je hebt een afspraak gemaakt voor het boek: {item.title}\n'
            f'- Datum: {gekozen_datum}\n'
            f'- Tijd: {gekozen_tijd}\n'
            f'- Verkoper: {verkoper.username} ({verkoper.email})\n'
        )
        msg_koper = Message(sender_id=verkoper.id, receiver_id=current_user.id, content=bevestiging_content)

        from app import db
        db.session.add(msg)
        db.session.add(msg_koper)
        db.session.commit()

        # Verwijder het item uit de winkelmand van de koper
        # Database-cart
        if current_user.is_authenticated:
            from app.models import CartItem
            cart_item = CartItem.query.filter_by(user_id=current_user.id, item_type='book', item_id=item.id).first()
            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
        # Session-cart
        cart = session.get('cart', [])
        cart = [ci for ci in cart if not (ci['type'] == 'book' and ci['id'] == item.id)]
        session['cart'] = cart

        # Stuur een mail naar de verkoper
        from app.utils import send_appointment_email
        base_url = request.host_url.rstrip('/')
        message_url = f"{base_url}/messages"
        send_appointment_email(
            recipient=verkoper.email,
            buyer_name=current_user.username,
            buyer_email=current_user.email,
            book_title=item.title,
            date=gekozen_datum,
            time=gekozen_tijd,
            message_url=message_url
        )

        flash(f'Afspraak bevestigd voor {gekozen_datum} om {gekozen_tijd}. De verkoper is geïnformeerd via een bericht en e-mail.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('make_appointment.html', item=item, tijdsloten=tijdsloten)


from mollie.api.client import Client







from mollie.api.client import Client
from mollie.api.error import RequestError
import os

# Mollie client
mollie_client = Client()
mollie_client.set_api_key(os.environ.get("MOLLIE_API_KEY", "test_test"))

@main.route("/start-mollie-payment/<string:item_type>/<int:item_id>", methods=["POST"])
@login_required
def start_mollie_payment(item_type, item_id):
    # Haal het item op afhankelijk van type
    if item_type == "book":
        item = Book.query.get_or_404(item_id)
    elif item_type == "poster":
        item = Poster.query.get_or_404(item_id)
    elif item_type == "postcard":
        item = Postcard.query.get_or_404(item_id)
    else:
        flash("Ongeldig item type.", "danger")
        return redirect(url_for("main.cart"))

    try:
        payment = mollie_client.payments.create({
            "amount": {"currency": "EUR", "value": f"{item.price:.2f}"},
            "description": f"Betaling voor {item.title}",
            "redirectUrl": url_for("main.payment_return", _external=True),
            "webhookUrl": url_for("main.payment_webhook", _external=True),
            "metadata": {
                "item_id": item.id,
                "user_id": current_user.id,
                "item_type": item_type  # belangrijk voor webhook
            }
        })

        payment_update_url = url_for("main.payment_return", payment_id=payment.id, _external=True)
        mollie_client.payments.update(payment.id, {"redirectUrl": payment_update_url})

        return redirect(payment.checkout_url)
    except RequestError:
        flash("We konden geen verbinding maken met de betaalprovider. Probeer het later opnieuw.", "danger")
        return redirect(url_for("main.cart"))
    except Exception:
        flash("Er is een onverwachte fout opgetreden tijdens het starten van de betaling.", "danger")
        return redirect(url_for("main.cart"))



@main.route("/payment-return")
@login_required
def payment_return():
    payment_id = request.args.get("payment_id")
    if not payment_id:
        return "Geen payment ID ontvangen."
    return render_template("payment_loading.html", payment_id=payment_id)



@main.route("/check-payment-status/<payment_id>")
@login_required
def check_payment_status(payment_id):
    try:
        payment = mollie_client.payments.get(payment_id)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    if payment.is_paid():
        return {"status": "paid"}
    elif payment.is_canceled():
        return {"status": "canceled"}
    else:
        return {"status": payment.status}



@main.route("/payment-webhook", methods=["POST"])
def payment_webhook():
    """Wordt aangeroepen door Mollie server-to-server"""
    payment_id = request.form.get("id")
    if not payment_id:
        return "Geen payment ID ontvangen", 400

    payment = mollie_client.payments.get(payment_id)

    # Haal metadata op
    item_id = payment.metadata.get("item_id")
    item_type = payment.metadata.get("item_type")  # we voegen dit toe

    if not item_id or not item_type:
        return "Geen item metadata ontvangen", 400

    # Update database afhankelijk van status
    if payment.is_paid():
        print(f"Order {item_id} betaald.")
        if item_type == "book":
            item = Book.query.get(item_id)
        elif item_type == "postcard":
            item = Postcard.query.get(item_id)
        elif item_type == "poster":
            item = Poster.query.get(item_id)
        else:
            item = None

        if item:
            item.sold = True
            db.session.commit()

    elif payment.is_canceled():
        print(f"Order {item_id} geannuleerd.")
        # hier kun je eventueel status opslaan als geannuleerd
    else:
        print(f"Order {item_id} status: {payment.status}")

    return "OK"



@main.route("/bedankt")
@login_required
def bedankt():
    return render_template("bedankt.html")



@main.route("/betaling-mislukt")
@login_required
def payment_failed():
    return render_template("betaling_mislukt.html")


#---------------beheer antiquariaat-----------------------


@main.route('/beheer-antiquariaat')
@login_required
def beheer_antiquariaat():
    verkochte_boeken = Book.query.filter_by(user_id=current_user.id, sold=True).all()
    verkochte_postkaarten = Postcard.query.filter_by(user_id=current_user.id, sold=True).all()
    verkochte_posters = Poster.query.filter_by(user_id=current_user.id, sold=True).all()
    rek_form = RekForm()
    rekken = Rek.query.all()
    boeken = Book.query.filter_by(user_id=current_user.id, sold=False).all()
    boek_id = request.args.get('boek_id')
    if boek_id == 'all':
        boek = None
    else:
        boek = Book.query.get(int(boek_id)) if boek_id else (boeken[0] if boeken else None)
    # Verzamel gereserveerde slots voor de kalender
    if boek:
        reserved_slots = [
            {'year': s.year, 'month': s.month, 'day': s.day, 'time': s.time}
            for s in boek.appointment_slots if s.reserved_by_id is not None
        ]
    else:
        reserved_slots = []
    # Ensure slots and pagination are always defined for template
    slots = []
    pagination = None
    return render_template(
        'beheer_antiquariaat.html',
        verkochte_boeken=verkochte_boeken,
        verkochte_postkaarten=verkochte_postkaarten,
        verkochte_posters=verkochte_posters,
        rek_form=rek_form,
        rekken=rekken,
        boeken=boeken,
        boek=boek,
        reserved_slots=reserved_slots,
        user=current_user,
        slots=slots,
        pagination=pagination
    )


# Route voor toevoegen van een rek
@main.route('/add_rek', methods=['POST'])
@login_required
def add_rek():
    from flask import request
    form = RekForm()
    if request.method == 'POST':
        naam = request.form.get('naam')
        aantal_verdiepingen = int(request.form.get('aantal_verdiepingen', 1))
        if not naam or aantal_verdiepingen < 1:
            flash('Fout bij toevoegen rek. Vul alle velden correct in.', 'danger')
            return redirect(url_for('main.beheer_antiquariaat', sectie='goederenplaats'))
        nieuw_rek = Rek(
            naam=naam,
            user_id=current_user.id
        )
        db.session.add(nieuw_rek)
        db.session.flush()
        for nummer in range(aantal_verdiepingen):
            links = request.form.get(f'verdiepingen-{nummer}-links')
            midden = request.form.get(f'verdiepingen-{nummer}-midden')
            rechts = request.form.get(f'verdiepingen-{nummer}-rechts')
            verdieping = RekVerdieping(
                rek_id=nieuw_rek.id,
                nummer=nummer+1,
                links=links,
                midden=midden,
                rechts=rechts
            )
            db.session.add(verdieping)
        db.session.commit()
        totaal_rekken = Rek.query.count()
    
    return redirect(url_for('main.beheer_antiquariaat', sectie='bestaande-rekken'))
    


#---------------upgrade account------------------------------------



from flask import flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from app import db
from app.forms import UpgradeAccountForm

@main.route('/upgrade_account', methods=['GET', 'POST'])
@login_required
def upgrade_account():
    if current_user.pro_tier:  # Als al Pro
        flash('Je hebt al een Pro-account!', 'info')
        return redirect(url_for('main.dashboard'))

    form = UpgradeAccountForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.street = form.street.data
        current_user.house_number = form.house_number.data
        current_user.postal_code = form.postal_code.data
        current_user.city = form.city.data
        current_user.business_name = form.business_name.data
        current_user.vat_number = form.vat_number.data
        current_user.show_on_map = form.show_on_map.data
        # Profielfoto opslaan
        if form.image.data:
            picture_file = save_picture(form.image.data)
            current_user.image_file = picture_file
        current_user.account_type = "pro"
        current_user.pro_tier = "basic"
        db.session.commit()
        flash('Je account is succesvol geüpgraded naar Pro!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('upgrade_account.html', user=current_user, form=form)


@main.route('/upgrade_pro')
def upgrade_pro():
    return render_template('upgrade_pro.html')


# Route voor verwijderen van een rek
@main.route('/delete_rek/<int:rek_id>', methods=['POST'])
@login_required
def delete_rek(rek_id):
    rek = Rek.query.get_or_404(rek_id)
    db.session.delete(rek)
    db.session.commit()
    flash('Rek succesvol verwijderd!', 'success')
    return redirect(url_for('main.beheer_antiquariaat'))


@main.route('/api/verdiepingen', methods=['GET'])
def api_verdiepingen():
    rek_id = request.args.get('rek_id', type=int)
    verdiepingen = RekVerdieping.query.filter_by(rek_id=rek_id).all()
    data = [{'id': v.id, 'nummer': v.nummer} for v in verdiepingen]
    return jsonify(data)

@main.route('/books/<int:book_id>/pickup')
@login_required
def book_pickup_timeslot(book_id):
    return render_template('pickup_timeslot.html', book_id=book_id)

@main.route('/afspraken-overzicht')
@login_required
def afspraken_overzicht():
    from app.models import AppointmentSlot
    page = int(request.args.get('page', 1))
    per_page = 10
    pagination = AppointmentSlot.query.filter(AppointmentSlot.reserved_by_id.isnot(None)).order_by(
        AppointmentSlot.year, AppointmentSlot.month, AppointmentSlot.day, AppointmentSlot.time
    ).paginate(page=page, per_page=per_page, error_out=False)
    slots = pagination.items
    # Render beheer_antiquariaat.html, show afspraken-overzicht section
    from .forms import RekForm
    rek_form = RekForm()
    from .models import Rek, Book
    rekken = Rek.query.all()
    boeken = Book.query.filter_by(user_id=current_user.id, sold=False).all()
    boek_id = request.args.get('boek_id')
    if boek_id == 'all':
        boek = None
    else:
        boek = Book.query.get(int(boek_id)) if boek_id else (boeken[0] if boeken else None)
    reserved_slots = []
    return render_template(
        'beheer_antiquariaat.html',
        slots=slots,
        pagination=pagination,
        sectie='afspraken-overzicht',
        user=current_user,
        rek_form=rek_form,
        rekken=rekken,
        boeken=boeken,
        boek=boek,
        reserved_slots=reserved_slots
    )


@main.route('/api/appointments/save', methods=['POST'])
@login_required
def save_appointment_slots():
    from app.models import AppointmentSlot
    try:
        data = request.get_json()
        slots = data.get('slots', [])
        book_id = data.get('book_id')
        if book_id == 'all' or not book_id:
            book_id = None
        else:
            book_id = int(book_id)
        if not slots:
            return jsonify({'status': 'error', 'errors': ['slots ontbreekt']}), 400
        created_count = 0
        skipped_count = 0
        for slot in slots:
            year = slot.get('year')
            month = slot.get('month')
            day = slot.get('day')
            time = slot.get('time')
            if None in [year, month, day, time]:
                continue
            exists = AppointmentSlot.query.filter_by(
                user_id=current_user.id,
                book_id=book_id,
                year=year,
                month=month,
                day=day,
                time=time
            ).first()
            if not exists:
                new_slot = AppointmentSlot(
                    user_id=current_user.id,
                    book_id=book_id,
                    year=year,
                    month=month,
                    day=day,
                    time=time
                )
                db.session.add(new_slot)
                created_count += 1
            else:
                skipped_count += 1
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Tijdsloten succesvol opgeslagen. Nieuw: {created_count}, overgeslagen: {skipped_count}', 'created': created_count, 'skipped': skipped_count})
    except Exception as e:
        return jsonify({'status': 'error', 'errors': [str(e)]}), 500
