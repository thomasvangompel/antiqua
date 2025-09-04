
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, TextAreaField,SelectField,DateField,
    DecimalField, BooleanField, DateTimeField, RadioField, IntegerField, FieldList, FormField
)
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import (
    DataRequired, Email, EqualTo, InputRequired, Length,
    Optional, NumberRange, Regexp, ValidationError
)
from datetime import datetime, timedelta
from flask_login import current_user
from app.models import User  # pas 'app' aan naar jouw projectnaam indien nodig


class VerdiepingForm(FlaskForm):
    links = StringField('Links', validators=[Length(max=1)])
    midden = StringField('Midden', validators=[Length(max=1)])
    rechts = StringField('Rechts', validators=[Length(max=1)])

class RekForm(FlaskForm):
    naam = StringField('Naam van het rek', validators=[DataRequired(), Length(max=100)])
    aantal_verdiepingen = IntegerField('Aantal verdiepingen', validators=[DataRequired(), NumberRange(min=1, max=20)])
    verdiepingen = FieldList(FormField(VerdiepingForm), min_entries=1, max_entries=20)
    submit = SubmitField('Rek toevoegen')

class VerdiepingForm(FlaskForm):
    links = StringField('Links', validators=[Length(max=1)])
    midden = StringField('Midden', validators=[Length(max=1)])
    rechts = StringField('Rechts', validators=[Length(max=1)])


# ─────────── UPGRADE ACCOUNT ───────────
class UpgradeAccountForm(FlaskForm):
    username = StringField('Naam', validators=[DataRequired(), Length(max=150)])
    email = StringField('E-mailadres', validators=[DataRequired(), Email()])
    street = StringField('Straat', validators=[DataRequired(), Length(max=100)])
    house_number = StringField('Huisnummer', validators=[DataRequired(), Length(max=10)])
    postal_code = StringField('Postcode', validators=[DataRequired(), Regexp(r'^\d{4}$', message="Postcode moet uit 4 cijfers bestaan.")])
    city = StringField('Stad', validators=[DataRequired(), Length(max=100)])
    business_name = StringField('Winkelnaam', validators=[DataRequired(), Length(max=150)])
    vat_number = StringField('BTW-nummer', validators=[DataRequired(), Length(max=32)])
    image = FileField('Profielfoto', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Alleen JPG of PNG toegestaan.')])
    show_on_map = BooleanField("Zichtbaar op de kaart")
    submit = SubmitField('Upgrade naar Pro')

    def validate_business_name(self, business_name):
        user = User.query.filter_by(business_name=business_name.data).first()
        if user:
            raise ValidationError('Deze winkelnaam is al in gebruik. Kies een andere.')

    def validate_vat_number(self, vat_number):
        import re
        value = vat_number.data.replace(' ', '').replace('-', '').upper()
        if not re.match(r'^BE0?\d{9}$', value):
            raise ValidationError('Ongeldig Belgisch BTW-nummer. Formaat: BE0123456789')
        # VIES check
        try:
            from zeep import Client
            country_code = value[:2]
            number = value[2:]
            client = Client('https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl')
            result = client.service.checkVat(countryCode=country_code, vatNumber=number)
            if not result['valid']:
                raise ValidationError('Dit BTW-nummer is niet geldig volgens VIES.')
        except Exception:
            # Fallback: laat het formulier doorgaan, maar log het probleem
            import logging
            logging.warning(f'VIES-controle kon niet worden uitgevoerd voor {value}.')
            pass
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, TextAreaField,SelectField,DateField,
    DecimalField, BooleanField, DateTimeField, RadioField, IntegerField
)

from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import (
    DataRequired, Email, EqualTo, InputRequired, Length,
    Optional, NumberRange, Regexp, ValidationError
)
from datetime import datetime, timedelta
from flask_login import current_user
from app.models import User  # pas 'app' aan naar jouw projectnaam indien nodig


# ─────────── REGISTRATIE ───────────

class RegisterForm(FlaskForm):
    email = StringField('E-mailadres', validators=[
        InputRequired(), Email()
    ])
    password = PasswordField('Wachtwoord', validators=[
        InputRequired(), Length(min=6)
    ])
    confirm_password = PasswordField('Bevestig wachtwoord', validators=[
        InputRequired(), EqualTo('password', message='Wachtwoorden komen niet overeen.')
    ])
    submit = SubmitField('Registreren')


# ─────────── INLOG ───────────

class LoginForm(FlaskForm):
    email = StringField('E-mailadres', validators=[InputRequired(), Email()])
    password = PasswordField('Wachtwoord', validators=[InputRequired()])
    submit = SubmitField('Inloggen')


# ─────────── NIEUW BOEK / UPDATE ───────────

