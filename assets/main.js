/* 数据分析面试速通课 · 全站交互 */

function prefersReducedMotion() {
  return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// 保留给旧章节使用的打字机能力；新版课程标题默认直接显示。
function initTypewriter(elementId, lines) {
  const element = document.getElementById(elementId);
  if (!element) return;
  if (prefersReducedMotion()) {
    element.textContent = (lines || []).join(' / ');
    return;
  }

  let lineIndex = 0;
  let characterIndex = 0;
  function type() {
    if (lineIndex >= lines.length) return;
    const line = lines[lineIndex];
    if (characterIndex < line.length) {
      const character = document.createElement('span');
      character.className = 'char-reveal gradient-text';
      character.textContent = line[characterIndex];
      element.appendChild(character);
      characterIndex += 1;
      window.setTimeout(type, 80 + Math.random() * 40);
      return;
    }
    if (lineIndex < lines.length - 1) element.appendChild(document.createElement('br'));
    lineIndex += 1;
    characterIndex = 0;
    window.setTimeout(type, 200);
  }
  type();
}

function initReveal() {
  const elements = document.querySelectorAll('.reveal');
  if (!elements.length) return;

  if (prefersReducedMotion() || !('IntersectionObserver' in window)) {
    elements.forEach(element => element.classList.add('visible'));
    return;
  }

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  elements.forEach(element => observer.observe(element));
}

function initOptions() {
  document.querySelectorAll('.option').forEach(option => {
    option.setAttribute('role', 'button');
    option.setAttribute('tabindex', '0');

    const select = () => {
      const group = option.closest('[data-question]') || option.parentElement;
      const siblings = group ? group.querySelectorAll('.option') : [option];
      siblings.forEach(item => {
        item.classList.remove('selected', 'correct', 'incorrect');
        item.setAttribute('aria-pressed', 'false');
      });

      option.classList.add('selected');
      option.setAttribute('aria-pressed', 'true');
      if (option.dataset.correct === 'true') option.classList.add('correct');
      if (option.dataset.correct === 'false') option.classList.add('incorrect');

      if (!option.dataset.feedback || !group) return;
      let feedback = group.querySelector('.option-feedback');
      if (!feedback) {
        feedback = document.createElement('p');
        feedback.className = 'option-feedback';
        feedback.setAttribute('aria-live', 'polite');
        group.appendChild(feedback);
      }
      feedback.textContent = option.dataset.feedback;
      feedback.classList.toggle('is-correct', option.dataset.correct === 'true');
      feedback.classList.toggle('is-incorrect', option.dataset.correct === 'false');
    };

    option.addEventListener('click', select);
    option.addEventListener('keydown', event => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      select();
    });
  });
}

function initReadingMode() {
  const learnMode = document.getElementById('learn-mode');
  const reviewMode = document.getElementById('review-mode');
  const controls = Array.from(document.querySelectorAll('[data-mode-target]'));
  if (!learnMode || !reviewMode || !controls.length) return;

  const validModes = new Set(['learn', 'review']);
  const params = new URLSearchParams(window.location.search);
  const requestedMode = params.get('mode');
  const defaultMode = document.body.dataset.defaultMode || 'learn';

  function setMode(mode, updateAddress = true, moveFocus = false) {
    const nextMode = validModes.has(mode) ? mode : 'learn';
    learnMode.classList.toggle('active', nextMode === 'learn');
    reviewMode.classList.toggle('active', nextMode === 'review');
    learnMode.setAttribute('aria-hidden', String(nextMode !== 'learn'));
    reviewMode.setAttribute('aria-hidden', String(nextMode !== 'review'));
    document.body.dataset.readingMode = nextMode;

    controls.forEach(control => {
      const active = control.dataset.modeTarget === nextMode;
      control.classList.toggle('active', active);
      if (control.matches('button')) control.setAttribute('aria-pressed', String(active));
    });

    // 切换后，新展示区域内的渐显内容应立即可见。
    const activePanel = nextMode === 'learn' ? learnMode : reviewMode;
    activePanel.querySelectorAll('.reveal').forEach(element => element.classList.add('visible'));

    if (updateAddress && window.history && window.history.replaceState) {
      const url = new URL(window.location.href);
      if (nextMode === 'review') url.searchParams.set('mode', 'review');
      else url.searchParams.delete('mode');
      window.history.replaceState({}, '', url);
    }

    if (moveFocus) {
      const target = nextMode === 'review' ? reviewMode.querySelector('h2') : document.querySelector('.lesson-header h1');
      if (target) {
        target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
      }
      document.querySelector('.lesson-header')?.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
    }
  }

  controls.forEach(control => control.addEventListener('click', () => {
    setMode(control.dataset.modeTarget, true, !control.closest('.mode-switch'));
  }));
  setMode(validModes.has(requestedMode) ? requestedMode : defaultMode, false, false);
}

