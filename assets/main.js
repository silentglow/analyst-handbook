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
  const current = window.TOC_CURRENT;
  const moduleNames = new Map(modules.map(module => [module.id, `模块 ${module.num} · ${module.title}`]));

  if (chapters.length) {
    const fragment = document.createDocumentFragment();
    const heading = document.createElement('h3');
    heading.textContent = '课程目录';
    fragment.appendChild(heading);

    let activeModule = null;
    chapters.forEach(chapter => {
      if (chapter.module !== activeModule) {
        activeModule = chapter.module;
        const label = document.createElement('div');
        label.className = 'toc-module-label';
        label.textContent = moduleNames.get(activeModule) || activeModule;
        fragment.appendChild(label);
      }

      const link = document.createElement('a');
      link.href = chapter.href;
      link.className = `toc-item${current === chapter.slug ? ' active' : ''}`;
      if (current === chapter.slug) link.setAttribute('aria-current', 'page');
      const number = document.createElement('span');
      number.className = 'toc-num';
      number.textContent = chapter.num;
      link.append(number, document.createTextNode(chapter.title));
      fragment.appendChild(link);
    });
    panel.replaceChildren(fragment);
  }

  toggle.setAttribute('aria-controls', panel.id);
  toggle.setAttribute('aria-expanded', 'false');

  function open() {
    panel.classList.add('open');
    overlay.classList.add('open');
    toggle.setAttribute('aria-expanded', 'true');
    document.body.classList.add('toc-open');
    panel.querySelector('a')?.focus();
  }

  function close(returnFocus = false) {
    panel.classList.remove('open');
    overlay.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('toc-open');
    if (returnFocus) toggle.focus();
  }

  toggle.addEventListener('click', () => panel.classList.contains('open') ? close() : open());
  overlay.addEventListener('click', () => close());
  panel.addEventListener('click', event => {
    if (event.target.closest('a')) close();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && panel.classList.contains('open')) close(true);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initReveal();
  initOptions();
  initReadingMode();
  initTOC();
});
