from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RequirementStatus(BaseModel):
    id: str
    name: str
    category: str  # "供給体制要件(様式87-3-1)", "十分な体制要件", "実績要件(様式87-3-2)"
    requirement_type: str  # "supply_87_1", "structural", "performance_87_2"
    current_value_text: str
    target_value_text: str
    is_satisfied: bool
    progress_percentage: float
    shortage_text: str
    advice: str
    official_ref: str  # 例: "様式87の3の1 第(8)項"

class RegionalEvaluationResult(BaseModel):
    current_tier: str  # "地域支援・医薬品供給対応体制加算1〜5" または "算定不可"
    tier_code: str     # "tier_1", "tier_2", "tier_3", "tier_4", "tier_5", "none"
    points_earned: int # 39, 47, 17, 39, 60, 0
    supply_system_qualified: bool  # 様式87の3の1 共通8項目
    structural_system_qualified: bool # 十分な体制
    performance_system_qualified: bool # 実績要件
    summary_message: str
    
    # 3大要件リスト
    supply_requirements: List[RequirementStatus] = Field(default_factory=list)
    structural_requirements: List[RequirementStatus] = Field(default_factory=list)
    performance_requirements: List[RequirementStatus] = Field(default_factory=list)
    
    # アクション指針
    supply_actions: List[str] = Field(default_factory=list)
    structural_actions: List[str] = Field(default_factory=list)
    performance_actions: List[str] = Field(default_factory=list)
    
    # 監査トレーサビリティ
    audit_trail: List[str] = Field(default_factory=list)

class PharmacyMetrics(BaseModel):
    pharmacy_name: str = "ひまわり調剤薬局"
    dispensing_basic_fee_type: str = "basic_1"  # "basic_1" または "other" (2, 3イ, 3ロ等)
    monthly_prescriptions: int = 1200
    
    # 1. 医薬品供給対応体制（様式87の3の1: 共通8項目）
    generic_percentage: float = 86.4  # (8) 後発品割合 (>= 85.0%)
    generic_percentage_special_applied: Optional[float] = None
    has_planned_procurement: bool = True       # (1) 計画的調達・在庫管理
    has_drug_distribution_record: bool = True  # (2) 薬局間分譲実績
    has_shortage_response_protocol: bool = True # (3) 供給不足時対応手順
    has_single_item_negotiation: bool = True   # (4) 単品単価交渉
    has_rush_delivery_prevention: bool = True  # (5) 頻回配送抑制
    has_return_suppression: bool = True        # (6) 返品抑制
    has_generic_promotion_notice: bool = True  # (7) 後発品積極調剤の掲示
    
    # 2. 地域医療への貢献に係る十分な体制
    stock_drugs_count: int = 1350              # 備蓄品目数 (>=1200品目)
    has_24h_system: bool = True                # 24時間調剤・在宅体制
    has_narcotics_license: bool = True         # 麻薬小売業免許
    has_sterile_preparation_system: bool = True # 無菌調剤体制
    has_medical_dx_system: bool = True         # 医療DX推進体制（電子処方箋等）
    has_infection_agreement: bool = True       # 感染症指定（第二種協定等）
    otc_drug_categories_count: int = 50        # OTC備蓄 (>=48薬効群)
    has_private_counseling_counter: bool = True # 個別相談カウンター
    self_medication_device_count: int = 3      # セルフメディケーション機器設置数 (>=3種)
    has_medical_equipment_sales_license: bool = True # 医療材料・高度管理医療機器
    
    # 3. 地域医療への貢献に係る実績（様式87の3の2: 全9項目 (1)〜(9)）
    rec_1_night_holiday_count: int = 45        # (1) 夜間休日等調剤 (加算2:40, 加算4:400)
    rec_2_narcotics_count: int = 3             # (2) 麻薬調剤 (加算2:1, 加算4:10)
    rec_3_prevention_adjustment_count: int = 25 # (3) 重複防止・残薬調整 (加算2:20, 加算4:40)
    rec_4_guidance_1a_2a_count: int = 22       # (4) 服薬指導料1イ・2イ (加算2:20【必須】, 加算4:40【必須】)
    rec_5_outpatient_support_1_count: int = 2  # (5) 外来服薬支援料1 (加算2:1, 加算4:12)
    rec_6_home_visit_count: int = 26           # (6) 在宅訪問指導 (加算2:24, 加算4:24【必須】)
    rec_7_info_provision_tr_count: int = 35    # (7) 服薬情報等提供料TR (加算2:30, 加算4:60)
    rec_8_pediatric_special_count: int = 2     # (8) 小児特定加算等 (加算2:1, 加算4:1)
    rec_9_multidisciplinary_conference_count: int = 2 # (9) 多職種連携会議出席 (加算2:1, 加算4:5)

    # 4. 届出ライフサイクル・年度管理
    notification_status: str = "active_billed" # "not_submitted", "submitted", "active_billed"
    assessment_period: str = "2025年5月1日〜2026年4月30日"
    effective_period: str = "2026年6月1日〜2027年5月31日"

# 個別患者加算モデル（維持）
class PatientCondition(BaseModel):
    patient_name: str = "来局患者様"
    age: int = 68
    has_medicine_notebook: bool = True
    family_pharmacist_agreed: bool = False
    is_home_care: bool = False
    has_narcotics: bool = False
    has_high_risk_drug: bool = False
    has_anticancer_drug: bool = False
    has_inhalation_drug: bool = False
    is_first_inhalation_or_device_change: bool = False
    has_leftover_drugs: bool = False
    has_prescription_query_changed: bool = False
    is_new_drug_or_dosage_changed: bool = False
    has_doctor_feedback_requested: bool = False
    has_spontaneous_doctor_feedback: bool = False
    has_hospital_discharge_cooperation: bool = False
    is_pediatric_special: bool = False

class PatientBillingItem(BaseModel):
    code: str
    name: str
    points: int
    category: str
    description: str
    chart_notes: str
    contributes_to_regional_support: Optional[str] = None

class PatientEvaluationResult(BaseModel):
    total_points: int
    recommended_items: List[PatientBillingItem]
    advice_comments: List[str]
    regional_contributions: List[str]
