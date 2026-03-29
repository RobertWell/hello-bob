const symbolSelect = document.getElementById("symbol-select");
const daysSelect = document.getElementById("days-select");
const refreshButton = document.getElementById("refresh-button");
const errorBanner = document.getElementById("error-banner");

let trendChart = null;

function getInitialState() {
  const params = new URLSearchParams(window.location.search);
  return {
    symbol: params.get("symbol") || null,
    days: params.get("days") || null,
  };
}

function formatSignedPercent(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function formatSignedValue(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}`;
}

function formatVolume(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return new Intl.NumberFormat("en-US").format(value);
}

function setError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.remove("hidden");
}

function clearError() {
  errorBanner.textContent = "";
  errorBanner.classList.add("hidden");
}

function renderSummary(payload) {
  const { summary } = payload;
  document.getElementById("stock-title").textContent = `${payload.symbol} · ${payload.name}`;
  document.getElementById("updated-at").textContent = `Updated ${payload.updated_at}`;
  document.getElementById("latest-close").textContent = summary.latest_close.toFixed(2);

  const changeEl = document.getElementById("day-change");
  changeEl.textContent = `${formatSignedValue(summary.change_amount)} (${formatSignedPercent(summary.change_pct)})`;
  changeEl.className = "pill";
  if (summary.change_amount > 0) {
    changeEl.classList.add("rise");
  } else if (summary.change_amount < 0) {
    changeEl.classList.add("fall");
  }

  document.getElementById("period-change").textContent = formatSignedPercent(summary.period_change_pct);
  document.getElementById("momentum-status").textContent = summary.momentum || "neutral";
  document.getElementById("rsi-value").textContent = summary.rsi_14 !== null ? summary.rsi_14.toFixed(2) : "-";
  document.getElementById("volume-value").textContent = formatVolume(summary.volume);
  document.getElementById("trend-copy").textContent = `${summary.trend_direction || "unknown"} trend with ${summary.momentum || "neutral"} momentum over the selected window.`;
}

function renderChart(payload) {
  const ctx = document.getElementById("trend-chart");
  const labels = payload.series.map((point) => point.date);
  const closeData = payload.series.map((point) => point.close);
  const smaData = payload.series.map((point) => point.sma20);
  const emaData = payload.series.map((point) => point.ema20);

  if (trendChart) {
    trendChart.destroy();
  }

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Close",
          data: closeData,
          borderColor: "#17352d",
          backgroundColor: "rgba(23, 53, 45, 0.12)",
          tension: 0.28,
          borderWidth: 3,
          pointRadius: 0,
          fill: true,
        },
        {
          label: "SMA 20",
          data: smaData,
          borderColor: "#d98e04",
          tension: 0.22,
          borderWidth: 2,
          pointRadius: 0,
        },
        {
          label: "EMA 20",
          data: emaData,
          borderColor: "#9d5333",
          tension: 0.22,
          borderWidth: 2,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          labels: {
            usePointStyle: true,
            boxWidth: 8,
          },
        },
      },
      scales: {
        x: {
          grid: {
            display: false,
          },
        },
        y: {
          grid: {
            color: "rgba(21, 37, 31, 0.08)",
          },
        },
      },
    },
  });
}

async function loadStock() {
  const symbol = symbolSelect.value;
  const days = daysSelect.value;

  refreshButton.disabled = true;
  refreshButton.textContent = "Loading...";

  try {
    const response = await fetch(`/api/stocks/${symbol}?days=${days}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Failed to load stock data");
    }

    clearError();
    renderSummary(payload);
    renderChart(payload);
  } catch (error) {
    setError(error.message);
  } finally {
    refreshButton.disabled = false;
    refreshButton.textContent = "Refresh Trend";
  }
}

refreshButton.addEventListener("click", loadStock);
symbolSelect.addEventListener("change", loadStock);
daysSelect.addEventListener("change", loadStock);

async function bootstrap() {
  try {
    const response = await fetch("/api/stocks");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Failed to load stock list");
    }

    const initial = getInitialState();
    payload.stocks.forEach((stock) => {
      const option = document.createElement("option");
      option.value = stock.symbol;
      option.textContent = `${stock.symbol} · ${stock.name}`;
      symbolSelect.appendChild(option);
    });

    symbolSelect.value = initial.symbol || payload.default_symbol;
    daysSelect.value = initial.days || String(payload.default_days);
    await loadStock();
  } catch (error) {
    setError(error.message);
  }
}

bootstrap();
