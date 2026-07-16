(() => {
  document.addEventListener('DOMContentLoaded', () => {
  const rows = [...document.querySelectorAll('[data-ledger-row]')];
  const search = document.querySelector('[data-ledger-search]');
  const category = document.querySelector('[data-ledger-category]');
  const empty = document.querySelector('[data-ledger-empty]');
  const apply = () => {
    const query = (search?.value || '').trim().toLowerCase();
    const selected = category?.value || 'all';
    let visible = 0;
    rows.forEach(row => {
      const show = (!query || row.dataset.search.includes(query)) && (selected === 'all' || row.dataset.category === selected);
      row.hidden = !show; if (show) visible += 1;
    });
    if (empty) empty.hidden = visible > 0;
  };
  search?.addEventListener('input', apply); category?.addEventListener('change', apply);
  });
})();
