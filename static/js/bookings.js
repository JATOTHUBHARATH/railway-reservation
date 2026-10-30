const body = document.getElementById("bookingBody");

async function loadBookings() {
  try {
    const list = await api("/api/bookings");
    if (list.length === 0) {
      body.innerHTML = '<tr><td colspan="9" class="muted">No bookings yet</td></tr>';
      return;
    }
    body.innerHTML = list.map(b => {
      const confirmed = b.status === "confirmed";
      return `
        <tr>
          <td>${b.booking_id}</td>
          <td>${esc(b.passenger_name)}</td>
          <td>${esc(b.train_name)}</td>
          <td>${esc(b.source)} → ${esc(b.destination)}</td>
          <td>${esc(b.travel_date)}</td>
          <td>${b.seats_booked}</td>
          <td>${b.total_fare.toFixed(2)}</td>
          <td><span class="badge ${confirmed ? "ok" : "low"}">${esc(b.status)}</span></td>
          <td>${confirmed
            ? `<button class="btn small danger" onclick="cancelBooking(${b.booking_id})">Cancel</button>`
            : "-"}</td>
        </tr>`;
    }).join("");
  } catch (err) {
    body.innerHTML = `<tr><td colspan="9" class="muted">${esc(err.message)}</td></tr>`;
  }
}

async function cancelBooking(id) {
  if (!confirm("Cancel booking " + id + "?")) return;
  try {
    const res = await api("/api/bookings/" + id + "/cancel", "PUT");
    toast(res.message);
    loadBookings();
  } catch (err) {
    toast(err.message, "error");
  }
}

loadBookings();
