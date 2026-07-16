(() => {
  const messages = {
    wrong: ['这条路容易被带偏', '渠道 GMV 能告诉你增长来自哪里，却不能回答增长是否创造价值。你仍然需要回到完整的增量利润。'],
    right: ['判断顺序正确', '先拆增量收入和完整成本，能最快确认“增长”是否真的值得继续，再进一步解释商品与用户结构。'],
    partial: ['有用，但不是第一步', '爆款清单能解释商品结构，却可能忽略投放、履约与退款。先看完整结果，再决定向哪个结构下钻。']
  };
  document.querySelectorAll('[data-choice-group]').forEach(group => {
    const feedback = group.querySelector('[data-choice-feedback]');
    group.querySelectorAll('[data-choice]').forEach(button => {
      button.addEventListener('click', () => {
        group.querySelectorAll('[data-choice]').forEach(item => item.classList.remove('is-selected'));
        button.classList.add('is-selected');
        const [title, body] = messages[button.dataset.choice] || [];
        feedback.className = `choice-feedback is-${button.dataset.choice}`;
        feedback.innerHTML = `<strong>${title}</strong><span>${body}</span>`;
      });
    });
  });
})();
