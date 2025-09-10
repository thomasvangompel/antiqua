from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import AppointmentSlot

bp_appointments = Blueprint('appointments', __name__)

@bp_appointments.route('/api/appointments/save', methods=['POST'])
@login_required
def save_appointment_slots():
    try:
        data = request.get_json()
        slots = data.get('slots', [])
        book_id = data.get('book_id')
        if not slots or book_id is None:
            return jsonify({'status': 'error', 'errors': ['slots of book_id ontbreekt']}), 400
        created_count = 0
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
                db.session.add(AppointmentSlot(
                    user_id=current_user.id,
                    book_id=book_id,
                    year=year,
                    month=month,
                    day=day,
                    time=time
                ))
                created_count += 1
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Tijdsloten opgeslagen', 'created': created_count})
    except Exception as e:
        return jsonify({'status': 'error', 'errors': [str(e)]}), 500
