(() => {
  const safeRead = key => { try { return JSON.parse(localStorage.getItem(key) || 'null'); } catch (_) { return null; } };
  const safeWrite = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) {} };
  document.addEventListener('DOMContentLoaded', () => {
    const cards = [...document.querySelectorAll('[data-lab-card]')];
    const bookmarks = new Set(safeRead('analyst-handbook:bookmarks') || []);
    let latest = null;
    cards.forEach(card => {
      const id = card.dataset.labCard;
      const scenes = Number(card.dataset.scenes || 5);
      const state = safeRead(`analyst-handbook:lab:${id}`);
      const percent = state ? Math.round(((Number(state.scene) + 1) / scenes) * 100) : 0;
      card.style.setProperty('--progress', `${percent}%`);
      card.querySelector('[data-card-progress]').textContent = state?.completed ? '已完成 · 可复习' : percent ? `已学习 ${percent}%` : '尚未开始';
      if (state?.updatedAt && (!latest || state.updatedAt > latest.state.updatedAt)) latest = { card, state, percent };
      const button = card.querySelector('[data-bookmark]');
      if (button) {
        button.classList.toggle('active', bookmarks.has(id));
        button.setAttribute('aria-pressed', String(bookmarks.has(id)));
        button.addEventListener('click', event => {
          event.preventDefault(); event.stopPropagation();
          bookmarks.has(id) ? bookmarks.delete(id) : bookmarks.add(id);
          safeWrite('analyst-handbook:bookmarks', [...bookmarks]);
          button.classList.toggle('active', bookmarks.has(id));
          button.setAttribute('aria-pressed', String(bookmarks.has(id)));
          document.querySelector('[data-bookmark-count]').textContent = bookmarks.size;
        });
      }
    });
    const continueTitle = document.querySelector('[data-continue-title]');
    const continueLink = document.querySelector('[data-continue-link]');
    const continueText = document.querySelector('[data-continue-text]');
    const continueBar = document.querySelector('[data-continue-bar]');
    if (latest && continueTitle && continueLink) {
      continueTitle.textContent = latest.card.querySelector('h3').textContent;
      continueLink.href = latest.card.querySelector('.lab-card-hit').href;
      continueLink.textContent = latest.state.completed ? '重新复习' : '继续这一课';
      continueText.textContent = latest.state.completed ? '这节课已完成，可以进入速览和面试复习。' : `已进行到第 ${Number(latest.state.scene) + 1} 个动画步骤。`;
      continueBar.style.setProperty('--value', `${latest.percent}%`);
    }
    document.querySelector('[data-bookmark-count]')?.replaceChildren(String(bookmarks.size));
    document.querySelector('[data-complete-count]')?.replaceChildren(String(cards.filter(card => safeRead(`analyst-handbook:lab:${card.dataset.labCard}`)?.completed).length));
  });
})();
