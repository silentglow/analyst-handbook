(() => {
  const meta = window.STORY_META;
  if (!meta) return;
  const escapeHTML = value => String(value || '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const shell = document.createElement('div');
  shell.id = 'site-story-shell-root';
  shell.innerHTML = `
    <nav class="site-story-bar" aria-label="案例故事导航">
      <a class="site-story-bar__back" href="${escapeHTML(meta.indexHref)}">← 返回案例库</a>
      <div class="site-story-bar__identity"><span>案例 ${escapeHTML(meta.num)} / ${escapeHTML(meta.storyCount || '')}</span><strong>${escapeHTML(meta.title)}</strong></div>
      <div class="site-story-bar__nav">
        <a href="${meta.prev ? escapeHTML(meta.prev.href) : '#'}" ${meta.prev ? '' : 'aria-disabled="true"'} title="${meta.prev ? escapeHTML(meta.prev.title) : '已经是第一篇'}">上一篇</a>
        <a href="${meta.next ? escapeHTML(meta.next.href) : '#'}" ${meta.next ? '' : 'aria-disabled="true"'} title="${meta.next ? escapeHTML(meta.next.title) : '已经是最后一篇'}">下一篇</a>
      </div>
    </nav>`;
  document.body.prepend(shell);

  const tags = (meta.tags || []).map(tag => `<span>${escapeHTML(tag)}</span>`).join('');
  const debrief = document.createElement('aside');
  debrief.className = 'site-story-debrief';
  debrief.setAttribute('aria-label', '案例学习复盘');
  debrief.innerHTML = `
    <div class="site-story-debrief__kicker">案例复盘 · ${escapeHTML(meta.category)} · ${escapeHTML(meta.duration)} 分钟</div>
    <h2>先别急着记答案，复盘你的判断顺序</h2>
    <p class="site-story-debrief__subtitle">你刚刚完成了“${escapeHTML(meta.title)}”。用下面三个问题检查：自己是在分析证据，还是只是在为最初的猜测找理由。</p>
    <div class="site-story-debrief__tags">${tags}</div>
    <ol class="site-story-debrief__questions"><li><b>01</b><span>我最先检查了什么证据？为什么它应该排在第一步？</span></li><li><b>02</b><span>哪一步最容易发生误判？还缺少什么反证？</span></li><li><b>03</b><span>如果交给业务执行，下一步行动和复核标准是什么？</span></li></ol>
    <div class="site-story-debrief__actions"><a href="${escapeHTML(meta.indexHref)}">查看全部案例</a>${meta.next ? `<a href="${escapeHTML(meta.next.href)}">下一个案例：${escapeHTML(meta.next.title)} →</a>` : `<a href="${escapeHTML(meta.homeHref)}">回到手册首页 →</a>`}</div>`;
  document.body.append(debrief);
})();
