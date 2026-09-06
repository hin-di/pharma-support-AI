// PharmaSupport AI (薬サポ) - 令和8年度改定完全準拠版 Frontend

let currentMetrics = null;
let regionalResult = null;
let pendingImportData = null;

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  
  document.querySelectorAll('.tab-btn').forEach(el => {
    el.classList.remove('border-white', 'text-white');
    el.classList.add('border-transparent', 'text-emerald-200');
  });
  
  document.querySelectorAll('.m-tab-btn').forEach(el => {
    el.classList.remove('text-emerald-800', 'font-bold');
    el.classList.add('text-slate-500', 'font-medium');
  });

  const targetTab = document.getElementById('tab-' + tabId);
  const targetBtn = document.getElementById('tab-btn-' + tabId);
  const targetMBtn = document.getElementById('m-tab-btn-' + tabId);

  if (targetTab) targetTab.classList.remove('hidden');
  if (targetBtn) {
    targetBtn.classList.remove('border-transparent', 'text-emerald-200');
    targetBtn.classList.add('border-white', 'text-white');
  }
  if (targetMBtn) {
    targetMBtn.classList.remove('text-slate-500', 'font-medium');
    targetMBtn.classList.add('text-emerald-800', 'font-bold');
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (tabId === 'report') {
    updateReportView();
  }

  lucide.createIcons();
}

function toggleSimulatorDrawer(forceState) {
  const drawer = document.getElementById('simulatorDrawer');
  if (!drawer) return;
  if (typeof forceState === 'boolean') {
    if (forceState) drawer.classList.remove('hidden');
    else drawer.classList.add('hidden');
  } else {
    drawer.classList.toggle('hidden');
  }
  lucide.createIcons();
}

document.addEventListener('click', (e) => {
  const drawer = document.getElementById('simulatorDrawer');
  if (drawer && e.target === drawer) {
    toggleSimulatorDrawer(false);
  }
});

async function loadMetrics() {
  try {
    const res = await fetch('/api/metrics');
    currentMetrics = await res.json();
    populateMetricsForm(currentMetrics);
    await evaluateRegional(currentMetrics);
  } catch (err) {
    console.error('Failed to load metrics:', err);
  }
}

function populateMetricsForm(m) {
  const pNameEls = [document.getElementById('headerPharmacyName'), document.getElementById('reportPharmacyName')];
  pNameEls.forEach(el => { if (el) el.innerText = m.pharmacy_name; });

  document.getElementById('inputPharmacyName').value = m.pharmacy_name;
  document.getElementById('inputBasicFeeType').value = m.dispensing_basic_fee_type;
  document.getElementById('inputMonthlyRx').value = m.monthly_prescriptions;
  
  document.getElementById('inputGeneric').value = m.generic_percentage;
  document.getElementById('inputStockDrugs').value = m.stock_drugs_count;
  document.getElementById('inputDeviceCount').value = m.self_medication_device_count;

  document.getElementById('inputRec1').value = m.rec_1_night_holiday_count;
  document.getElementById('inputRec2').value = m.rec_2_narcotics_count;
  document.getElementById('inputRec3').value = m.rec_3_prevention_adjustment_count;
  document.getElementById('inputRec4').value = m.rec_4_guidance_1a_2a_count;
  document.getElementById('inputRec5').value = m.rec_5_outpatient_support_1_count;
  document.getElementById('inputRec6').value = m.rec_6_home_visit_count;
  document.getElementById('inputRec7').value = m.rec_7_info_provision_tr_count;
  document.getElementById('inputRec8').value = m.rec_8_pediatric_special_count;
  document.getElementById('inputRec9').value = m.rec_9_multidisciplinary_conference_count;

  document.getElementById('statMonthlyRx').innerText = m.monthly_prescriptions.toLocaleString();
  document.getElementById('statStockDrugs').innerText = m.stock_drugs_count.toLocaleString();
  document.getElementById('genericRateDisplay').innerText = `${m.generic_percentage.toFixed(1)} %`;
}