class BookForm(FlaskForm):
    title        = StringField('Titel', validators=[DataRequired()])
    author       = StringField('Auteur', validators=[DataRequired()])
    
    front_image  = FileField('Voorkant afbeelding', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    side_image   = FileField('Zijkant afbeelding', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    back_image   = FileField('Achterkant afbeelding', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    
    author_description = TextAreaField('Auteursbeschrijving', validators=[Optional(), Length(max=2000)])
    description  = TextAreaField('Beschrijving', validators=[Optional(), Length(max=2000)])
    genre        = StringField('Genre', validators=[Optional(), Length(max=100)])  # Automatisch gegenereerd, optioneel bewerkbaar
    tags         = StringField('Tags (komma-gescheiden)', validators=[Optional(), Length(max=150)])  # Vrij in te vullen of AI-gegenereerd

    is_auction   = BooleanField('Bieden toestaan i.p.v. vaste prijs?')
    price        = DecimalField('Vaste prijs (€)', places=2, validators=[
        Optional(), NumberRange(min=0.01, message="Prijs moet positief zijn.")
    ])
    auction_min  = DecimalField('Minimum bod (€)', places=2, validators=[
        Optional(), NumberRange(min=0.01, message="Minimum bod moet positief zijn.")
    ])
    auction_days = IntegerField('Aantal dagen voor veiling', validators=[
        Optional(), NumberRange(min=1, max=30, message="Aantal dagen moet tussen 1 en 30 liggen.")
    ])


    allow_shipping       = BooleanField('Verzenden toegestaan')
    shipping_cost        = DecimalField('Verzendkosten (€)', places=2, validators=[Optional(), NumberRange(min=0)])
    pickup_only          = BooleanField('Alleen afhalen')
    platform_payment_only = BooleanField('Alleen platformbetaling')
    cash_payment_only    = BooleanField('Alleen contante betaling')
    is_admin             = BooleanField('Admin status')


    rek = SelectField('Rek', coerce=int, validators=[Optional()])
    verdieping = SelectField('Verdieping', coerce=int, validators=[Optional()])
    positie = SelectField('Positie', choices=[('links','Links'),('midden','Midden'),('rechts','Rechts')], validators=[Optional()])
    submit       = SubmitField('Opslaan')

    def validate(self, extra_validators=None):
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False

        if self.is_auction.data:
            if not self.auction_min.data:
                self.auction_min.errors.append('Min. bod verplicht bij veiling.')
                return False
            if not self.auction_days.data:
                self.auction_days.errors.append('Aantal dagen verplicht bij veiling.')
                return False
            if not (1 <= self.auction_days.data <= 30):
                self.auction_days.errors.append('Aantal dagen moet tussen 1 en 30 liggen.')
                return False
            
            # Check of de veiling einddatum in de toekomst ligt
            auction_end = datetime.utcnow() + timedelta(days=self.auction_days.data)
            if auction_end <= datetime.utcnow():
                self.auction_days.errors.append('Einddatum moet in de toekomst liggen.')
                return False
        else:
            if not self.price.data:
                self.price.errors.append('Prijs verplicht bij vaste verkoop.')
                return False

        return True


# ─────────── PROFIEL ───────────

class UpdateProfileForm(FlaskForm):
    username = StringField('Naam', validators=[
        DataRequired(), Length(max=150)
    ])

    email = StringField('E-mailadres', validators=[
        DataRequired(), Email()
    ])

    street = StringField('Straat', validators=[
        DataRequired(), Length(max=100)
    ])

    house_number = StringField('Huisnummer', validators=[
        DataRequired(), Length(max=10)
    ])

    postal_code = StringField('Postcode', validators=[
        DataRequired(),
        Regexp(r'^\d{4}$', message="Postcode moet uit 4 cijfers bestaan.")  # Belgische postcode
    ])

    city = StringField('Stad', validators=[
        DataRequired(), Length(max=100)
    ])

    business_name = StringField('Winkelnaam', validators=[
        Optional(), Length(max=150)
    ])

    image = FileField('Profielfoto', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Alleen JPG of PNG toegestaan.')
    ])

    show_on_map = BooleanField("Zichtbaar op de kaart")

    submit = SubmitField('Bijwerken')

    def validate_business_name(self, business_name):
        if business_name.data != current_user.business_name:
            user = User.query.filter_by(business_name=business_name.data).first()
            if user:
                raise ValidationError('Deze winkelnaam is al in gebruik. Kies een andere.')


# ─────────── BERICHT ───────────

class MessageForm(FlaskForm):
    content = TextAreaField('Bericht', validators=[
        DataRequired(), Length(min=1, max=500)
    ])
    submit = SubmitField('Stuur bericht')


# ─────────── BOD ───────────

class BidForm(FlaskForm):
    amount = DecimalField('Bod (€)', places=2, validators=[
        InputRequired(), NumberRange(min=0.01, message="Bod moet groter zijn dan nul.")
    ])
    submit = SubmitField('Plaats bod')


# ─────────── REPLY ───────────

class ReplyForm(FlaskForm):
    reply = TextAreaField('Jouw antwoord', validators=[DataRequired()])
    submit = SubmitField('Verzend Antwoord')



# ─────────── SHIPPING ───────────



# forms.py

class ShippingForm(FlaskForm):
    allow_shipping = BooleanField('Verzending toestaan?')
    shipping_cost = DecimalField('Verzendkost (€)', places=2, validators=[
        Optional(), NumberRange(min=0, message='Verzendkost moet positief zijn.')
    ])
    pickup_only = BooleanField('Afhalen toestaan?')  # <-- precies zoals in model
    platform_payment_only = BooleanField('Betaling via platform toestaan', default=True)
    cash_payment_allowed = BooleanField('Betaling ter plaatse toestaan')

    submit = SubmitField('Opslaan')

    def validate(self, extra_validators=None):
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False
        
        if not self.allow_shipping.data and not self.pickup_only.data:
            self.allow_shipping.errors.append('Je moet minstens één transportmethode kiezen.')
            self.pickup_only.errors.append('')
            return False
        
        if not self.platform_payment_only.data and not self.cash_payment_allowed.data:
            self.platform_payment_only.errors.append('Je moet minstens één betaalmethode kiezen.')
            self.cash_payment_allowed.errors.append('')
            return False

        return True




# ─────────── POSTCARD ───────────


from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, BooleanField, DateTimeField, FileField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from flask_wtf.file import FileAllowed

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField, DecimalField, BooleanField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, Optional, NumberRange
from flask_wtf.file import FileAllowed

class PostcardForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired()])
    description = TextAreaField('Beschrijving', validators=[Optional()])
    
    condition = SelectField('Staat', choices=[
        ('Uitstekend', 'Uitstekend'),
        ('Goed', 'Goed'),
        ('Redelijk', 'Redelijk'),
        ('Slecht', 'Slecht')
    ], validators=[Optional()])
    
    front_image = FileField('Voorzijde Afbeelding', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Alleen afbeeldingen zijn toegestaan!'), Optional()])
    back_image = FileField('Achterzijde Afbeelding', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Alleen afbeeldingen zijn toegestaan!'), Optional()])
    publisher = StringField('Uitgever (optioneel)', validators=[Optional()])

    price = DecimalField('Prijs (€)', places=2, rounding=None, validators=[Optional(), NumberRange(min=0)])
    
    is_auction = BooleanField('Veiling actief')
    auction_min_price = DecimalField('Minimum veilingprijs (€)', places=2, validators=[Optional(), NumberRange(min=0)])
    auction_end = DateTimeField('Veiling einddatum', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    allow_shipping       = BooleanField('Verzenden toegestaan')
    shipping_cost        = DecimalField('Verzendkosten (€)', places=2, validators=[Optional(), NumberRange(min=0)])
    pickup_only          = BooleanField('Alleen afhalen')
    platform_payment_only = BooleanField('Alleen platformbetaling')
    cash_payment_only    = BooleanField('Alleen contante betaling')
    is_admin             = BooleanField('Admin status')
    
    rek = SelectField('Rek', coerce=int, validators=[Optional()])
    verdieping = SelectField('Verdieping', coerce=int, validators=[Optional()])
    positie = SelectField('Positie', choices=[('links','Links'),('midden','Midden'),('rechts','Rechts')], validators=[Optional()])
    submit = SubmitField('Opslaan')

   

    
    
class PosterForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired()])
    description = TextAreaField('Beschrijving', validators=[Optional()])
    
    condition = SelectField('Staat', choices=[
        ('Uitstekend', 'Uitstekend'),
        ('Goed', 'Goed'),
        ('Redelijk', 'Redelijk'),
        ('Slecht', 'Slecht')
    ], validators=[Optional()])
    
    front_image = FileField('Voorzijde Afbeelding', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Alleen afbeeldingen zijn toegestaan!'), Optional()])
    back_image = FileField('Achterzijde Afbeelding', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Alleen afbeeldingen zijn toegestaan!'), Optional()])
    publisher = StringField('Uitgever (optioneel)', validators=[Optional()])

    price = DecimalField('Prijs (€)', places=2, rounding=None, validators=[Optional(), NumberRange(min=0)])
    
    is_auction = BooleanField('Veiling actief')
    auction_min_price = DecimalField('Minimum veilingprijs (€)', places=2, validators=[Optional(), NumberRange(min=0)])
    auction_end = DateTimeField('Veiling einddatum', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    
    allow_shipping       = BooleanField('Verzenden toegestaan')
    shipping_cost        = DecimalField('Verzendkosten (€)', places=2, validators=[Optional(), NumberRange(min=0)])
    pickup_only          = BooleanField('Alleen afhalen')
    platform_payment_only = BooleanField('Alleen platformbetaling')
    cash_payment_only    = BooleanField('Alleen contante betaling')
    is_admin             = BooleanField('Admin status')
    
    rek = SelectField('Rek', coerce=int, validators=[Optional()])
    verdieping = SelectField('Verdieping', coerce=int, validators=[Optional()])
    positie = SelectField('Positie', choices=[('links','Links'),('midden','Midden'),('rechts','Rechts')], validators=[Optional()])
    submit = SubmitField('Opslaan')


                