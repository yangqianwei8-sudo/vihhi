/**
 * 商机表单：加权金额计算、高德行政区划选择器、表单校验
 * 依赖：#opportunityFormConfig（JSON）、AmapDistrictSelector、#opportunityForm
 */
(function() {
  'use strict';

  function getConfig() {
    var el = document.getElementById('opportunityFormConfig');
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent.trim());
    } catch (e) {
      return null;
    }
  }

  function run() {
    var config = getConfig() || {};
    var apiBaseUrl = config.apiBaseUrl || '/api/customer/districts/';

    var estimatedAmountInput = document.getElementById('estimated_amount');
    var successProbabilitySelect = document.getElementById('success_probability');
    var weightedAmountDisplay = document.getElementById('weighted_amount_display');

    function calculateWeightedAmount() {
      if (!estimatedAmountInput || !successProbabilitySelect || !weightedAmountDisplay) return;
      var estimatedAmount = parseFloat(estimatedAmountInput.value) || 0;
      var successProbability = parseFloat(successProbabilitySelect.value) || 0;
      weightedAmountDisplay.value = (estimatedAmount * successProbability / 100).toFixed(2);
    }

    if (estimatedAmountInput && successProbabilitySelect && weightedAmountDisplay) {
      estimatedAmountInput.addEventListener('input', calculateWeightedAmount);
      successProbabilitySelect.addEventListener('change', calculateWeightedAmount);
      calculateWeightedAmount();
    }

    if (typeof AmapDistrictSelector !== 'undefined') {
      var districtSelector = new AmapDistrictSelector({
        provinceSelectId: 'provinceSelect',
        citySelectId: 'citySelect',
        districtSelectId: 'districtSelect',
        addressFieldId: 'projectAddressField',
        detailInputId: 'addressDetailInput',
        apiBaseUrl: apiBaseUrl,
        autoUpdateAddress: true,
        enableLogging: false
      });
      districtSelector.init();
    }

    var form = document.getElementById('opportunityForm');
    if (form) {
      form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
