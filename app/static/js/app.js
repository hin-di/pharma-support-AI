// PharmaSupport AI Frontend Script (Mobile & Desktop Responsive)

let currentMetrics = null;
let regionalResult = null;
let metricsChart = null;

// Tab Management (Supporting Desktop & Mobile Bottom Nav)
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  
  // Desktop Tab Buttons
  document.querySelectorAll('.tab-btn').forEach(el => {
    el.classList.remove('border-white', 'text-white');
    el.classList.add('border-transparent', 'text-emerald-200');
  });
  
  // Mobile Tab Buttons
  document.querySelectorAll('.m-tab-btn').forEach(el => {
    el.classList.remove('text-emerald-700', 'font-bold');
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
    targetMBtn.classList.add('text-emerald-700', 'font-bold');
  }

  // Scroll to top on tab switch
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
    if (forceState) {
      drawer.classList.remove('hidden');
    } else {
      drawer.classList.add('hidden');
    }
  } else {
    drawer.classList.toggle('hidden');
  }
  
  lucide.createIcons();
}

// Close modal when clicking background overlay
document.addEventListener('click', (e) => {
  const drawer = document.getElementById('simulatorDrawer');
  if (drawer && e.target === drawer) {
    toggleSimulatorDrawer(false);
  }
});

function toggleInhaleChild() {
  const isChecked = document.getElementById('pInhale').checked;
  const childBox = document.getElementById('inhaleChildBox');
  if (isChecked) {
    childBox.classList.remove('hidden');
    document.getElementById('pInhaleFirst').checked = true;
  } else {
    childBox.classList.add('hidden');
    document.getElementById('pInhaleFirst').checked = false;
  }
}

