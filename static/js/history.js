"use strict";

// Filters the bounded set of recent history rows already rendered by Flask.
const searchInput = document.getElementById("history-search");
const historyRows = Array.from(document.querySelectorAll(".history-row"));
const emptyMessage = document.getElementById("filter-empty");
const visibleCount = document.getElementById("visible-count");

if (searchInput && historyRows.length) {
  searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim().toLocaleLowerCase();
    let visible = 0;

    historyRows.forEach((row) => {
      const matches = row.dataset.filter.toLocaleLowerCase().includes(query);
      row.hidden = !matches;
      if (matches) visible += 1;
    });

    emptyMessage.hidden = visible !== 0;
    visibleCount.textContent = `${visible} ${visible === 1 ? "record" : "records"}`;
  });
}
