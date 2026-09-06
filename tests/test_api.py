import unittest
import math
from app.models.schemas import (
    PharmacyMetrics,
    ADD01_POINTS, ADD02_POINTS, ADD03_POINTS, ADD04_POINTS, ADD05_POINTS
)
from app.rules.regional_support import evaluate_regional_support
from app.rules.patient_billing import evaluate_patient_billing
from app.models.schemas import PatientCondition

class TestRegionalSupportRevision2026(unittest.TestCase):
    
    def test_point_master_constants(self):
        """正式告示点数のマスター値検証: 27, 59, 67, 37, 59"""
        self.assertEqual(ADD01_POINTS, 27)
        self.assertEqual(ADD02_POINTS, 59)
        self.assertEqual(ADD03_POINTS, 67)
        self.assertEqual(ADD04_POINTS, 37)
        self.assertEqual(ADD05_POINTS, 59)

    def test_tc_08_a_tier1_basic1_supply_only(self):
        """TC-08-A: 調剤基本料1 + 供給体制8項目(GE>=85%) -> 加算1 (27点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=12000,
            generic_percentage=85.5,
            stock_drugs_count=800,
            self_medication_device_count=1,
            rec_4_guidance_1a_2a_count=0
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertEqual(res.tier_code, "tier_1")
        self.assertEqual(res.points_earned, 27)
        self.assertTrue(res.supply_system_qualified)
        self.assertFalse(res.structural_system_qualified)

    def test_tc_08_b_tier2_basic1_structural_and_perf3(self):
        """TC-08-B: 調剤基本料1 + 供給体制 + 十分な体制 + 実績(4)+3項目 -> 加算2 (59点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=86.0,
            stock_drugs_count=1250,
            self_medication_device_count=3,
            rec_1_night_holiday_count=45,
            rec_2_narcotics_count=0,
            rec_3_prevention_adjustment_count=22,
            rec_4_guidance_1a_2a_count=25,
            rec_5_outpatient_support_1_count=0,
            rec_6_home_visit_count=0,
            rec_7_info_provision_tr_count=0,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算2")
        self.assertEqual(res.tier_code, "tier_2")
        self.assertEqual(res.points_earned, 59)
        self.assertTrue(res.supply_system_qualified)
        self.assertTrue(res.structural_system_qualified)

    def test_tc_08_c_tier3_basic1_structural_and_perf7(self):
        """TC-08-C: 調剤基本料1 + 供給体制 + 十分な体制 + 実績7項目 -> 加算3 (67点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1300,
            self_medication_device_count=4,
            rec_1_night_holiday_count=50,
            rec_2_narcotics_count=2,
            rec_3_prevention_adjustment_count=25,
            rec_4_guidance_1a_2a_count=30,
            rec_5_outpatient_support_1_count=3,
            rec_6_home_visit_count=30,
            rec_7_info_provision_tr_count=40,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算3")
        self.assertEqual(res.tier_code, "tier_3")
        self.assertEqual(res.points_earned, 67)

    def test_tc_08_d_tier4_basic2_structural_and_perf3_req4_req6(self):
        """TC-08-D: 調剤基本料2 + 供給体制 + 十分な体制 + 実績(4)&(6)必須+3項目 -> 加算4 (37点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_2",
            annual_prescriptions=10000,
            generic_percentage=87.0,
            stock_drugs_count=1200,
            self_medication_device_count=3,
            rec_1_night_holiday_count=410,
            rec_2_narcotics_count=0,
            rec_3_prevention_adjustment_count=0,
            rec_4_guidance_1a_2a_count=45,
            rec_5_outpatient_support_1_count=0,
            rec_6_home_visit_count=25,
            rec_7_info_provision_tr_count=0,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算4")
        self.assertEqual(res.tier_code, "tier_4")
        self.assertEqual(res.points_earned, 37)

    def test_tc_08_e_tier5_basic3a_structural_and_perf7(self):
        """TC-08-E: 調剤基本料3イ + 供給体制 + 十分な体制 + 上位実績7項目 -> 加算5 (59点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_3_a",
            annual_prescriptions=10000,
            generic_percentage=89.0,
            stock_drugs_count=1400,
            self_medication_device_count=3,
            rec_1_night_holiday_count=420,
            rec_2_narcotics_count=12,
            rec_3_prevention_adjustment_count=45,
            rec_4_guidance_1a_2a_count=50,
            rec_5_outpatient_support_1_count=15,
            rec_6_home_visit_count=30,
            rec_7_info_provision_tr_count=70,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算5")
        self.assertEqual(res.tier_code, "tier_5")
        self.assertEqual(res.points_earned, 59)

    def test_tc_neg_special_b(self):
        """特別調剤基本料B (special_b): 全要件を満たしても加算1〜5不可 (0点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="special_b",
            annual_prescriptions=10000,
            generic_percentage=95.0,
            stock_drugs_count=2000,
            self_medication_device_count=5,
            rec_1_night_holiday_count=500,
            rec_2_narcotics_count=20,
            rec_3_prevention_adjustment_count=50,
            rec_4_guidance_1a_2a_count=60,
            rec_5_outpatient_support_1_count=20,
            rec_6_home_visit_count=40,
            rec_7_info_provision_tr_count=80,
            rec_8_pediatric_special_count=5,
            rec_9_multidisciplinary_conference_count=10
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.current_tier, "算定不可")
        self.assertEqual(res.points_earned, 0)
        self.assertTrue(any("特別調剤基本料B" in s for s in res.audit_trail))

    def test_tc_ge_boundary_and_special(self):
        """後発医薬品割合 境界値テスト (84.9% vs 85.0%) および特例除外計算"""
        m_fail = PharmacyMetrics(dispensing_basic_fee_type="basic_1", generic_percentage=84.9)
        res_fail = evaluate_regional_support(m_fail)
        self.assertEqual(res_fail.current_tier, "算定不可")
        self.assertFalse(res_fail.supply_system_qualified)

        m_pass = PharmacyMetrics(dispensing_basic_fee_type="basic_1", generic_percentage=85.0, stock_drugs_count=500)
        res_pass = evaluate_regional_support(m_pass)
        self.assertEqual(res_pass.current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertEqual(res_pass.points_earned, 27)

        m_spec = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            generic_percentage=83.0,
            temporary_exclusion_enabled=True,
            generic_percentage_special_applied=86.5,
            stock_drugs_count=500
        )
        res_spec = evaluate_regional_support(m_spec)
        self.assertEqual(res_spec.current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertEqual(res_spec.points_earned, 27)

    def test_tc_rx_count_scaling_correction(self):
        """処方箋受付回数1万枚補正テスト (8,000枚: 係数1.0 vs 15,000枚: 係数1.5)"""
        m_small = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=8000,
            rec_1_night_holiday_count=40
        )
        res_small = evaluate_regional_support(m_small)
        req1_small = next(r for r in res_small.performance_requirements if r.id == "REQ-PRF-01")
        self.assertEqual(req1_small.target_value_text, "基準: 40 回 (上位: 400)")
        self.assertTrue(req1_small.is_satisfied)

        m_large = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=15000,
            rec_1_night_holiday_count=59
        )
        res_large = evaluate_regional_support(m_large)
        req1_large = next(r for r in res_large.performance_requirements if r.id == "REQ-PRF-01")
        self.assertEqual(req1_large.target_value_text, "基準: 60 回 (上位: 600)")
        self.assertFalse(req1_large.is_satisfied)

    def test_tc_structural_conditions_boundary(self):
        """十分な体制の境界値テスト (備蓄1199 vs 1200, 機器2種 vs 3種)"""
        m_stock = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            stock_drugs_count=1199,
            self_medication_device_count=3,
            rec_1_night_holiday_count=50,
            rec_3_prevention_adjustment_count=25,
            rec_4_guidance_1a_2a_count=30
        )
        res_stock = evaluate_regional_support(m_stock)
        self.assertEqual(res_stock.current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertFalse(res_stock.structural_system_qualified)

        m_device = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            stock_drugs_count=1200,
            self_medication_device_count=2,
            rec_1_night_holiday_count=50,
            rec_3_prevention_adjustment_count=25,
            rec_4_guidance_1a_2a_count=30
        )
        res_device = evaluate_regional_support(m_device)
        self.assertEqual(res_device.current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertFalse(res_device.structural_system_qualified)

    def test_tc_mandatory_perf_rules(self):
        """加算2における(4)必須要件、加算4における(4)および(6)必須要件の検証"""
        m_t2_fail = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            stock_drugs_count=1200,
            self_medication_device_count=3,
            rec_1_night_holiday_count=50,
            rec_2_narcotics_count=5,
            rec_3_prevention_adjustment_count=30,
            rec_4_guidance_1a_2a_count=0, # 必須未達
            rec_5_outpatient_support_1_count=0,
            rec_6_home_visit_count=0,
            rec_7_info_provision_tr_count=0,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        res_t2 = evaluate_regional_support(m_t2_fail)
        self.assertEqual(res_t2.current_tier, "地域支援・医薬品供給対応体制加算1")

        m_t4_fail = PharmacyMetrics(
            dispensing_basic_fee_type="basic_2",
            annual_prescriptions=10000,
            stock_drugs_count=1200,
            self_medication_device_count=3,
            rec_1_night_holiday_count=500,
            rec_2_narcotics_count=0,
            rec_3_prevention_adjustment_count=50,
            rec_4_guidance_1a_2a_count=50,
            rec_5_outpatient_support_1_count=0,
            rec_6_home_visit_count=0, # 必須未達 (基準24)
            rec_7_info_provision_tr_count=0,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        res_t4 = evaluate_regional_support(m_t4_fail)
        self.assertEqual(res_t4.current_tier, "算定不可")
        self.assertEqual(res_t4.points_earned, 0)

    def test_tc_other_eligible_fee_types(self):
        """特別調剤基本料Bを除く他の基本料（basic_3_b, basic_3_c, special_a）での加算4適合テスト"""
        for fee in ["basic_3_b", "basic_3_c", "special_a"]:
            m = PharmacyMetrics(
                dispensing_basic_fee_type=fee,
                annual_prescriptions=10000,
                generic_percentage=87.0,
                stock_drugs_count=1200,
                self_medication_device_count=3,
                rec_1_night_holiday_count=410,
                rec_2_narcotics_count=0,
                rec_3_prevention_adjustment_count=0,
                rec_4_guidance_1a_2a_count=45,
                rec_5_outpatient_support_1_count=0,
                rec_6_home_visit_count=25,
                rec_7_info_provision_tr_count=0,
                rec_8_pediatric_special_count=0,
                rec_9_multidisciplinary_conference_count=0
            )
            res = evaluate_regional_support(m)
            self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算4", f"Failed for {fee}")
            self.assertEqual(res.points_earned, 37, f"Failed for {fee}")

    def test_tc_patient_billing(self):
        """個別患者指導ナビゲーターの算定判定テスト"""
        p = PatientCondition(
            patient_name="テスト患者",
            age=72,
            has_medicine_notebook=True,
            family_pharmacist_agreed=False,
            has_high_risk_drug=True,
            is_new_drug_or_dosage_changed=True
        )
        b_res = evaluate_patient_billing(p)
        self.assertTrue(b_res.total_points > 0)
        self.assertTrue(any(item.code == "140049910" for item in b_res.recommended_items))
        self.assertTrue(any(item.code == "140058770" for item in b_res.recommended_items))

if __name__ == '__main__':
    unittest.main()



