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
    
    # ----------------------------------------------------
    # ① 実績要件（日々の現場アクションで積み上げる要件）
    # ----------------------------------------------------
    perf_reqs = []
    
    # 1. 麻薬調剤実績
    target_narc = 1 if is_basic_1 else 10
    narc_sat = m.narcotics_count >= target_narc
    narc_short = max(0, target_narc - m.narcotics_count)
    perf_reqs.append(RequirementStatus(
        name='麻薬調剤実績',
        category='調剤実績',
        requirement_type='performance',
        current_value_text=f'{m.narcotics_count}回',
        target_value_text=f'{target_narc}回/年',
        unit='回',
        is_satisfied=narc_sat,
        progress_percentage=min(100.0, round((m.narcotics_count / target_narc) * 100, 1)),
        shortage_text=f'不足 {narc_short}回' if not narc_sat else None,
        advice='麻薬処方時は麻薬管理指導加算（100点）の積極的な算定と薬歴管理を行いましょう。' if not narc_sat else '目標基準を達成中。継続算定を維持しましょう。'
    ))
    
    # 2. 在宅訪問薬剤管理指導実績
    target_home = 24 if is_basic_1 else 48
    home_sat = m.home_visit_count >= target_home
    home_short = max(0, target_home - m.home_visit_count)
    perf_reqs.append(RequirementStatus(
        name='在宅訪問薬剤管理指導実績',
        category='在宅実績',
        requirement_type='performance',
        current_value_text=f'{m.home_visit_count}回',
        target_value_text=f'{target_home}回/年',
        unit='回',
        is_satisfied=home_sat,
        progress_percentage=min(100.0, round((m.home_visit_count / target_home) * 100, 1)),
        shortage_text=f'不足 {home_short}回' if not home_sat else None,
        advice=f'あと{home_short}回で基準達成です。通院困難患者への在宅訪問提案を強化しましょう。' if not home_sat else '目標基準を達成中。'
    ))
    
    # 3. かかりつけ薬剤師指導料実績
    target_fam = 40 if is_basic_1 else 100
    fam_sat = m.family_pharmacist_count >= target_fam
    fam_short = max(0, target_fam - m.family_pharmacist_count)
    perf_reqs.append(RequirementStatus(
        name='かかりつけ薬剤師指導料実績',
        category='服薬指導',
        requirement_type='performance',
        current_value_text=f'{m.family_pharmacist_count}回',
        target_value_text=f'{target_fam}回/年',
        unit='回',
        is_satisfied=fam_sat,
        progress_percentage=min(100.0, round((m.family_pharmacist_count / target_fam) * 100, 1)),
        shortage_text=f'不足 {fam_short}回' if not fam_sat else None,
        advice=f'あと{fam_short}回で基準達成です。定期来局される複数疾患患者への同意取得を進めましょう。' if not fam_sat else '目標基準を達成中。'
    ))
    
    # 4. 服薬情報等提供料（トレーシングレポート等）実績
    target_info = 12 if is_basic_1 else 60
    info_sat = m.info_provision_count >= target_info
    info_short = max(0, target_info - m.info_provision_count)
    perf_reqs.append(RequirementStatus(
        name='服薬情報等提供料実績',
        category='医療連携',
        requirement_type='performance',
        current_value_text=f'{m.info_provision_count}回',
        target_value_text=f'{target_info}回/年',
        unit='回',
        is_satisfied=info_sat,
        progress_percentage=min(100.0, round((m.info_provision_count / target_info) * 100, 1)),
        shortage_text=f'不足 {info_short}回' if not info_sat else None,
        advice='残薬整理や副作用疑い、アドヒアランス低下など医師へのトレーシングレポート作成を習慣化しましょう。' if not info_sat else '目標基準を達成中。'
    ))
    
    # 5. プレアボイド事例報告実績
    target_pre = 1
    pre_sat = m.preavoid_count >= target_pre
    pre_short = max(0, target_pre - m.preavoid_count)
    perf_reqs.append(RequirementStatus(
        name='プレアボイド事例報告実績',
        category='医療安全',
        requirement_type='performance',
        current_value_text=f'{m.preavoid_count}件',
        target_value_text=f'{target_pre}件/年',
        unit='件',
        is_satisfied=pre_sat,
        progress_percentage=min(100.0, round((m.preavoid_count / target_pre) * 100, 1)),
        shortage_text=f'不足 {pre_short}件' if not pre_sat else None,
        advice='疑義照会による処方変更や副作用回避事例を日薬プレアボイドシステムに年1件以上登録しましょう。' if not pre_sat else '報告実績を満たしています。'
    ))
    
    # 6. 後発医薬品使用割合
    target_gen = 80.0
    gen_sat = m.generic_percentage >= target_gen
    gen_short = max(0.0, round(target_gen - m.generic_percentage, 1))
    perf_reqs.append(RequirementStatus(
        name='後発医薬品使用割合',
        category='医薬品供給',
        requirement_type='performance',
        current_value_text=f'{m.generic_percentage:.1f}%',
        target_value_text=f'{target_gen:.1f}%以上',
        unit='%',
        is_satisfied=gen_sat,
        progress_percentage=min(100.0, round((m.generic_percentage / target_gen) * 100, 1)),
        shortage_text=f'不足 {gen_short}%' if not gen_sat else None,
        advice=f'基準まであと{gen_short}%です。先発希望患者へのジェネリック案内を強化しましょう。' if not gen_sat else '後発医薬品割合の基準（80%以上）をクリアしています。'
    ))

    # ----------------------------------------------------
    # ② 体制要件（薬局の設備・協定・システム等の基盤要件）
    # ----------------------------------------------------
    struct_reqs = []
    
    # 1. 備蓄医薬品品目数 (1,200品目以上)
    stock_sat = m.stock_drugs_count >= 1200
    stock_short = max(0, 1200 - m.stock_drugs_count)
    struct_reqs.append(RequirementStatus(
        name='備蓄医薬品品目数',
        category='供給体制',
        requirement_type='structural',
        current_value_text=f'{m.stock_drugs_count}品目',
        target_value_text='1,200品目以上',
        unit='品目',
        is_satisfied=stock_sat,
        progress_percentage=min(100.0, round((m.stock_drugs_count / 1200) * 100, 1)),
        shortage_text=f'不足 {stock_short}品目' if not stock_sat else None,
        advice='医薬品供給対応体制加算の基準（1,200品目）を満たすよう備蓄品目を調整してください。' if not stock_sat else '備蓄品目数要件（1,200品目以上）をクリアしています。'
    ))
    
    # 2. 24時間調剤・在宅対応体制
    struct_reqs.append(RequirementStatus(
        name='24時間調剤・在宅対応体制',
        category='対応体制',
        requirement_type='structural',
        current_value_text='体制整備済' if m.has_24h_system else '未整備',
        target_value_text='体制整備必須',
        unit='',
        is_satisfied=m.has_24h_system,
        progress_percentage=100.0 if m.has_24h_system else 0.0,
        shortage_text='体制未整備' if not m.has_24h_system else None,
        advice='夜間・休日等の24時間対応体制および連絡先周知が必要です。' if not m.has_24h_system else '24時間対応体制を整備済みです。'
    ))
    
    # 3. 新興感染症対応・連携協定
    struct_reqs.append(RequirementStatus(
        name='新興感染症対応・連携協定',
        category='感染症対応',
        requirement_type='structural',
        current_value_text='協定締結済' if m.has_infection_system else '未締結',
        target_value_text='協定締結必須',
        unit='',
        is_satisfied=m.has_infection_system,
        progress_percentage=100.0 if m.has_infection_system else 0.0,
        shortage_text='協定未締結' if not m.has_infection_system else None,
        advice='自治体・医師会との新興感染症連携協定の締結を進めてください。' if not m.has_infection_system else '連携協定を締結済みです。'
    ))
    
    # 4. オンライン資格確認・電子処方箋体制
    it_sat = m.has_online_qualification and m.has_electronic_prescription
    struct_reqs.append(RequirementStatus(
        name='オンライン資格確認 ＆ 電子処方箋体制',
        category='医療DX',
        requirement_type='structural',
        current_value_text='DX基盤導入済' if it_sat else '一部未対応',
        target_value_text='両方導入必須',
        unit='',
        is_satisfied=it_sat,
        progress_percentage=100.0 if it_sat else 50.0,
        shortage_text='未導入あり' if not it_sat else None,
        advice='マイナ保険証対応および電子処方箋の受付体制を整備してください。' if not it_sat else '医療DXの基盤整備をクリアしています。'
    ))
    
    # 5. 要指導医薬品・一般用医薬品の備蓄販売
    struct_reqs.append(RequirementStatus(
        name='OTC・要指導医薬品の備蓄販売',
        category='地域支援',
        requirement_type='structural',
        current_value_text='販売体制あり' if m.has_otc_sales else '取扱なし',
        target_value_text='取扱必須',
        unit='',
        is_satisfied=m.has_otc_sales,
        progress_percentage=100.0 if m.has_otc_sales else 0.0,
        shortage_text='取扱なし' if not m.has_otc_sales else None,
        advice='要指導医薬品・一般用医薬品（第1類〜第3類）の陳列・販売体制を維持してください。' if not m.has_otc_sales else 'OTC備蓄販売体制をクリアしています。'
    ))

    # ----------------------------------------------------
    # 加算判定ロジック
    # ----------------------------------------------------
    supply_qualified = (stock_sat and gen_sat and m.has_24h_system and m.has_online_qualification)
    infection_qualified = (m.has_infection_system and m.has_otc_sales and m.has_electronic_prescription)
    
    all_perf_met = (narc_sat and home_sat and fam_sat and info_sat and pre_sat and gen_sat)
    all_struct_met = (m.has_24h_system and m.has_online_qualification)
    
    tier_statuses = {
        '地域支援体制加算1': False,
        '地域支援体制加算2': False,
        '地域支援体制加算3': False,
        '地域支援体制加算4': False
    }
    
    is_tier2_met = all_perf_met and all_struct_met and (m.home_visit_count >= 48) and (m.family_pharmacist_count >= 80) and (m.narcotics_count >= 3)
    
    if is_basic_1:
        if is_tier2_met:
            tier_statuses['地域支援体制加算2'] = True
            tier_statuses['地域支援体制加算1'] = True
            current_tier = '地域支援体制加算2'
            points = 47
        elif all_perf_met and all_struct_met:
            tier_statuses['地域支援体制加算1'] = True
            current_tier = '地域支援体制加算1'
            points = 39
        else:
            current_tier = '加算未達（要件不足）'
            points = 0
    else:
        is_tier3_met = all_perf_met and all_struct_met and (m.narcotics_count >= 10) and (m.home_visit_count >= 48) and (m.family_pharmacist_count >= 100)
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
            
    # 実績面と体制面でのアクション提示
    perf_actions = []
    struct_actions = []
    
    for r in perf_reqs:
        if not r.is_satisfied:
            perf_actions.append(f'【{r.name}】{r.shortage_text} （現在: {r.current_value_text} / 目標: {r.target_value_text}）')
            
    for r in struct_reqs:
        if not r.is_satisfied:
            struct_actions.append(f'【{r.name}】{r.advice}')
            
    if not perf_actions and not struct_actions:
        summary_msg = f'現在【{current_tier}】の全要件をクリアしています！この調子で実績を維持しましょう。'
    elif perf_actions and not struct_actions:
        summary_msg = f'体制要件はすべてクリア済みです！実績要件の残り {len(perf_actions)} 項目を重点的に積み上げましょう。'
    elif not perf_actions and struct_actions:
        summary_msg = f'実績要件は達成しています！体制要件（設備・協定等）の残り {len(struct_actions)} 項目を整備しましょう。'
    else:
        summary_msg = f'実績要件に {len(perf_actions)} 件、体制要件に {len(struct_actions)} 件の不足があります。'
        
    return RegionalEvaluationResult(
        current_tier=current_tier,
        is_basic_fee_1=is_basic_1,
        supply_system_addition_qualified=supply_qualified,
        infection_enhancement_qualified=infection_qualified,
        points_earned=points,
        tier_statuses=tier_statuses,
        performance_requirements=perf_reqs,
        structural_requirements=struct_reqs,
        summary_message=summary_msg,
        performance_actions=perf_actions,
        structural_actions=struct_actions
    )
