const filter = document.querySelector("#issueFilter");
const table = document.querySelector("#issuesTable");

if (filter && table) {
  filter.addEventListener("input", () => {
    const term = filter.value.toLowerCase();
    table.querySelectorAll("tbody tr").forEach((row) => {
      row.style.display = row.textContent.toLowerCase().includes(term) ? "" : "none";
    });
  });
}