// ----------------------------------------------------
// Pharmacy Metrics & Regional Support Logic
// ----------------------------------------------------
async function loadMetrics() {
  try {
    const res = await fetch('/api/metrics');
    currentMetrics = await res.json();
    populateMetricsForm(currentMetrics);
    await evaluateRegional(currentMetrics);
    renderMetricsChart();
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
  document.getElementById('inputNarcotics').value = m.narcotics_count;
  document.getElementById('inputHomeVisit').value = m.home_visit_count;
  document.getElementById('inputFamilyPharm').value = m.family_pharmacist_count;
  document.getElementById('inputInfoProv').value = m.info_provision_count;
  document.getElementById('inputPreavoid').value = m.preavoid_count;
  document.getElementById('inputGeneric').value = m.generic_percentage;
  document.getElementById('inputStockDrugs').value = m.stock_drugs_count;

  document.getElementById('statMonthlyRx').innerText = m.monthly_prescriptions.toLocaleString();
  document.getElementById('statStockDrugs').innerText = m.stock_drugs_count.toLocaleString();
  document.getElementById('statGenericRate').innerText = m.generic_percentage.toFixed(1);
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
  // 1. Tier Badge
  const tierTitle = document.getElementById('tierBadgeTitle');
  tierTitle.innerText = result.current_tier;
  if (result.points_earned > 0) {
    tierTitle.className = 'text-xl sm:text-2xl font-black text-emerald-700 mt-0.5 sm:mt-1';
  } else {
    tierTitle.className = 'text-xl sm:text-2xl font-black text-rose-600 mt-0.5 sm:mt-1';
  }
  document.getElementById('tierPoints').innerText = `+${result.points_earned} 点`;

  // 2. Supply System Addition
  const supplyTitle = document.getElementById('supplyStatusTitle');
  if (result.supply_system_addition_qualified) {
    supplyTitle.innerText = '適合（備蓄OK）';
    supplyTitle.className = 'text-lg sm:text-xl font-bold text-emerald-700 mt-0.5 sm:mt-1';
  } else {
    supplyTitle.innerText = '要件未達';
    supplyTitle.className = 'text-lg sm:text-xl font-bold text-rose-600 mt-0.5 sm:mt-1';
  }

  // 3. Annual Impact
  const annualYen = metrics.monthly_prescriptions * 12 * result.points_earned * 10;
  document.getElementById('annualRevenueEst').innerText = `¥ ${annualYen.toLocaleString()}`;

  // 4. Advices Banner
  document.getElementById('summaryMsgText').innerText = result.summary_message;
  const listEl = document.getElementById('priorityActionList');
  listEl.innerHTML = '';
  result.priority_actions.forEach(act => {
    const li = document.createElement('li');
    li.innerText = act;
    listEl.appendChild(li);
  });

  // 5. Requirements Cards
  const grid = document.getElementById('requirementsGrid');
  grid.innerHTML = '';

  result.requirements.forEach(req => {
    const isOk = req.is_satisfied;
    const progress = Math.min(100, Math.max(0, req.progress_percentage));
    
    const card = document.createElement('div');
    card.className = `bg-white rounded-xl shadow-sm border ${isOk ? 'border-slate-200' : 'border-amber-300 bg-amber-50/20'} p-3.5 sm:p-4 flex flex-col justify-between`;
    card.innerHTML = `
      <div>
        <div class="flex justify-between items-start mb-1.5 sm:mb-2">
          <div>
            <span class="text-[9px] sm:text-[10px] font-bold text-slate-400 uppercase tracking-wider">${req.category}</span>
            <h4 class="text-xs sm:text-sm font-bold text-slate-900 leading-snug">${req.name}</h4>
          </div>
          <span class="text-[10px] sm:text-xs px-2 py-0.5 rounded-full font-bold ${isOk ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-800'}">
            ${isOk ? '達成' : `不足:${req.shortage}${req.unit}`}
          </span>
        </div>

        <div class="mt-2 flex items-baseline justify-between text-xs mb-1">
          <span class="font-bold text-slate-800 text-sm sm:text-base">${req.current_value} <span class="text-[10px] sm:text-xs font-normal text-slate-500">${req.unit}</span></span>
          <span class="text-slate-400 text-[10px] sm:text-xs">目標: ${req.target_value} ${req.unit}</span>
        </div>

        <!-- Progress Bar -->
        <div class="w-full bg-slate-100 rounded-full h-1.5 sm:h-2 overflow-hidden mb-1.5">
          <div class="h-full rounded-full transition-all duration-500 ${isOk ? 'bg-emerald-500' : 'bg-amber-500'}" style="width: ${progress}%"></div>
        </div>
      </div>

      <p class="text-[10px] sm:text-[11px] text-slate-500 mt-1.5 pt-1.5 border-t border-slate-100 leading-normal">
        <strong class="text-slate-700">指針:</strong> ${req.advice}
      </p>
    `;
    grid.appendChild(card);
  });

  lucide.createIcons();
}

async function handleSaveMetrics(e) {
  e.preventDefault();
  const updated = {
    pharmacy_name: document.getElementById('inputPharmacyName').value || 'ひまわり調剤薬局',
    dispensing_basic_fee_type: document.getElementById('inputBasicFeeType').value,
    monthly_prescriptions: parseInt(document.getElementById('inputMonthlyRx').value) || 1000,
    concentration_rate: 75.0,
    narcotics_count: parseInt(document.getElementById('inputNarcotics').value) || 0,
    home_visit_count: parseInt(document.getElementById('inputHomeVisit').value) || 0,
    family_pharmacist_count: parseInt(document.getElementById('inputFamilyPharm').value) || 0,
    info_provision_count: parseInt(document.getElementById('inputInfoProv').value) || 0,
    preavoid_count: parseInt(document.getElementById('inputPreavoid').value) || 0,
    generic_percentage: parseFloat(document.getElementById('inputGeneric').value) || 80.0,
    night_holiday_count: 120,
    stock_drugs_count: parseInt(document.getElementById('inputStockDrugs').value) || 1200,
    has_24h_system: true,
    has_infection_system: true,
    has_online_qualification: true,
    has_electronic_prescription: true,
    has_otc_sales: true
  };

  currentMetrics = updated;
  populateMetricsForm(updated);

  await fetch('/api/metrics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updated)
  });

  await evaluateRegional(updated);
  toggleSimulatorDrawer();
}

function resetToDefaultMetrics() {
  fetch('/api/metrics')
    .then(res => res.json())
    .then(data => {
      populateMetricsForm(data);
      evaluateRegional(data);
    });
}

function renderMetricsChart() {
  const ctx = document.getElementById('metricsChart');
  if (!ctx) return;

  const months = ['9月', '10月', '11月', '12月', '1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月'];

  if (metricsChart) {
    metricsChart.destroy();
  }

  metricsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: '在宅訪問実績 (件/月)',
          data: [1, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2],
          borderColor: '#059669',
          backgroundColor: 'rgba(5, 150, 105, 0.1)',
          tension: 0.3,
          fill: true
        },
        {
          label: 'かかりつけ指導 (件/月)',
          data: [3, 3, 4, 3, 3, 4, 3, 3, 3, 3, 3, 3],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.3,
          fill: false
        },
        {
          label: '服薬情報等提供 (件/月)',
          data: [1, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1],
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          tension: 0.3,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { boxWidth: 10, font: { size: 10 } }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, font: { size: 9 } }
        },
        x: {
          ticks: { font: { size: 9 } }
        }
      }
    }
  });
}

