const form = document.getElementById("bookForm");
const passengerSel = document.getElementById("passenger");
const trainSel = document.getElementById("train");
const dateInput = document.getElementById("travelDate");
const seatsInput = document.getElementById("seats");
const preview = document.getElementById("preview");

let trains = [];

// Today's date as YYYY-MM-DD in the browser's local time (blocks past dates)
function today() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}
dateInput.min = today();

async function loadOptions() {
  try {
    const [passengers, trainList] = await Promise.all([
      api("/api/passengers"),
      api("/api/trains"),
    ]);
    trains = trainList;

    passengerSel.innerHTML = '<option value="">Select passenger</option>' +
      passengers.map(p =>
        `<option value="${p.passenger_id}">${p.passenger_id} - ${esc(p.passenger_name)}</option>`
      ).join("");

    trainSel.innerHTML = '<option value="">Select train</option>' +
      trains.map(t =>
        `<option value="${t.train_id}">${esc(t.train_name)} (${esc(t.source)} → ${esc(t.destination)}) - ${t.available_seats} seats left</option>`
      ).join("");
  } catch (err) {
    toast(err.message, "error");
  }
}

function updatePreview() {
  const train = trains.find(t => t.train_id === Number(trainSel.value));
  const seats = Number(seatsInput.value);
  if (!train) {
    preview.textContent = "Select a train to see the fare.";
    return;
  }
  if (!seats || seats <= 0) {
    preview.textContent = "Enter a valid number of seats.";
    return;
  }
  const total = (train.fare * seats).toFixed(2);
  const warn = seats > train.available_seats
    ? ` ⚠ Only ${train.available_seats} seats available`
    : "";
  preview.textContent = `${seats} × ₹${train.fare.toFixed(2)} = ₹${total}${warn}`;
}

trainSel.addEventListener("change", updatePreview);
seatsInput.addEventListener("input", updatePreview);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    const res = await api("/api/bookings", "POST", data);
    toast(res.message);
    form.reset();
    seatsInput.value = 1;
    await loadOptions();        // refresh seats left
    updatePreview();
  } catch (err) {
    toast(err.message, "error");
  }
});

loadOptions();
