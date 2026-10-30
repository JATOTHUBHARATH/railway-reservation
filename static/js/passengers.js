const body = document.getElementById("passengerBody");
const search = document.getElementById("search");
const addForm = document.getElementById("addForm");
const addToggle = document.getElementById("addToggle");

async function loadPassengers() {
  const q = search.value.trim();
  try {
    const list = await api("/api/passengers" + (q ? "?q=" + encodeURIComponent(q) : ""));
    if (list.length === 0) {
      body.innerHTML = '<tr><td colspan="6" class="muted">No passenger found</td></tr>';
      return;
    }
    body.innerHTML = list.map(p => `
      <tr>
        <td>${p.passenger_id}</td>
        <td>${esc(p.passenger_name)}</td>
        <td>${p.age}</td>
        <td>${esc(p.gender)}</td>
        <td>${esc(p.phone)}</td>
        <td class="actions">
          <button class="btn small" onclick="editPhone(${p.passenger_id}, '${esc(p.phone)}')">Update phone</button>
          <button class="btn small danger" onclick="removePassenger(${p.passenger_id})">Delete</button>
        </td>
      </tr>`).join("");
  } catch (err) {
    body.innerHTML = `<tr><td colspan="6" class="muted">${esc(err.message)}</td></tr>`;
  }
}

async function editPhone(id, current) {
  const input = prompt("New phone (10 digits) for passenger " + id + ":", current);
  if (input === null) return;
  if (!/^[0-9]{10}$/.test(input.trim())) {
    toast("Phone must be exactly 10 digits", "error");
    return;
  }
  try {
    const res = await api("/api/passengers/" + id, "PUT", { phone: input.trim() });
    toast(res.message);
    loadPassengers();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function removePassenger(id) {
  if (!confirm("Delete passenger " + id + "?")) return;
  try {
    const res = await api("/api/passengers/" + id, "DELETE");
    toast(res.message);
    loadPassengers();
  } catch (err) {
    toast(err.message, "error");
  }
}

addForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(addForm).entries());
  try {
    const res = await api("/api/passengers", "POST", data);
    toast(res.message);
    addForm.reset();
    addForm.classList.add("hidden");
    loadPassengers();
  } catch (err) {
    toast(err.message, "error");
  }
});

addToggle.addEventListener("click", () => addForm.classList.toggle("hidden"));

let timer;
search.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(loadPassengers, 250);
});

loadPassengers();