// ----------------------------------------------------
// Patient Billing Navigator Logic
// ----------------------------------------------------
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
    has_inhalation_drug: document.getElementById('pInhale').checked,
    is_first_inhalation_or_device_change: document.getElementById('pInhaleFirst').checked,
    has_leftover_drugs: document.getElementById('pLeftover').checked,
    has_prescription_query_changed: false,
    is_new_drug_or_dosage_changed: document.getElementById('pFollowUp').checked,
    has_doctor_feedback_requested: false,
    has_spontaneous_doctor_feedback: document.getElementById('pTraceReport').checked,
    has_hospital_discharge_cooperation: false,
    is_pediatric_special: false
  };
}

let evalTimeout = null;
function triggerPatientEval() {
  if (evalTimeout) clearTimeout(evalTimeout);
  evalTimeout = setTimeout(async () => {
    const condition = getPatientConditionFromUI();
    try {
      const res = await fetch('/api/suggest-patient-billing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(condition)
      });
      const result = await res.json();
      renderPatientBillingResult(result);
    } catch (err) {
      console.error('Patient evaluation failed:', err);
    }
  }, 100);
}

function renderPatientBillingResult(result) {
  // Total Points
  document.getElementById('patientTotalPts').innerText = `+${result.total_points}`;
  const yen1 = result.total_points * 10;
  const yen3 = result.total_points * 30;
  document.getElementById('patientTotalYen').innerText = `(1割: +${yen1}円 / 3割: +${yen3}円)`;

  // Regional Contribution Badges
  const badgeContainer = document.getElementById('regionalContribBadges');
  badgeContainer.innerHTML = '';
  result.regional_contributions.forEach(badgeText => {
    const span = document.createElement('span');
    span.className = 'bg-amber-400 text-slate-900 text-[10px] sm:text-xs px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full font-bold shadow-sm flex items-center gap-1';
    span.innerHTML = `<i data-lucide="star" class="w-3 h-3 fill-current text-slate-900"></i> ${badgeText}`;
    badgeContainer.appendChild(span);
  });

  // Advice Card
  const adviceCard = document.getElementById('patientAdviceCard');
  adviceCard.innerHTML = '';
  result.advice_comments.forEach(c => {
    const p = document.createElement('p');
    p.className = 'flex items-start gap-1.5 leading-snug';
    p.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5"></i> <span>${c}</span>`;
    adviceCard.appendChild(p);
  });

  // Billing Items List
  const container = document.getElementById('patientBillingCards');
  container.innerHTML = '';
  document.getElementById('patientItemCount').innerText = `${result.recommended_items.length} 件算定可能`;

  if (result.recommended_items.length === 0) {
    container.innerHTML = `
      <div class="p-6 text-center bg-white rounded-xl border border-slate-200 text-slate-400">
        <i data-lucide="info" class="w-6 h-6 mx-auto mb-1.5 opacity-50"></i>
        <p class="text-xs">算定可能な個別加算はありません。基本の服薬管理指導料を算定してください。</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  result.recommended_items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl shadow-sm border border-slate-200 p-3.5 sm:p-4 space-y-2 sm:space-y-2.5';
    
    let contribBadgeHtml = '';
    if (item.contributes_to_regional_support) {
      contribBadgeHtml = `
        <div class="bg-emerald-50 border border-emerald-200 rounded-md px-2 py-1 text-[10px] sm:text-[11px] text-emerald-800 font-bold flex items-center gap-1">
          <i data-lucide="award" class="w-3 h-3 text-emerald-600"></i>
          <span>${item.contributes_to_regional_support}</span>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="flex justify-between items-start gap-2">
        <div>
          <span class="text-[9px] sm:text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">${item.category}</span>
          <h4 class="text-xs sm:text-sm font-bold text-slate-900 mt-0.5">${item.name}</h4>
        </div>
        <div class="text-right shrink-0">
          <span class="text-sm sm:text-base font-black text-emerald-700">+${item.points} 点</span>
          <div class="text-[9px] sm:text-[10px] text-slate-400">${item.points * 10}円分</div>
        </div>
      </div>

      <p class="text-[11px] sm:text-xs text-slate-600 leading-snug">${item.description}</p>

      ${contribBadgeHtml}

      <!-- Chart Notes Box -->
      <div class="bg-slate-50 border border-slate-200 rounded-lg p-2 sm:p-2.5 text-xs">
        <div class="flex justify-between items-center mb-1">
          <span class="font-bold text-[10px] sm:text-xs text-slate-700 flex items-center gap-1">
            <i data-lucide="file-edit" class="w-3 h-3 text-emerald-600"></i>
            薬歴記載の必須要点（監査対策）
          </span>
          <button onclick="copyChartText('${item.name}: ${item.chart_notes}')" class="text-[10px] text-emerald-700 hover:text-emerald-800 font-bold flex items-center gap-1 bg-white px-2 py-0.5 rounded border border-slate-200 shadow-2xs">
            <i data-lucide="copy" class="w-3 h-3"></i> コピー
          </button>
        </div>
        <p class="text-[10px] sm:text-[11px] text-slate-600 leading-normal">${item.chart_notes}</p>
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
  document.getElementById('pInhale').checked = false;
  document.getElementById('pInhaleFirst').checked = false;
  document.getElementById('inhaleChildBox').classList.add('hidden');
  document.getElementById('pFollowUp').checked = true;
  document.getElementById('pLeftover').checked = false;
  document.getElementById('pTraceReport').checked = false;

  triggerPatientEval();
}

function copyChartText(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert('薬歴テンプレート文をコピーしました！電子薬歴に貼り付けてご利用ください。');
  });
}

