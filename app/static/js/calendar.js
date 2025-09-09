// Eenvoudige kalender met dagselectie en tijdslots
// Vereist een <div id="calendar"></div> en <div id="time-slots"></div> in de template

let selectedSlots = [];
let currentYear, currentMonth;
let lastSelectedDay = null; // Track last selected calendar day

function renderCalendar(year, month) {
  currentYear = year;
  currentMonth = month;
  const calendarDiv = document.getElementById('calendar');
  calendarDiv.innerHTML = '';
  const date = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDay = date.getDay();
  let html = '<div class="d-flex justify-content-between align-items-center mb-2">';
  html += `<button class="btn btn-sm btn-outline-secondary" id="prevMonth">&lt;</button>`;
  html += `<span class="fw-bold">${date.toLocaleString('nl-NL', { month: 'long', year: 'numeric' })}</span>`;
  html += `<button class="btn btn-sm btn-outline-secondary" id="nextMonth">&gt;</button>`;
  html += '</div>';
  html += '<table class="table table-bordered"><thead><tr>';
  ['Zo', 'Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za'].forEach(d => html += `<th>${d}</th>`);
  html += '</tr></thead><tbody><tr>';
  for (let i = 0; i < firstDay; i++) html += '<td></td>';
  for (let day = 1; day <= daysInMonth; day++) {
    if ((firstDay + day - 1) % 7 === 0 && day !== 1) html += '</tr><tr>';
    // Controleer of er een slot is voor deze dag
    const hasSlot = selectedSlots.some(s => s.year === year && s.month === month && s.day === day);
    const slotClass = hasSlot ? 'bg-success text-white' : '';
    html += `<td class="calendar-day ${slotClass}" data-day="${day}">${day}</td>`;
  }
  html += '</tr></tbody></table>';
  calendarDiv.innerHTML = html;
  document.getElementById('prevMonth').onclick = () => renderCalendar(year, month - 1);
  document.getElementById('nextMonth').onclick = () => renderCalendar(year, month + 1);
  document.querySelectorAll('.calendar-day').forEach(td => {
    td.addEventListener('click', function() {
      document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('bg-primary', 'text-white'));
      this.classList.add('bg-primary', 'text-white');
      lastSelectedDay = { year, month, day: parseInt(this.dataset.day) };
      renderTimeSlots(year, month, this.dataset.day);
    });
  });

function addBulkSaveButton() {
  const btn = document.getElementById('openBulkModal');
  if (btn) {
    btn.style.display = selectedSlots.length > 0 ? 'inline-block' : 'none';
  }
}

function renderTimeSlots(year, month, day) {
  const timeSlotsDiv = document.getElementById('time-slots');
  timeSlotsDiv.innerHTML = '<h5>Kies beschikbare tijdsloten</h5>';
  let html = '<div class="d-flex flex-wrap gap-2">';
  for (let hour = 9; hour <= 18; hour++) {
    [":00", ":30"].forEach(min => {
      const time = `${hour}${min}`;
      const isReserved = selectedSlots.some(s => s.year === year && s.month === month && s.day === parseInt(day) && s.time === time);
  html += `<button class="btn time-slot-btn ${isReserved ? 'btn-success' : 'btn-outline-primary'}" data-time="${time}">${time}${isReserved ? ' <span style=\'font-size:0.8em\'>verwijder</span>' : ''}</button>`;
    });
  }
  html += '</div>';

  timeSlotsDiv.innerHTML += html;
  document.querySelectorAll('.time-slot-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const slot = { year, month, day: parseInt(day), time: this.dataset.time, book_id: window.bookId };
      const before = selectedSlots.length;
      // Verwijder ALLE matching slots
      const wasPresent = selectedSlots.some(s => s.year === slot.year && s.month === slot.month && s.day === slot.day && s.time === slot.time);
      if (wasPresent) {
        // Verwijder uit backend
        fetch('/api/appointments/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(slot)
        }).then(res => res.json()).then(data => {
          if (data.status === 'success') {
            selectedSlots = selectedSlots.filter(s => !(s.year === slot.year && s.month === slot.month && s.day === slot.day && s.time === slot.time));
            this.classList.remove('btn-success');
            this.classList.add('btn-outline-primary');
            this.innerHTML = slot.time;
            addBulkSaveButton();
            renderCalendar(year, month);
            renderTimeSlots(year, month, day);
          } else {
            alert('Verwijderen mislukt: ' + (data.message || 'Onbekende fout'));
          }
        });
      } else {
        // Slot was niet aanwezig, dus toevoegen (alleen frontend, opslaan via bulk)
        selectedSlots.push(slot);
        this.classList.remove('btn-outline-primary');
        this.classList.add('btn-success');
        this.innerHTML = `${slot.time} <span style='font-size:0.8em'>verwijder</span>`;
        addBulkSaveButton();
        renderCalendar(year, month);
        renderTimeSlots(year, month, day);
      }
    });
  });

}

