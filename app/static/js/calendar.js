// Eenvoudige kalender met dagselectie en tijdslots
// Vereist een <div id="calendar"></div> en <div id="time-slots"></div> in de template

let selectedSlots = [];
let currentYear, currentMonth;

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
    html += `<td class="calendar-day" data-day="${day}">${day}</td>`;
  }
  html += '</tr></tbody></table>';
  calendarDiv.innerHTML = html;
  document.getElementById('prevMonth').onclick = () => renderCalendar(year, month - 1);
  document.getElementById('nextMonth').onclick = () => renderCalendar(year, month + 1);
  document.querySelectorAll('.calendar-day').forEach(td => {
    td.addEventListener('click', function() {
      document.querySelectorAll('.calendar-day').forEach(d => d.classList.remove('bg-primary', 'text-white'));
      this.classList.add('bg-primary', 'text-white');
      renderTimeSlots(year, month, this.dataset.day);
    });
  });
}

function renderTimeSlots(year, month, day) {
  const timeSlotsDiv = document.getElementById('time-slots');
  timeSlotsDiv.innerHTML = '<h5>Kies beschikbare tijdsloten</h5>';
  let html = '<div class="d-flex flex-wrap gap-2">';
  for (let hour = 9; hour <= 18; hour++) {
    html += `<button class="btn btn-outline-primary time-slot-btn" data-time="${hour}:00">${hour}:00</button>`;
    html += `<button class="btn btn-outline-primary time-slot-btn" data-time="${hour}:30">${hour}:30</button>`;
  }
  html += '</div>';
  timeSlotsDiv.innerHTML += html;
  document.querySelectorAll('.time-slot-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const slot = { year, month, day, time: this.dataset.time };
      const idx = selectedSlots.findIndex(s => s.year === slot.year && s.month === slot.month && s.day === slot.day && s.time === slot.time);
      if (idx === -1) {
        selectedSlots.push(slot);
        this.classList.add('active');
      } else {
        selectedSlots.splice(idx, 1);
        this.classList.remove('active');
      }
      showSelectedSlots();
      addSaveButton();
    });
  });
}

function addSaveButton() {
  const timeSlotsDiv = document.getElementById('time-slots');
  if (!document.getElementById('save-slots-btn')) {
    const btn = document.createElement('button');
    btn.id = 'save-slots-btn';
    btn.className = 'btn btn-success mt-3';
    btn.textContent = 'Beschikbare tijdsloten opslaan';
    btn.onclick = function() {
      const bookId = window.bookId === '' ? 'all' : window.bookId;
      fetch('/api/appointments/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slots: selectedSlots, book_id: bookId })
      })
      .then(res => res.json())
      .then(data => {
        document.getElementById('afspraak-feedback').innerHTML = `<div class='alert alert-success'>${data.message}</div>`;
      });
    };
    timeSlotsDiv.appendChild(btn);
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
    });
  renderCalendar(now.getFullYear(), now.getMonth());
}
