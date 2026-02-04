/**
 * 项目团队配置页：添加成员（切 tab + 滚动）、移除成员（P3 S1 C4 治理：从 project_team.html 迁出）
 * 事件委托：data-action="project-team-open-add-member" | project-team-remove-member（配合 data-member-id）
 * 配置：<script type="application/json" id="projectTeamConfig">
 */
(function() {
  'use strict';

  function getConfig() {
    var el = document.getElementById('projectTeamConfig');
    if (!el || !el.textContent) return {};
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return {};
    }
  }

  function openAddMemberDialog() {
    var targetTabTrigger = document.querySelector('#profession-tab');
    if (targetTabTrigger && typeof bootstrap !== 'undefined' && bootstrap.Tab) {
      var tabInstance = bootstrap.Tab.getOrCreateInstance(targetTabTrigger);
      tabInstance.show();
    }
    var targetPanel = document.querySelector('#tab-professions');
    if (targetPanel) {
      targetPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
      targetPanel.classList.add('focus-flash');
      setTimeout(function() { targetPanel.classList.remove('focus-flash'); }, 1500);
    }
  }

  function removeMember(memberId, deleteUrlPattern) {
    if (!confirm('确定要移除该成员吗？')) return;
    var url = (deleteUrlPattern || '/api/project/project-teams/').replace(/\/$/, '') + '/' + memberId + '/';
    var csrfEl = document.querySelector('[name=csrfmiddlewaretoken]');
    var csrf = csrfEl ? csrfEl.value : '';
    fetch(url, {
      method: 'DELETE',
      headers: { 'X-CSRFToken': csrf }
    }).then(function(response) {
      if (response.ok) {
        location.reload();
      } else {
        alert('移除失败，请稍后再试');
      }
    }).catch(function() {
      alert('移除失败，请稍后再试');
    });
  }

  document.addEventListener('click', function(e) {
    var target = e.target && (e.target.closest ? e.target.closest('[data-action="project-team-open-add-member"]') : null);
    if (target) {
      e.preventDefault();
      openAddMemberDialog();
      return;
    }
    target = e.target && (e.target.closest ? e.target.closest('[data-action="project-team-remove-member"]') : null);
    if (target) {
      e.preventDefault();
      var memberId = target.dataset && target.dataset.memberId;
      if (memberId) {
        var cfg = getConfig();
        removeMember(memberId, cfg.deleteUrlPattern);
      }
      return;
    }
  }, true);
})();