// ----------------------------------------------------
// Report & Printing Logic
// ----------------------------------------------------
function updateReportView() {
  if (!currentMetrics || !regionalResult) return;

  const today = new Date();
  const dateStr = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日（${['日','月','火','水','木','金','土'][today.getDay()]}）`;
  document.getElementById('reportDate').innerText = dateStr;
  document.getElementById('reportPharmacyName').innerText = currentMetrics.pharmacy_name;
  document.getElementById('reportCurrentTier').innerText = regionalResult.current_tier;

  document.getElementById('repTier').innerText = regionalResult.current_tier;
  document.getElementById('repPoints').innerText = `+${regionalResult.points_earned}`;
  document.getElementById('repSupply').innerText = regionalResult.supply_system_addition_qualified ? '適合' : '未達';
  document.getElementById('repStock').innerText = currentMetrics.stock_drugs_count;
  document.getElementById('repGeneric').innerText = currentMetrics.generic_percentage.toFixed(1);

  // Focus list
  const focusList = document.getElementById('reportFocusList');
  focusList.innerHTML = '';
  regionalResult.priority_actions.forEach(act => {
    const li = document.createElement('li');
    li.innerText = act;
    focusList.appendChild(li);
  });

  // Table rows
  const tbody = document.getElementById('reportTableBody');
  tbody.innerHTML = '';

  regionalResult.requirements.forEach(req => {
    const tr = document.createElement('tr');
    const isOk = req.is_satisfied;
    tr.className = isOk ? 'bg-white' : 'bg-amber-50/50';
    tr.innerHTML = `
      <td class="border border-slate-200 p-1.5 sm:p-2 font-bold text-slate-800">${req.name}</td>
      <td class="border border-slate-200 p-1.5 sm:p-2 text-center">${req.current_value}${req.unit}</td>
      <td class="border border-slate-200 p-1.5 sm:p-2 text-center text-slate-500">${req.target_value}${req.unit}</td>
      <td class="border border-slate-200 p-1.5 sm:p-2 text-center font-semibold">${req.progress_percentage}%</td>
      <td class="border border-slate-200 p-1.5 sm:p-2 text-center">
        <span class="px-1.5 py-0.5 rounded text-[9px] sm:text-[10px] font-bold ${isOk ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
          ${isOk ? 'OK' : '不足'}
        </span>
      </td>
      <td class="border border-slate-200 p-1.5 sm:p-2 text-slate-600 leading-tight text-[10px] sm:text-xs">${req.advice}</td>
    `;
    tbody.appendChild(tr);
  });

  lucide.createIcons();
}

function printReport() {
  switchTab('report');
  setTimeout(() => {
    window.print();
  }, 300);
}

// Initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  loadMetrics();
  triggerPatientEval();
});
