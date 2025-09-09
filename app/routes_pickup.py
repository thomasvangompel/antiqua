
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.models import AppointmentSlot, Book
from app import db
from datetime import date, timedelta
from flask_mail import Message
from app import mail

bp_pickup = Blueprint('bp_pickup', __name__)

@bp_pickup.route('/api/appointments/delete', methods=['POST'])
@login_required
def delete_appointment_slot():
    data = request.json
    year = data.get('year')
    month = data.get('month')
    day = data.get('day')
    time = data.get('time')
    book_id = data.get('book_id')
    # book_id normaliseren
    if book_id in [None, '', 0, '0', 'null', 'undefined']: book_id = None
    # month normaliseren (JS: 0-based, DB: 1-based)
    if isinstance(month, str):
        try:
            month = int(month)
        except:
            pass
    if month is not None and month < 1:
        month += 1
    from flask_login import current_user
    print(f"[DEBUG] Delete request: user_id={current_user.id}, year={year}, month={month}, day={day}, time={time}, book_id={book_id}")
    slot = AppointmentSlot.query.filter_by(
        user_id=current_user.id,
        year=year,
        month=month,
        day=day,
        time=time,
        book_id=book_id
    ).first()
    print(f"[DEBUG] Found slot: {slot}")
    if slot:
        db.session.delete(slot)
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Slot niet gevonden'}), 404

@bp_pickup.route('/api/appointments/bulk_reserve', methods=['POST'])
@login_required
def bulk_reserve_slots():
    data = request.json
    slots = data.get('slots', [])  # [{year, month, day, time}]
    bulk_type = data.get('bulkType', 'once')
    book_id = data.get('book_id')
    created = 0
    errors = []
    def is_thursday(y, m, d):
        return date(y, m+1, d).weekday() == 3
    if bulk_type == 'once':
        # Sla alle geselecteerde slots op, ongeacht de dag
        for slot in slots:
            s = AppointmentSlot(
                user_id=current_user.id,
                year=slot['year'],
                month=slot['month'],
                day=slot['day'],
                time=slot['time'],
                book_id=book_id
            )
            db.session.add(s)
            created += 1
    elif bulk_type in ['month', 'year'] and slots:
        # Use first slot as template
        first = slots[0]
        y, m, t = first['year'], first['month'], first['time']
        if bulk_type == 'month':
            # All Thursdays in this month
            d = date(y, m+1, 1)
            while d.month == m+1:
                if d.weekday() == 3:
                    s = AppointmentSlot(
                        user_id=current_user.id,
                        year=d.year,
                        month=d.month-1,
                        day=d.day,
                        time=t,
                        book_id=book_id
                    )
                    db.session.add(s)
                    created += 1
                d += timedelta(days=1)
        elif bulk_type == 'year':
            # All Thursdays in this year
            d = date(y, 1, 1)
            while d.year == y:
                if d.weekday() == 3:
                    s = AppointmentSlot(
                        user_id=current_user.id,
                        year=d.year,
                        month=d.month-1,
                        day=d.day,
                        time=t,
                        book_id=book_id
                    )
                    db.session.add(s)
                    created += 1
                d += timedelta(days=1)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        errors.append(str(e))
    return jsonify({'status': 'success' if not errors else 'error', 'created': created, 'errors': errors})

@bp_pickup.route('/api/appointments/available/<int:book_id>', methods=['GET'])
@login_required
def get_available_slots(book_id):
    from flask_login import current_user
    if book_id == 0:
        slots = AppointmentSlot.query.filter_by(book_id=None, reserved_by_id=None, user_id=current_user.id).order_by(
            AppointmentSlot.year, AppointmentSlot.month, AppointmentSlot.day,
            AppointmentSlot.time.asc()
        ).all()
    else:
        slots = AppointmentSlot.query.filter_by(book_id=book_id, reserved_by_id=None, user_id=current_user.id).order_by(
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
    boek_title = slot.book.title if slot.book else 'Onbekend boek'
    msg = Message(
        subject='Bevestiging afhaalafspraak',
        recipients=[current_user.email],
        body=f'Je hebt een afhaalafspraak gemaakt voor het boek "{boek_title}" op {slot.day}-{slot.month+1}-{slot.year} om {slot.time}.'
    )
    mail.send(msg)
    return jsonify({'status': 'success', 'message': 'Tijdslot gereserveerd'})
