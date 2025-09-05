from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.models import AppointmentSlot, Book
from app import db

bp_pickup = Blueprint('pickup', __name__)

@bp_pickup.route('/api/appointments/available/<int:book_id>', methods=['GET'])
@login_required
def get_available_slots(book_id):
    if book_id == 0:
        slots = AppointmentSlot.query.filter_by(book_id=None, reserved_by_id=None).order_by(
            AppointmentSlot.year, AppointmentSlot.month, AppointmentSlot.day,
            AppointmentSlot.time.asc()
        ).all()
    else:
        slots = AppointmentSlot.query.filter_by(book_id=book_id, reserved_by_id=None).order_by(
            AppointmentSlot.year, AppointmentSlot.month, AppointmentSlot.day,
            AppointmentSlot.time.asc()
        ).all()
    data = [
        {
            'id': slot.id,
            'year': slot.year,
            'month': slot.month,
            'day': slot.day,
            'time': slot.time
        } for slot in slots
    ]
    return jsonify(data)

@bp_pickup.route('/api/appointments/reserve', methods=['POST'])
@login_required
def reserve_slot():
    slot_id = request.json.get('slot_id')
    slot = AppointmentSlot.query.get_or_404(slot_id)
    if slot.reserved_by_id:
        return jsonify({'status': 'error', 'message': 'Tijdslot is al gereserveerd'}), 400
    slot.reserved_by_id = current_user.id
    slot.reserved_at = db.func.now()
    db.session.commit()
    # Bevestigingsmail sturen
    from flask_mail import Message
    from app import mail
    boek_title = slot.book.title if slot.book else 'Onbekend boek'
    msg = Message(
        subject='Bevestiging afhaalafspraak',
        recipients=[current_user.email],
        body=f'Je hebt een afhaalafspraak gemaakt voor het boek "{boek_title}" op {slot.day}-{slot.month+1}-{slot.year} om {slot.time}.'
    )
    mail.send(msg)
    return jsonify({'status': 'success', 'message': 'Tijdslot gereserveerd'})