async function evaluateRegional(metrics) {
  try {
    const res = await fetch('/api/evaluate-regional', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(metrics)
    });
    regionalResult = await res.json();
    renderRegionalDashboard(regionalResult, metrics);
  } catch (err) {
    console.error('Evaluation failed:', err);
  }
}

function renderRegionalDashboard(result, metrics) {
  const tierTitle = document.getElementById('tierBadgeTitle');
  tierTitle.innerText = result.current_tier;
  tierTitle.className = result.points_earned > 0 
    ? 'text-xl sm:text-2xl font-black text-emerald-800 mt-0.5 sm:mt-1' 
    : 'text-xl sm:text-2xl font-black text-rose-600 mt-0.5 sm:mt-1';
  
  document.getElementById('tierPoints').innerText = `+${result.points_earned} 点`;
  document.getElementById('genericStatusText').innerText = metrics.generic_percentage >= 85.0 ? '適合 (85%以上)' : '未達 (85%未満)';

  const annualYen = metrics.monthly_prescriptions * 12 * result.points_earned * 10;
  document.getElementById('annualRevenueEst').innerText = `¥ ${annualYen.toLocaleString()}`;

  document.getElementById('summaryMsgText').innerText = result.summary_message;

  // Supply Actions
  const sList = document.getElementById('supplyActionList');
  sList.innerHTML = result.supply_actions.length === 0 
    ? '<li class="text-emerald-800 font-bold">全8項目を完全クリア中！</li>' 
    : result.supply_actions.map(a => `<li>${a}</li>`).join('');

  // Struct Actions
  const stList = document.getElementById('structActionList');
  stList.innerHTML = result.structural_actions.length === 0 
    ? '<li class="text-emerald-800 font-bold">十分な体制要件をクリア中！</li>' 
    : result.structural_actions.map(a => `<li>${a}</li>`).join('');

  // Perf Actions
  const pList = document.getElementById('perfActionList');
  pList.innerHTML = result.performance_actions.length === 0 
    ? '<li class="text-emerald-800 font-bold">全実績基準をクリア中！</li>' 
    : result.performance_actions.map(a => `<li>${a}</li>`).join('');

  // 1. Performance 9 Grid
  const perfGrid = document.getElementById('perfRequirementsGrid');
  perfGrid.innerHTML = '';
  result.performance_requirements.forEach(req => {
    const isOk = req.is_satisfied;
    const progress = Math.min(100, Math.max(0, req.progress_percentage));
    const card = document.createElement('div');
    card.className = `bg-white rounded-xl shadow-sm border ${isOk ? 'border-slate-200' : 'border-amber-300 bg-amber-50/20'} p-3.5 flex flex-col justify-between`;
    card.innerHTML = `
      <div>
        <div class="flex justify-between items-start mb-1">
          <h4 class="text-xs sm:text-sm font-bold text-slate-900 leading-snug">${req.name}</h4>
          <span class="text-[10px] px-2 py-0.5 rounded-full font-bold ${isOk ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
            ${isOk ? '達成' : req.shortage_text}
          </span>
        </div>
        <div class="mt-2 flex items-baseline justify-between text-xs mb-1">
          <span class="font-black text-slate-800 text-sm sm:text-base">${req.current_value_text}</span>
          <span class="text-slate-400 text-[10px]">${req.target_value_text}</span>
        </div>
        <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden mb-1">
          <div class="h-full rounded-full ${isOk ? 'bg-emerald-600' : 'bg-amber-500'}" style="width: ${progress}%"></div>
        </div>
      </div>
      <p class="text-[10px] text-slate-500 mt-1 pt-1 border-t border-slate-100">
        <strong class="text-slate-700">指針:</strong> ${req.advice}
      </p>
    `;
    perfGrid.appendChild(card);
  });

  // 2. Supply 8 Grid
  const supplyGrid = document.getElementById('supplyRequirementsGrid');
  supplyGrid.innerHTML = '';
  result.supply_requirements.forEach(req => {
    const isOk = req.is_satisfied;
    const card = document.createElement('div');
    card.className = `bg-white rounded-lg border ${isOk ? 'border-slate-200' : 'border-rose-300 bg-rose-50/20'} p-2.5 flex flex-col justify-between text-xs`;
    card.innerHTML = `
      <div class="flex justify-between items-center mb-1">
        <span class="font-bold text-slate-800 text-[11px]">${req.name}</span>
        <span class="text-[9px] px-1.5 py-0.2 rounded font-bold ${isOk ? 'bg-blue-100 text-blue-800' : 'bg-rose-100 text-rose-800'}">
          ${isOk ? '適' : '未達'}
        </span>
      </div>
      <span class="text-[10px] text-slate-500">${req.official_ref}</span>
    `;
    supplyGrid.appendChild(card);
  });

  // 3. Structural Grid
  const structGrid = document.getElementById('structRequirementsGrid');
  structGrid.innerHTML = '';
  result.structural_requirements.forEach(req => {
    const isOk = req.is_satisfied;
    const card = document.createElement('div');
    card.className = `bg-white rounded-xl shadow-sm border ${isOk ? 'border-slate-200' : 'border-purple-300 bg-purple-50/20'} p-3 flex flex-col justify-between text-xs`;
    card.innerHTML = `
      <div class="flex justify-between items-start mb-1">
        <h5 class="font-bold text-slate-900 text-xs">${req.name}</h5>
        <span class="text-[10px] px-2 py-0.5 rounded-full font-bold ${isOk ? 'bg-purple-100 text-purple-800' : 'bg-rose-100 text-rose-800'}">
          ${isOk ? '適合' : '要整備'}
        </span>
      </div>
      <div class="text-[11px] text-slate-600 mt-1">${req.current_value_text}</div>
    `;
    structGrid.appendChild(card);
  });

  lucide.createIcons();
}

