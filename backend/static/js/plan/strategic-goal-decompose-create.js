/**
 * 新建目标分解页：选择父目标卡片与表单提交（P3 S1 治理：由模板 inline script 外移）
 */
(function () {
  var selectedGoalId = null;

  function getConfig() {
    var el = document.getElementById('strategicGoalDecomposeCreateConfig');
    if (!el || !el.textContent) return {};
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return {};
    }
  }

  function selectGoal(goalId) {
    var cards = document.querySelectorAll('.goal-card');
    cards.forEach(function (card) {
      card.classList.remove('selected');
    });
    var selectedCard = document.querySelector('[data-goal-id="' + goalId + '"]');
    if (selectedCard) {
      selectedCard.classList.add('selected');
      selectedGoalId = goalId;
      var input = document.getElementById('parentGoalId');
      var btn = document.getElementById('createBtn');
      if (input) input.value = goalId;
      if (btn) btn.disabled = false;
    }
  }

  function init() {
    var config = getConfig();
    if (config.initialParentGoalId != null) {
      selectGoal(config.initialParentGoalId);
    }

    document.addEventListener('click', function (e) {
      var el = e.target && e.target.closest ? e.target.closest('[data-action="strategic-goal-decompose-select"]') : null;
      if (!el) return;
      e.preventDefault();
      var id = el.getAttribute('data-goal-id');
      if (id) selectGoal(id);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
