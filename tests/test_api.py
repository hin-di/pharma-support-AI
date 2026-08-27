from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Test 1: GET /
res = client.get('/')
assert res.status_code == 200, f'Status {res.status_code}'
assert 'PharmaSupport AI' in res.text
print('Test 1 Passed: GET / (HTML response)')

# Test 2: GET /api/metrics
res = client.get('/api/metrics')
assert res.status_code == 200
data = res.json()
assert 'pharmacy_name' in data
print('Test 2 Passed: GET /api/metrics ->', data['pharmacy_name'])

# Test 3: POST /api/evaluate-regional
res = client.post('/api/evaluate-regional', json=data)
assert res.status_code == 200
eval_data = res.json()
print('Test 3 Passed: POST /api/evaluate-regional -> Tier:', eval_data['current_tier'], '| Points:', eval_data['points_earned'])
print('Requirements count:', len(eval_data['requirements']))

# Test 4: POST /api/suggest-patient-billing
patient_input = {
    'patient_name': '山田花子',
    'age': 72,
    'has_medicine_notebook': True,
    'family_pharmacist_agreed': True,
    'is_home_care': False,
    'has_narcotics': True,
    'has_high_risk_drug': True,
    'has_anticancer_drug': False,
    'has_inhalation_drug': False,
    'is_first_inhalation_or_device_change': False,
    'has_leftover_drugs': True,
    'has_prescription_query_changed': True,
    'is_new_drug_or_dosage_changed': True,
    'has_doctor_feedback_requested': False,
    'has_spontaneous_doctor_feedback': True,
    'has_hospital_discharge_cooperation': False,
    'is_pediatric_special': False
}
res = client.post('/api/suggest-patient-billing', json=patient_input)
assert res.status_code == 200
billing_data = res.json()
print('Test 4 Passed: POST /api/suggest-patient-billing -> Items:', len(billing_data['recommended_items']), '| Total Points:', billing_data['total_points'])
for item in billing_data['recommended_items']:
    name = item['name']
    pts = item['points']
    cat = item['category']
    print(f"  - {name}: +{pts}点 ({cat})")
print('Regional contributions:', billing_data['regional_contributions'])
