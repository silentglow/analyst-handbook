/* 专题课连续演示：每一次播放都必须有即时、持续且可理解的反馈。 */
(() => {
  const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  class TopicPlayer {
    constructor(root) {
      this.root = root;
      this.scenes = [...root.querySelectorAll('[data-scene]')];
      this.index = 0;
      this.speed = 1;
      this.playing = false;
      this.frame = null;
      this.startedAt = 0;
      this.elapsed = 0;
      this.prev = root.querySelector('[data-player-prev]');
      this.next = root.querySelector('[data-player-next]');
      this.play = root.querySelector('[data-player-play]');
      this.restart = root.querySelector('[data-player-restart]');
      this.speedControl = root.querySelector('[data-player-speed]');
      this.progress = root.querySelector('[data-player-progress]');
      this.counter = root.querySelector('[data-player-counter]');
      this.label = root.querySelector('[data-player-label]');
      this.status = this.createStatus();
      this.bind();
      this.show(0, { announce: false });
      this.setState('ready', '准备播放 · 点击播放后将连续演示每一步');
      if (reducedMotion()) root.dataset.reducedMotion = 'true';
    }

    createStatus() {
      const status = document.createElement('div');
      status.className = 'player-live-status';
      status.setAttribute('aria-live', 'polite');
      status.innerHTML = '<i></i><span data-player-state-label>准备播放</span><b data-player-countdown></b>';
      this.root.querySelector('.player-head')?.insertAdjacentElement('afterend', status);
      return status;
    }

    bind() {
      this.prev?.addEventListener('click', () => this.manualStep(this.index - 1));
      this.next?.addEventListener('click', () => this.manualStep(this.index + 1));
      this.play?.addEventListener('click', () => this.playing ? this.pause() : this.start());
      this.restart?.addEventListener('click', () => {
        this.pause(false);
        this.show(0);
        this.start();
      });
      this.speedControl?.addEventListener('change', event => {
        this.speed = Number(event.target.value) || 1;
        if (this.playing) {
          this.elapsed = 0;
          this.startedAt = performance.now();
          this.updateStatus('playing');
        }
      });
      this.progress?.addEventListener('input', event => {
        this.pause(false);
        this.show(Number(event.target.value));
        this.setState('paused', '已定位到当前步骤 · 点击播放继续');
      });
      this.root.addEventListener('keydown', event => {
        if (event.target.matches('select,input,button')) return;
        if (event.key === 'ArrowLeft') { event.preventDefault(); this.manualStep(this.index - 1); }
        if (event.key === 'ArrowRight') { event.preventDefault(); this.manualStep(this.index + 1); }
        if (event.key === ' ') { event.preventDefault(); this.playing ? this.pause() : this.start(); }
      });
      document.addEventListener('visibilitychange', () => {
        if (document.hidden && this.playing) this.pause();
      });
    }

    duration() {
      const raw = Number(this.scenes[this.index]?.dataset.duration || 4800);
      return Math.max(1500, raw / this.speed);
    }

    show(nextIndex, options = {}) {
      this.index = Math.max(0, Math.min(nextIndex, this.scenes.length - 1));
      this.elapsed = 0;
      this.scenes.forEach((scene, index) => {
        const active = index === this.index;
        scene.classList.toggle('is-active', active);
        scene.classList.remove('is-animating');
        scene.toggleAttribute('hidden', !active);
        if ('inert' in scene) scene.inert = !active;
      });
      const scene = this.scenes[this.index];
      if (scene) {
        // Force a fresh animation timeline whenever the learner changes step.
        void scene.offsetWidth;
        scene.classList.add('is-animating');
      }
      if (this.counter) this.counter.textContent = `${String(this.index + 1).padStart(2, '0')} / ${String(this.scenes.length).padStart(2, '0')}`;
      if (this.label) this.label.textContent = scene?.dataset.label || '';
      if (this.progress) {
        this.progress.max = Math.max(0, this.scenes.length - 1);
        this.progress.value = this.index;
        this.progress.setAttribute('aria-valuetext', `第 ${this.index + 1} 步，共 ${this.scenes.length} 步`);
      }
      if (this.prev) this.prev.disabled = this.index === 0;
      if (this.next) this.next.disabled = this.index === this.scenes.length - 1;
      this.root.style.setProperty('--scene-progress', '0%');
      this.root.style.setProperty('--player-progress', `${(this.index / this.scenes.length) * 100}%`);
      if (options.announce !== false && !this.playing) this.setState('paused', `已切换：${scene?.dataset.label || `第 ${this.index + 1} 步`}`);
    }

    manualStep(index) {
      const wasPlaying = this.playing;
      this.pause(false);
      this.show(index);
      if (wasPlaying) this.start();
    }

    start() {
      if (!this.scenes.length) return;
      if (this.index === this.scenes.length - 1 && this.root.dataset.playerState === 'complete') this.show(0, { announce: false });
      this.playing = true;
      this.startedAt = performance.now() - this.elapsed;
      this.setState('playing');
      if (this.play) {
        this.play.innerHTML = '<span aria-hidden="true">Ⅱ</span> 暂停';
        this.play.setAttribute('aria-pressed', 'true');
      }
      cancelAnimationFrame(this.frame);
      this.frame = requestAnimationFrame(time => this.tick(time));
    }

    pause(announce = true) {
      this.playing = false;
      cancelAnimationFrame(this.frame);
      if (this.play) {
        this.play.innerHTML = '<span aria-hidden="true">▶</span> 播放';
        this.play.setAttribute('aria-pressed', 'false');
      }
      if (announce && this.root.dataset.playerState !== 'complete') this.setState('paused', '已暂停 · 当前内容会保留在画面中');
    }

    tick(time) {
      if (!this.playing) return;
      this.elapsed = time - this.startedAt;
      const duration = this.duration();
      const ratio = Math.min(1, this.elapsed / duration);
      const overall = ((this.index + ratio) / this.scenes.length) * 100;
      this.root.style.setProperty('--scene-progress', `${ratio * 100}%`);
      this.root.style.setProperty('--player-progress', `${overall}%`);
      this.updateStatus('playing', Math.max(0, duration - this.elapsed));

      if (ratio >= 1) {
        if (this.index >= this.scenes.length - 1) {
          this.complete();
          return;
        }
        this.show(this.index + 1, { announce: false });
        this.startedAt = time;
      }
      this.frame = requestAnimationFrame(next => this.tick(next));
    }

    updateStatus(state, remaining = this.duration()) {
      const scene = this.scenes[this.index];
      const label = state === 'playing' ? `正在演示：${scene?.dataset.label || `第 ${this.index + 1} 步`}` : '';
      this.setState(state, label, state === 'playing' ? `${Math.ceil(remaining / 1000)} 秒后进入下一步` : '');
    }

    setState(state, message = '', countdown = '') {
      this.root.dataset.playerState = state;
      const label = this.status?.querySelector('[data-player-state-label]');
      const timer = this.status?.querySelector('[data-player-countdown]');
      if (label && message) label.textContent = message;
      if (timer) timer.textContent = countdown;
    }

    complete() {
      this.pause(false);
      this.elapsed = 0;
      this.root.style.setProperty('--scene-progress', '100%');
      this.root.style.setProperty('--player-progress', '100%');
      this.setState('complete', '演示完成 · 你可以重播或进入下方完整知识', '全部步骤已完成');
      if (this.play) this.play.innerHTML = '<span aria-hidden="true">↻</span> 再播一次';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-player]').forEach(root => new TopicPlayer(root));
  });
})();
