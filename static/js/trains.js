const body = document.getElementById("trainBody");
const search = document.getElementById("search");
const addForm = document.getElementById("addForm");
const addToggle = document.getElementById("addToggle");

async function loadTrains() {
  const q = search.value.trim();
  try {
    const trains = await api("/api/trains" + (q ? "?q=" + encodeURIComponent(q) : ""));
    if (trains.length === 0) {
      body.innerHTML = '<tr><td colspan="8" class="muted">No train found</td></tr>';
      return;
    }
    body.innerHTML = trains.map(t => {
      const low = t.available_seats <= 5;
      return `
        <tr>
          <td>${t.train_id}</td>
          <td>${esc(t.train_name)}</td>
          <td>${esc(t.source)}</td>
          <td>${esc(t.destination)}</td>
          <td>${t.departure_time ? t.departure_time.slice(0, 5) : "-"}</td>
          <td><span class="badge ${low ? "low" : "ok"}">${t.available_seats} / ${t.total_seats}</span></td>
          <td>${t.fare.toFixed(2)}</td>
          <td class="actions">
            <button class="btn small" onclick="editFare(${t.train_id}, ${t.fare})">Edit fare</button>
            <button class="btn small danger" onclick="removeTrain(${t.train_id})">Delete</button>
          </td>
        </tr>`;
    }).join("");
  } catch (err) {
    body.innerHTML = `<tr><td colspan="8" class="muted">${esc(err.message)}</td></tr>`;
  }
}

async function editFare(id, current) {
  const input = prompt("New fare for train " + id + ":", current);
  if (input === null) return;
  try {
    const res = await api("/api/trains/" + id, "PUT", { fare: input });
    toast(res.message);
    loadTrains();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function removeTrain(id) {
  if (!confirm("Delete train " + id + "?")) return;
  try {
    const res = await api("/api/trains/" + id, "DELETE");
    toast(res.message);
    loadTrains();
  } catch (err) {
    toast(err.message, "error");
  }
}

addForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(addForm).entries());
  try {
    const res = await api("/api/trains", "POST", data);
    toast(res.message);
    addForm.reset();
    addForm.classList.add("hidden");
    loadTrains();
  } catch (err) {
    toast(err.message, "error");
  }
});

addToggle.addEventListener("click", () => addForm.classList.toggle("hidden"));

let timer;
search.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(loadTrains, 250);   // wait until typing pauses
});

loadTrains();
