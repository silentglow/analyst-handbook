(() => {
  const engine = document.querySelector('[data-course-engine]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (engine && !reducedMotion) {
    const nodes = [...engine.querySelectorAll('.decision-pipeline span')];
    let activeIndex = 0;
    window.setInterval(() => {
      nodes[activeIndex]?.classList.remove('is-active');
      activeIndex = (activeIndex + 1) % nodes.length;
      nodes[activeIndex]?.classList.add('is-active');
    }, 1450);
  }

  const rail = document.querySelector('.stage-rail');
  const links = [...document.querySelectorAll('[data-stage-link]')];
  const stages = [...document.querySelectorAll('[data-course-stage]')];
  if (!rail || !links.length || !stages.length) return;

  const setCurrentStage = id => {
    links.forEach(link => {
      const current = link.dataset.stageLink === id;
      link.classList.toggle('is-current', current);
      if (current) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });

    const active = links.find(link => link.dataset.stageLink === id);
    if (active && rail.scrollWidth > rail.clientWidth) {
      const targetLeft = active.offsetLeft - (rail.clientWidth - active.offsetWidth) / 2;
      rail.scrollTo({ left: Math.max(0, targetLeft), behavior: reducedMotion ? 'auto' : 'smooth' });
    }
  };

  const stageObserver = new IntersectionObserver(entries => {
    const visible = entries
      .filter(entry => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
    if (visible[0]) setCurrentStage(visible[0].target.dataset.courseStage);
  }, { rootMargin: '-24% 0px -54% 0px', threshold: [0, .08, .22, .45] });

  const visualObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        visualObserver.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -16% 0px', threshold: .12 });

  stages.forEach(stage => {
    stageObserver.observe(stage);
    visualObserver.observe(stage);
  });

  links.forEach(link => link.addEventListener('click', () => setCurrentStage(link.dataset.stageLink)));
  setCurrentStage(stages[0].dataset.courseStage);
})();