async function handleSaveMetrics(e) {
  e.preventDefault();
  const updated = {
    pharmacy_name: document.getElementById('inputPharmacyName').value || 'ひまわり調剤薬局',
    dispensing_basic_fee_type: document.getElementById('inputBasicFeeType').value,
    monthly_prescriptions: parseInt(document.getElementById('inputMonthlyRx').value) || 1200,
    generic_percentage: parseFloat(document.getElementById('inputGeneric').value) || 85.0,
    stock_drugs_count: parseInt(document.getElementById('inputStockDrugs').value) || 1200,
    self_medication_device_count: parseInt(document.getElementById('inputDeviceCount').value) || 3,
    
    rec_1_night_holiday_count: parseInt(document.getElementById('inputRec1').value) || 0,
    rec_2_narcotics_count: parseInt(document.getElementById('inputRec2').value) || 0,
    rec_3_prevention_adjustment_count: parseInt(document.getElementById('inputRec3').value) || 0,
    rec_4_guidance_1a_2a_count: parseInt(document.getElementById('inputRec4').value) || 0,
    rec_5_outpatient_support_1_count: parseInt(document.getElementById('inputRec5').value) || 0,
    rec_6_home_visit_count: parseInt(document.getElementById('inputRec6').value) || 0,
    rec_7_info_provision_tr_count: parseInt(document.getElementById('inputRec7').value) || 0,
    rec_8_pediatric_special_count: parseInt(document.getElementById('inputRec8').value) || 0,
    rec_9_multidisciplinary_conference_count: parseInt(document.getElementById('inputRec9').value) || 0
  };

  currentMetrics = Object.assign(currentMetrics, updated);
  populateMetricsForm(currentMetrics);

  await fetch('/api/metrics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(currentMetrics)
  });

  await evaluateRegional(currentMetrics);
  toggleSimulatorDrawer(false);
}

function resetToDefaultMetrics() {
  fetch('/api/metrics')
    .then(res => res.json())
    .then(data => {
      populateMetricsForm(data);
      evaluateRegional(data);
    });
}

