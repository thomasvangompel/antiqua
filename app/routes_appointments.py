from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import AppointmentSlot

bp_appointments = Blueprint('appointments', __name__)

@bp_appointments.route('/api/appointments/save', methods=['POST'])
@login_required
def save_appointment_slots():
    data = request.get_json()
    slots = data.get('slots', [])
    book_id = data.get('book_id')
    for slot in slots:
        year = slot['year']
        month = slot['month']
        day = slot['day']
        time = slot['time']
        db.session.add(AppointmentSlot(
            user_id=current_user.id,
            book_id=book_id,
            year=year,
            month=month,
            day=day,
            time=time
        ))
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Tijdsloten opgeslagen'})
