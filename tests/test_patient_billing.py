import unittest
from app.models.schemas import PatientCondition
from app.rules.patient_billing import evaluate_patient_billing

class TestPatientBilling(unittest.TestCase):
    def test_tc_patient_billing_basic_and_high_risk(self):
        p = PatientCondition(
            patient_name="テスト患者",
            age=72,
            has_medicine_notebook=True,
            family_pharmacist_agreed=False,
            has_high_risk_drug=True,
            is_new_drug_or_dosage_changed=True
        )
        res = evaluate_patient_billing(p)
        self.assertTrue(res.total_points > 0)
        self.assertTrue(any(item.code == "140049910" for item in res.recommended_items))
        self.assertTrue(any(item.code == "140058770" for item in res.recommended_items))

if __name__ == '__main__':
    unittest.main()
