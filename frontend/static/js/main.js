/* ─────────────────────────────────────────────
   main.js  —  Shared utilities across all pages
───────────────────────────────────────────── */

/**
 * Show a message in a message box element.
 * @param {HTMLElement} el
 * @param {string} text
 * @param {'success'|'error'|'info'} type
 */
function showMessage(el, text, type = "info") {
  el.textContent = text;
  el.className   = `message-box ${type}`;
  el.classList.remove("hidden");
}

/** Hide and clear a message box. */
function clearMessage(el) {
  el.textContent = "";
  el.className   = "message-box hidden";
}

/**
 * Toggle button between loading state and normal state.
 * @param {HTMLButtonElement} btn
 * @param {boolean} loading
 */
function setLoading(btn, loading) {
  const text    = btn.querySelector(".btn-text");
  const spinner = btn.querySelector(".btn-spinner");
  btn.disabled  = loading;
  if (loading) {
    text?.classList.add("hidden");
    spinner?.classList.remove("hidden");
  } else {
    text?.classList.remove("hidden");
    spinner?.classList.add("hidden");
  }
}

/**
 * Toggle password field visibility.
 * @param {string} inputId
 * @param {HTMLButtonElement} btn
 */
function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type  = input.type === "password" ? "text" : "password";
  btn.textContent = input.type === "password" ? "👁" : "🙈";
}

/**
 * Show a toast notification at the bottom-right of the screen.
 * @param {string} message
 * @param {number} duration  ms to auto-hide (default 3000)
 */
function showToast(message, duration = 3000) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.add("hidden"), duration);
}
