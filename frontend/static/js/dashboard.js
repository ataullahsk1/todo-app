/* ─────────────────────────────────────────────
   dashboard.js  —  Todo Dashboard Logic
   Handles: load, create, update, delete todos
───────────────────────────────────────────── */

let allTodos  = [];
let activeFilter = "all";

// ── On load ──────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadTodos();
  setupAddForm();
  setupFilterTabs();
});

// ══════════════════════════════════════════════
//  LOAD TODOS  (GET /todos)
// ══════════════════════════════════════════════
async function loadTodos() {
  try {
    const res  = await fetch("/todos");
    const data = await res.json();
    if (data.success) {
      allTodos = data.todos;
      renderTodos();
      updateStats();
    }
  } catch (err) {
    showToast("⚠️ Could not load tasks. Please refresh.");
  }
}

// ══════════════════════════════════════════════
//  RENDER TODOS
// ══════════════════════════════════════════════
function renderTodos() {
  const list  = document.getElementById("todo-list");
  const empty = document.getElementById("empty-state");
  const now   = new Date();

  // Apply filter
  let filtered = allTodos;
  if (activeFilter === "pending") {
    filtered = allTodos.filter(t => !t.is_done);
  } else if (activeFilter === "done") {
    filtered = allTodos.filter(t => t.is_done);
  } else if (activeFilter === "overdue") {
    filtered = allTodos.filter(t => !t.is_done && t.due_date && new Date(t.due_date) < now);
  }

  // Clear old cards (keep empty-state)
  list.querySelectorAll(".todo-card").forEach(c => c.remove());

  if (filtered.length === 0) {
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");

  filtered.forEach(todo => {
    const card = buildTodoCard(todo, now);
    list.appendChild(card);
  });
}

// ── Build a single todo card element ─────────
function buildTodoCard(todo, now) {
  const dueDate  = todo.due_date ? new Date(todo.due_date) : null;
  const isOverdue= dueDate && !todo.is_done && dueDate < now;

  const card = document.createElement("div");
  card.className = `todo-card priority-${todo.priority}${todo.is_done ? " done" : ""}${isOverdue ? " overdue" : ""}`;
  card.dataset.id = todo.id;

  // ── Priority badge ──
  const priorityColors = { High: "badge-high", Medium: "badge-medium", Low: "badge-low" };
  const priorityEmojis = { High: "🔴", Medium: "🟡", Low: "🟢" };

  // ── Due date badge ──
  let dueBadge = "";
  if (dueDate) {
    const dateStr = dueDate.toLocaleString("en-IN", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
    });
    dueBadge = isOverdue
      ? `<span class="badge badge-overdue">⚠️ Overdue · ${dateStr}</span>`
      : `<span class="badge badge-due">📅 ${dateStr}</span>`;
  }

  // ── Done badge ──
  const doneBadge = todo.is_done ? `<span class="badge badge-done">✅ Done</span>` : "";

  card.innerHTML = `
    <button class="todo-check ${todo.is_done ? "checked" : ""}"
            onclick="toggleDone(${todo.id})"
            title="${todo.is_done ? "Mark as pending" : "Mark as done"}"
            id="check-${todo.id}">
      ${todo.is_done ? "✓" : ""}
    </button>
    <div class="todo-content">
      <div class="todo-title" id="title-${todo.id}">${escapeHtml(todo.title)}</div>
      ${todo.description ? `<div class="todo-desc">${escapeHtml(todo.description)}</div>` : ""}
      <div class="todo-meta">
        <span class="badge ${priorityColors[todo.priority]}">${priorityEmojis[todo.priority]} ${todo.priority}</span>
        ${dueBadge}
        ${doneBadge}
        ${todo.reminder_sent ? `<span class="badge badge-due">📲 Reminded</span>` : ""}
      </div>
    </div>
    <div class="todo-actions">
      <button class="btn btn-danger btn-sm"
              onclick="deleteTodo(${todo.id})"
              id="delete-${todo.id}"
              title="Delete task">🗑</button>
    </div>
  `;
  return card;
}

