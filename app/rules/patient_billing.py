from app.models.schemas import PatientCondition, PatientBillingItem, PatientEvaluationResult
from typing import List

def evaluate_patient_billing(condition: PatientCondition) -> PatientEvaluationResult:
    """
    個別患者の処方・来局条件に応じた算定可能加算ナビゲーション
    """
    items: List[PatientBillingItem] = []
    advice: List[str] = []
    regional_contributions: List[str] = []

    # 1. 基本の服薬管理指導料
    if condition.has_medicine_notebook:
        items.append(PatientBillingItem(
            code="140049910",
            name="服薬管理指導料1の「イ」（手帳持参・6か月以内）",
            points=45,
            category="服薬管理指導料",
            description="手帳を持参し、原則6か月以内に再来局された患者様への指導。",
            chart_notes="お薬手帳の提示を確認。直近の服薬状況、重複投薬・相互作用なしを確認し指導。",
            contributes_to_regional_support="【様式87-3-2 実績(4)】加算2・4の必須要件に貢献"
        ))
        regional_contributions.append("実績(4)指導料1イ/2イ")
    else:
        items.append(PatientBillingItem(
            code="140050010",
            name="服薬管理指導料1の「ロ」（手帳なし / 6か月超）",
            points=59,
            category="服薬管理指導料",
            description="手帳持参なし、または前回から6か月超経過しての来局。",
            chart_notes="手帳不持参の理由を確認。過去の服薬履歴及び体調変化を聴取し薬歴に記録。"
        ))

    # 2. 麻薬管理指導加算
    if condition.has_narcotics:
        items.append(PatientBillingItem(
            code="140008770",
            name="麻薬管理指導加算",
            points=100,
            category="薬学的管理加算",
            description="医療用麻薬が処方されている患者への疼痛管理・副作用指導。",
            chart_notes="疼痛緩和状態（NRSスコア）、レスキュー服用の有無、便秘・嘔気の副作用状況を確認。",
            contributes_to_regional_support="【様式87-3-2 実績(2)】麻薬調剤実績に貢献"
        ))
        regional_contributions.append("実績(2)麻薬調剤")

    # 3. 特定薬剤管理指導加算（ハイリスク薬）
    if condition.has_high_risk_drug:
        items.append(PatientBillingItem(
            code="140058770",
            name="特定薬剤管理指導加算1（ハイリスク薬）",
            points=10,
            category="薬学的管理加算",
            description="抗血栓薬、不整脈薬、抗てんかん薬、免疫抑制剤等の重点的指導。",
            chart_notes="ハイリスク薬の服用状況、自覚症状（出血傾向等）、最新の検査値（INR、eGFR等）を確認し指導。"
        ))

    # 4. 残薬調整・重複防止
    if condition.has_leftover_drugs:
        items.append(PatientBillingItem(
            code="140040670",
            name="重複投薬・相互作用等防止加算（残薬調整）",
            points=30,
            category="薬学的管理加算",
            description="残薬確認に伴い処方医へ疑義照会を行い、日数短縮等を実施。",
            chart_notes="残薬数（○日分）を確認。処方医へ疑義照会を行い処方日数○日へ短縮変更合意。",
            contributes_to_regional_support="【様式87-3-2 実績(3)】重複防止・残薬調整実績に貢献"
        ))
        regional_contributions.append("実績(3)残薬調整")

    # 5. 服薬情報等提供料（TR）
    if condition.has_spontaneous_doctor_feedback:
        items.append(PatientBillingItem(
            code="140058910",
            name="服薬情報等提供料2（トレーシングレポート提案）",
            points=20,
            category="情報提供料",
            description="患者の服薬状況や提案事項を処方医へ文書で情報提供。",
            chart_notes="服薬状況及び副作用疑いを主治医へ文書（TR）にて情報提供・報告。",
            contributes_to_regional_support="【様式87-3-2 実績(7)】服薬情報等提供料実績に貢献"
        ))
        regional_contributions.append("実績(7)服薬情報TR")

    total_pts = sum(i.points for i in items)
    advice.append(f"現在、合計 +{total_pts} 点 の算定が可能です。")
    if regional_contributions:
        advice.append(f"本算定により、施設基準の地域医療貢献実績（{', '.join(regional_contributions)}）に寄与します。")

    return PatientEvaluationResult(
        total_points=total_pts,
        recommended_items=items,
        advice_comments=advice,
        regional_contributions=regional_contributions
    )
