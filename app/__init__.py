import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv

load_dotenv()  # Laad .env bestand

# Extensies initialiseren
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)
    # Algemene configuratie
    app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY") or os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mailconfiguratie
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL')
    app.config['MOLLIE_API_KEY'] = os.getenv('MOLLIE_API_KEY')
    app.config['BASE_URL'] = os.getenv('BASE_URL', 'http://localhost:5000')
    # Voor lokaal testen (alleen dev!)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Extensies koppelen
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'


    # Context processor voor cart_count beschikbaar maken in alle templates
    @app.context_processor
    def inject_cart_count():
        from app.routes import get_items_in_cart
        all_items = get_items_in_cart(only_available=False)
        cart_count = sum(item['quantity'] for item in all_items)
        sold_count = sum(item['quantity'] for item in all_items if item['item'].sold)
        return {'cart_count': cart_count - sold_count}

    # Blueprints registeren


    from .routes import main
    app.register_blueprint(main)
    from .routes_appointments import bp_appointments
    app.register_blueprint(bp_appointments)
    from .routes_pickup import bp_pickup
    app.register_blueprint(bp_pickup)

    from .routes_shop_profile import shop_profile_bp
    app.register_blueprint(shop_profile_bp)

    return app



