
# Antiqua

Antiqua is een webapplicatie voor het beheren, verkopen en analyseren van boeken, postkaarten en posters in een antiquariaat.

## Features
- Gebruikersregistratie en login
- Toevoegen, bewerken en verwijderen van boeken, postkaarten en posters
- Winkelwagen en checkout functionaliteit
- Afspraak maken voor ophalen
- Dashboard voor verkopers en admins
- Berichten sturen tussen gebruikers
- Statistieken en analytics voor boeken
- Uploaden van afbeeldingen
- Beheer van genres, tags en auteurs

## Installatie
1. **Clone de repository**
	```
	git clone https://github.com/thomasvangompel/antiqua.git
	```
2. **Ga naar de projectmap**
	```
	cd antiqua
	```
3. **Installeer de vereiste Python packages**
	```
	pip install -r requirements.txt
	```
4. **Start de applicatie**
	```
	python run.py
	```

## Projectstructuur
- `app/` - Bevat de hoofdcode van de webapplicatie
- `app/templates/` - HTML templates
- `app/static/` - Statische bestanden (CSS, JS, afbeeldingen)
- `instance/` - Databasebestand
- `migrations/` - Database migraties
- `requirements.txt` - Vereiste Python packages
- `run.py` - Startpunt van de applicatie

## Database
De applicatie gebruikt SQLite als standaard database. Het bestand staat in `instance/site.db`.

## Licentie
Dit project is open source en mag vrij gebruikt en aangepast worden.

## Contact
Voor vragen of bijdragen: [thomasvangompel op GitHub](https://github.com/thomasvangompel)
