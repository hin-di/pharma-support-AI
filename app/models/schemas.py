from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# 正式告示点数定数
ADD01_POINTS = 27
ADD02_POINTS = 59
ADD03_POINTS = 67
ADD04_POINTS = 37
ADD05_POINTS = 59

class RequirementStatus(BaseModel):
    id: str
    name: str
    category: str
    requirement_type: str
    current_value_text: str
    target_value_text: str
    is_satisfied: bool
    progress_percentage: float
    shortage_text: str
    official_ref: str
    advice: Optional[str] = None

class RegionalEvaluationResult(BaseModel):
    current_tier: str
    tier_code: str
    points_earned: int
    supply_system_qualified: bool
    structural_system_qualified: bool
    performance_system_qualified: bool
    summary_message: str
    
    supply_requirements: List[RequirementStatus] = Field(default_factory=list)
    structural_requirements: List[RequirementStatus] = Field(default_factory=list)
    performance_requirements: List[RequirementStatus] = Field(default_factory=list)
    
    supply_actions: List[str] = Field(default_factory=list)
    structural_actions: List[str] = Field(default_factory=list)
    performance_actions: List[str] = Field(default_factory=list)
    audit_trail: List[str] = Field(default_factory=list)

class PharmacyMetrics(BaseModel):
    pharmacy_name: str = "ひまわり調剤薬局"
    dispensing_basic_fee_type: str = "basic_1"  # "basic_1", "basic_2", "basic_3_a", "basic_3_b", "special_a", "special_b"
    annual_prescriptions: int = 14400          # 直近1年間の総処方箋受付回数（1万枚補正用）
    monthly_prescriptions: int = 1200
    
    # 評価期間定義
    generic_ratio_period: str = "直近3か月間"
    performance_period: str = "直近1年間（前年5月1日〜当年4月30日）"

    # 1. 医薬品供給対応体制（様式87の3の1: 共通8項目）
    generic_percentage: float = 86.4           # (8) 後発品割合 (規格単位数量ベース >= 85.0%)
    generic_percentage_special_applied: Optional[float] = None
    temporary_exclusion_enabled: bool = False  # 令和8年9月30日までの臨時除外特例
    has_planned_procurement: bool = True       # (1) 計画的調達・在庫管理
    has_drug_distribution_record: bool = True  # (2) 薬局間分譲実績
    has_shortage_response_protocol: bool = True # (3) 供給不足時対応手順
    has_single_item_negotiation: bool = True   # (4) 単品単価交渉
    has_rush_delivery_prevention: bool = True  # (5) 頻回配送抑制
    has_return_suppression: bool = True        # (6) 返品抑制
    has_generic_promotion_notice: bool = True  # (7) 後発品積極調剤の掲示
    
    # 2. 地域医療への貢献に係る十分な体制（加算2: 1200品目以上 / 加算4: 1500品目以上）
    stock_drugs_count: int = 1350              # 備蓄品目数 (基本料1: >=1200品目, 基本料1以外: >=1500品目)
    has_24h_system: bool = True                # (2) 24時間調剤・在宅対応体制
    has_narcotics_license: bool = True         # (3) 麻薬小売業免許及び管理保管設備
    has_sterile_preparation_system: bool = True # (4) 無菌製剤処理体制（自店又は共同利用）
    has_medical_dx_system: bool = True         # (5) 医療DX推進体制（電子処方箋・オン資等）
    has_infection_agreement: bool = True       # (6) 感染症法第38条第二種協定指定等の体制
    otc_drug_categories_count: int = 50        # (7) OTC備蓄販売 (>=48薬効群)
    has_private_counseling_counter: bool = True # (8) 個別服薬指導相談カウンター
    self_medication_device_count: int = 3      # (9) セルフメディケーション機器設置数 (8種中>=3種)
    has_medical_materials_supply: bool = True  # (10) 医療材料・衛生材料の供給体制
    has_medical_device_sales_license: bool = True # (10) 高度管理医療機器等販売業許可
    has_medical_equipment_sales_license: Optional[bool] = None # 後方互換用エイリアス
    
    # 3. 地域医療への貢献に係る実績（様式87の3の2: 全9項目 (1)〜(9) 実績回数）
    rec_1_night_holiday_count: int = 60        # (1) 時間外・夜間休日等加算等 (基準: 40 / 400 /万枚)
    rec_2_narcotics_count: int = 4             # (2) 麻薬の調剤 (基準: 1 / 10 /万枚)
    rec_3_prevention_adjustment_count: int = 35 # (3) 残薬調整・有害事象防止 (基準: 20 / 40 /万枚)
    rec_4_guidance_1a_2a_count: int = 32       # (4) 服薬管理指導料1イ・2イ (基準: 20 / 40 /万枚)【加算2・4必須】
    rec_5_outpatient_support_1_count: int = 3  # (5) 外来服薬支援料1 (基準: 1 / 12 /万枚)
    rec_6_home_visit_count: int = 36           # (6) 訪問薬剤管理指導料等 (基準: 24 / 24 /万枚)【加算4必須】
    rec_7_info_provision_tr_count: int = 48    # (7) 服薬情報等提供料等TR (基準: 30 / 60 /万枚)
    rec_8_pediatric_special_count: int = 2     # (8) 小児特定加算等 (基準: 1 / 1 /万枚)
    rec_9_multidisciplinary_conference_count: int = 2 # (9) 多職種連携会議出席 (基準: 1 / 5 /万枚)

# 個別患者加算モデル
class PatientCondition(BaseModel):
    patient_name: str = "来局患者様"
    age: int = 68
    has_medicine_notebook: bool = True
    family_pharmacist_agreed: bool = False
    is_home_care: bool = False
    has_narcotics: bool = False
    has_high_risk_drug: bool = False
    has_anticancer_drug: bool = False
    is_new_drug_or_dosage_changed: bool = False
    has_leftover_drugs: bool = False
    has_spontaneous_doctor_feedback: bool = False

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