// File Upload & Sample
async function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('/api/import-file', { method: 'POST', body: formData });
  const data = await res.json();
  if (data.status === 'success') {
    applyImportedParsed(data.parsed_data);
  }
}

async function loadSampleData() {
  const res = await fetch('/api/sample-import', { method: 'POST' });
  const data = await res.json();
  if (data.status === 'success') {
    applyImportedParsed(data.parsed_data);
  }
}

async function applyImportedParsed(parsed) {
  Object.assign(currentMetrics, parsed);
  populateMetricsForm(currentMetrics);
  await fetch('/api/metrics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(currentMetrics)
  });
  await evaluateRegional(currentMetrics);
  alert('⚡ レセコンデータの実績9項目 ＆ 後発品割合を自動集計・反映しました！');
}

function setupDropZone() {
  const zone = document.getElementById('dropZone');
  if (!zone) return;
  ['dragenter', 'dragover'].forEach(name => {
    zone.addEventListener(name, (e) => { e.preventDefault(); zone.classList.add('drop-zone-active'); });
  });
  ['dragleave', 'drop'].forEach(name => {
    zone.addEventListener(name, (e) => { e.preventDefault(); zone.classList.remove('drop-zone-active'); });
  });
  zone.addEventListener('drop', async (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const formData = new FormData();
      formData.append('file', files[0]);
      const res = await fetch('/api/import-file', { method: 'POST', body: formData });
      const data = await res.json();
      if (data.status === 'success') {
        applyImportedParsed(data.parsed_data);
      }
    }
  });
}

// Patient Navigator Logic
function getPatientConditionFromUI() {
  return {
    patient_name: '来局患者様',
    age: parseInt(document.getElementById('pAge').value) || 60,
    has_medicine_notebook: document.getElementById('pNotebook').checked,
    family_pharmacist_agreed: document.getElementById('pFamily').checked,
    is_home_care: document.getElementById('pHomeCare').checked,
    has_narcotics: document.getElementById('pNarcotics').checked,
    has_high_risk_drug: document.getElementById('pHighRisk').checked,
    has_anticancer_drug: document.getElementById('pCancer').checked,
    is_new_drug_or_dosage_changed: document.getElementById('pFollowUp').checked,
    has_leftover_drugs: document.getElementById('pLeftover').checked,
    has_spontaneous_doctor_feedback: document.getElementById('pTraceReport').checked
  };
}

let evalTimeout = null;
function triggerPatientEval() {
  if (evalTimeout) clearTimeout(evalTimeout);
  evalTimeout = setTimeout(async () => {
    const condition = getPatientConditionFromUI();
    const res = await fetch('/api/suggest-patient-billing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(condition)
    });
    const result = await res.json();
    renderPatientBillingResult(result);
  }, 100);
}

