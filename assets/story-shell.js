(() => {
  const meta = window.STORY_META;
  if (!meta) return;
  const escapeHTML = value => String(value || '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const shell = document.createElement('div');
  shell.id = 'site-story-shell-root';
  shell.innerHTML = `
    <nav class="site-story-bar" aria-label="案例故事导航">
      <a class="site-story-bar__back" href="${escapeHTML(meta.indexHref)}">← 返回案例库</a>
      <div class="site-story-bar__identity"><span>CASE ${escapeHTML(meta.num)} / ${escapeHTML(meta.storyCount || '')}</span><strong>${escapeHTML(meta.title)}</strong></div>
      <div class="site-story-bar__nav">
        <a href="${meta.prev ? escapeHTML(meta.prev.href) : '#'}" ${meta.prev ? '' : 'aria-disabled="true"'} title="${meta.prev ? escapeHTML(meta.prev.title) : '已经是第一篇'}">上一篇</a>
        <a href="${meta.next ? escapeHTML(meta.next.href) : '#'}" ${meta.next ? '' : 'aria-disabled="true"'} title="${meta.next ? escapeHTML(meta.next.title) : '已经是最后一篇'}">下一篇</a>
      </div>
    </nav>`;
  document.body.prepend(shell);

  const courses = (meta.relatedChapters || []).map(chapter => {
    const number = String(chapter.num || '');
    const label = number.startsWith('ML') ? number : `CH${number}`;
    return `<a href="${escapeHTML(chapter.href)}"><span>${escapeHTML(label)}</span>${escapeHTML(chapter.title)}</a>`;
  }).join('');
  const tags = (meta.tags || []).map(tag => `<span>${escapeHTML(tag)}</span>`).join('');
  const debrief = document.createElement('aside');
  debrief.className = 'site-story-debrief';
  debrief.setAttribute('aria-label', '案例学习复盘');
  debrief.innerHTML = `
    <div class="site-story-debrief__kicker">CASE DEBRIEF · ${escapeHTML(meta.category)} · ${escapeHTML(meta.duration)} MIN</div>
    <h2>故事结束，把方法带回课程</h2>
    <p class="site-story-debrief__subtitle">你刚刚完成了“${escapeHTML(meta.title)}”。回到相关课程，用结构化框架复盘自己的判断顺序。</p>
    <div class="site-story-debrief__tags">${tags}</div>
    <div class="site-story-debrief__courses">${courses}</div>
    <div class="site-story-debrief__actions"><a href="${escapeHTML(meta.indexHref)}">查看全部案例</a>${meta.next ? `<a href="${escapeHTML(meta.next.href)}">下一个案例：${escapeHTML(meta.next.title)} →</a>` : `<a href="${escapeHTML(meta.homeHref)}">回到课程首页 →</a>`}</div>`;
  document.body.append(debrief);
})();