function initTOC() {
  const toggle = document.getElementById('toc-toggle');
  const panel = document.getElementById('toc-panel');
  const overlay = document.getElementById('toc-overlay');
  if (!toggle || !panel || !overlay) return;

  const chapters = Array.isArray(window.TOC_CHAPTERS) ? window.TOC_CHAPTERS : [];
  const modules = Array.isArray(window.COURSE_MODULES) ? window.COURSE_MODULES : [];
  const currentSlug = window.TOC_CURRENT;
  const currentChapter = chapters.find(chapter => chapter.slug === currentSlug);
  const currentModuleId = currentChapter?.module || window.TOC_CURRENT_MODULE;
  const currentModule = modules.find(module => module.id === currentModuleId);

  const make = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };

  const closeButton = make('button', 'toc-close', '关闭');
  closeButton.type = 'button';
  closeButton.setAttribute('aria-label', '关闭课程路线');

  const panelHeader = make('header', 'toc-header');
  const headerTop = make('div', 'toc-header-top');
  const headingCopy = make('div', 'toc-heading-copy');
  headingCopy.append(make('span', '', 'COURSE ROUTE'), make('h2', '', '只看此刻要走的路'));
  headerTop.append(headingCopy, closeButton);

  const stageChapters = chapters.filter(chapter => chapter.module === currentModuleId);
  const stageIndex = Math.max(0, stageChapters.findIndex(chapter => chapter.slug === currentSlug));
  const progress = make('div', 'toc-stage-progress');
  const progressCopy = make('div', 'toc-stage-progress-copy');
  progressCopy.append(make('span', '', `阶段 ${currentModule?.num || ''}`), make('strong', '', currentModule?.title || '当前学习阶段'));
  const progressCount = make('b', '', `${stageIndex + 1} / ${stageChapters.length}`);
  const progressTrack = make('div', 'toc-progress-track');
  const progressFill = make('i');
  progressFill.style.width = `${stageChapters.length ? ((stageIndex + 1) / stageChapters.length) * 100 : 0}%`;
  progressTrack.append(progressFill);
  progress.append(progressCopy, progressCount, progressTrack);
  panelHeader.append(headerTop, progress);

  const route = make('div', 'toc-route');
  route.append(make('p', 'toc-route-label', '本阶段路线'));
  stageChapters.forEach((chapter, index) => {
    const link = document.createElement('a');
    link.href = chapter.href;
    const isCurrent = chapter.slug === currentSlug;
    const isDone = index < stageIndex;
    link.className = `toc-route-item${isCurrent ? ' active' : ''}${isDone ? ' done' : ''}`;
    if (isCurrent) link.setAttribute('aria-current', 'page');
    const marker = make('span', 'toc-route-marker', isDone ? '✓' : chapter.num);
    const copy = make('span', 'toc-route-item-copy');
    copy.append(make('strong', '', chapter.title), make('small', '', isCurrent ? '正在学习' : (isDone ? '已经过' : '接下来')));
    link.append(marker, copy);
    route.append(link);
  });

  const otherStages = make('div', 'toc-other-stages');
  otherStages.append(make('p', 'toc-route-label', '完整课程地图'));
  modules.forEach(module => {
    if (module.id === currentModuleId) return;
    const details = make('details', 'toc-stage-group');
    const summary = document.createElement('summary');
    const title = make('span', 'toc-stage-title');
    title.append(make('small', '', `阶段 ${module.num}`), make('strong', '', module.title));
    const moduleItems = chapters.filter(chapter => chapter.module === module.id);
    summary.append(title, make('b', '', `${moduleItems.length} 章`));
    const links = make('div', 'toc-stage-links');
    moduleItems.forEach(chapter => {
      const link = document.createElement('a');
      link.href = chapter.href;
      link.append(make('span', '', chapter.num), make('strong', '', chapter.title));
      links.append(link);
    });
    details.append(summary, links);
    otherStages.append(details);
  });

  const fullMap = document.createElement('a');
  fullMap.className = 'toc-full-map';
  fullMap.href = window.location.pathname.includes('/articles/') ? '../courses.html' : 'courses.html';
  fullMap.textContent = '打开完整课程地图 →';
  panel.replaceChildren(panelHeader, route, otherStages, fullMap);

  toggle.setAttribute('aria-controls', panel.id);
  toggle.setAttribute('aria-expanded', 'false');

  function open() {
    panel.classList.add('open');
    overlay.classList.add('open');
    toggle.setAttribute('aria-expanded', 'true');
    document.body.classList.add('toc-open');
    closeButton.focus();
  }

  function close(returnFocus = false) {
    panel.classList.remove('open');
    overlay.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('toc-open');
    if (returnFocus) toggle.focus();
  }

  toggle.addEventListener('click', () => panel.classList.contains('open') ? close() : open());
  closeButton.addEventListener('click', () => close(true));
  overlay.addEventListener('click', () => close());
  panel.addEventListener('click', event => { if (event.target.closest('a')) close(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && panel.classList.contains('open')) close(true); });
}

function initMetricExplorer() {
  document.querySelectorAll('[data-metric-explorer]').forEach(explorer => {
    const rows = Array.from(explorer.querySelectorAll('.data-row[data-insight]'));
    const title = explorer.querySelector('[data-metric-title]');
    const insight = explorer.querySelector('[data-metric-insight]');
    const question = explorer.querySelector('[data-metric-question]');
    if (!rows.length || !title || !insight || !question) return;

    const select = row => {
      rows.forEach(item => {
        const active = item === row;
        item.classList.toggle('is-selected', active);
        item.setAttribute('aria-pressed', String(active));
      });
      title.textContent = row.querySelector('.data-label')?.textContent?.trim() || '当前指标';
      insight.textContent = row.dataset.insight || '';
      question.textContent = row.dataset.question || '';
      const panel = explorer.querySelector('.metric-insight');
      panel?.classList.remove('has-update');
      window.requestAnimationFrame(() => panel?.classList.add('has-update'));
    };

    rows.forEach(row => {
      row.setAttribute('aria-pressed', 'false');
      row.addEventListener('click', () => select(row));
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initReveal();
  initOptions();
  initMetricExplorer();
  initReadingMode();
  initTOC();
});
