(() => {
  const grid = document.getElementById('story-grid');
  const input = document.getElementById('story-search');
  const buttons = Array.from(document.querySelectorAll('[data-filter]'));
  const empty = document.getElementById('story-empty');
  if (!grid || !input) return;

  let category = 'all';
  const normalize = value => String(value || '').trim().toLowerCase();

  function applyFilters() {
    const query = normalize(input.value);
    let visible = 0;
    grid.querySelectorAll('.story-library-card').forEach(card => {
      const categoryMatch = category === 'all' || card.dataset.category === category;
      const searchMatch = !query || normalize(card.dataset.title).includes(query);
      const show = categoryMatch && searchMatch;
      card.classList.toggle('filtered-out', !show);
      if (show) visible += 1;
    });
    empty.hidden = visible !== 0;
  }

  buttons.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.filter;
    buttons.forEach(item => item.classList.toggle('active', item === button));
    applyFilters();
  }));
  input.addEventListener('input', applyFilters);
})();
