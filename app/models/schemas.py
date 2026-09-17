from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# 正式告示点数定数（地域支援・医薬品供給対応体制加算）
ADD01_POINTS = 27
ADD02_POINTS = 59
ADD03_POINTS = 67
ADD04_POINTS = 37
ADD05_POINTS = 59

# 正式告示点数定数（調剤基本料マスター）
BASIC_FEE_MASTER: Dict[str, Dict[str, Any]] = {
    "basic_1": {"name": "調剤基本料1", "points": 47, "desc": "調剤基本料２・３、特別調剤基本料以外"},
    "basic_2": {"name": "調剤基本料2", "points": 30, "desc": "処方箋受付回数月4,000回超かつ集中率70%超等"},
    "basic_3_a": {"name": "調剤基本料3イ", "points": 25, "desc": "同一グループ月3.5万回超〜40万回 かつ 集中率85%超"},
    "basic_3_b": {"name": "調剤基本料3ロ", "points": 20, "desc": "同一グループ月40万回超 かつ 集中率85%超"},
    "basic_3_c": {"name": "調剤基本料3ハ", "points": 37, "desc": "同一グループ月40万回超 かつ 集中率85%以下"},
    "special_a": {"name": "特別調剤基本料A", "points": 5, "desc": "いわゆる同一敷地内薬局（所定点数100分の10算定）"},
    "special_b": {"name": "特別調剤基本料B", "points": 3, "desc": "調剤基本料の届出がない保険薬局（全加算算定不可）"}
}

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
    basic_fee_name: str = "調剤基本料1"
    basic_fee_base_points: int = 47
    basic_fee_final_points: int = 47
    basic_fee_deductions_applied: List[str] = Field(default_factory=list)
    total_basic_and_regional_points: int = 47
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
    dispensing_basic_fee_type: str = "basic_1"  # "basic_1", "basic_2", "basic_3_a", "basic_3_b", "basic_3_c", "special_a", "special_b"
    evaluation_mode: str = "continuous"         # "continuous" (継続判定・定例報告), "new" (新規届出)
    annual_prescriptions: int = 14400          # 直近1年間の総処方箋受付回数（1万枚補正用実数）
    monthly_prescriptions: int = 1200          # 月平均処方箋枚数

    # 0. 調剤基本料 減算判定項目（注3, 注4, 注8, 注15）
    has_unsettled_or_unreported_discount: bool = False  # (注4-ア/イ) 妥結率50%以下または報告未提出 (50/100算定)
    basic_services_count: int = 25                     # (注4-ウ) 直近1年間のかかりつけ基本的業務算定回数 (基準:10回以上、特別A/Bは100回以上)
    is_new_location_dependent_pharmacy: bool = False    # (注15) 門前薬局等立地依存減算 (R8.6.1以降新規開設かつ集中率85%超等: ▲15点)
    is_multiple_reception_second: bool = False          # (注3) 複数保険医療機関処方箋同時受付（2回目以降受付: 80/100算定)
    
    # 評価期間定義
    generic_ratio_period: str = "直近3か月間"
    performance_period: str = "直近1年間（前年5月1日〜当年4月30日）"

    # 1. 医薬品供給対応体制（様式87の3の1: 加算1〜5全区分共通）
    generic_percentage: float = 86.4           # (8) 後発品割合 (規格単位数量ベース >= 85.0%)
    generic_percentage_special_applied: Optional[float] = None
    temporary_exclusion_enabled: bool = False  # 令和8年9月30日までの臨時除外特例
    has_planned_procurement: bool = True       # (1) 計画的調達・在庫管理
    has_drug_distribution_record: bool = True  # (2) 薬局間分譲実績 (別紙様式4-1、2年保存)
    has_shortage_response_protocol: bool = True # (3) 供給不足時対応手順 (別紙様式4-2等)
    has_single_item_negotiation: bool = True   # (4) 原則単品単価交渉
    has_rush_delivery_prevention: bool = True  # (5) 頻回配送抑制
    has_return_suppression: bool = True        # (6) 返品抑制
    has_generic_promotion_notice: bool = True  # (7) 後発品積極調剤の掲示
    has_critical_drugs_stock: bool = True      # (8) 重要供給確保医薬品（内用・外用）の1ヶ月程度備蓄
    has_regional_drug_collaboration: bool = True # (9) 地域医療機関・薬局との品目情報共有連携
    
    # 2. 地域医療への貢献に係る十分な体制（加算2〜5共通の体制要件）
    stock_drugs_count: int = 1350              # 備蓄品目数 (基本料1: >=1200品目, 基本料1以外: >=1500品目)
    has_pharmacy_home_care_24: bool = True     # 薬局としての年間在宅実績 24回以上 (体制要件)
    has_24h_system: bool = True                # (2) 24時間調剤・在宅対応体制 (週45時間以上開局等)
    has_narcotics_license: bool = True         # (3) 麻薬小売業免許及び管理保管設備
    has_sterile_preparation_system: bool = True # (4) 無菌製剤処理体制（自店又は共同利用）
    has_medical_dx_system: bool = True         # (5) 医療DX推進体制（電子処方箋・オン資等）
    has_infection_agreement: bool = True       # (6) 感染症法第38条第二種指定医療機関協定等の体制
    otc_drug_categories_count: int = 50        # (7) OTC備蓄販売 (48薬効群を参考に多種取扱 >=48)
    has_private_counseling_counter: bool = True # (8) 個別服薬指導相談カウンター (着座対応等)
    self_medication_device_count: int = 3      # (9) セルフメディケーション機器設置数 (7〜8種中>=3種)
    has_medical_materials_supply: bool = True  # (10) 医療材料・衛生材料の供給体制
    has_medical_device_sales_license: bool = True # (10) 高度管理医療機器等販売業・貸与業許可
    has_medical_equipment_sales_license: Optional[bool] = None # 後方互換用エイリアス
    has_clean_environment: bool = True         # 敷地内禁煙・たばこ販売禁止・未承認研究用試薬非提供
    has_managing_pharmacist_req: bool = True   # 管理薬剤師要件 (勤務5年・週31h・在籍1年)
    
    # 3. 地域医療への貢献に係る実績（様式87の3の2: 全9項目 (1)〜(9) 実績回数）
    rec_1_night_holiday_count: int = 60        # (1) 時間外・夜間休日等加算等 (基準: 40 / 400 /万枚)
    rec_2_narcotics_count: int = 4             # (2) 麻薬の調剤 (基準: 1 / 10 /万枚)
    rec_3_prevention_adjustment_count: int = 35 # (3) 調剤時残薬調整加算及び薬学的有害事象等防止加算 (基準: 20 / 40 /万枚)
    rec_4_guidance_1a_2a_count: int = 32       # (4) 服薬管理指導料1イ・2イ (基準: 20 / 40 /万枚)【加算2・4で必須】
    rec_5_outpatient_support_1_count: int = 3  # (5) 外来服薬支援料1 (基準: 1 / 12 /万枚)
    rec_6_home_visit_count: int = 36           # (6) 単一建物診療患者1人の在宅薬剤管理 (基準: 24 / 24 /万枚)【加算4で必須】
    rec_7_info_provision_tr_count: int = 48    # (7) 服薬情報等提供料等の算定実績 (基準: 30 / 60 /万枚)
    rec_8_pediatric_special_count: int = 2     # (8) 小児特定加算等 (基準: 1 / 1 /万枚)
    rec_9_multidisciplinary_conference_count: int = 2 # (9) 地域多職種連携会議出席 (基準: 1 / 5 【薬局当たり年間】)

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

