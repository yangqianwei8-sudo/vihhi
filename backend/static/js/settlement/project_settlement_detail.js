/**
 * 项目结算详情页：审核明细项弹窗与表单提交（P3 S1 治理：由模板 inline script 外移）
 */
(function () {
    var REVIEW_PLACEHOLDER = '999999';

    function getConfig() {
        var el = document.getElementById('projectSettlementDetailConfig');
        if (!el || !el.textContent) return {};
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            return {};
        }
    }

    function reviewItem(itemId, action) {
        var config = getConfig();
        var reviewItemUrlTemplate = config.reviewItemUrlTemplate;
        if (!reviewItemUrlTemplate) return;

        var modal = document.getElementById('reviewItemModal');
        var form = document.getElementById('reviewItemForm');
        var actionInput = document.getElementById('reviewAction');
        var approveSection = document.getElementById('approveSection');
        var rejectSection = document.getElementById('rejectSection');
        var itemInfo = document.getElementById('itemInfo');
        var submitBtn = document.getElementById('submitReviewBtn');
        var adjustedAmountInput = document.getElementById('adjustedSavingAmount');
        var adjustmentReasonInput = document.getElementById('adjustmentReason');
        var reviewCommentInput = document.getElementById('reviewComment');
        var rejectionReasonInput = document.getElementById('rejectionReason');

        if (!modal || !form || !actionInput) return;

        if (adjustedAmountInput) adjustedAmountInput.value = '';
        if (adjustmentReasonInput) adjustmentReasonInput.value = '';
        if (reviewCommentInput) reviewCommentInput.value = '';
        if (rejectionReasonInput) rejectionReasonInput.value = '';

        form.action = reviewItemUrlTemplate.replace(REVIEW_PLACEHOLDER, String(itemId));
        actionInput.value = action;

        var row = document.getElementById('item-row-' + itemId);
        var originalAmountValue = 0;
        if (row && itemInfo) {
            var cells = row.querySelectorAll('td');
            var opinionNumber = cells[0] ? cells[0].textContent.trim() : '';
            var opinionTitle = cells[1] ? cells[1].textContent.trim() : '';
            var originalAmountText = cells[4] ? cells[4].textContent.trim() : '';
            originalAmountValue = parseFloat(originalAmountText.replace(/[^\d.-]/g, ''), 10) || 0;
            itemInfo.innerHTML =
                '<div class="alert alert-info">' +
                '<strong>意见编号：</strong>' + opinionNumber + '<br>' +
                '<strong>意见标题：</strong>' + opinionTitle + '<br>' +
                '<strong>原始节省金额：</strong>' + originalAmountText +
                '</div>';
        }

        if (action === 'approve') {
            if (approveSection) { approveSection.classList.remove('d-none'); }
            if (rejectSection) { rejectSection.classList.add('d-none'); }
            submitBtn.className = 'btn btn-success';
            submitBtn.textContent = '确认通过';
            var labelEl = document.getElementById('reviewItemModalLabel');
            if (labelEl) labelEl.textContent = '确认结算明细项';
            if (adjustedAmountInput && originalAmountValue > 0) {
                adjustedAmountInput.placeholder = originalAmountValue.toFixed(2);
            }
        } else if (action === 'reject') {
            if (approveSection) { approveSection.classList.add('d-none'); }
            if (rejectSection) { rejectSection.classList.remove('d-none'); }
            submitBtn.className = 'btn btn-danger';
            submitBtn.textContent = '确认驳回';
            var labelEl2 = document.getElementById('reviewItemModalLabel');
            if (labelEl2) labelEl2.textContent = '驳回结算明细项';
        }

        var bsModal = window.bootstrap && window.bootstrap.Modal ? new window.bootstrap.Modal(modal) : null;
        if (bsModal) bsModal.show();
    }

    function init() {
        var config = getConfig();
        if (!config.reviewItemUrlTemplate) return;

        document.addEventListener('click', function (e) {
            var t = e.target.closest('[data-action="settlement-review-item"]');
            if (!t) return;
            e.preventDefault();
            var itemId = t.getAttribute('data-item-id');
            var action = t.getAttribute('data-review-action');
            if (itemId && (action === 'approve' || action === 'reject')) {
                reviewItem(itemId, action);
            }
        });

        var form = document.getElementById('reviewItemForm');
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                var formEl = this;
                var submitBtn = document.getElementById('submitReviewBtn');
                var formData = new FormData(formEl);
                submitBtn.disabled = true;
                submitBtn.textContent = '提交中...';

                fetch(formEl.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                    .then(function (response) { return response.json(); })
                    .then(function (data) {
                        if (data.success) {
                            location.reload();
                        } else {
                            alert(data.message || '操作失败，请重试');
                            submitBtn.disabled = false;
                            submitBtn.textContent = submitBtn.className.indexOf('danger') !== -1 ? '确认驳回' : '确认通过';
                        }
                    })
                    .catch(function (err) {
                        console.error('Error:', err);
                        alert('操作失败，请重试');
                        submitBtn.disabled = false;
                        submitBtn.textContent = submitBtn.className.indexOf('danger') !== -1 ? '确认驳回' : '确认通过';
                    });
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
