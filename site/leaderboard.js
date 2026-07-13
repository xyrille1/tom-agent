(async function () {
  const legend = document.getElementById("gap-legend");
  legend.innerHTML = `
    <span><span class="swatch" style="background:var(--series-f)"></span>False-belief (F)</span>
    <span><span class="swatch" style="background:var(--series-t)"></span>True-belief control (T)</span>
  `;

  let scores;
  try {
    scores = await fetchJSON("../data/scores.json");
  } catch (e) {
    document.getElementById("gap-empty").hidden = false;
    document.getElementById("scores-empty").hidden = false;
    console.error(e);
    return;
  }

  renderGapChart(scores.gaps);
  renderScoresTable(scores.rows);
  renderAgreementTable(scores.agreement);

  function renderGapChart(gaps) {
    const container = document.getElementById("gap-chart");
    if (!gaps || gaps.length === 0) {
      document.getElementById("gap-empty").hidden = false;
      return;
    }
    container.innerHTML = "";
    for (const gap of gaps) {
      const row = document.createElement("div");
      row.className = "chart-row";

      const label = document.createElement("div");
      label.className = "model-label";
      label.textContent = `${gap.model_name} · ${gap.task_type}`;
      label.title = `ToM gap: ${fmtSigned(gap.tom_gap)}`;

      const group = document.createElement("div");
      group.className = "bar-group";
      group.appendChild(bar("f", gap.f_accuracy, `F accuracy: ${fmtPct(gap.f_accuracy)} (n=${gap.n_f})`));
      group.appendChild(bar("t", gap.t_accuracy, `T accuracy: ${fmtPct(gap.t_accuracy)} (n=${gap.n_t})`));

      row.appendChild(label);
      row.appendChild(group);
      container.appendChild(row);
    }
  }

  function bar(cls, value, title) {
    const track = document.createElement("div");
    track.className = "bar-track";
    track.title = title;

    const fill = document.createElement("div");
    fill.className = `bar-fill ${cls}`;
    const pct = Math.max(0, Math.min(1, value || 0)) * 100;
    fill.style.width = `${pct}%`;

    const valueLabel = document.createElement("span");
    valueLabel.className = "bar-value";
    valueLabel.style.left = `calc(${pct}% + 4px)`;
    valueLabel.textContent = fmtPct(value);

    track.appendChild(fill);
    track.appendChild(valueLabel);
    return track;
  }

  function renderScoresTable(rows) {
    const tbody = document.querySelector("#scores-table tbody");
    if (!rows || rows.length === 0) {
      document.getElementById("scores-empty").hidden = false;
      return;
    }
    for (const row of rows) {
      const tr = document.createElement("tr");
      tr.dataset.model = row.model_name;
      tr.dataset.task = row.task_type;
      tr.dataset.condition = row.condition;
      tr.dataset.acc = row.accuracy;
      tr.dataset.ci = `${row.ci_low.toFixed(2)}-${row.ci_high.toFixed(2)}`;
      tr.dataset.n = row.n;
      tr.innerHTML = `
        <td>${row.model_name}</td>
        <td><span class="pill">${row.task_type}</span></td>
        <td><span class="pill">${row.condition === "F" ? "False-belief" : "True-belief"}</span></td>
        <td class="num">${fmtPct(row.accuracy)}</td>
        <td class="num">[${fmtPct(row.ci_low)}, ${fmtPct(row.ci_high)}]</td>
        <td class="num">${row.n}</td>
        <td><a href="replay.html?model=${encodeURIComponent(row.model_name)}&task_type=${row.task_type}&condition=${row.condition}">browse →</a></td>
      `;
      tbody.appendChild(tr);
    }
    makeSortable(document.getElementById("scores-table"));
  }

  function renderAgreementTable(agreement) {
    const tbody = document.querySelector("#agreement-table tbody");
    if (!agreement || agreement.length === 0) return;
    for (const a of agreement) {
      const tr = document.createElement("tr");
      tr.dataset.model = a.model_name;
      tr.dataset.interactive = a.interactive_accuracy ?? "";
      tr.dataset.quiz = a.quiz_accuracy ?? "";
      tr.dataset.diff = a.point_difference ?? "";
      tr.dataset.pearson = a.pearson_r ?? "";
      tr.dataset.npaired = a.n_paired;
      tr.innerHTML = `
        <td>${a.model_name}</td>
        <td class="num">${fmtPct(a.interactive_accuracy)}</td>
        <td class="num">${fmtPct(a.quiz_accuracy)}</td>
        <td class="num">${fmtSigned(a.point_difference)}</td>
        <td class="num">${a.pearson_r === null || a.pearson_r === undefined ? "—" : a.pearson_r.toFixed(2)}</td>
        <td class="num">${a.n_paired}</td>
      `;
      tbody.appendChild(tr);
    }
    makeSortable(document.getElementById("agreement-table"));
  }
})();