// ══════════════════════════════════════════════
//  UPDATE STATS
// ══════════════════════════════════════════════
function updateStats() {
  const now     = new Date();
  const total   = allTodos.length;
  const done    = allTodos.filter(t => t.is_done).length;
  const pending = allTodos.filter(t => !t.is_done).length;
  const overdue = allTodos.filter(t => !t.is_done && t.due_date && new Date(t.due_date) < now).length;

  animateNumber("count-total",   total);
  animateNumber("count-pending", pending);
  animateNumber("count-done",    done);
  animateNumber("count-overdue", overdue);
}

function animateNumber(id, target) {
  const el  = document.getElementById(id);
  if (!el) return;
  const start    = parseInt(el.textContent) || 0;
  const duration = 400;
  const step     = (target - start) / (duration / 16);
  let current    = start;
  const tick = () => {
    current += step;
    const done = step > 0 ? current >= target : current <= target;
    el.textContent = done ? target : Math.round(current);
    if (!done) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// ══════════════════════════════════════════════
//  ADD TODO  (POST /todos)
// ══════════════════════════════════════════════
function setupAddForm() {
  const form = document.getElementById("add-todo-form");
  const btn  = document.getElementById("add-btn");
  const msg  = document.getElementById("add-message");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title    = document.getElementById("todo-title").value.trim();
    const desc     = document.getElementById("todo-desc").value.trim();
    const priority = document.getElementById("todo-priority").value;
    const dueDate  = document.getElementById("todo-due").value;

    if (!title) {
      showMessage(msg, "Please enter a task title.", "error");
      return;
    }

    setLoading(btn, true);
    clearMessage(msg);

    try {
      const res  = await fetch("/todos", {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({ title, description: desc, priority, due_date: dueDate }),
      });
      const data = await res.json();

      if (data.success) {
        allTodos.unshift(data.todo);
        form.reset();
        renderTodos();
        updateStats();
        showToast(`✅ "${data.todo.title}" added!`);
      } else {
        showMessage(msg, data.message, "error");
      }
    } catch {
      showMessage(msg, "Network error. Please try again.", "error");
    } finally {
      setLoading(btn, false);
    }
  });
}

// ══════════════════════════════════════════════
//  TOGGLE DONE  (PUT /todos/:id)
// ══════════════════════════════════════════════
async function toggleDone(todoId) {
  const todo = allTodos.find(t => t.id === todoId);
  if (!todo) return;

  const newState = !todo.is_done;

  try {
    const res  = await fetch(`/todos/${todoId}`, {
      method : "PUT",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ is_done: newState }),
    });
    const data = await res.json();

    if (data.success) {
      // Update local state
      const idx = allTodos.findIndex(t => t.id === todoId);
      if (idx !== -1) allTodos[idx] = data.todo;
      renderTodos();
      updateStats();
      showToast(newState ? "✅ Task marked as done!" : "↩️ Task marked as pending.");
    } else {
      showToast("⚠️ Could not update task.");
    }
  } catch {
    showToast("⚠️ Network error.");
  }
}

// ══════════════════════════════════════════════
//  DELETE TODO  (DELETE /todos/:id)
// ══════════════════════════════════════════════
async function deleteTodo(todoId) {
  if (!confirm("Delete this task? This cannot be undone.")) return;

  try {
    const res  = await fetch(`/todos/${todoId}`, { method: "DELETE" });
    const data = await res.json();

    if (data.success) {
      allTodos = allTodos.filter(t => t.id !== todoId);
      // Animate card out
      const card = document.querySelector(`.todo-card[data-id="${todoId}"]`);
      if (card) {
        card.style.transition = "all .3s ease";
        card.style.opacity    = "0";
        card.style.transform  = "translateX(20px)";
        setTimeout(() => { renderTodos(); updateStats(); }, 300);
      } else {
        renderTodos();
        updateStats();
      }
      showToast("🗑️ Task deleted.");
    } else {
      showToast("⚠️ Could not delete task.");
    }
  } catch {
    showToast("⚠️ Network error.");
  }
}

// ══════════════════════════════════════════════
//  FILTER TABS
// ══════════════════════════════════════════════
function setupFilterTabs() {
  document.querySelectorAll(".filter-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      activeFilter = tab.dataset.filter;
      renderTodos();
    });
  });
}

// ── Utility: escape HTML to prevent XSS ──────
function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
