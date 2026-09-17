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

    def test_addition_1_all_basic_fees_entry(self):
        """加算1（27点）は特別調剤基本料Bを除く全区分共通の医薬品安定供給エントリー加算"""
        # 1. 調剤基本料1 + 供給体制のみ -> 加算1 (27点)
        m_b1 = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=12000,
            generic_percentage=85.5,
            stock_drugs_count=800, # 1200未満
            self_medication_device_count=1,
            rec_4_guidance_1a_2a_count=0
        )
        res_b1 = evaluate_regional_support(m_b1)
        self.assertEqual(res_b1.current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertEqual(res_b1.tier_code, "tier_1")
        self.assertEqual(res_b1.points_earned, 27)
        self.assertTrue(res_b1.supply_system_qualified)
        self.assertFalse(res_b1.structural_system_qualified)

        # 2. 調剤基本料2 + 供給体制のみ -> 加算1 (27点)
        m_b2 = PharmacyMetrics(
            dispensing_basic_fee_type="basic_2",
            annual_prescriptions=12000,
            generic_percentage=86.0,
            stock_drugs_count=1000, # 1500未満
            self_medication_device_count=1
        )
        res_b2 = evaluate_regional_support(m_b2)
        self.assertEqual(res_b2.current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertEqual(res_b2.points_earned, 27)

        # 3. 特別調剤基本料A + 供給体制のみ -> 加算1 (100分の10 = 3点)
        m_spa = PharmacyMetrics(
            dispensing_basic_fee_type="special_a",
            annual_prescriptions=10000,
            generic_percentage=86.0,
            stock_drugs_count=800
        )
        res_spa = evaluate_regional_support(m_spa)
        self.assertEqual(res_spa.current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertEqual(res_spa.points_earned, 3)

        # 4. 特別調剤基本料B -> 算定不可 (0点)
        m_spb = PharmacyMetrics(
            dispensing_basic_fee_type="special_b",
            annual_prescriptions=10000,
            generic_percentage=90.0,
            stock_drugs_count=2000
        )
        res_spb = evaluate_regional_support(m_spb)
        self.assertEqual(res_spb.current_tier, "算定不可")
        self.assertEqual(res_spb.points_earned, 0)

    def test_addition_2_basic_1(self):
        """加算2（59点）: 基本料1 + 供給体制 + 体制（1200品目・在宅24回等）+ (4)を含む3項目以上"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=86.0,
            stock_drugs_count=1200,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=45, # (1) 充足
            rec_2_narcotics_count=0,
            rec_3_prevention_adjustment_count=22, # (3) 充足
            rec_4_guidance_1a_2a_count=25, # (4) 充足【必須】
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

    def test_addition_3_basic_1(self):
        """加算3（67点）: 基本料1 + 供給体制 + 体制 + 任意の実績7項目以上（(4)は単独必須ではない）"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1250,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=50, # (1) 充足
            rec_2_narcotics_count=2,      # (2) 充足
            rec_3_prevention_adjustment_count=25, # (3) 充足
            rec_4_guidance_1a_2a_count=0, # (4) 未達でも他の7項目あれば加算3達成
            rec_5_outpatient_support_1_count=3, # (5) 充足
            rec_6_home_visit_count=30,    # (6) 充足
            rec_7_info_provision_tr_count=40, # (7) 充足
            rec_8_pediatric_special_count=2,  # (8) 充足
            rec_9_multidisciplinary_conference_count=0
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算3")
        self.assertEqual(res.tier_code, "tier_3")
        self.assertEqual(res.points_earned, 67)

    def test_addition_4_basic_other(self):
        """加算4（37点）: 基本料1以外 + 供給体制 + 体制（1500品目・在宅24回等）+ (4)及び(6)を含む3項目以上"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_2",
            annual_prescriptions=10000,
            generic_percentage=87.0,
            stock_drugs_count=1500, # 基本料1以外基準(1500)
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=410, # (1) 充足
            rec_2_narcotics_count=0,
            rec_3_prevention_adjustment_count=0,
            rec_4_guidance_1a_2a_count=45, # (4) 充足【必須】
            rec_5_outpatient_support_1_count=0,
            rec_6_home_visit_count=25,     # (6) 充足【必須】
            rec_7_info_provision_tr_count=0,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算4")
        self.assertEqual(res.tier_code, "tier_4")
        self.assertEqual(res.points_earned, 37)

    def test_addition_5_basic_other(self):
        """加算5（59点）: 基本料1以外 + 供給体制 + 体制（1500品目）+ 上位実績7項目以上"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_3_a",
            annual_prescriptions=10000,
            generic_percentage=89.0,
            stock_drugs_count=1600,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=420, # (1) 充足
            rec_2_narcotics_count=12,     # (2) 充足
            rec_3_prevention_adjustment_count=45, # (3) 充足
            rec_4_guidance_1a_2a_count=50, # (4) 充足
            rec_5_outpatient_support_1_count=15, # (5) 充足
            rec_6_home_visit_count=30,    # (6) 充足
            rec_7_info_provision_tr_count=70, # (7) 充足
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算5")
        self.assertEqual(res.tier_code, "tier_5")
        self.assertEqual(res.points_earned, 59)

    def test_rx_scaling_factor_and_item9_per_pharmacy(self):
        """処方箋受付回数3万枚（係数3.0）の比例計算と、(9)多職種連携会議の薬局当たり固定検証"""
        m_30k = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=30000, # 係数 3.0倍
            rec_1_night_holiday_count=119, # 基準40*3=120 -> 119は未達
            rec_4_guidance_1a_2a_count=60, # 基準20*3=60 -> 60は達成
            rec_6_home_visit_count=72,     # 基準24*3=72 -> 72は達成
            rec_9_multidisciplinary_conference_count=1 # 基準1回（3倍にならない） -> 達成
        )
        res = evaluate_regional_support(m_30k)
        
        req1 = next(r for r in res.performance_requirements if r.id == "REQ-PRF-01")
        self.assertEqual(req1.target_value_text, "基準: 120 回 (上位: 1,200)")
        self.assertFalse(req1.is_satisfied)

        req4 = next(r for r in res.performance_requirements if r.id == "REQ-PRF-04")
        self.assertEqual(req4.target_value_text, "基準: 60 回 (上位: 120)")
        self.assertTrue(req4.is_satisfied)

        req9 = next(r for r in res.performance_requirements if r.id == "REQ-PRF-09")
        # (9)は3倍ではなく1回固定
        self.assertEqual(req9.target_value_text, "基準: 1 回 (上位: 5)")
        self.assertTrue(req9.is_satisfied)

    def test_pharmacy_home_care_24_structural_requirement(self):
        """加算2〜5共通の体制要件「薬局として年間24回以上の在宅実績」の未達テスト"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1300,
            has_pharmacy_home_care_24=False, # 体制要件未達
            self_medication_device_count=3,
            rec_4_guidance_1a_2a_count=30,
            rec_1_night_holiday_count=50,
            rec_3_prevention_adjustment_count=30
        )
        res = evaluate_regional_support(m)
        self.assertFalse(res.structural_system_qualified)
        # 体制未達のため加算2にはならず加算1へフォールバック
        self.assertEqual(res.current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertEqual(res.points_earned, 27)

    def test_stock_drugs_boundary_basic1_vs_non_basic1(self):
        """備蓄品目数の基本料別境界値テスト（基本料1: 1199 vs 1200 / 基本料2: 1499 vs 1500）"""
        # 基本料1: 1,199品目は未達
        m_b1_fail = PharmacyMetrics(dispensing_basic_fee_type="basic_1", stock_drugs_count=1199)
        self.assertFalse(evaluate_regional_support(m_b1_fail).structural_system_qualified)
        
        # 基本料1: 1,200品目は適合
        m_b1_pass = PharmacyMetrics(dispensing_basic_fee_type="basic_1", stock_drugs_count=1200)
        self.assertTrue(evaluate_regional_support(m_b1_pass).structural_system_qualified)

        # 基本料2: 1,499品目は未達
        m_b2_fail = PharmacyMetrics(dispensing_basic_fee_type="basic_2", stock_drugs_count=1499)
        self.assertFalse(evaluate_regional_support(m_b2_fail).structural_system_qualified)

        # 基本料2: 1,500品目は適合
        m_b2_pass = PharmacyMetrics(dispensing_basic_fee_type="basic_2", stock_drugs_count=1500)
        self.assertTrue(evaluate_regional_support(m_b2_pass).structural_system_qualified)

    def test_ge_boundary_and_special(self):
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

    def test_fallback_dag_basic1(self):
        """基本料1のフォールバック階層: 加算3 -> 加算2 -> 加算1 -> 算定不可"""
        # 加算3 (7項目達成)
        m_add3 = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1200,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=40,
            rec_2_narcotics_count=1,
            rec_3_prevention_adjustment_count=20,
            rec_4_guidance_1a_2a_count=20,
            rec_5_outpatient_support_1_count=1,
            rec_6_home_visit_count=24,
            rec_7_info_provision_tr_count=30
        )
        self.assertEqual(evaluate_regional_support(m_add3).current_tier, "地域支援・医薬品供給対応体制加算3")

        # 加算2 (3項目達成、(4)を含む)
        m_add2 = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1200,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=40,
            rec_2_narcotics_count=0,
            rec_3_prevention_adjustment_count=20,
            rec_4_guidance_1a_2a_count=20, # (4)含む計3項目
            rec_5_outpatient_support_1_count=0,
            rec_6_home_visit_count=0,
            rec_7_info_provision_tr_count=0,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        self.assertEqual(evaluate_regional_support(m_add2).current_tier, "地域支援・医薬品供給対応体制加算2")

        # 加算1 (実績2項目のみ / または体制未達)
        m_add1 = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1200,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=40,
            rec_2_narcotics_count=0,
            rec_3_prevention_adjustment_count=0,
            rec_4_guidance_1a_2a_count=20, # 2項目のみ
            rec_5_outpatient_support_1_count=0,
            rec_6_home_visit_count=0,
            rec_7_info_provision_tr_count=0,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        self.assertEqual(evaluate_regional_support(m_add1).current_tier, "地域支援・医薬品供給対応体制加算1")

        # 算定不可 (後発品未達)
        m_none = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            generic_percentage=80.0
        )
        self.assertEqual(evaluate_regional_support(m_none).current_tier, "算定不可")

    def test_fallback_dag_basic_other(self):
        """基本料1以外のフォールバック階層: 加算5 -> 加算4 -> 加算1 -> 算定不可"""
        # 加算5 (7項目達成)
        m_add5 = PharmacyMetrics(
            dispensing_basic_fee_type="basic_2",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1500,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=400,
            rec_2_narcotics_count=10,
            rec_3_prevention_adjustment_count=40,
            rec_4_guidance_1a_2a_count=40,
            rec_5_outpatient_support_1_count=12,
            rec_6_home_visit_count=24,
            rec_7_info_provision_tr_count=60
        )
        self.assertEqual(evaluate_regional_support(m_add5).current_tier, "地域支援・医薬品供給対応体制加算5")

        # 加算4 (3項目達成、(4)(6)を含む)
        m_add4 = PharmacyMetrics(
            dispensing_basic_fee_type="basic_2",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1500,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=400,
            rec_2_narcotics_count=0,
            rec_3_prevention_adjustment_count=0,
            rec_4_guidance_1a_2a_count=40, # (4)
            rec_5_outpatient_support_1_count=0,
            rec_6_home_visit_count=24,     # (6)
            rec_7_info_provision_tr_count=0,
            rec_8_pediatric_special_count=0,
            rec_9_multidisciplinary_conference_count=0
        )
        self.assertEqual(evaluate_regional_support(m_add4).current_tier, "地域支援・医薬品供給対応体制加算4")

        # 加算1 (実績不足または体制1500未達でも供給体制充足なら加算1にフォールバック)
        m_add1 = PharmacyMetrics(
            dispensing_basic_fee_type="basic_2",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1200 # 1500未満
        )
        self.assertEqual(evaluate_regional_support(m_add1).current_tier, "地域支援・医薬品供給対応体制加算1")
        self.assertEqual(evaluate_regional_support(m_add1).points_earned, 27)

    def test_special_basic_fee_a_points(self):
        """特別調剤基本料Aの所定点数100分の10（四捨五入）計算検証"""
        # 加算5相当 -> 59 * 0.1 = 5.9 -> 6点
        m_add5_spa = PharmacyMetrics(
            dispensing_basic_fee_type="special_a",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1500,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=400,
            rec_2_narcotics_count=10,
            rec_3_prevention_adjustment_count=40,
            rec_4_guidance_1a_2a_count=40,
            rec_5_outpatient_support_1_count=12,
            rec_6_home_visit_count=24,
            rec_7_info_provision_tr_count=60
        )
        res_add5 = evaluate_regional_support(m_add5_spa)
        self.assertEqual(res_add5.current_tier, "地域支援・医薬品供給対応体制加算5")
        self.assertEqual(res_add5.points_earned, 6)

        # 加算4相当 -> 37 * 0.1 = 3.7 -> 4点
        m_add4_spa = PharmacyMetrics(
            dispensing_basic_fee_type="special_a",
            annual_prescriptions=10000,
            generic_percentage=88.0,
            stock_drugs_count=1500,
            has_pharmacy_home_care_24=True,
            self_medication_device_count=3,
            rec_1_night_holiday_count=400,
            rec_4_guidance_1a_2a_count=40,
            rec_6_home_visit_count=24
        )
        res_add4 = evaluate_regional_support(m_add4_spa)
        self.assertEqual(res_add4.current_tier, "地域支援・医薬品供給対応体制加算4")
        self.assertEqual(res_add4.points_earned, 4)

    def test_basic_fee_deduction_note4(self):
        """注4減算: 未妥結または基本的業務10回未満で所定点数の50/100算定（基本料1: 47 -> 24点）"""
        # 1. 基本的業務9回（基準10回未満）
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            basic_services_count=9
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.basic_fee_base_points, 47)
        self.assertEqual(res.basic_fee_final_points, 24) # round(47 * 0.5) = 24
        self.assertTrue(any("注4減算" in d for d in res.basic_fee_deductions_applied))

        # 2. 未妥結・未報告フラグ True
        m2 = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            basic_services_count=20,
            has_unsettled_or_unreported_discount=True
        )
        res2 = evaluate_regional_support(m2)
        self.assertEqual(res2.basic_fee_final_points, 24)

    def test_basic_fee_deduction_note3(self):
        """注3減算: 複数医療機関処方箋の同時受付2回目以降で80/100算定（基本料1: 47 -> 38点）"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            is_multiple_reception_second=True
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.basic_fee_final_points, 38) # round(47 * 0.8) = 37.6 -> 38
        self.assertTrue(any("注3減算" in d for d in res.basic_fee_deductions_applied))

    def test_basic_fee_deduction_note15(self):
        """注15減算: 新設立地依存（門前薬局減算）▲15点（基本料1: 47 -> 32点）"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            is_new_location_dependent_pharmacy=True
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.basic_fee_final_points, 32) # 47 - 15 = 32
        self.assertTrue(any("注15減算" in d for d in res.basic_fee_deductions_applied))

    def test_basic_fee_deduction_note8(self):
        """注8減算: 後発品割合50%以下かつ月600回超で▲5点（基本料1: 47 -> 42点）"""
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_1",
            generic_percentage=48.0,
            monthly_prescriptions=1200
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.basic_fee_final_points, 42) # 47 - 5 = 42
        self.assertTrue(any("注8減算" in d for d in res.basic_fee_deductions_applied))
        # かつGE50%以下は地域支援加算も算定不可
        self.assertEqual(res.current_tier, "算定不可")
        self.assertEqual(res.points_earned, 0)

    def test_basic_fee_minimum_guarantee(self):
        """下限3点保障テスト: 重複減算により3点未満になる場合でも最低3点を算定"""
        # 調剤基本料3ロ (20点) + 注4 (10点) + 注15 (▲15点) = -5点 -> 最低3点
        m = PharmacyMetrics(
            dispensing_basic_fee_type="basic_3_b", # 20点
            basic_services_count=5,               # 注4該当 -> 10点
            is_new_location_dependent_pharmacy=True # 注15該当 -> 10 - 15 = -5点
        )
        res = evaluate_regional_support(m)
        self.assertEqual(res.basic_fee_base_points, 20)
        self.assertEqual(res.basic_fee_final_points, 3) # 最低3点保障
        self.assertEqual(res.total_basic_and_regional_points, 3 + res.points_earned)

if __name__ == '__main__':
    unittest.main()






