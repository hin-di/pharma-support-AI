from app.models.schemas import PatientCondition, BillingItem, PatientBillingResult

def evaluate_patient_billing(c: PatientCondition) -> PatientBillingResult:
    items = []
    regional_contributions = []
    advice = []
    
    # 1. かかりつけ薬剤師指導料 / 包括管理料
    if c.family_pharmacist_agreed:
        items.append(BillingItem(
            code='FAM_01',
            name='かかりつけ薬剤師指導料',
            points=76,
            category='かかりつけ指導',
            description='担当薬剤師による一元的な服薬管理と24時間相談対応',
            requirements_summary='同意書締結済・専任薬剤師による指導・お薬手帳への記載・24時間連絡先交付',
            chart_notes='患者の他科受診状況、一般用医薬品等の併用確認、次回予定等の記録を記載すること。',
            contributes_to_regional_support='かかりつけ薬剤師指導料実績（年間目標に+1カウント）'
        ))
        regional_contributions.append('かかりつけ薬剤師指導料実績 (+1)')
        
    # 2. 麻薬管理指導加算
    if c.has_narcotics:
        items.append(BillingItem(
            code='NARC_01',
            name='麻薬管理指導加算',
            points=100,
            category='薬剤管理指導',
            description='医療用麻薬の適正使用・保管管理・副作用確認',
            requirements_summary='麻薬の服薬状況、保管管理状況、疼痛緩和状況、便秘等の副作用有無を確認',
            chart_notes='残薬数、痛みのコントロール状態（NRSスコア等）、下剤併用・排便状況、保管場所の確認記録が必須。',
            contributes_to_regional_support='麻薬調剤実績（地域支援加算の必須要件に+1カウント）'
        ))
        regional_contributions.append('麻薬調剤実績 (+1 ★重要要件)')
        
    # 3. 特定薬剤管理指導加算1 (ハイリスク薬)
    if c.has_high_risk_drug and not c.has_anticancer_drug:
        items.append(BillingItem(
            code='HIGH_01',
            name='特定薬剤管理指導加算1（ハイリスク薬）',
            points=10,
            category='薬剤管理指導',
            description='特に安全管理が必要な医薬品（抗不整脈、抗てんかん、抗凝固、免疫抑制等）の指導',
            requirements_summary='対象薬剤の薬学的管理・副作用の初期症状等の確認と説明',
            chart_notes='血液検査値の確認状況、併用注意薬のチェック、特有の副作用（出血傾向、ふらつき等）の確認内容を記録。',
            contributes_to_regional_support=None
        ))
        
    # 4. 特定薬剤管理指導加算2 (抗悪性腫瘍剤)
    if c.has_anticancer_drug:
        items.append(BillingItem(
            code='CANCER_01',
            name='特定薬剤管理指導加算2（抗悪性腫瘍剤）',
            points=100,
            category='薬剤管理指導',
            description='経口抗がん剤のレジメン・服薬計画・副作用（骨髄抑制、口内炎、手足症候群等）モニタリング',
            requirements_summary='レジメン把握、服薬休薬スケジュールの確認、副作用発現状況の評価と医療機関連携',
            chart_notes='休薬期間の遵守状況、Grade判定による副作用評価、支持療法の奏効状況を詳細に記録。',
            contributes_to_regional_support='トレーシングレポート提出により服薬情報等提供料にも連動可能'
        ))
        
    # 5. 吸入薬指導加算
    if c.has_inhalation_drug and c.is_first_inhalation_or_device_change:
        items.append(BillingItem(
            code='INH_01',
            name='吸入薬指導加算',
            points=30,
            category='手技・手技指導',
            description='吸入薬のデバイス特性に応じた適正手技の実地指導・確認（3月に1回算定）',
            requirements_summary='練習用吸入器（デモ機）を用いた手技確認、吸入力・息止め等の手技評価と記録',
            chart_notes='指導したデバイス名、吸気流速や残薬確認、吸入手技の改善点、うがいの徹底を記録。',
            contributes_to_regional_support=None
        ))
        
    # 6. 服用後薬剤管理指導加算 (新薬・用法変更等のフォローアップ)
    if c.is_new_drug_or_dosage_changed:
        items.append(BillingItem(
            code='FOLLOW_01',
            name='服用後薬剤管理指導加算',
            points=60,
            category='フォローアップ',
            description='新規処方または用法用量変更後の電話やアプリ等による服用状況・副作用確認と医師へのフィードバック',
            requirements_summary='調剤後の適切な時期（数日〜2週間以内）に電話等で服薬状況・効果・副作用を確認し、必要に応じ医師へ情報提供',
            chart_notes='フォローアップ実施日時、確認した服薬アドヒアランス、副作用発現の有無、次回提案内容を記録。',
            contributes_to_regional_support='医師へ文書情報提供を行った場合は服薬情報等提供料実績にも貢献'
        ))
        
    # 7. 重複投薬・相互作用等防止加算 (残薬調整 / 処方変更)
    if c.has_leftover_drugs or c.has_prescription_query_changed:
        is_change = c.has_prescription_query_changed
        name_label = '重複投薬・相互作用等防止加算（処方変更）' if is_change else '重複投薬・相互作用等防止加算（残薬調整）'
        pts = 40 if is_change else 30
        desc = '疑義照会による処方変更（用量変更・削除・別剤形変更等）' if is_change else '残薬確認に伴う日数調整・処方医への連絡調整'
        items.append(BillingItem(
            code='PREV_01',
            name=name_label,
            points=pts,
            category='疑義照会・適正化',
            description=desc,
            requirements_summary='処方医への疑義照会・残薬調整の実施と処方変更の確定',
            chart_notes='照会日時、照会先医師名、残薬理由・照会内容、変更前後の処方内容を記録。',
            contributes_to_regional_support=None
        ))
        
    # 8. 服薬情報等提供料 (トレーシングレポート)
    if c.has_doctor_feedback_requested:
        items.append(BillingItem(
            code='INFO_01',
            name='服薬情報等提供料1（医師からの求め）',
            points=30,
            category='医療連携',
            description='医療機関からの求めに応じた患者の服薬状況・残薬等の文書提供',
            requirements_summary='医師からの照会・求めに応じた文書（トレーシングレポート等）の作成と送付',
            chart_notes='提供日時、提供先医療機関・診療科・医師名、提供文書の写しを添付・記録。',
            contributes_to_regional_support='服薬情報等提供料実績（地域支援加算の必須要件に+1カウント）'
        ))
        regional_contributions.append('服薬情報等提供料実績 (+1 ★重要要件)')
    elif c.has_spontaneous_doctor_feedback:
        items.append(BillingItem(
            code='INFO_02',
            name='服薬情報等提供料2（薬局からの提案）',
            points=20,
            category='医療連携',
            description='薬剤師の判断による服薬アドヒアランス・残薬・副作用等の医師への文書情報提供',
            requirements_summary='患者同意を得た上での処方医へのトレーシングレポート提出',
            chart_notes='情報提供の必要性判断、同意取得状況、提供文書の写しと医師からのフィードバックを記録。',
            contributes_to_regional_support='服薬情報等提供料実績（地域支援加算の必須要件に+1カウント）'
        ))
        regional_contributions.append('服薬情報等提供料実績 (+1 ★重要要件)')
        
    # 9. 乳幼児服薬指導加算 (6歳未満)
    if c.age < 6:
        items.append(BillingItem(
            code='PEDI_01',
            name='乳幼児服薬指導加算',
            points=12,
            category='小児服薬指導',
            description='6歳未満の乳幼児に対する体重・年齢に応じた服用指導とお薬手帳記載',
            requirements_summary='体重・年齢確認、服薬ゼリー等の飲ませ方指導、保護者への適切な服薬説明とお薬手帳への特記事項記載',
            chart_notes='患児の体重、保護者への飲ませ方説明、お薬手帳への指導内容記載を記録。',
            contributes_to_regional_support=None
        ))
        
    # 10. 在宅患者訪問薬剤管理指導料
    if c.is_home_care:
        items.append(BillingItem(
            code='HOME_01',
            name='在宅患者訪問薬剤管理指導料1（単一建物1人）',
            points=650,
            category='在宅医療',
            description='医師の指示に基づく在宅訪問・服薬管理・カレンダーセット・多職種連携',
            requirements_summary='在宅療養計画書の作成、定期訪問、居宅療養指導、医師およびケアマネジャー等への報告書提出',
            chart_notes='訪問日時、保管管理状態、バイタル・副作用チェック、他職種（看護師・ケアマネ）との情報共有内容を記録。',
            contributes_to_regional_support='在宅患者訪問薬剤管理指導実績（地域支援加算の最重要要件に+1カウント）'
        ))
        regional_contributions.append('在宅訪問薬剤管理指導実績 (+1 ★重要要件)')
        
    # 小児特定加算（小児在宅など）
    if c.is_home_care and c.is_pediatric_special:
        items.append(BillingItem(
            code='PEDI_SPEC_01',
            name='小児特定加算（在宅医療）',
            points=350,
            category='小児在宅医療',
            description='医療的ケア児等に対する高度な在宅薬剤管理指導',
            requirements_summary='18歳未満または医療的ケア児に対する計画的な訪問指導',
            chart_notes='経管栄養・吸入器等のデバイス管理、成長に応じた用量調整確認を記録。',
            contributes_to_regional_support=None
        ))
        
    total_pts = sum(item.points for item in items)
    if not items:
        advice.append('現在の選択条件では特別な個別加算の対象はありません（基本の服薬管理指導料等を算定）。')
    else:
        advice.append(f'算定可能な加算が {len(items)} 件見つかりました（合計: +{total_pts}点 / 1割負担:+{total_pts*1}円, 3割負担:+{total_pts*3}円）。')
        if regional_contributions:
            contrib_text = '、'.join(regional_contributions)
            advice.append(f'★ この調剤は薬局全体の【 {contrib_text} 】に貢献します！')
            
    if not c.has_medicine_notebook:
        advice.append('※ お薬手帳の持参がない場合、服薬管理指導料の基本点数が異なる点にご注意ください。')
        
    return PatientBillingResult(
        recommended_items=items,
        total_points=total_pts,
        regional_contributions=regional_contributions,
        advice_comments=advice
    )
