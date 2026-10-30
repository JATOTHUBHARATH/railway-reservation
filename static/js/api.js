// Shared helpers used by every page.

async function api(path, method = "GET", body = null) {
  const options = { method, headers: {} };
  if (body !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const res = await fetch(path, options);
  let data = {};
  try { data = await res.json(); } catch (e) { /* empty body */ }
  if (!res.ok) {
    throw new Error(data.error || "Something went wrong");
  }
  return data;
}

let toastTimer;
function toast(message, type = "success") {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = "toast show " + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.className = "toast"; }, 3000);
}

// Prevent HTML injection when printing database text into the page.
function esc(value) {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}
