import unittest
import math
from app.models.schemas import (
    PharmacyMetrics,
    ADD01_POINTS, ADD02_POINTS, ADD03_POINTS, ADD04_POINTS, ADD05_POINTS
)
from app.rules.regional_support import evaluate_regional_support

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
            stock_drugs_count=800, # 基本料1基準(1200)未満
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
        """TC-08-B: 調剤基本料1 + 供給体制 + 十分な体制(1200品目等) + 実績(4)+3項目 -> 加算2 (59点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=86.0,
            stock_drugs_count=1200,
            self_medication_device_count=3,
            has_medical_materials_supply=True,
            has_medical_device_sales_license=True,
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
        """TC-08-C: 調剤基本料1 + 供給体制 + 十分な体制(1200品目等) + 実績7項目 -> 加算3 (67点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1250,
            self_medication_device_count=4,
            has_medical_materials_supply=True,
            has_medical_device_sales_license=True,
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
        """TC-08-D: 調剤基本料2 + 供給体制 + 十分な体制(1500品目等) + 実績(4)&(6)必須+3項目 -> 加算4 (37点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_2",
            annual_prescriptions=10000,
            generic_percentage=87.0,
            stock_drugs_count=1500, # 基本料1以外基準(1500)
            self_medication_device_count=3,
            has_medical_materials_supply=True,
            has_medical_device_sales_license=True,
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
        """TC-08-E: 調剤基本料3イ + 供給体制 + 十分な体制(1500品目等) + 上位実績7項目 -> 加算5 (59点)"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_3_a",
            annual_prescriptions=10000,
            generic_percentage=89.0,
            stock_drugs_count=1600,
            self_medication_device_count=3,
            has_medical_materials_supply=True,
            has_medical_device_sales_license=True,
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

    def test_tc_stock_drugs_boundary_basic1_vs_non_basic1(self):
        """備蓄品目数の基本料別境界値テスト（基本料1: 1199 vs 1200 / 基本料2: 1499 vs 1500）"""
        # 基本料1: 1,199品目は未達
        m_b1_fail = PharmacyMetrics(dispensing_basic_fee_type="basic_1", stock_drugs_count=1199)
        self.assertFalse(evaluate_regional_support(m_b1_fail).structural_system_qualified)
        
        # 基本料1: 1,200品目は適合
        m_b1_pass = PharmacyMetrics(dispensing_basic_fee_type="basic_1", stock_drugs_count=1200)
        self.assertTrue(evaluate_regional_support(m_b1_pass).structural_system_qualified)

        # 基本料2: 1,499品目は未達 (1200あっても基本料2では1500必要)
        m_b2_fail = PharmacyMetrics(dispensing_basic_fee_type="basic_2", stock_drugs_count=1499)
        self.assertFalse(evaluate_regional_support(m_b2_fail).structural_system_qualified)

        # 基本料2: 1,500品目は適合
        m_b2_pass = PharmacyMetrics(dispensing_basic_fee_type="basic_2", stock_drugs_count=1500)
        self.assertTrue(evaluate_regional_support(m_b2_pass).structural_system_qualified)

    def test_tc_structural_each_item_isolated_negative(self):
        """十分な体制の全項目（11項目）単独未達時の負例テスト"""
        # 1. 24時間体制なし
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(has_24h_system=False)).structural_system_qualified)
        # 2. 麻薬免許なし
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(has_narcotics_license=False)).structural_system_qualified)
        # 3. 無菌製剤処理なし
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(has_sterile_preparation_system=False)).structural_system_qualified)
        # 4. 医療DXなし
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(has_medical_dx_system=False)).structural_system_qualified)
        # 5. 感染症協定なし
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(has_infection_agreement=False)).structural_system_qualified)
        # 6. OTC 47薬効群（48未満）
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(otc_drug_categories_count=47)).structural_system_qualified)
        # 7. 個別相談カウンターなし
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(has_private_counseling_counter=False)).structural_system_qualified)
        # 8. セルフメディケーション機器 2種（3種未満）
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(self_medication_device_count=2)).structural_system_qualified)
        # 9. 医療材料供給体制なし
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(has_medical_materials_supply=False)).structural_system_qualified)
        # 10. 高度管理医療機器販売業許可なし
        self.assertFalse(evaluate_regional_support(PharmacyMetrics(has_medical_device_sales_license=False)).structural_system_qualified)

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
            stock_drugs_count=1500,
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
                stock_drugs_count=1500,
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

if __name__ == '__main__':
    unittest.main()




