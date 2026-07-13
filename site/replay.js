(async function () {
  const params = new URLSearchParams(location.search);
  let index = [];
  try {
    index = await fetchJSON("../data/trials_index.json");
  } catch (e) {
    document.getElementById("list-empty").hidden = false;
    console.error(e);
    return;
  }

  if (index.length === 0) {
    document.getElementById("list-empty").hidden = false;
    return;
  }

  populateFilter("filter-model", [...new Set(index.map((t) => t.model_name))].sort());
  populateFilter("filter-task", [...new Set(index.map((t) => t.task_type))].sort());
  populateFilter("filter-condition", [...new Set(index.map((t) => t.condition))].sort());

  document.getElementById("filter-model").value = params.get("model") || "";
  document.getElementById("filter-task").value = params.get("task_type") || "";
  document.getElementById("filter-condition").value = params.get("condition") || "";

  for (const id of ["filter-model", "filter-task", "filter-condition", "filter-correct"]) {
    document.getElementById(id).addEventListener("change", renderList);
  }

  renderList();

  function populateFilter(id, values) {
    const select = document.getElementById(id);
    for (const v of values) {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = v;
      select.appendChild(opt);
    }
  }

  function currentFilters() {
    return {
      model: document.getElementById("filter-model").value,
      task: document.getElementById("filter-task").value,
      condition: document.getElementById("filter-condition").value,
      correct: document.getElementById("filter-correct").value,
    };
  }

  function renderList() {
    const f = currentFilters();
    const filtered = index.filter((t) => {
      if (f.model && t.model_name !== f.model) return false;
      if (f.task && t.task_type !== f.task) return false;
      if (f.condition && t.condition !== f.condition) return false;
      if (f.correct === "true" && t.is_correct !== true) return false;
      if (f.correct === "false" && t.is_correct !== false) return false;
      return true;
    });

    const list = document.getElementById("trial-list");
    list.innerHTML = "";
    if (filtered.length === 0) {
      list.innerHTML = '<p class="empty-state">No trials match these filters.</p>';
      return;
    }

    for (const t of filtered.slice(0, 300)) {
      const row = document.createElement("div");
      row.className = "trial-row";
      row.dataset.id = t.id;
      row.innerHTML = `
        ${badgeHtml(t)}
        <span class="pill">${t.condition}</span>
        <span class="id">${t.model_name} · ${t.task_type}</span>
      `;
      row.addEventListener("click", () => selectTrial(t.id, row));
      list.appendChild(row);
    }
  }

  function badgeHtml(t) {
    if (t.is_correct === true) return '<span class="badge correct">correct</span>';
    if (t.is_correct === false) return '<span class="badge incorrect">wrong</span>';
    return '<span class="badge unscored">unscored</span>';
  }

  async function selectTrial(id, rowEl) {
    document.querySelectorAll(".trial-row.selected").forEach((r) => r.classList.remove("selected"));
    rowEl.classList.add("selected");

    const detail = document.getElementById("trial-detail");
    detail.innerHTML = '<p class="empty-state">Loading…</p>';

    try {
      const trial = await fetchJSON(`../data/trials/${id}.json`);
      const scenario = await fetchJSON(`../data/scenarios/${trial.scenario_id}.json`);
      renderDetail(trial, scenario);
    } catch (e) {
      detail.innerHTML = `<p class="empty-state">Failed to load trial: ${e.message}</p>`;
      console.error(e);
    }
  }

  function renderDetail(trial, scenario) {
    const detail = document.getElementById("trial-detail");

    const roomsHtml = scenario.rooms
      .map(
        (r) => `
      <div class="room-card">
        <h4>${r.name}${r.name === scenario.initial_location ? " 🅿️" : ""}${r.name === scenario.final_location ? " 🅡" : ""}</h4>
        <ul>${r.containers.map((c) => `<li>${c}</li>`).join("")}</ul>
      </div>`
      )
      .join("");

    const timelineHtml = scenario.event_log
      .map((e) => `<li>${e.text}</li>`)
      .join("");

    const correctnessBadge = badgeHtml(trial);
    const failureTag = trial.failure_tag ? `<span class="pill">${trial.failure_tag}</span>` : "";

    detail.innerHTML = `
      <h3>${scenario.seeker_name} · ${scenario.target_object} <span class="pill">${scenario.condition === "F" ? "False-belief" : "True-belief control"}</span></h3>
      <p class="muted" style="font-size:0.85rem;">
        Trial <code>${trial.id}</code> — model <strong>${trial.model_name}</strong>, task
        <strong>${trial.task_type}</strong>. ${correctnessBadge} ${failureTag}
      </p>

      <h4>Room layout <span class="muted" style="font-weight:400;">(🅿️ = where it was placed, 🅡 = where it ended up)</span></h4>
      <div class="rooms-grid">${roomsHtml}</div>

      <h4>Event log</h4>
      <ol class="timeline">${timelineHtml}</ol>

      <h4>Answer</h4>
      <div class="answer-compare">
        <div class="box">
          <div class="label">Ground truth (Seeker's belief)</div>
          <div class="value">${scenario.ground_truth_belief_location}</div>
        </div>
        <div class="box">
          <div class="label">Model's parsed answer</div>
          <div class="value">${trial.parsed_answer ?? "— unparseable —"}</div>
        </div>
        <div class="box">
          <div class="label">True current location</div>
          <div class="value">${scenario.final_location}</div>
        </div>
      </div>

      <h4>Prompt sent to model</h4>
      <pre class="raw">${escapeHtml(trial.prompt)}</pre>

      <h4>Raw model response</h4>
      <pre class="raw">${escapeHtml(trial.raw_response ?? "(no response — call failed)")}</pre>
    `;
  }

  function escapeHtml(s) {
    return (s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
})();
