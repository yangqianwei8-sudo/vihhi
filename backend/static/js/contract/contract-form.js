/**
 * 合同表单逻辑 - 维海科技信息化管理平台
 * 配置从 #contractFormConfig 读取 JSON，依赖 dynamic-table.js
 */
(function() {
    'use strict';
    var cfg = {};
    var configEl = document.getElementById('contractFormConfig');
    if (configEl && configEl.textContent) {
        try { cfg = JSON.parse(configEl.textContent); } catch (e) { console.warn('contract-form: 配置解析失败', e); }
    }
    var recognizeUrl = cfg.recognizeUrl || '/api/customer/contracts/recognize/';
    var opportunitiesUrl = cfg.opportunitiesUrl || '/api/customer/authorization-letters/opportunities/';
    var ourUnits = cfg.ourUnits || [];

    function getCsrf() {
        var el = document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

    function initRecognition() {
        var fileInput = document.getElementById('contract-file-input');
        var btn = document.getElementById('recognize-contract-btn');
        var statusEl = document.getElementById('recognition-status');
        var resultEl = document.getElementById('recognition-result');
        var msgEl = document.getElementById('recognition-message');
        if (!btn || !fileInput) return;
        btn.addEventListener('click', async function() {
            var file = fileInput.files[0];
            if (!file) { alert('请先选择合同文件'); return; }
            if (file.size > 10 * 1024 * 1024) { alert('文件大小不能超过10MB'); return; }
            statusEl.style.display = 'block';
            resultEl.style.display = 'none';
            msgEl.textContent = '正在识别中，请稍候...';
            btn.disabled = true;
            var formData = new FormData();
            formData.append('file', file);
            try {
                var resp = await fetch(recognizeUrl, { method: 'POST', body: formData, headers: { 'X-CSRFToken': getCsrf() } });
                var result = await resp.json();
                if (result.success) {
                    fillFormWithRecognitionResult(result.data);
                    msgEl.textContent = '识别完成！';
                    statusEl.style.display = 'none';
                    resultEl.style.display = 'block';
                } else {
                    msgEl.textContent = '识别失败：' + (result.error || '未知错误');
                    if (statusEl.querySelector('.alert')) statusEl.querySelector('.alert').className = 'alert alert-danger';
                }
            } catch (err) {
                msgEl.textContent = '识别失败：' + err.message;
                if (statusEl.querySelector('.alert')) statusEl.querySelector('.alert').className = 'alert alert-danger';
            } finally { btn.disabled = false; }
        });
    }

    function fillFormWithRecognitionResult(data) {
        function setF(sel, val) { var el = document.querySelector(sel); if (el && !el.value && val) el.value = val; }
        if (data.contract_name) setF('[name="contract_name"]', data.contract_name);
        if (data.contract_number) setF('[name="project_number"]', data.contract_number);
        if (data.description) setF('[name="description"]', data.description);
        if (data.contract_type) {
            var el = document.querySelector('[name="contract_type"]');
            if (el) {
                var opts = el.querySelectorAll('option');
                for (var i = 0; i < opts.length; i++) {
                    if (opts[i].textContent.indexOf(data.contract_type) >= 0 || data.contract_type.indexOf(opts[i].textContent) >= 0) {
                        el.value = opts[i].value; break;
                    }
                }
            }
        }
        var rows = document.querySelectorAll('.party-row');
        function setParty(row, sel, val) {
            var inp = row ? row.querySelector(sel) : null;
            if (inp && !inp.value && val) inp.value = val;
        }
        if (data.party_a && data.party_a.name && rows.length > 0) {
            var r = rows[0];
            setParty(r, 'input[name*="[party_name]"]', data.party_a.name);
            setParty(r, 'input[name*="[party_contact]"]', data.party_a.contact);
            setParty(r, 'input[name*="[contact_phone]"]', data.party_a.phone);
            setParty(r, 'input[name*="[contact_email]"]', data.party_a.email);
            setParty(r, 'input[name*="[address]"]', data.party_a.address);
            setParty(r, 'input[name*="[credit_code]"]', data.party_a.credit_code);
            setParty(r, 'input[name*="[legal_representative]"]', data.party_a.legal_representative);
        }
        if (data.party_b && data.party_b.name) {
            var r2 = rows.length > 1 ? rows[1] : null;
            if (!r2) {
                setTimeout(function() {
                    var rs = document.querySelectorAll('.party-row');
                    if (rs.length > 1) {
                        var rr = rs[1];
                        setParty(rr, 'input[name*="[party_name]"]', data.party_b.name);
                        setParty(rr, 'input[name*="[party_contact]"]', data.party_b.contact);
                        setParty(rr, 'input[name*="[contact_phone]"]', data.party_b.phone);
                        setParty(rr, 'input[name*="[contact_email]"]', data.party_b.email);
                        setParty(rr, 'input[name*="[address]"]', data.party_b.address);
                        setParty(rr, 'input[name*="[credit_code]"]', data.party_b.credit_code);
                        setParty(rr, 'input[name*="[legal_representative]"]', data.party_b.legal_representative);
                    }
                }, 300);
            } else {
                setParty(r2, 'input[name*="[party_name]"]', data.party_b.name);
                setParty(r2, 'input[name*="[party_contact]"]', data.party_b.contact);
                setParty(r2, 'input[name*="[contact_phone]"]', data.party_b.phone);
                setParty(r2, 'input[name*="[contact_email]"]', data.party_b.email);
                setParty(r2, 'input[name*="[address]"]', data.party_b.address);
                setParty(r2, 'input[name*="[credit_code]"]', data.party_b.credit_code);
                setParty(r2, 'input[name*="[legal_representative]"]', data.party_b.legal_representative);
            }
        }
    }

    function initAmountCalculation() {
        function calc() {
            var amt = document.querySelector('input[name="contract_amount"]');
            var tax = document.querySelector('input[name="tax_rate"]');
            var excl = document.getElementById('contract_amount_excl_tax_display');
            var taxDisp = document.getElementById('contract_amount_tax_display');
            var pay = document.getElementById('payment_amount_display');
            var unpaid = document.getElementById('unpaid_amount_display');
            if (!amt || !tax || !excl || !taxDisp || !unpaid) return;
            var ca = parseFloat(amt.value) || 0;
            var tr = parseFloat(tax.value) || 0;
            var pa = parseFloat(pay ? pay.value : 0) || 0;
            if (ca > 0 && tr >= 0) {
                var rd = tr / 100;
                excl.value = rd > 0 ? (ca / (1 + rd)).toFixed(2) : ca.toFixed(2);
                taxDisp.value = rd > 0 ? (ca - ca / (1 + rd)).toFixed(2) : '0.00';
            } else { excl.value = '0.00'; taxDisp.value = '0.00'; }
            unpaid.value = Math.max(0, ca - pa).toFixed(2);
        }
        var amt = document.querySelector('input[name="contract_amount"]');
        var tax = document.querySelector('input[name="tax_rate"]');
        if (amt && tax) {
            amt.addEventListener('input', calc);
            amt.addEventListener('change', calc);
            tax.addEventListener('input', calc);
            tax.addEventListener('change', calc);
            calc();
        }
    }

    function initOpportunityClientFilter() {
        var client = document.querySelector('[name="client"]');
        var opp = document.querySelector('[name="opportunity"]');
        var pbt = document.getElementById('project_business_type');
        if (!client || !opp) return;
        opp.addEventListener('change', function() {
            var opt = this.options[this.selectedIndex];
            var id = this.value;
            if (id) {
                var cid = opt.getAttribute('data-client-id');
                var pt = opt.getAttribute('data-project-type');
                if (cid && client) client.value = cid;
                if (pt && pbt) pbt.value = pt;
                if (!cid || !pt) {
                    fetch(opportunitiesUrl + '?opportunity_id=' + encodeURIComponent(id), {
                        method: 'GET', headers: { 'X-CSRFToken': getCsrf() }
                    }).then(function(r) { return r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status)); })
                    .then(function(d) {
                        if (d.success && d.opportunity) {
                            var o = d.opportunity;
                            if (o.client && o.client.id && client) client.value = o.client.id;
                            if (o.project_type && pbt) pbt.value = o.project_type;
                        }
                    }).catch(function(e) { console.error('获取商机详情失败:', e); });
                }
            } else { if (client) client.value = ''; if (pbt) pbt.value = ''; }
        });
        for (var i = 0; i < opp.options.length; i++) {
            (function(opt) {
                if (opt.value && !opt.getAttribute('data-client-id')) {
                    fetch(opportunitiesUrl + '?opportunity_id=' + encodeURIComponent(opt.value), {
                        method: 'GET', headers: { 'X-CSRFToken': getCsrf() }
                    }).then(function(r) { return r.json(); }).then(function(d) {
                        if (d.success && d.opportunity) {
                            var o = d.opportunity;
                            var el = opp.querySelector('option[value="' + opt.value + '"]');
                            if (el) {
                                if (o.client && o.client.id) { el.setAttribute('data-client-id', o.client.id); el.setAttribute('data-client-name', o.client.name || ''); }
                                if (o.project_type) el.setAttribute('data-project-type', o.project_type);
                            }
                        }
                    }).catch(function(e) { console.error('获取商机详情失败:', e); });
                }
            })(opp.options[i]);
        }
        if (opp.value) setTimeout(function() { opp.dispatchEvent(new Event('change')); }, 300);
    }

    function initContractNumberAutoGen() {
        var pn = document.querySelector('[name="project_number"]');
        var cn = document.querySelector('[name="contract_number"]');
        if (!pn || !cn) return;
        var manual = false;
        var orig = cn.value;
        cn.addEventListener('input', function() {
            var v = this.value;
            var auto = pn.value ? 'HT-' + pn.value : '';
            if (v !== auto && v !== orig) manual = true;
        });
        pn.addEventListener('change', function() {
            if (!manual) cn.value = this.value ? 'HT-' + this.value : '';
        });
        if (pn.value && !cn.value) cn.value = 'HT-' + pn.value;
    }

    function initOurUnitsSelect() {
        var sel = document.getElementById('our_signing_party');
        if (!sel || !Array.isArray(ourUnits)) return;
        for (var i = 0; i < ourUnits.length; i++) {
            var o = document.createElement('option');
            o.value = ourUnits[i];
            o.textContent = ourUnits[i];
            sel.appendChild(o);
        }
    }

    function initPartiesTable() {
        if (typeof DynamicTableManager === 'undefined') { console.error('DynamicTableManager 未加载'); return; }
        var existing = cfg.existingParties || [];
        function tpl(i, d) {
            var p = d || {};
            var esc = function(v) { return (v || '').replace(/"/g, '&quot;'); };
            return '<td class="cf-text-center"><strong>' + (i + 1) + '</strong></td>' +
                '<td><input type="text" name="parties[' + i + '][party_name]" class="form-control form-control-sm" value="' + esc(p.party_name) + '" placeholder="请输入单位名称" required></td>' +
                '<td><input type="text" name="parties[' + i + '][credit_code]" class="form-control form-control-sm" value="' + esc(p.credit_code) + '"></td>' +
                '<td><input type="text" name="parties[' + i + '][legal_representative]" class="form-control form-control-sm" value="' + esc(p.legal_representative) + '"></td>' +
                '<td><input type="text" name="parties[' + i + '][project_manager]" class="form-control form-control-sm" value="' + esc(p.project_manager) + '"></td>' +
                '<td><input type="text" name="parties[' + i + '][contact_phone]" class="form-control form-control-sm" value="' + esc(p.contact_phone) + '"></td>' +
                '<td><input type="email" name="parties[' + i + '][contact_email]" class="form-control form-control-sm" value="' + esc(p.contact_email) + '"></td>' +
                '<td><input type="text" name="parties[' + i + '][address]" class="form-control form-control-sm" value="' + esc(p.address) + '"></td>' +
                '<td class="cf-text-center"><button type="button" class="btn btn-sm btn-danger remove-party-btn"><i class="bi bi-trash"></i> 删除</button></td>';
        }
        var mgr = new DynamicTableManager({
            containerId: 'parties-container', rowClass: 'party-row', addButtonId: 'add-party-btn', removeButtonClass: 'remove-party-btn',
            minRows: 1, rowTemplate: tpl, autoUpdateNumbers: true, numberCellSelector: 'td:first-child',
            onAdd: function() {}, onRemove: function() { return true; }
        });
        var c = document.getElementById('parties-container');
        if (c) c.innerHTML = '';
        if (existing.length) { for (var i = 0; i < existing.length; i++) mgr.addRow(existing[i]); }
        else mgr.addRow();
        mgr.updateIndexCounter();
    }

    function initServiceContentsTable() {
        if (typeof DynamicTableManager === 'undefined') { console.error('DynamicTableManager 未加载'); return; }
        var stData = cfg.serviceTypesData || [];
        var dsData = cfg.designStagesData || [];
        var btData = cfg.businessTypesData || [];
        var spData = cfg.serviceProfessionsData || [];
        var existing = cfg.existingServiceContents || [];
        function populate(row, stId, dsId, btId, profIds) {
            if (!row) return;
            var stSel = row.querySelector('select[name*="[service_type]"]');
            var dsSel = row.querySelector('select[name*="[design_stage]"]');
            var btSel = row.querySelector('select[name*="[business_type]"]');
            var profSel = row.querySelector('select[name*="[service_professions]"]');
            function fill(sel, arr, selected) {
                if (!sel || !Array.isArray(arr)) return;
                sel.innerHTML = '<option value="">-- 请选择 --</option>';
                for (var j = 0; j < arr.length; j++) {
                    var o = document.createElement('option');
                    o.value = arr[j].id;
                    o.textContent = arr[j].name;
                    if (selected && String(arr[j].id) === String(selected)) o.selected = true;
                    sel.appendChild(o);
                }
            }
            fill(stSel, stData, stId);
            fill(dsSel, dsData, dsId);
            fill(btSel, btData, btId);
            if (profSel && Array.isArray(spData)) {
                profSel.innerHTML = '<option value="">-- 请选择 --</option>';
                var st = stId || (stSel ? stSel.value : null);
                for (var j = 0; j < spData.length; j++) {
                    var sp = spData[j];
                    if (st && sp.service_type_id && String(sp.service_type_id) !== String(st)) continue;
                    var o = document.createElement('option');
                    o.value = sp.id;
                    o.textContent = sp.name;
                    if (Array.isArray(profIds) && profIds.indexOf(sp.id) >= 0) o.selected = true;
                    profSel.appendChild(o);
                }
                if (stSel) stSel.addEventListener('change', function() {
                    profSel.innerHTML = '<option value="">-- 请选择 --</option>';
                    for (var j = 0; j < spData.length; j++) {
                        var sp = spData[j];
                        if (!this.value || !sp.service_type_id || String(sp.service_type_id) === String(this.value)) {
                            var o = document.createElement('option');
                            o.value = sp.id;
                            o.textContent = sp.name;
                            profSel.appendChild(o);
                        }
                    }
                });
            }
        }
        function tpl(i, d) {
            var s = d || {};
            return '<td class="cf-text-center"><strong>' + (i + 1) + '</strong></td>' +
                '<td><select name="service_contents[' + i + '][service_type]" class="form-select form-select-sm"><option value="">-- 请选择 --</option></select></td>' +
                '<td><select name="service_contents[' + i + '][design_stage]" class="form-select form-select-sm"><option value="">-- 请选择 --</option></select></td>' +
                '<td><input type="number" name="service_contents[' + i + '][building_area]" class="form-control form-control-sm" step="0.01" placeholder="0.00" value="' + (s.building_area || '') + '"></td>' +
                '<td><select name="service_contents[' + i + '][business_type]" class="form-select form-select-sm"><option value="">-- 请选择 --</option></select></td>' +
                '<td><select name="service_contents[' + i + '][service_professions]" class="form-select form-select-sm cf-select-multi" multiple><option value="">-- 请选择 --</option></select><small class="form-text text-muted cf-text-10">可多选</small></td>' +
                '<td class="cf-text-center"><button type="button" class="btn btn-sm btn-danger remove-service-content-btn"><i class="bi bi-trash"></i> 删除</button></td>';
        }
        var mgr = new DynamicTableManager({
            containerId: 'service-contents-container', rowClass: 'service-content-row', addButtonId: 'add-service-content-btn', removeButtonClass: 'remove-service-content-btn',
            minRows: 1, rowTemplate: tpl, autoUpdateNumbers: true, numberCellSelector: 'td:first-child',
            onAdd: function(row) { populate(row, null, null, null, []); },
            onRemove: function() { return true; }
        });
        var c = document.getElementById('service-contents-container');
        if (c) c.innerHTML = '';
        if (existing.length) {
            for (var i = 0; i < existing.length; i++) {
                var sd = existing[i];
                var row = mgr.addRow(sd);
                if (row) populate(row, sd.service_type_id, sd.design_stage_id, sd.business_type_id, sd.service_profession_ids || []);
            }
        } else { var row = mgr.addRow(); if (row) populate(row, null, null, null, []); }
        mgr.updateIndexCounter();
    }

    function initPaymentInfoTable() {
        if (typeof DynamicTableManager === 'undefined') { console.error('DynamicTableManager 未加载'); return; }
        var existing = cfg.existingPaymentPlans || [];
        function tpl(i, d) {
            var p = d || {};
            var esc = function(v) { return (v || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
            return '<td class="cf-text-center"><strong>' + (i + 1) + '</strong></td>' +
                '<td><input type="text" name="payment_plans[' + i + '][phase_name]" class="form-control form-control-sm" value="' + esc(p.phase_name) + '" placeholder="请输入阶段名称" required></td>' +
                '<td><input type="text" name="payment_plans[' + i + '][trigger_condition]" class="form-control form-control-sm" value="' + esc(p.trigger_condition) + '"></td>' +
                '<td><input type="text" name="payment_plans[' + i + '][payment_method]" class="form-control form-control-sm" value="' + esc(p.payment_method) + '"></td>' +
                '<td><input type="number" name="payment_plans[' + i + '][planned_amount]" class="form-control form-control-sm" step="0.01" value="' + esc(p.planned_amount) + '"></td>' +
                '<td><textarea name="payment_plans[' + i + '][condition_detail]" class="form-control form-control-sm" rows="2">' + esc(p.condition_detail) + '</textarea></td>' +
                '<td class="cf-text-center"><button type="button" class="btn btn-sm btn-danger remove-payment-info-btn"><i class="bi bi-trash"></i> 删除</button></td>';
        }
        var mgr = new DynamicTableManager({
            containerId: 'payment-info-container', rowClass: 'payment-info-row', addButtonId: 'add-payment-info-btn', removeButtonClass: 'remove-payment-info-btn',
            minRows: 1, rowTemplate: tpl, autoUpdateNumbers: true, numberCellSelector: 'td:first-child',
            onAdd: function() {}, onRemove: function() { return true; }
        });
        var c = document.getElementById('payment-info-container');
        if (c) c.innerHTML = '';
        if (existing.length) { for (var i = 0; i < existing.length; i++) mgr.addRow(existing[i]); }
        else mgr.addRow();
        mgr.updateIndexCounter();
    }

    function run() {
        initRecognition();
        initAmountCalculation();
        initOpportunityClientFilter();
        initContractNumberAutoGen();
        initOurUnitsSelect();
        initPartiesTable();
        initServiceContentsTable();
        initPaymentInfoTable();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
    else run();
})();
