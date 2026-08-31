from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PharmacyMetrics(BaseModel):
    pharmacy_name: str = 'ひまわり調剤薬局'
    dispensing_basic_fee_type: str = 'basic_1'  # 'basic_1' or 'other'
    monthly_prescriptions: int = Field(1200, description='月平均処方箋受付回数')
    concentration_rate: float = Field(78.5, description='特定の医療機関への処方箋集中率(%)')
    
    # 年間実績値（直近12ヶ月の実績要件）
    narcotics_count: int = Field(4, description='麻薬調剤実績（年間回数）')
    home_visit_count: int = Field(22, description='在宅患者訪問薬剤管理指導実績（年間回数）')
    family_pharmacist_count: int = Field(38, description='かかりつけ薬剤師指導料実績（年間回数）')
    info_provision_count: int = Field(15, description='服薬情報等提供料実績（年間回数）')
    preavoid_count: int = Field(2, description='プレアボイド事例報告実績（年間件数）')
    generic_percentage: float = Field(84.2, description='後発医薬品使用割合(%)')
    night_holiday_count: int = Field(110, description='夜間・休日等の対応実績（年間回数）')
    
    # 薬局体制要件（設備・協定・システム等）
    stock_drugs_count: int = Field(1280, description='備蓄医薬品品目数')
    has_24h_system: bool = Field(True, description='24時間調剤・在宅対応体制')
    has_infection_system: bool = Field(True, description='新興感染症対応・連携体制')
    has_online_qualification: bool = Field(True, description='オンライン資格確認体制')
    has_electronic_prescription: bool = Field(True, description='電子処方箋対応体制')
    has_otc_sales: bool = Field(True, description='要指導医薬品・一般用医薬品の備蓄販売')

class RequirementStatus(BaseModel):
    name: str
    category: str
    requirement_type: str  # 'performance' (実績要件) or 'structural' (体制要件)
    current_value_text: str
    target_value_text: str
    unit: str
    is_satisfied: bool
    progress_percentage: float
    shortage_text: Optional[str] = None
    advice: str

class RegionalEvaluationResult(BaseModel):
    current_tier: str
    is_basic_fee_1: bool
    supply_system_addition_qualified: bool
    infection_enhancement_qualified: bool
    points_earned: int
    tier_statuses: Dict[str, bool]
    performance_requirements: List[RequirementStatus]  # 実績要件
    structural_requirements: List[RequirementStatus]   # 体制要件
    summary_message: str
    performance_actions: List[str]                     # 実績面でのアクション
    structural_actions: List[str]                      # 体制面でのアクション

class PatientCondition(BaseModel):
    patient_name: Optional[str] = 'サンプル患者様'
    age: int = Field(68, description='年齢')
    has_medicine_notebook: bool = Field(True, description='お薬手帳持参')
    family_pharmacist_agreed: bool = Field(False, description='かかりつけ薬剤師同意書あり')
    is_home_care: bool = Field(False, description='在宅療養患者')
    has_narcotics: bool = Field(False, description='麻薬処方あり')
    has_high_risk_drug: bool = Field(True, description='特定薬剤(ハイリスク薬)処方あり')
    has_anticancer_drug: bool = Field(False, description='抗悪性腫瘍剤処方あり')
    has_inhalation_drug: bool = Field(False, description='吸入薬処方あり')
    is_first_inhalation_or_device_change: bool = Field(False, description='吸入器の手技指導・確認実施')
    has_leftover_drugs: bool = Field(False, description='残薬あり・整理または日数調整実施')
    has_prescription_query_changed: bool = Field(False, description='疑義照会により処方変更')
    is_new_drug_or_dosage_changed: bool = Field(True, description='新規処方・用法変更に伴う服用後フォローアップ実施')
    has_doctor_feedback_requested: bool = Field(False, description='医師からの求めによる情報提供')
    has_spontaneous_doctor_feedback: bool = Field(False, description='薬剤師主導のトレーシングレポート提出')
    has_hospital_discharge_cooperation: bool = Field(False, description='退院時共同指導・カンファレンス参加')
    is_pediatric_special: bool = Field(False, description='小児特定加算対象（医療的ケア児等）')

class BillingItem(BaseModel):
    code: str
    name: str
    points: int
    category: str
    description: str
    requirements_summary: str
    chart_notes: str
    contributes_to_regional_support: Optional[str] = None

class PatientBillingResult(BaseModel):
    recommended_items: List[BillingItem]
    total_points: int
    regional_contributions: List[str]
    advice_comments: List[str]
