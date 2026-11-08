(() => {
  const dashboard = document.querySelector("[data-dashboard]");
  if (!dashboard) return;

  const form = dashboard.querySelector("[data-filters]");
  const status = dashboard.querySelector("[data-status]");
  const endpoint = dashboard.dataset.endpoint;
  const metricElements = dashboard.querySelectorAll("[data-metric]");
  const skillElements = dashboard.querySelectorAll("[data-skill]");
  const plotConfig = {
    displayModeBar: false,
    responsive: true,
    scrollZoom: false,
  };
  const plotLayout = {
    autosize: true,
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "Manrope, sans-serif", color: "#c5cfdf", size: 11 },
    margin: { l: 8, r: 12, t: 12, b: 12 },
    xaxis: { gridcolor: "rgba(255,255,255,0.08)", zerolinecolor: "rgba(255,255,255,0.08)" },
    yaxis: { gridcolor: "rgba(255,255,255,0.08)", zerolinecolor: "rgba(255,255,255,0.08)" },
    showlegend: false,
  };

  async function loadDashboard() {
    if (!window.Plotly) {
      status.textContent = "The chart library did not load. Check your connection and reload the page.";
      status.classList.add("is-error");
      return;
    }

    status.textContent = "Updating this filtered view…";
    status.classList.remove("is-error");
    const query = new URLSearchParams(new FormData(form));

    try {
      const response = await fetch(`${endpoint}?${query.toString()}`, {
        headers: { Accept: "application/json" },
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Could not load market insights.");

      metricElements.forEach((element) => {
        const key = element.dataset.metric;
        element.textContent = new Intl.NumberFormat().format(payload.metrics[key] ?? 0);
      });
      skillElements.forEach((element) => {
        const skill = element.dataset.skill;
        element.textContent = new Intl.NumberFormat().format(
          payload.metrics.core_skills[skill] ?? 0,
        );
      });

      Object.entries(payload.charts).forEach(([name, figure]) => {
        const target = dashboard.querySelector(`[data-chart="${name}"]`);
        if (target) {
          window.Plotly.react(target, figure.data, { ...plotLayout, ...figure.layout }, plotConfig);
        }
      });

      dashboard.querySelector("[data-source]").textContent = payload.metadata.source;
      dashboard.querySelector("[data-updated]").textContent = formatDate(payload.metadata.updated_at);
      dashboard.querySelector("[data-methodology]").textContent = payload.metadata.methodology;
      updateSources(payload);
      const count = payload.metrics.opportunities;
      const recordLabel = payload.metadata.demo === "true" ? "example record" : "record";
      status.textContent = `${new Intl.NumberFormat().format(count)} ${recordLabel}${count === 1 ? "" : "s"} match your choices.`;
      if (count === 0) status.textContent += " Try widening the date range or clearing a filter.";
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : "Could not load market insights.";
      status.classList.add("is-error");
    }
  }

  function updateSources(payload) {
    const list = dashboard.querySelector("[data-source-list]");
    const summary = dashboard.querySelector("[data-source-summary]");
    if (!list || !summary) return;

    summary.textContent = payload.metadata.source;
    list.replaceChildren();

    const sources = payload.sources.length
      ? payload.sources
      : [{ label: payload.metadata.source, url: "" }];
    sources.forEach((source) => {
      const item = document.createElement("li");
      if (source.url) {
        const link = document.createElement("a");
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.append(document.createTextNode(source.label));
        const arrow = document.createElement("span");
        arrow.textContent = " ↗";
        link.append(arrow);
        item.append(link);
      } else {
        item.textContent = source.label;
      }
      list.append(item);
    });
  }

  function formatDate(value) {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "UTC",
    }).format(parsed) + " UTC";
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    loadDashboard();
  });
  form.addEventListener("reset", () => {
    window.setTimeout(loadDashboard, 0);
  });
  loadDashboard();
})();
