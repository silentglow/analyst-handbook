/* 专题课连续演示：不依赖账户、后端或本地学习记录。 */
(() => {
  const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  class TopicPlayer {
    constructor(root) {
      this.root = root;
      this.scenes = [...root.querySelectorAll('[data-scene]')];
      this.index = 0;
      this.speed = 1;
      this.timer = null;
      this.playing = false;
      this.prev = root.querySelector('[data-player-prev]');
      this.next = root.querySelector('[data-player-next]');
      this.play = root.querySelector('[data-player-play]');
      this.restart = root.querySelector('[data-player-restart]');
      this.speedControl = root.querySelector('[data-player-speed]');
      this.progress = root.querySelector('[data-player-progress]');
      this.counter = root.querySelector('[data-player-counter]');
      this.label = root.querySelector('[data-player-label]');
      this.bind();
      this.show(0);
      if (reducedMotion()) root.dataset.reducedMotion = 'true';
    }

    bind() {
      this.prev?.addEventListener('click', () => this.show(this.index - 1));
      this.next?.addEventListener('click', () => this.show(this.index + 1));
      this.play?.addEventListener('click', () => this.playing ? this.pause() : this.start());
      this.restart?.addEventListener('click', () => { this.pause(); this.show(0); });
      this.speedControl?.addEventListener('change', event => {
        this.speed = Number(event.target.value) || 1;
        if (this.playing) this.schedule();
      });
      this.progress?.addEventListener('input', event => {
        this.pause();
        this.show(Number(event.target.value));
      });
      this.root.addEventListener('keydown', event => {
        if (event.target.matches('select,input')) return;
        if (event.key === 'ArrowLeft') { event.preventDefault(); this.show(this.index - 1); }
        if (event.key === 'ArrowRight') { event.preventDefault(); this.show(this.index + 1); }
        if (event.key === ' ') { event.preventDefault(); this.playing ? this.pause() : this.start(); }
      });
    }

    show(nextIndex) {
      this.index = Math.max(0, Math.min(nextIndex, this.scenes.length - 1));
      this.scenes.forEach((scene, index) => {
        const active = index === this.index;
        scene.classList.toggle('is-active', active);
        scene.toggleAttribute('hidden', !active);
        if ('inert' in scene) scene.inert = !active;
      });
      const scene = this.scenes[this.index];
      if (this.counter) this.counter.textContent = `${String(this.index + 1).padStart(2, '0')} / ${String(this.scenes.length).padStart(2, '0')}`;
      if (this.label) this.label.textContent = scene?.dataset.label || '';
      if (this.progress) {
        this.progress.max = Math.max(0, this.scenes.length - 1);
        this.progress.value = this.index;
        this.progress.setAttribute('aria-valuetext', `第 ${this.index + 1} 步，共 ${this.scenes.length} 步`);
      }
      if (this.prev) this.prev.disabled = this.index === 0;
      if (this.next) this.next.disabled = this.index === this.scenes.length - 1;
      this.root.style.setProperty('--player-progress', `${((this.index + 1) / this.scenes.length) * 100}%`);
      if (this.playing) this.schedule();
    }

    start() {
      if (this.index === this.scenes.length - 1) this.show(0);
      this.playing = true;
      if (this.play) { this.play.textContent = '暂停'; this.play.setAttribute('aria-pressed', 'true'); }
      this.schedule();
    }

    pause() {
      this.playing = false;
      clearTimeout(this.timer);
      if (this.play) { this.play.textContent = '播放'; this.play.setAttribute('aria-pressed', 'false'); }
    }

    schedule() {
      clearTimeout(this.timer);
      if (!this.playing) return;
      const milliseconds = Number(this.scenes[this.index]?.dataset.duration || 4200) / this.speed;
      this.timer = setTimeout(() => {
        if (this.index >= this.scenes.length - 1) return this.pause();
        this.show(this.index + 1);
      }, reducedMotion() ? Math.max(1800, milliseconds * .6) : milliseconds);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-player]').forEach(root => new TopicPlayer(root));
  });
})();
