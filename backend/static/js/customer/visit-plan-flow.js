/**
 * 拜访计划流程页：步骤切换、定位与地址回填
 */
(function() {
  'use strict';

  function run() {
    var stepItems = document.querySelectorAll('.step-item');
    var stepContents = document.querySelectorAll('.step-content');
    var currentStepInput = document.getElementById('currentStep');
    if (!currentStepInput) return;
    var currentStep = parseInt(currentStepInput.value, 10) || 1;

    function updateStepDisplay(step) {
      stepItems.forEach(function(item, index) {
        var stepNum = index + 1;
        item.classList.remove('active', 'completed');
        if (stepNum < step) item.classList.add('completed');
        else if (stepNum === step) item.classList.add('active');
      });
      stepContents.forEach(function(content) {
        var contentStep = parseInt(content.dataset.step, 10);
        content.classList.remove('active');
        if (contentStep === step) content.classList.add('active');
      });
      currentStepInput.value = step;
    }

    function updateLocationDisplay(latitude, longitude, address) {
      var locationDisplay = document.getElementById('locationDisplay');
      var currentLocationDisplay = document.getElementById('currentLocationDisplay');
      if (latitude && longitude) {
        var lat = parseFloat(latitude);
        var lon = parseFloat(longitude);
        if (isNaN(lat)) lat = 0;
        if (isNaN(lon)) lon = 0;
        lat = lat.toFixed(7);
        lon = lon.toFixed(7);
        var displayHtml = '<div class="d-flex align-items-center gap-2 mb-2"><i class="bi bi-check-circle-fill text-success"></i><span class="fw-bold text-success">定位成功</span></div>';
        if (address) displayHtml += '<div class="mb-2"><div class="text-muted small">地址：</div><div class="fw-semibold">' + address + '</div></div>';
        displayHtml += '<div><div class="text-muted small">坐标：</div><div class="font-monospace small">纬度 ' + lat + '，经度 ' + lon + '</div></div>';
        if (locationDisplay) locationDisplay.innerHTML = displayHtml;
        if (currentLocationDisplay) {
          var cur = '<div class="d-flex align-items-center gap-2"><i class="bi bi-check-circle-fill text-success"></i><span class="fw-bold text-success">定位成功</span></div>';
          if (address) cur += '<div class="w-100 mt-2"><div class="text-muted small">地址：</div><div class="fw-semibold">' + address + '</div></div>';
          cur += '<div class="w-100 mt-2"><div class="text-muted small">坐标：</div><div class="font-monospace small">纬度 ' + lat + '，经度 ' + lon + '</div></div>';
          currentLocationDisplay.innerHTML = cur;
        }
      } else {
        var msg = '<div class="text-muted"><i class="bi bi-exclamation-circle"></i> 未获取到位置信息</div>';
        if (locationDisplay) locationDisplay.innerHTML = msg;
        if (currentLocationDisplay) currentLocationDisplay.innerHTML = msg;
      }
    }

    function updateCurrentLocationStatus(message, isSuccess) {
      var currentLocationDisplay = document.getElementById('currentLocationDisplay');
      if (!currentLocationDisplay) return;
      var icon = isSuccess ? 'bi-hourglass-split' : 'bi-exclamation-circle';
      var color = isSuccess ? 'text-info' : 'text-danger';
      currentLocationDisplay.innerHTML = '<div class="' + color + '"><i class="bi ' + icon + '"></i> ' + message + '</div>';
    }

    function getAddressFromCoordinates(latitude, longitude) {
      updateCurrentLocationStatus('正在解析地址...', true);
      var tokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
      var token = tokenEl ? tokenEl.value : '';
      return fetch('/api/customer/regeocode/?latitude=' + latitude + '&longitude=' + longitude, {
        method: 'GET',
        headers: { 'X-CSRFToken': token },
        credentials: 'same-origin'
      }).then(function(response) { return response.json(); }).then(function(data) {
        if (data.success && data.formatted_address) {
          var locationInput = document.getElementById('id_checkin_location');
          if (locationInput) {
            locationInput.value = data.formatted_address;
            locationInput.removeAttribute('readonly');
          }
          updateLocationDisplay(latitude, longitude, data.formatted_address);
          return true;
        }
        updateLocationDisplay(latitude, longitude, null);
        return false;
      }).catch(function() {
        updateLocationDisplay(latitude, longitude, null);
        return false;
      });
    }

    function getLocation(showStatus) {
      if (showStatus === undefined) showStatus = true;
      var locationDisplay = document.getElementById('locationDisplay');
      var latitudeInput = document.getElementById('id_latitude');
      var longitudeInput = document.getElementById('id_longitude');
      if (!navigator.geolocation) {
        if (showStatus) updateCurrentLocationStatus('浏览器不支持GPS定位，尝试IP定位...', false);
        setTimeout(function() { getIPLocation(); }, 1000);
        return;
      }
      if (showStatus) updateCurrentLocationStatus('正在获取GPS位置...', true);
      if (locationDisplay) locationDisplay.innerHTML = '<div class="text-muted"><i class="bi bi-hourglass-split"></i> 正在获取位置信息...</div>';
      navigator.geolocation.getCurrentPosition(
        function(position) {
          var lat = position.coords.latitude.toFixed(7);
          var lon = position.coords.longitude.toFixed(7);
          if (latitudeInput) latitudeInput.value = lat;
          if (longitudeInput) longitudeInput.value = lon;
          getAddressFromCoordinates(lat, lon);
        },
        function(error) {
          var errorMessage = 'GPS定位失败';
          if (error.code === 1) errorMessage = '定位权限被拒绝，尝试IP定位...';
          else if (error.code === 2) errorMessage = '位置信息不可用，尝试IP定位...';
          else if (error.code === 3) errorMessage = '定位超时，尝试IP定位...';
          if (showStatus) updateCurrentLocationStatus(errorMessage, false);
          if (locationDisplay) locationDisplay.innerHTML = '<div class="text-danger"><i class="bi bi-exclamation-circle"></i> 定位失败</div>';
          setTimeout(function() { getIPLocation(); }, 1000);
        },
        { enableHighAccuracy: false, timeout: 30000, maximumAge: 60000 }
      );
    }

    function getIPLocation() {
      updateCurrentLocationStatus('正在通过IP获取位置...', true);
      var tokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
      var token = tokenEl ? tokenEl.value : '';
      fetch('/api/customer/ip-location/', {
        method: 'GET',
        headers: { 'X-CSRFToken': token },
        credentials: 'same-origin'
      }).then(function(r) { return r.json(); }).then(function(data) {
        if (data.success && data.center_latitude && data.center_longitude) {
          var lat = data.center_latitude.toFixed(7);
          var lon = data.center_longitude.toFixed(7);
          var latitudeInput = document.getElementById('id_latitude');
          var longitudeInput = document.getElementById('id_longitude');
          if (latitudeInput) latitudeInput.value = lat;
          if (longitudeInput) longitudeInput.value = lon;
          getAddressFromCoordinates(lat, lon).then(function() {
            updateCurrentLocationStatus('IP定位成功（' + (data.city || '城市级别') + '）', true);
          });
        } else {
          updateCurrentLocationStatus('IP定位失败：' + (data.message || '无法获取位置信息'), false);
        }
      }).catch(function() {
        updateCurrentLocationStatus('IP定位失败，请检查网络连接', false);
      });
    }

    updateStepDisplay(currentStep);

    if (currentStep === 3) {
      var latitudeInput = document.getElementById('id_latitude');
      var longitudeInput = document.getElementById('id_longitude');
      var locationInput = document.getElementById('id_checkin_location');
      if (latitudeInput && latitudeInput.value && longitudeInput && longitudeInput.value) {
        updateLocationDisplay(latitudeInput.value, longitudeInput.value, locationInput ? locationInput.value : '');
      } else {
        setTimeout(function() {
          if (navigator.geolocation) {
            updateCurrentLocationStatus('正在自动获取位置...', true);
            getLocation(true);
          } else getIPLocation();
        }, 1000);
      }
    }

    var getLocationBtn = document.querySelector('button[data-click="handle_onclick_0"]');
    if (!getLocationBtn) getLocationBtn = document.querySelector('.step-content[data-step="3"] .btn');
    if (getLocationBtn) getLocationBtn.addEventListener('click', function() { getLocation(true); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