function renderReservedSlots(year, month, day) {
  const reservedDivId = 'reserved-slots-list';
  let reservedDiv = document.getElementById(reservedDivId);
  if (!reservedDiv) {
    reservedDiv = document.createElement('div');
    reservedDiv.id = reservedDivId;
    document.getElementById('time-slots').appendChild(reservedDiv);
  }
  // Filter slots voor deze dag
  const reservedSlots = selectedSlots.filter(s => s.year === year && s.month === month && s.day === parseInt(day));
  if (reservedSlots.length === 0) {
    reservedDiv.innerHTML = '<div class="alert alert-info mt-3">Geen gereserveerde tijdsloten voor deze dag.</div>';
    return;
  }
  let html = '<div class="mt-3"><strong>Gereserveerde tijdsloten:</strong><ul class="list-group">';
  reservedSlots.forEach((slot, idx) => {
    html += `<li class="list-group-item d-flex justify-content-between align-items-center">${slot.time}
      <button class="btn btn-sm btn-danger remove-slot-btn" data-index="${idx}">Verwijder</button></li>`;
  });
  html += '</ul></div>';
  reservedDiv.innerHTML = html;
  // Verwijderknoppen
  reservedDiv.querySelectorAll('.remove-slot-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const slotIdx = parseInt(this.dataset.index);
      // Vind het juiste slot in selectedSlots
      const slot = reservedSlots[slotIdx];
      const globalIdx = selectedSlots.findIndex(s => s.year === slot.year && s.month === slot.month && s.day === slot.day && s.time === slot.time);
      if (globalIdx !== -1) {
        selectedSlots.splice(globalIdx, 1);
        renderReservedSlots(year, month, day);
        renderCalendar(year, month); // update kalender kleuren
        renderTimeSlots(year, month, day); // update slot knoppen
      }
    });
  });
}
}

function showSelectedSlots() {
  const feedback = document.getElementById('afspraak-feedback');
  if (selectedSlots.length === 0) {
    feedback.innerHTML = '<div class="alert alert-info">Geen tijdsloten geselecteerd.</div>';
    return;
  }
  let html = '<div class="alert alert-success"><strong>Beschikbare tijdsloten:</strong><ul>';
  selectedSlots.forEach(s => {
    html += `<li>${s.day}-${s.month+1}-${s.year} om ${s.time}</li>`;
  });
  html += '</ul></div>';
  feedback.innerHTML = html;
}

function isThursday(year, month, day) {
  // JS: zondag=0, maandag=1, ..., donderdag=4
  return new Date(year, month, day).getDay() === 4;
}

function getWeekdayName(dayIndex) {
  return ['zondag', 'maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag'][dayIndex];
}

function updateBulkModalOptions() {
  const bulkOptionsDiv = document.getElementById('bulkOptions');
  bulkOptionsDiv.innerHTML = '';
  if (selectedSlots.length > 0 && lastSelectedDay) {
    const dateObj = new Date(lastSelectedDay.year, lastSelectedDay.month, lastSelectedDay.day);
    const weekdayIndex = dateObj.getDay();
    const weekdayName = getWeekdayName(weekdayIndex);
    bulkOptionsDiv.innerHTML = `
      <div class="form-check">
        <input class="form-check-input" type="radio" name="bulkType" id="bulkOnce" value="once" checked>
        <label class="form-check-label" for="bulkOnce">Alleen deze datum</label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="radio" name="bulkType" id="bulkMonth" value="month">
        <label class="form-check-label" for="bulkMonth">Elke ${weekdayName} van deze maand</label>
      </div>
      <div class="form-check">
        <input class="form-check-input" type="radio" name="bulkType" id="bulkYear" value="year">
        <label class="form-check-label" for="bulkYear">Elke ${weekdayName} van dit jaar</label>
      </div>
    `;
  }
}

// Initialiseren
if (document.getElementById('calendar')) {
  const now = new Date();
  window.bookId = document.getElementById('calendar') ? document.getElementById('calendar').dataset.bookId : null;
  // Stel bookId in voor ophalen van tijdsloten
  const bookId = window.bookId === '' || window.bookId === 'all' ? 0 : window.bookId;
  fetch(`/api/appointments/available/${bookId}`)
    .then(res => res.json())
    .then(data => {
      // Zet opgehaalde tijdsloten als geselecteerd
      selectedSlots = data.map(s => ({ year: s.year, month: s.month, day: s.day, time: s.time }));
      renderCalendar(now.getFullYear(), now.getMonth());
    });
  // renderCalendar wordt nu pas aangeroepen na het laden van de slots
}

document.addEventListener('DOMContentLoaded', function() {
  const bulkModal = new bootstrap.Modal(document.getElementById('bulkSlotModal'));
  document.getElementById('openBulkModal').addEventListener('click', function() {
    updateBulkModalOptions();
    bulkModal.show();
  });
  document.getElementById('bulkSlotForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const bulkType = document.querySelector('input[name="bulkType"]:checked').value;
    const bookId = window.bookId === '' ? null : window.bookId;
  let slotsToSend = selectedSlots;
  // Voor 'once' gewoon alle geselecteerde slots meesturen
    fetch('/api/appointments/bulk_reserve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slots: slotsToSend, bulkType: bulkType, book_id: bookId })
    })
    .then(res => res.json())
    .then(data => {
      bulkModal.hide();
      if (data.status === 'success') {
        document.getElementById('afspraak-feedback').innerHTML = `<div class='alert alert-success'>${data.created} tijdslot(s) opgeslagen (${bulkType}).</div>`;
        // Na bulkactie: slots opnieuw ophalen en kalender updaten
        const bookId = window.bookId === '' || window.bookId === 'all' ? 0 : window.bookId;
        fetch(`/api/appointments/available/${bookId}`)
          .then(res => res.json())
          .then(slots => {
            // Normaliseer maand naar 0-based voor de kalender
            selectedSlots = slots.map(s => ({ year: s.year, month: s.month - 1, day: s.day, time: s.time }));
            renderCalendar(currentYear, currentMonth);
          });
      } else {
        document.getElementById('afspraak-feedback').innerHTML = `<div class='alert alert-danger'>Fout: ${data.errors.join(', ')}</div>`;
      }
      selectedSlots = [];
      document.getElementById('openBulkModal').style.display = 'none';
      document.querySelectorAll('.time-slot-btn').forEach(btn => btn.classList.remove('active'));
    });
  });
});
