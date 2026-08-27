from app.models.schemas import PharmacyMetrics, RegionalEvaluationResult, RequirementStatus

def get_default_metrics() -> PharmacyMetrics:
    return PharmacyMetrics(
        pharmacy_name='ひまわり調剤薬局',
        dispensing_basic_fee_type='basic_1',
        monthly_prescriptions=1200,
        concentration_rate=78.5,
        narcotics_count=4,
        home_visit_count=22,
        family_pharmacist_count=38,
        info_provision_count=15,
        preavoid_count=2,
        generic_percentage=84.2,
        night_holiday_count=110,
        stock_drugs_count=1280,
        has_24h_system=True,
        has_infection_system=True,
        has_online_qualification=True,
        has_electronic_prescription=True,
        has_otc_sales=True
    )

def evaluate_regional_support(m: PharmacyMetrics) -> RegionalEvaluationResult:
    is_basic_1 = (m.dispensing_basic_fee_type == 'basic_1')
    
    # 医薬品供給対応体制加算の判定（備蓄1200品目以上、後発品80%以上、24時間対応等）
    supply_qualified = (
        m.stock_drugs_count >= 1200 and
        m.generic_percentage >= 80.0 and
        m.has_24h_system and
        m.has_online_qualification
    )
    
    # 連携強化加算の判定（感染症連携、OTC備蓄、電子処方箋等）
    infection_qualified = (
        m.has_infection_system and
        m.has_otc_sales and
        m.has_electronic_prescription
    )
    
    # 個別要件リストの生成
    reqs = []
    
    # 1. 麻薬調剤実績 (加算1基準: 1回, 加算2基準: 3回, 加算3/4基準: 10回)
    target_narcotics = 1 if is_basic_1 else 10
    narc_sat = m.narcotics_count >= target_narcotics
    narc_short = max(0, target_narcotics - m.narcotics_count)
    reqs.append(RequirementStatus(
        name='麻薬調剤実績',
        category='調剤実績',
        current_value=float(m.narcotics_count),
        target_value=float(target_narcotics),
        unit='回/年',
        is_satisfied=narc_sat,
        progress_percentage=min(100.0, round((m.narcotics_count / target_narcotics) * 100, 1)),
        shortage=float(narc_short),
        advice='麻薬処方患者が来局時は、麻薬管理指導加算（100点）の積極的な算定と薬歴記録を行いましょう。' if not narc_sat else '目標基準を達成しています。継続的な算定を維持しましょう。'
    ))
    
    # 2. 在宅患者訪問薬剤管理指導等の実績 (加算1基準: 24回, 加算2基準: 48回, 加算3/4基準: 48回)
    target_home = 24 if is_basic_1 else 48
    home_sat = m.home_visit_count >= target_home
    home_short = max(0, target_home - m.home_visit_count)
    reqs.append(RequirementStatus(
        name='在宅訪問薬剤管理指導実績',
        category='在宅実績',
        current_value=float(m.home_visit_count),
        target_value=float(target_home),
        unit='回/年',
        is_satisfied=home_sat,
        progress_percentage=min(100.0, round((m.home_visit_count / target_home) * 100, 1)),
        shortage=float(home_short),
        advice=f'あと{home_short}回で基準達成です。外来通院が難しくなった患者様へ在宅療養移行の提案を行いましょう。' if not home_sat else '目標基準を達成しています。'
    ))
    
    # 3. かかりつけ薬剤師指導料等実績 (加算1基準: 40回, 加算2基準: 80回, 加算3/4基準: 100回)
    target_family = 40 if is_basic_1 else 100
    fam_sat = m.family_pharmacist_count >= target_family
    fam_short = max(0, target_family - m.family_pharmacist_count)
    reqs.append(RequirementStatus(
        name='かかりつけ薬剤師指導料実績',
        category='服薬指導',
        current_value=float(m.family_pharmacist_count),
        target_value=float(target_family),
        unit='回/年',
        is_satisfied=fam_sat,
        progress_percentage=min(100.0, round((m.family_pharmacist_count / target_family) * 100, 1)),
        shortage=float(fam_short),
        advice=f'あと{fam_short}回で基準達成です。定期来局される複数疾患の患者様へ同意取得を進めましょう。' if not fam_sat else '目標基準を達成しています。'
    ))
    
    # 4. 服薬情報等提供料（トレーシングレポート等）実績 (加算1基準: 12回, 加算2基準: 30回, 加算3/4基準: 60回)
    target_info = 12 if is_basic_1 else 60
    info_sat = m.info_provision_count >= target_info
    info_short = max(0, target_info - m.info_provision_count)
    reqs.append(RequirementStatus(
        name='服薬情報等提供料実績',
        category='医療連携',
        current_value=float(m.info_provision_count),
        target_value=float(target_info),
        unit='回/年',
        is_satisfied=info_sat,
        progress_percentage=min(100.0, round((m.info_provision_count / target_info) * 100, 1)),
        shortage=float(info_short),
        advice='残薬整理や副作用疑い、服用状況のフィードバックなど、医師へのトレーシングレポート作成を習慣化しましょう。' if not info_sat else '目標基準を達成しています。'
    ))
    
    # 5. プレアボイド事例報告実績 (加算1〜4共通: 1件以上)
    target_preavoid = 1
    pre_sat = m.preavoid_count >= target_preavoid
    pre_short = max(0, target_preavoid - m.preavoid_count)
    reqs.append(RequirementStatus(
        name='プレアボイド事例報告実績',
        category='医療安全',
        current_value=float(m.preavoid_count),
        target_value=float(target_preavoid),
        unit='件/年',
        is_satisfied=pre_sat,
        progress_percentage=min(100.0, round((m.preavoid_count / target_preavoid) * 100, 1)),
        shortage=float(pre_short),
        advice='疑義照会による処方変更や重篤な副作用回避事例を日薬プレアボイドシステムに年1件以上登録しましょう。' if not pre_sat else '日本薬剤師会への報告実績を満たしています。'
    ))
    
    # 6. 後発医薬品使用割合 (加算基準: 80.0%以上)
    target_gen = 80.0
    gen_sat = m.generic_percentage >= target_gen
    gen_short = max(0.0, round(target_gen - m.generic_percentage, 1))
    reqs.append(RequirementStatus(
        name='後発医薬品使用割合',
        category='医薬品供給',
        current_value=m.generic_percentage,
        target_value=target_gen,
        unit='%',
        is_satisfied=gen_sat,
        progress_percentage=min(100.0, round((m.generic_percentage / target_gen) * 100, 1)),
        shortage=gen_short,
        advice=f'基準まであと{gen_short}%です。先発品希望患者への丁寧なジェネリック変更案内を強化しましょう。' if not gen_sat else '後発医薬品割合の基準（80%以上）をクリアしています。'
    ))
    
    # 7. 備蓄医薬品品目数 (医薬品供給対応基準: 1,200品目以上)
    target_stock = 1200
    stock_sat = m.stock_drugs_count >= target_stock
    stock_short = max(0, target_stock - m.stock_drugs_count)
    reqs.append(RequirementStatus(
        name='備蓄医薬品品目数',
        category='供給体制',
        current_value=float(m.stock_drugs_count),
        target_value=float(target_stock),
        unit='品目',
        is_satisfied=stock_sat,
        progress_percentage=min(100.0, round((m.stock_drugs_count / target_stock) * 100, 1)),
        shortage=float(stock_short),
        advice=f'医薬品供給対応体制加算の基準まであと{stock_short}品目です。' if not stock_sat else '備蓄品目数要件（1,200品目以上）をクリアしています。'
    ))
    
    # 加算1〜4の判定
    tier_statuses = {
        '地域支援体制加算1': False,
        '地域支援体制加算2': False,
        '地域支援体制加算3': False,
        '地域支援体制加算4': False
    }
    
    all_basic_reqs_met = (narc_sat and home_sat and fam_sat and info_sat and pre_sat and gen_sat and m.has_24h_system)
    
    # 上位要件（加算2判定用: 在宅48回以上、かかりつけ80回以上等）
    is_tier2_met = all_basic_reqs_met and (m.home_visit_count >= 48) and (m.family_pharmacist_count >= 80) and (m.narcotics_count >= 3)
    
    if is_basic_1:
        if is_tier2_met:
            tier_statuses['地域支援体制加算2'] = True
            tier_statuses['地域支援体制加算1'] = True
            current_tier = '地域支援体制加算2'
            points = 47
        elif all_basic_reqs_met:
            tier_statuses['地域支援体制加算1'] = True
            current_tier = '地域支援体制加算1'
            points = 39
        else:
            current_tier = '加算未達（要件不足）'
            points = 0
    else:
        # 基本料1以外の場合（加算3 or 4）
        is_tier3_met = all_basic_reqs_met and (m.narcotics_count >= 10) and (m.home_visit_count >= 48) and (m.family_pharmacist_count >= 100)
        is_tier4_met = is_tier3_met and (m.night_holiday_count >= 400)
        if is_tier4_met:
            tier_statuses['地域支援体制加算4'] = True
            tier_statuses['地域支援体制加算3'] = True
            current_tier = '地域支援体制加算4'
            points = 39
        elif is_tier3_met:
            tier_statuses['地域支援体制加算3'] = True
            current_tier = '地域支援体制加算3'
            points = 17
        else:
            current_tier = '加算未達（要件不足）'
            points = 0
            
    # サマリーと優先アクションの生成
    priority_actions = []
    unsatisfied = [r for r in reqs if not r.is_satisfied]
    
    if not unsatisfied:
        summary_msg = f'現在【{current_tier}】の全要件を満たしています！この調子で算定実績を維持しましょう。'
        if current_tier == '地域支援体制加算1' and is_basic_1:
            diff_home = max(0, 48 - m.home_visit_count)
            diff_fam = max(0, 80 - m.family_pharmacist_count)
            if diff_home > 0 or diff_fam > 0:
                priority_actions.append(f'【ステップアップ】上位の「地域支援体制加算2」まで、あと在宅訪問{diff_home}回、かかりつけ{diff_fam}回です。')
    else:
        summary_msg = f'現在、基準未達の項目が {len(unsatisfied)} 項目あります。以下の優先アクションを実施することで加算算定が可能になります。'
        for r in unsatisfied:
            priority_actions.append(f'【{r.name}】不足: {r.shortage}{r.unit} （現在 {r.current_value}{r.unit} / 目標 {r.target_value}{r.unit}）')
            
    if supply_qualified:
        priority_actions.append('医薬品供給対応体制加算（備蓄1,200品目・後発品80%等）の要件をクリアしています。')
    else:
        priority_actions.append('医薬品供給対応体制加算: 備蓄品目数または後発品割合の要件をご確認ください。')
        
    return RegionalEvaluationResult(
        current_tier=current_tier,
        is_basic_fee_1=is_basic_1,
        supply_system_addition_qualified=supply_qualified,
        infection_enhancement_qualified=infection_qualified,
        points_earned=points,
        tier_statuses=tier_statuses,
        requirements=reqs,
        summary_message=summary_msg,
        priority_actions=priority_actions
    )
