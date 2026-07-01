/* ========================================
   共用JS · 数据分析面试速通课
   每章HTML引用此文件，不需要重复写
   ======================================== */

// ========== 打字机效果 ==========
function initTypewriter(elementId, lines) {
  const el = document.getElementById(elementId);
  if (!el) return;
  let lineIdx = 0, charIdx = 0;
  function type() {
    if (lineIdx >= lines.length) return;
    const line = lines[lineIdx];
    if (charIdx < line.length) {
      const span = document.createElement('span');
      span.className = 'char-reveal gradient-text';
      span.textContent = line[charIdx];
      el.appendChild(span);
      charIdx++;
      setTimeout(type, 80 + Math.random() * 40);
    } else {
      if (lineIdx < lines.length - 1) el.appendChild(document.createElement('br'));
      lineIdx++;
      charIdx = 0;
      setTimeout(type, 200);
    }
  }
  type();
}

// ========== 滚动渐显 ==========
function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// ========== 选择题交互 ==========
function initOptions() {
  document.querySelectorAll('.option').forEach(opt => {
    opt.addEventListener('click', () => {
      // 同组取消其他选中
      const siblings = opt.parentElement.querySelectorAll('.option');
      siblings.forEach(s => {
        s.style.borderColor = 'rgba(255,255,255,0.05)';
        s.style.background = 'rgba(255,255,255,0.02)';
      });
      // 选中当前
      opt.style.borderColor = 'rgba(var(--theme-rgb,94,234,212),0.5)';
      opt.style.background = 'rgba(var(--theme-rgb,94,234,212),0.06)';
    });
  });
}

// ========== 自动初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
  initReveal();
  initOptions();
  initTOC();
});

// ========== 悬浮目录面板 ==========
function initTOC() {
  const toggle = document.getElementById('toc-toggle');
  const panel = document.getElementById('toc-panel');
  const overlay = document.getElementById('toc-overlay');
  if (!toggle || !panel) return;

  // Build chapter list
  if (typeof TOC_CHAPTERS !== 'undefined' && TOC_CHAPTERS.length) {
    let html = '<h3>课程目录</h3>';
    TOC_CHAPTERS.forEach(ch => {
      const link = ch.is_root ? '../index.html' : ch.slug + '.html';
      const isActive = (typeof TOC_CURRENT !== 'undefined' && TOC_CURRENT === ch.slug);
      html += `<a href="${link}" class="toc-item${isActive ? ' active' : ''}"><span class="toc-num">${ch.num}</span>${ch.title}</a>`;
    });
    panel.innerHTML = html;
  }

  function open() {
    panel.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    panel.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  toggle.addEventListener('click', () => {
    panel.classList.contains('open') ? close() : open();
  });

  overlay.addEventListener('click', close);
  
  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && panel.classList.contains('open')) close();
  });
}