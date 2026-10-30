const body = document.getElementById("reportBody");
const bars = document.getElementById("bars");
const summary = document.getElementById("summary");

async function loadReport() {
  try {
    const rows = await api("/api/report/revenue");
    if (rows.length === 0) {
      body.innerHTML = '<tr><td colspan="3" class="muted">No confirmed bookings yet</td></tr>';
      bars.innerHTML = '<p class="muted">No data</p>';
      summary.innerHTML = "";
      return;
    }

    const totalRevenue = rows.reduce((s, r) => s + r.revenue, 0);
    const totalBookings = rows.reduce((s, r) => s + r.bookings, 0);
    summary.innerHTML = `
      <div class="stat"><span>Total revenue</span><strong>₹${totalRevenue.toFixed(2)}</strong></div>
      <div class="stat"><span>Confirmed bookings</span><strong>${totalBookings}</strong></div>
      <div class="stat"><span>Top train</span><strong>${esc(rows[0].train_name)}</strong></div>`;

    // Bar chart: one sorted horizontal bar per train, drawn with plain CSS
    const max = Math.max(...rows.map(r => r.revenue));
    bars.innerHTML = rows.map(r => `
      <div class="bar-row">
        <span class="bar-label">${esc(r.train_name)}</span>
        <div class="bar-track">
          <div class="bar-fill" style="width:${(r.revenue / max * 100).toFixed(1)}%"></div>
        </div>
        <span class="bar-value">₹${r.revenue.toFixed(2)}</span>
      </div>`).join("");

    body.innerHTML = rows.map(r => `
      <tr>
        <td>${esc(r.train_name)}</td>
        <td>${r.bookings}</td>
        <td>${r.revenue.toFixed(2)}</td>
      </tr>`).join("");
  } catch (err) {
    body.innerHTML = `<tr><td colspan="3" class="muted">${esc(err.message)}</td></tr>`;
  }
}

loadReport();