function renderPatientBillingResult(result) {
  document.getElementById('patientTotalPts').innerText = `+${result.total_points}`;
  const yen1 = result.total_points * 10;
  const yen3 = result.total_points * 30;
  document.getElementById('patientTotalYen').innerText = `(1割: +${yen1}円 / 3割: +${yen3}円)`;

  const badgeContainer = document.getElementById('regionalContribBadges');
  badgeContainer.innerHTML = '';
  result.regional_contributions.forEach(badgeText => {
    const span = document.createElement('span');
    span.className = 'bg-amber-400 text-slate-900 text-[10px] sm:text-xs px-2 py-0.5 rounded-full font-bold shadow-sm flex items-center gap-1';
    span.innerHTML = `<i data-lucide="star" class="w-3 h-3 fill-current text-slate-900"></i> ${badgeText}`;
    badgeContainer.appendChild(span);
  });

  const adviceCard = document.getElementById('patientAdviceCard');
  adviceCard.innerHTML = '';
  result.advice_comments.forEach(c => {
    const p = document.createElement('p');
    p.className = 'flex items-start gap-1.5 leading-snug';
    p.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5"></i> <span>${c}</span>`;
    adviceCard.appendChild(p);
  });

  const container = document.getElementById('patientBillingCards');
  container.innerHTML = '';
  document.getElementById('patientItemCount').innerText = `${result.recommended_items.length} 件算定可能`;

  result.recommended_items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl shadow-sm border border-slate-200 p-3.5 space-y-2';
    card.innerHTML = `
      <div class="flex justify-between items-start gap-2">
        <div>
          <span class="text-[9px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">${item.category}</span>
          <h4 class="text-xs sm:text-sm font-bold text-slate-900 mt-0.5">${item.name}</h4>
        </div>
        <div class="text-right shrink-0">
          <span class="text-sm sm:text-base font-black text-emerald-800">+${item.points} 点</span>
          <div class="text-[9px] text-slate-400">${item.points * 10}円分</div>
        </div>
      </div>
      <p class="text-[11px] text-slate-600 leading-snug">${item.description}</p>
      <div class="bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs">
        <div class="flex justify-between items-center mb-1">
          <span class="font-bold text-[10px] text-slate-700 flex items-center gap-1">
            <i data-lucide="file-edit" class="w-3 h-3 text-emerald-600"></i> 薬歴記載の要点
          </span>
        </div>
        <p class="text-[10px] text-slate-600 leading-normal">${item.chart_notes}</p>
      </div>
    `;
    container.appendChild(card);
  });
  lucide.createIcons();
}

function resetPatientCondition() {
  document.getElementById('pAge').value = '68';
  document.getElementById('pNotebook').checked = true;
  document.getElementById('pFamily').checked = false;
  document.getElementById('pHomeCare').checked = false;
  document.getElementById('pNarcotics').checked = false;
  document.getElementById('pHighRisk').checked = true;
  document.getElementById('pCancer').checked = false;
  document.getElementById('pFollowUp').checked = true;
  document.getElementById('pLeftover').checked = false;
  document.getElementById('pTraceReport').checked = false;
  triggerPatientEval();
}

function updateReportView() {
  if (!currentMetrics || !regionalResult) return;
  const today = new Date();
  const dateStr = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;
  document.getElementById('reportDate').innerText = dateStr;
  document.getElementById('reportPharmacyName').innerText = currentMetrics.pharmacy_name;
  document.getElementById('reportCurrentTier').innerText = regionalResult.current_tier;
  document.getElementById('repTier').innerText = regionalResult.current_tier;
  document.getElementById('repPoints').innerText = `+${regionalResult.points_earned}`;
  document.getElementById('repGeneric').innerText = `${currentMetrics.generic_percentage.toFixed(1)}%`;
  document.getElementById('repDevice').innerText = `${currentMetrics.self_medication_device_count}種設置`;

  const perfTbody = document.getElementById('reportPerfTableBody');
  perfTbody.innerHTML = '';
  regionalResult.performance_requirements.forEach(req => {
    const tr = document.createElement('tr');
    tr.className = req.is_satisfied ? 'bg-white' : 'bg-amber-50/50';
    tr.innerHTML = `
      <td class="border border-slate-200 p-1.5 font-bold text-slate-800">${req.name}</td>
      <td class="border border-slate-200 p-1.5 text-center">${req.current_value_text}</td>
      <td class="border border-slate-200 p-1.5 text-center text-slate-500">${req.target_value_text}</td>
      <td class="border border-slate-200 p-1.5 text-center">
        <span class="px-1.5 py-0.5 rounded text-[9px] font-bold ${req.is_satisfied ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
          ${req.is_satisfied ? '達成' : '不足'}
        </span>
      </td>
      <td class="border border-slate-200 p-1.5 text-slate-600 text-[10px]">${req.advice}</td>
    `;
    perfTbody.appendChild(tr);
  });
  lucide.createIcons();
}

function printReport() {
  switchTab('report');
  setTimeout(() => { window.print(); }, 300);
}

document.addEventListener('DOMContentLoaded', () => {
  loadMetrics();
  triggerPatientEval();
  setupDropZone();
});
