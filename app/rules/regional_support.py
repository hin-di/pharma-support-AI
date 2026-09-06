import math
from typing import List
from app.models.schemas import (
    PharmacyMetrics, RegionalEvaluationResult, RequirementStatus,
    ADD01_POINTS, ADD02_POINTS, ADD03_POINTS, ADD04_POINTS, ADD05_POINTS
)

def get_default_metrics() -> PharmacyMetrics:
    return PharmacyMetrics()

def evaluate_regional_support(metrics: PharmacyMetrics) -> RegionalEvaluationResult:
    """
    厚生労働省 令和8年度（2026年6月1日施行）調剤報酬点数表・告示・施設基準通知
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
    # 1. 処方箋受付回数1万回当たりの補正係数の算出（様式87の3の2）
    # =========================================================================
    annual_rx = metrics.annual_prescriptions or (metrics.monthly_prescriptions * 12)
    # 直近1年間の受付回数が1万回未満の場合は1万回とみなす
    adjusted_rx_base = max(10000, annual_rx)
    rx_factor = adjusted_rx_base / 10000.0

    audit_trail.append(f"・直近1年間の総処方箋受付回数: {annual_rx:,} 枚（補正基準枚数: {adjusted_rx_base:,} 枚, 係数: {rx_factor:.2f}）")
    audit_trail.append(f"・後発品割合 評価期間: {metrics.generic_ratio_period}")
    audit_trail.append(f"・実績要件 評価期間: {metrics.performance_period}")

    # =========================================================================
    # 2. 様式87の3の1：医薬品供給対応体制（全加算共通 8項目）の判定
    # =========================================================================
    ge_rate = metrics.generic_percentage_special_applied if metrics.temporary_exclusion_enabled else metrics.generic_percentage
    ge_ok = ge_rate >= 85.0
    ge_progress = round((ge_rate / 85.0) * 100, 1)
    ge_shortage = "充足" if ge_ok else f"あと {(85.0 - ge_rate):.1f}% 不足"
    
    supply_reqs.append(RequirementStatus(
        id="REQ-SUP-01",
        name="後発医薬品調剤割合 85%以上（規格単位数量ベース）",
        category="医薬品供給対応体制(様式87-3-1)",
        requirement_type="supply_87_1",
        current_value_text=f"{ge_rate:.1f} % (直近3か月)",
        target_value_text="85.0 %以上",
        is_satisfied=ge_ok,
        progress_percentage=ge_progress,
        shortage_text=ge_shortage,
        official_ref="様式87の3の1 第(8)項"
    ))
    if not ge_ok:
        supply_actions.append(f"後発医薬品調剤割合が {ge_rate:.1f}%（基準: 85.0%）で未達です。")

    supply_items = [
        ("REQ-SUP-02", "計画的調達・在庫管理体制", metrics.has_planned_procurement, "様式87の3の1 第(1)項"),
        ("REQ-SUP-03", "近隣保険薬局への医薬品分譲実績", metrics.has_drug_distribution_record, "様式87の3の1 第(2)項"),
        ("REQ-SUP-04", "供給不足時の代替調剤・疑義照会手順書の策定", metrics.has_shortage_response_protocol, "様式87の3の1 第(3)項"),
        ("REQ-SUP-05", "医薬品卸との原則単品単価交渉", metrics.has_single_item_negotiation, "様式87の3の1 第(4)項"),
        ("REQ-SUP-06", "急配・頻回配送の抑制手順", metrics.has_rush_delivery_prevention, "様式87の3の1 第(5)項"),
        ("REQ-SUP-07", "在庫調整目的の返品抑制手順", metrics.has_return_suppression, "様式87の3の1 第(6)項"),
        ("REQ-SUP-08", "後発医薬品調剤の積極的推進の掲示", metrics.has_generic_promotion_notice, "様式87の3の1 第(7)項")
    ]

    supply_bools_ok = True
    for sid, sname, sval, sref in supply_items:
        s_ok = bool(sval)
        if not s_ok:
            supply_bools_ok = False
            supply_actions.append(f"【様式87-3-1】{sname} が未確認です。")
        supply_reqs.append(RequirementStatus(
            id=sid,
            name=sname,
            category="医薬品供給対応体制(様式87-3-1)",
            requirement_type="supply_87_1",
            current_value_text="適合" if s_ok else "未確認",
            target_value_text="必須",
            is_satisfied=s_ok,
            progress_percentage=100.0 if s_ok else 0.0,
            shortage_text="充足" if s_ok else "要確認",
            official_ref=sref
        ))

    supply_system_qualified = ge_ok and supply_bools_ok
    audit_trail.append(f"【様式87の3の1 供給体制】: {'適合 (全8項目充足)' if supply_system_qualified else '不適合'}")

    # =========================================================================
    # 3. 地域医療への貢献に係る十分な体制（加算2・加算4 共通要件群）
    # =========================================================================
    stock_ok = metrics.stock_drugs_count >= 1200
    struct_reqs.append(RequirementStatus(
        id="REQ-STR-01",
        name="医療用医薬品の備蓄品目数",
        category="十分な体制要件",
        requirement_type="structural",
        current_value_text=f"{metrics.stock_drugs_count:,} 品目",
        target_value_text="1,200 品目以上",
        is_satisfied=stock_ok,
        progress_percentage=round(min(100.0, (metrics.stock_drugs_count / 1200.0) * 100), 1),
        shortage_text="充足" if stock_ok else f"あと {1200 - metrics.stock_drugs_count} 品目不足",
        official_ref="施設基準通知 第8の2(2)イ"
    ))
    if not stock_ok:
        struct_actions.append(f"備蓄医薬品数が {metrics.stock_drugs_count} 品目で基準（1,200品目）に未達です。")

    device_ok = metrics.self_medication_device_count >= 3
    struct_reqs.append(RequirementStatus(
        id="REQ-STR-09",
        name="セルフメディケーション関連機器設置 (8種中3種以上)",
        category="十分な体制要件",
        requirement_type="structural",
        current_value_text=f"{metrics.self_medication_device_count} 種類",
        target_value_text="3 種類以上",
        is_satisfied=device_ok,
        progress_percentage=round(min(100.0, (metrics.self_medication_device_count / 3.0) * 100), 1),
        shortage_text="充足" if device_ok else f"あと {3 - metrics.self_medication_device_count} 種類不足",
        official_ref="施設基準通知 第8の2(2)イ"
    ))
    if not device_ok:
        struct_actions.append(f"セルフメディケーション機器が {metrics.self_medication_device_count} 種で基準（3種以上）に未達です。")

    struct_items = [
        ("REQ-STR-02", "24時間調剤及び在宅対応体制", metrics.has_24h_system, "施設基準通知 第8の2(2)イ"),
        ("REQ-STR-03", "麻薬小売業免許及び管理保管設備", metrics.has_narcotics_license, "施設基準通知 第8の2(2)イ"),
        ("REQ-STR-04", "無菌製剤処理の自店実施又は共同利用体制", metrics.has_sterile_preparation_system, "施設基準通知 第8の2(2)イ"),
        ("REQ-STR-05", "医療DX推進体制（電子処方箋・オン資等）", metrics.has_medical_dx_system, "施設基準通知 第8の2(2)イ"),
        ("REQ-STR-06", "新興感染症第二種指定協定締結等の体制", metrics.has_infection_agreement, "感染症法第38条"),
        ("REQ-STR-07", "要指導・一般用医薬品の備蓄販売 (48薬効群以上)", metrics.otc_drug_categories_count >= 48, "施設基準通知 第8の2(2)イ"),
        ("REQ-STR-08", "個別服薬指導相談カウンターの設置", metrics.has_private_counseling_counter, "施設基準通知 第8の2(2)イ"),
        ("REQ-STR-10", "医療材料・衛生材料供給及び高度管理医療機器許可", metrics.has_medical_equipment_sales_license, "施設基準通知 第8の2(2)イ")
    ]

    other_struct_ok = True
    for stid, stname, stval, stref in struct_items:
        st_ok = bool(stval)
        if not st_ok:
            other_struct_ok = False
            struct_actions.append(f"【十分な体制】{stname} が未整備です。")
        struct_reqs.append(RequirementStatus(
            id=stid,
            name=stname,
            category="十分な体制要件",
            requirement_type="structural",
            current_value_text="適合" if st_ok else "未整備",
            target_value_text="必須",
            is_satisfied=st_ok,
            progress_percentage=100.0 if st_ok else 0.0,
            shortage_text="充足" if st_ok else "要整備",
            official_ref=stref
        ))

    structural_system_qualified = stock_ok and device_ok and other_struct_ok
    audit_trail.append(f"【地域医療貢献に係る十分な体制】: {'適合' if structural_system_qualified else '不適合'}")

    # =========================================================================
    # 4. 様式87の3の2：地域医療貢献実績（全9項目）の補正後評価
    # =========================================================================
    raw_perf_specs = [
        ("REQ-PRF-01", "(1) 時間外加算等・夜間休日等加算等の調剤実績", metrics.rec_1_night_holiday_count, 40, 400, "回", "様式87の3の2 (1)"),
        ("REQ-PRF-02", "(2) 麻薬の調剤実績", metrics.rec_2_narcotics_count, 1, 10, "回", "様式87の3の2 (2)"),
        ("REQ-PRF-03", "(3) 調剤時残薬調整加算及び薬学的有害事象等防止加算等の実績", metrics.rec_3_prevention_adjustment_count, 20, 40, "回", "様式87の3の2 (3)"),
        ("REQ-PRF-04", "(4) 服薬管理指導料1の「イ」及び2の「イ」の算定実績【必須】", metrics.rec_4_guidance_1a_2a_count, 20, 40, "回", "様式87の3の2 (4)"),
        ("REQ-PRF-05", "(5) 外来服薬支援料1の算定実績", metrics.rec_5_outpatient_support_1_count, 1, 12, "回", "様式87の3の2 (5)"),
        ("REQ-PRF-06", "(6) 訪問薬剤管理指導料等の算定実績【加算4必須】", metrics.rec_6_home_visit_count, 24, 24, "回", "様式87の3の2 (6)"),
        ("REQ-PRF-07", "(7) 服薬情報等提供料等の算定実績", metrics.rec_7_info_provision_tr_count, 30, 60, "回", "様式87の3の2 (7)"),
        ("REQ-PRF-08", "(8) 小児特定加算等の算定実績", metrics.rec_8_pediatric_special_count, 1, 1, "回", "様式87の3の2 (8)"),
        ("REQ-PRF-09", "(9) 認定研修取得薬剤師による地域多職種連携会議出席実績", metrics.rec_9_multidisciplinary_conference_count, 1, 5, "回", "様式87の3の2 (9)")
    ]

    tier2_satisfied_count = 0
    tier4_satisfied_count = 0
    
    req_targets_t2: List[int] = []
    req_targets_t4: List[int] = []

    for _, _, _, t2_base, t4_base, _, _ in raw_perf_specs:
        req_targets_t2.append(math.ceil(t2_base * rx_factor))
        req_targets_t4.append(math.ceil(t4_base * rx_factor))

    rec_4_tier2_ok = metrics.rec_4_guidance_1a_2a_count >= req_targets_t2[3]
    rec_4_tier4_ok = metrics.rec_4_guidance_1a_2a_count >= req_targets_t4[3]
    rec_6_tier4_ok = metrics.rec_6_home_visit_count >= req_targets_t4[5]

    for idx, (pid, pname, pval, _, _, punit, pref) in enumerate(raw_perf_specs):
        t2_req = req_targets_t2[idx]
        t4_req = req_targets_t4[idx]
        
        is_t2_ok = pval >= t2_req
        is_t4_ok = pval >= t4_req
        
        if is_t2_ok:
            tier2_satisfied_count += 1
        if is_t4_ok:
            tier4_satisfied_count += 1
            
        prog_t2 = round(min(100.0, (pval / float(t2_req)) * 100), 1)
        shortage = "充足" if is_t2_ok else f"あと {t2_req - pval} {punit}不足"
        
        perf_reqs.append(RequirementStatus(
            id=pid,
            name=pname,
            category="地域医療貢献実績(様式87-3-2)",
            requirement_type="performance_87_2",
            current_value_text=f"{pval:,} {punit}",
            target_value_text=f"基準: {t2_req:,} {punit} (上位: {t4_req:,})",
            is_satisfied=is_t2_ok,
            progress_percentage=prog_t2,
            shortage_text=shortage,
            official_ref=pref
        ))
        if not is_t2_ok:
            perf_actions.append(f"【様式87-3-2】{pname}: 実績 {pval:,}/{t2_req:,} {punit}（{shortage}）")

    # =========================================================================
    # 5. 加算1〜5の告示参照論理式による判定
    # =========================================================================
    is_basic_1 = metrics.dispensing_basic_fee_type == "basic_1"
    is_not_special_b = metrics.dispensing_basic_fee_type != "special_b"

    # RULE-ADD01 (27点): 基本料1 ＋ 供給体制8項目
    rule_add01 = is_basic_1 and supply_system_qualified

    # RULE-ADD02 (59点): 基本料1 ＋ 加算1 ＋ 十分な体制 ＋ (4)>=基準 ＋ 3項目以上
    tier2_perf_qualified = rec_4_tier2_ok and (tier2_satisfied_count >= 3)
    rule_add02 = is_basic_1 and rule_add01 and structural_system_qualified and tier2_perf_qualified

    # RULE-ADD03 (67点): 供給体制8項目 ＋ 体制一部 ＋ 実績7項目以上
    tier3_perf_qualified = tier2_satisfied_count >= 7
    rule_add03 = supply_system_qualified and tier3_perf_qualified

    # RULE-ADD04 (37点): 基本料1又は特別基本料B以外 ＋ 加算1 ＋ 十分な体制 ＋ (4)>=基準 ＋ (6)>=基準 ＋ 3項目以上
    tier4_perf_qualified = rec_4_tier4_ok and rec_6_tier4_ok and (tier4_satisfied_count >= 3)
    rule_add04 = (is_basic_1 or is_not_special_b) and rule_add01 and structural_system_qualified and tier4_perf_qualified

    # RULE-ADD05 (59点): 加算4の体制要件 ＋ 実績7項目以上
    tier5_perf_qualified = tier4_satisfied_count >= 7
    rule_add05 = structural_system_qualified and supply_system_qualified and tier5_perf_qualified

    current_tier = "算定不可"
    tier_code = "none"
    points_earned = 0
    performance_system_qualified = False

    if rule_add03 and not is_basic_1:
        current_tier = "地域支援・医薬品供給対応体制加算3"
        tier_code = "tier_3"
        points_earned = ADD03_POINTS  # 67点
        performance_system_qualified = True
        summary_msg = f"調剤基本料1以外において実績7項目（現在{tier2_satisfied_count}項目）を満たし、加算3（{ADD03_POINTS}点）に適合しています。"
    elif rule_add02:
        current_tier = "地域支援・医薬品供給対応体制加算2"
        tier_code = "tier_2"
        points_earned = ADD02_POINTS  # 59点
        performance_system_qualified = True
        summary_msg = f"調剤基本料1において十分な体制及び実績（必須の項目(4)を含む{tier2_satisfied_count}項目）を満たし、加算2（{ADD02_POINTS}点）に適合しています。"
    elif rule_add05:
        current_tier = "地域支援・医薬品供給対応体制加算5"
        tier_code = "tier_5"
        points_earned = ADD05_POINTS  # 59点
        performance_system_qualified = True
        summary_msg = f"高度な地域医療連携体制及び実績7項目を満たし、加算5（{ADD05_POINTS}点）に適合しています。"
    elif rule_add04 and not is_basic_1:
        current_tier = "地域支援・医薬品供給対応体制加算4"
        tier_code = "tier_4"
        points_earned = ADD04_POINTS  # 37点
        performance_system_qualified = True
        summary_msg = f"特別調剤基本料B以外において十分な体制及び実績（必須の(4)・(6)を含む{tier4_satisfied_count}項目）を満たし、加算4（{ADD04_POINTS}点）に適合しています。"
    elif rule_add01:
        current_tier = "地域支援・医薬品供給対応体制加算1"
        tier_code = "tier_1"
        points_earned = ADD01_POINTS  # 27点
        performance_system_qualified = False
        summary_msg = f"医薬品供給対応体制（様式87の3の1の8項目）を満たし、加算1（{ADD01_POINTS}点）に適合しています。"
    else:
        current_tier = "算定不可"
        tier_code = "none"
        points_earned = 0
        summary_msg = "現在、施設基準の必須要件（医薬品供給対応体制、十分な体制、または実績）に未達項目があります。"

    audit_trail.append(f"【最終判定結果】: {current_tier} ({points_earned}点 / 処方箋)")

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
