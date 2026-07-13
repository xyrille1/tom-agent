// Shared helpers for the static demo site. Every page reads pre-computed
// JSON committed under ../data -- there is no backend and no live model
// calls (NFR "Latency" / "the public site never calls a model API at
// request time").

async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`Failed to load ${path}: ${res.status}`);
  }
  return res.json();
}

function fmtPct(x) {
  if (x === null || x === undefined) return "—";
  return `${(x * 100).toFixed(0)}%`;
}

function fmtSigned(x) {
  if (x === null || x === undefined) return "—";
  const pct = x * 100;
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(0)}%`;
}

function makeSortable(table) {
  const headers = table.querySelectorAll("th[data-sort-key]");
  headers.forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.sortKey;
      const type = th.dataset.sortType || "string";
      const tbody = table.querySelector("tbody");
      const rows = Array.from(tbody.querySelectorAll("tr"));
      const asc = !(th.classList.contains("sorted") && th.classList.contains("asc"));

      rows.sort((a, b) => {
        let av = a.dataset[key];
        let bv = b.dataset[key];
        if (type === "number") {
          av = parseFloat(av);
          bv = parseFloat(bv);
        }
        if (av < bv) return asc ? -1 : 1;
        if (av > bv) return asc ? 1 : -1;
        return 0;
      });

      headers.forEach((h) => h.classList.remove("sorted", "asc"));
      th.classList.add("sorted");
      if (asc) th.classList.add("asc");

      rows.forEach((r) => tbody.appendChild(r));
    });
  });
}
