from app.models.schemas import PharmacyMetrics, RegionalEvaluationResult, RequirementStatus
from typing import List

def get_default_metrics() -> PharmacyMetrics:
    return PharmacyMetrics()

def evaluate_regional_support(metrics: PharmacyMetrics) -> RegionalEvaluationResult:
    """
    厚生労働省 令和8年度（2026年6月1日施行）調剤報酬改定 公式基準
    「地域支援・医薬品供給対応体制加算1〜5」完全適合判定エンジン
    """
    audit_trail: List[str] = []
    supply_reqs: List[RequirementStatus] = []
    struct_reqs: List[RequirementStatus] = []
    perf_reqs: List[RequirementStatus] = []
    
    supply_actions: List[str] = []
    struct_actions: List[str] = []
    perf_actions: List[str] = []

    # =========================================================================
    # 1. 様式87の3の1：医薬品供給対応体制（全加算共通 8項目）の判定
    # =========================================================================
    ge_rate = metrics.generic_percentage_special_applied or metrics.generic_percentage
    ge_ok = ge_rate >= 85.0
    ge_progress = round((ge_rate / 85.0) * 100, 1)
    ge_shortage = f"あと {(85.0 - ge_rate):.1f}% 不足" if not ge_ok else "達成"
    ge_advice = "供給停止品目の臨時除外特例を適用するか、処方医へ後発品変更の疑義照会を行ってください。" if not ge_ok else "85%以上の高水準を維持しています。"
    
    supply_reqs.append(RequirementStatus(
        id="SUP-08",
        name="後発医薬品調剤割合 85%以上",
        category="医薬品供給対応体制(様式87-3-1)",
        requirement_type="supply_87_1",
        current_value_text=f"{ge_rate:.1f} %",
        target_value_text="85.0 %以上",
        is_satisfied=ge_ok,
        progress_percentage=ge_progress,
        shortage_text=ge_shortage,
        advice=ge_advice,
        official_ref="様式87の3の1 第(8)項"
    ))
    if not ge_ok:
        supply_actions.append(f"後発品調剤割合が {ge_rate:.1f}% と85%未満です。特例除外の適用またはGE変更を推進してください。")

    supply_items = [
        ("SUP-01", "計画的調達・在庫管理体制", metrics.has_planned_procurement, "様式87の3の1 第(1)項", "地域の需要に応じた計画発注手順書を整備してください。"),
        ("SUP-02", "近隣薬局への医薬品分譲実績", metrics.has_drug_distribution_record, "様式87の3の1 第(2)項", "近隣薬局との医薬品融通・分譲契約及び実績台帳を記録してください。"),
        ("SUP-03", "供給不足時の代替調剤・疑義照会手順", metrics.has_shortage_response_protocol, "様式87の3の1 第(3)項", "供給不安時の処方医提案手順書を策定・周知してください。"),
        ("SUP-04", "医薬品卸との原則単品単価交渉", metrics.has_single_item_negotiation, "様式87の3の1 第(4)項", "卸業者との取引で単品単価交渉を実施してください。"),
        ("SUP-05", "急配・頻回配送の抑制手順", metrics.has_rush_delivery_prevention, "様式87の3の1 第(5)項", "適正在庫発注により急配・頻回配送を抑制してください。"),
        ("SUP-06", "在庫調整目的の返品抑制", metrics.has_return_suppression, "様式87の3の1 第(6)項", "返品防止手順を遵守してください。"),
        ("SUP-07", "後発医薬品積極調剤の掲示", metrics.has_generic_promotion_notice, "様式87の3の1 第(7)項", "薬局内外に見やすい後発品積極調剤ポスターを掲示してください。")
    ]

    supply_bools_ok = True
    for sid, sname, sval, sref, sadvice in supply_items:
        s_ok = bool(sval)
        if not s_ok:
            supply_bools_ok = False
            supply_actions.append(f"【供給体制】{sname} が未整備です。{sadvice}")
        supply_reqs.append(RequirementStatus(
            id=sid,
            name=sname,
            category="医薬品供給対応体制(様式87-3-1)",
            requirement_type="supply_87_1",
            current_value_text="整備済" if s_ok else "未整備",
            target_value_text="必須整備",
            is_satisfied=s_ok,
            progress_percentage=100.0 if s_ok else 0.0,
            shortage_text="適合" if s_ok else "未整備",
            advice="基準を満たしています。" if s_ok else sadvice,
            official_ref=sref
        ))

    supply_system_qualified = ge_ok and supply_bools_ok
    audit_trail.append(f"【様式87の3の1 医薬品供給対応体制】: {'適合 (全8項目充足)' if supply_system_qualified else '不適合 (要件未達あり)'}")

    # =========================================================================
    # 2. 地域医療への貢献に係る十分な体制（加算2・加算4 共通要件群）
    # =========================================================================
    stock_ok = metrics.stock_drugs_count >= 1200
    struct_reqs.append(RequirementStatus(
        id="STR-01",
        name="医療用医薬品の備蓄品目数",
        category="十分な体制要件",
        requirement_type="structural",
        current_value_text=f"{metrics.stock_drugs_count:,} 品目",
        target_value_text="1,200 品目以上",
        is_satisfied=stock_ok,
        progress_percentage=round(min(100.0, (metrics.stock_drugs_count / 1200.0) * 100), 1),
        shortage_text="達成" if stock_ok else f"あと {1200 - metrics.stock_drugs_count} 品目不足",
        advice="十分な備蓄を維持しています。" if stock_ok else "採用薬を見直し1,200品目以上の常時備蓄を確保してください。",
        official_ref="施設基準通知 第8の2"
    ))
    if not stock_ok:
        struct_actions.append(f"備蓄医薬品数が {metrics.stock_drugs_count} 品目です。1,200品目以上の常時備蓄を確保してください。")

    device_ok = metrics.self_medication_device_count >= 3
    struct_reqs.append(RequirementStatus(
        id="STR-09",
        name="セルフメディケーション関連機器設置 (8種中3種以上)",
        category="十分な体制要件",
        requirement_type="structural",
        current_value_text=f"{metrics.self_medication_device_count} 種類設置",
        target_value_text="3 種類以上",
        is_satisfied=device_ok,
        progress_percentage=round(min(100.0, (metrics.self_medication_device_count / 3.0) * 100), 1),
        shortage_text="達成" if device_ok else f"あと {3 - metrics.self_medication_device_count} 種類不足",
        advice="健康チェックコーナーが整備されています。" if device_ok else "血圧計、体組成計、パルスオキシメータ等から3種以上を待合室に常時設置してください。",
        official_ref="施設基準通知 別添2"
    ))
    if not device_ok:
        struct_actions.append(f"セルフメディケーション機器が {metrics.self_medication_device_count} 種です。指定8機器中3種以上の設置が必要です。")

    struct_items = [
        ("STR-02", "24時間調剤・在宅対応体制", metrics.has_24h_system, "施設基準通知", "時間外連絡先を薬局前及び配布物に明記し輪番体制を整備してください。"),
        ("STR-03", "麻薬小売業免許・管理保管庫", metrics.has_narcotics_license, "施設基準通知", "麻薬免許を取得し固定式金庫等の保管設備を整備してください。"),
        ("STR-04", "無菌製剤処理体制（自店または共同利用）", metrics.has_sterile_preparation_system, "施設基準通知", "クリーンベンチ設置または地域の薬局等との共同利用契約を締結してください。"),
        ("STR-05", "医療DX推進体制（電子処方箋等）", metrics.has_medical_dx_system, "施設基準通知", "電子処方箋の受付管理体制を整備してください。"),
        ("STR-06", "新興感染症第二種指定協定締結", metrics.has_infection_agreement, "感染症法第38条", "都道府県との間で第二種協定指定医療機関協定を締結してください。"),
        ("STR-07", "要指導・一般用医薬品の備蓄販売 (48薬効群以上)", metrics.otc_drug_categories_count >= 48, "施設基準通知", "48薬効群以上のOTC医薬品を常時陳列・販売してください。"),
        ("STR-08", "個別服薬指導相談カウンター", metrics.has_private_counseling_counter, "施設基準通知", "パーテーション付きの着座相談ブースを設置してください。"),
        ("STR-10", "医療材料・衛生材料供給・高度管理医療機器許可", metrics.has_medical_equipment_sales_license, "施設基準通知", "高度管理医療機器販売業許可を取得し衛生材料の供給体制を整えてください。")
    ]

    other_struct_ok = True
    for stid, stname, stval, stref, stadvice in struct_items:
        st_ok = bool(stval)
        if not st_ok:
            other_struct_ok = False
            struct_actions.append(f"【体制要件】{stname} が未整備です。{stadvice}")
        struct_reqs.append(RequirementStatus(
            id=stid,
            name=stname,
            category="十分な体制要件",
            requirement_type="structural",
            current_value_text="適合" if st_ok else "未達",
            target_value_text="必須整備",
            is_satisfied=st_ok,
            progress_percentage=100.0 if st_ok else 0.0,
            shortage_text="クリア" if st_ok else "要整備",
            advice="基準を満たしています。" if st_ok else stadvice,
            official_ref=stref
        ))

    structural_system_qualified = stock_ok and device_ok and other_struct_ok
    audit_trail.append(f"【地域医療貢献に係る十分な体制】: {'適合' if structural_system_qualified else '不適合'}")

    # =========================================================================
    # 3. 様式87の3の2：地域医療貢献実績（全9項目）の評価
    # =========================================================================
    raw_perf_specs = [
        ("PERF-01", "(1) 夜間・休日等の調剤実績", metrics.rec_1_night_holiday_count, 40, 400, "回/年", "時間外・休日等の処方箋応需体制を強化してください。"),
        ("PERF-02", "(2) 麻薬の調剤実績", metrics.rec_2_narcotics_count, 1, 10, "回/年", "がん性疼痛等の麻薬処方箋の応需・在庫確保を行ってください。"),
        ("PERF-03", "(3) 重複投薬・相互作用等防止加算等", metrics.rec_3_prevention_adjustment_count, 20, 40, "回/年", "残薬確認・処方変更疑義照会を積極的に実施してください。"),
        ("PERF-04", "(4) 服薬管理指導料1イ・2イ算定実績", metrics.rec_4_guidance_1a_2a_count, 20, 40, "回/年", "手帳持参・継続管理患者への適切な指導料1イ/2イを算定してください（加算2・4必須）。"),
        ("PERF-05", "(5) 外来服薬支援料1算定実績", metrics.rec_5_outpatient_support_1_count, 1, 12, "回/年", "多剤併用患者の一包化・服薬カレンダー整理を支援してください。"),
        ("PERF-06", "(6) 訪問薬剤管理指導料等の算定実績", metrics.rec_6_home_visit_count, 24, 24, "回/年", "在宅患者・施設への計画的訪問指導を実施してください（加算4必須）。"),
        ("PERF-07", "(7) 服薬情報等提供料等の算定実績", metrics.rec_7_info_provision_tr_count, 30, 60, "回/年", "処方医へのトレーシングレポート（文書情報提供）を推進してください。"),
        ("PERF-08", "(8) 小児特定加算等の算定実績", metrics.rec_8_pediatric_special_count, 1, 1, "回/年", "小児患者への特別な薬学的指導を実施してください。"),
        ("PERF-09", "(9) 多職種連携会議への出席実績", metrics.rec_9_multidisciplinary_conference_count, 1, 5, "回/年", "認定薬剤師による地域の退院時・サービス担当者会議へ出席してください。")
    ]

    tier2_satisfied_count = 0
    tier4_satisfied_count = 0
    
    rec_4_tier2_ok = metrics.rec_4_guidance_1a_2a_count >= 20
    rec_4_tier4_ok = metrics.rec_4_guidance_1a_2a_count >= 40
    rec_6_tier4_ok = metrics.rec_6_home_visit_count >= 24

    for pid, pname, pval, t2_tgt, t4_tgt, punit, padvice in raw_perf_specs:
        is_t2_ok = pval >= t2_tgt
        is_t4_ok = pval >= t4_tgt
        if is_t2_ok:
            tier2_satisfied_count += 1
        if is_t4_ok:
            tier4_satisfied_count += 1
            
        prog_t2 = round(min(100.0, (pval / float(t2_tgt)) * 100), 1)
        shortage = "達成" if is_t2_ok else f"あと {t2_tgt - pval} {punit}不足"
        
        perf_reqs.append(RequirementStatus(
            id=pid,
            name=pname,
            category="地域医療貢献実績(様式87-3-2)",
            requirement_type="performance_87_2",
            current_value_text=f"{pval} {punit}",
            target_value_text=f"基準: {t2_tgt} {punit} (上位: {t4_tgt})",
            is_satisfied=is_t2_ok,
            progress_percentage=prog_t2,
            shortage_text=shortage,
            advice="基準クリア中。" if is_t2_ok else padvice,
            official_ref=f"様式87の3の2 {pname[:3]}"
        ))
        if not is_t2_ok:
            perf_actions.append(f"【実績】{pname}: 現在 {pval}/{t2_tgt} {punit}（{shortage}）。{padvice}")

    # =========================================================================
    # 4. 加算1〜5の階層的総合判定（告示・様式完全準拠）
    # =========================================================================
    is_basic_1 = metrics.dispensing_basic_fee_type == "basic_1"
    
    tier2_perf_qualified = rec_4_tier2_ok and (tier2_satisfied_count >= 3)
    tier2_qualified = is_basic_1 and supply_system_qualified and structural_system_qualified and tier2_perf_qualified
    
    tier1_qualified = is_basic_1 and supply_system_qualified
    
    tier4_perf_qualified = rec_4_tier4_ok and rec_6_tier4_ok and (tier4_satisfied_count >= 3)
    tier4_qualified = (not is_basic_1) and supply_system_qualified and structural_system_qualified and tier4_perf_qualified
    
    tier3_perf_qualified = tier2_satisfied_count >= 7
    tier3_qualified = (not is_basic_1) and supply_system_qualified and tier3_perf_qualified

    tier5_perf_qualified = tier4_satisfied_count >= 7
    tier5_qualified = supply_system_qualified and structural_system_qualified and tier5_perf_qualified

    current_tier = "算定不可"
    tier_code = "none"
    points_earned = 0
    performance_system_qualified = False

    if tier5_qualified:
        current_tier = "地域支援・医薬品供給対応体制加算5"
        tier_code = "tier_5"
        points_earned = 60
        performance_system_qualified = True
        summary_msg = "高度な地域医療連携・夜間対応体制及び実績7項目を達成し、加算5（60点）に適合しています。"
    elif tier2_qualified:
        current_tier = "地域支援・医薬品供給対応体制加算2"
        tier_code = "tier_2"
        points_earned = 47
        performance_system_qualified = True
        summary_msg = f"調剤基本料1において十分な体制及び実績（必須の指導料1イ/2イを含む{tier2_satisfied_count}項目）を満たし、加算2（47点）に適合しています。"
    elif tier4_qualified:
        current_tier = "地域支援・医薬品供給対応体制加算4"
        tier_code = "tier_4"
        points_earned = 39
        performance_system_qualified = True
        summary_msg = f"調剤基本料1以外において十分な体制及び実績（必須の(4)・(6)を含む{tier4_satisfied_count}項目）を満たし、加算4（39点）に適合しています。"
    elif tier1_qualified:
        current_tier = "地域支援・医薬品供給対応体制加算1"
        tier_code = "tier_1"
        points_earned = 39
        performance_system_qualified = False
        summary_msg = "医薬品供給対応体制（後発品85%以上を含む8項目）をクリアし、加算1（39点）に適合しています。加算2（47点）への上位移行を目指しましょう。"
    elif tier3_qualified:
        current_tier = "地域支援・医薬品供給対応体制加算3"
        tier_code = "tier_3"
        points_earned = 17
        performance_system_qualified = True
        summary_msg = f"調剤基本料1以外において実績7項目（現在{tier2_satisfied_count}項目）を達成し、加算3（17点）に適合しています。"
    else:
        current_tier = "算定不可"
        tier_code = "none"
        points_earned = 0
        summary_msg = "現在、施設基準の必須要件（供給体制、十分な体制、または実績）に未達項目があります。"

    audit_trail.append(f"【最終判定結果】: {current_tier} ({points_earned}点 / 処方箋)")
    audit_trail.append(f"・実績評価期間: {metrics.assessment_period}（直近1年）")
    audit_trail.append(f"・施設基準適用期間: {metrics.effective_period}")

    return RegionalEvaluationResult(
        current_tier=current_tier,
        tier_code=tier_code,
        points_earned=points_earned,
        supply_system_qualified=supply_system_qualified,
        structural_system_qualified=structural_system_qualified,
        performance_system_qualified=performance_system_qualified,
        summary_message=summary_msg,
        supply_requirements=supply_reqs,
        structural_requirements=struct_reqs,
        performance_requirements=perf_reqs,
        supply_actions=supply_actions,
        structural_actions=struct_actions,
        performance_actions=perf_actions,
        audit_trail=audit_trail
    )
