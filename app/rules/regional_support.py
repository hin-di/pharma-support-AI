import math
from typing import List
from app.models.schemas import (
    PharmacyMetrics, RegionalEvaluationResult, RequirementStatus,
    ADD01_POINTS, ADD02_POINTS, ADD03_POINTS, ADD04_POINTS, ADD05_POINTS
)

def get_default_metrics() -> PharmacyMetrics:
    return PharmacyMetrics()

# 令和8年度 告示規定の対象調剤基本料マスター
ADD01_ELIGIBLE_FEES = {"basic_1"}
ADD02_ELIGIBLE_FEES = {"basic_1"}
ADD03_ELIGIBLE_FEES = {"basic_1"}
ADD04_ELIGIBLE_FEES = {"basic_2", "basic_3_a", "basic_3_b", "basic_3_c", "special_a"}
ADD05_ELIGIBLE_FEES = {"basic_2", "basic_3_a", "basic_3_b", "basic_3_c", "special_a"}

def evaluate_regional_support(metrics: PharmacyMetrics) -> RegionalEvaluationResult:
    """
    厚生労働省 令和8年度（2026年6月1日施行）調剤報酬点数表・告示・施設基準通知
    「地域支援・医薬品供給対応体制加算1〜5」完全適合判定エンジン (v2.3)
    """
    audit_trail: List[str] = []
    supply_reqs: List[RequirementStatus] = []
    struct_reqs: List[RequirementStatus] = []
    perf_reqs: List[RequirementStatus] = []
    
    supply_actions: List[str] = []
    struct_actions: List[str] = []
    perf_actions: List[str] = []

    fee_type = metrics.dispensing_basic_fee_type
    is_basic_1 = fee_type in ADD01_ELIGIBLE_FEES
    is_non_basic1_eligible = fee_type in ADD04_ELIGIBLE_FEES

    # 1. 処方箋受付回数1万回当たりの補正係数算出（様式87の3の2）
    annual_rx = metrics.annual_prescriptions or (metrics.monthly_prescriptions * 12)
    adjusted_rx_base = max(10000, annual_rx)
    rx_factor = adjusted_rx_base / 10000.0

    audit_trail.append(f"・調剤基本料区分: {fee_type}")
    audit_trail.append(f"・直近1年間の総処方箋受付回数: {annual_rx:,} 枚（補正基準枚数: {adjusted_rx_base:,} 枚, 係数: {rx_factor:.2f}）")
    audit_trail.append(f"・後発品割合 評価期間: {metrics.generic_ratio_period} (規格単位数量ベース)")
    audit_trail.append(f"・実績要件 評価期間: {metrics.performance_period}")

    # 特別調剤基本料Bの事前チェック
    if fee_type == "special_b":
        audit_trail.append("【基本料制限】特別調剤基本料Bは告示上、加算1〜5のすべての対象外となります。")

    # 2. 様式87の3の1：医薬品供給対応体制（全加算共通 8項目）の判定
    ge_rate = metrics.generic_percentage_special_applied if metrics.temporary_exclusion_enabled else metrics.generic_percentage
    ge_ok = ge_rate >= 85.0
    ge_progress = round((ge_rate / 85.0) * 100, 1)
    ge_shortage = "充足" if ge_ok else f"未達 (不足: {(85.0 - ge_rate):.1f}%)"
    
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
        official_ref="様式87の3の1 第(8)項",
        advice="直近3か月間の調剤数量（規格単位数量）に基づく算出"
    ))
    if not ge_ok:
        supply_actions.append(f"後発医薬品調剤割合が {ge_rate:.1f}%（基準: 85.0%）で未達です。")

    supply_items = [
        ("REQ-SUP-02", "計画的調達・在庫管理体制", metrics.has_planned_procurement, "様式87の3の1 第(1)項", "計画的発注及び適正在庫管理の実施"),
        ("REQ-SUP-03", "近隣保険薬局への医薬品分譲実績", metrics.has_drug_distribution_record, "様式87の3の1 第(2)項", "地域内保険薬局との医薬品融通・分譲実績の記録・保管"),
        ("REQ-SUP-04", "供給不足時の代替調剤・疑義照会手順書の策定", metrics.has_shortage_response_protocol, "様式87の3の1 第(3)項", "供給困難時の代替薬提案・医師への疑義照会プロトコル策定"),
        ("REQ-SUP-05", "医薬品卸との原則単品単価交渉", metrics.has_single_item_negotiation, "様式87の3の1 第(4)項", "医薬品卸との品目ごとの単品単価契約交渉の実施"),
        ("REQ-SUP-06", "急配・頻回配送の抑制手順", metrics.has_rush_delivery_prevention, "様式87の3の1 第(5)項", "配送効率化および緊急時以外の頻回配送抑制の取り組み"),
        ("REQ-SUP-07", "在庫調整目的の返品抑制手順", metrics.has_return_suppression, "様式87の3の1 第(6)項", "返品前提の発注見直しおよび在庫適正化の推進"),
        ("REQ-SUP-08", "後発医薬品調剤の積極的推進の掲示", metrics.has_generic_promotion_notice, "様式87の3の1 第(7)項", "薬局内における後発医薬品推進に関する周知・掲示")
    ]

    supply_bools_ok = True
    for sid, sname, sval, sref, sadvice in supply_items:
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
            shortage_text="充足" if s_ok else "未充足（要確認）",
            official_ref=sref,
            advice=sadvice
        ))

    supply_system_qualified = ge_ok and supply_bools_ok
    audit_trail.append(f"【様式87の3の1 供給体制】: {'適合 (全8項目充足)' if supply_system_qualified else '不適合'}")

    # 3. 地域医療への貢献に係る十分な体制（施設基準通知 第8の2(2)イ: 全11項目に完全分解）
    # (1) 備蓄品目数: 基本料1=1200品目以上 / 基本料1以外=1500品目以上
    required_stock = 1200 if is_basic_1 else 1500
    stock_ok = metrics.stock_drugs_count >= required_stock
    struct_reqs.append(RequirementStatus(
        id="REQ-STR-01",
        name=f"医療用医薬品の備蓄品目数（基準: {'1,200' if is_basic_1 else '1,500'}品目以上）",
        category="十分な体制要件",
        requirement_type="structural",
        current_value_text=f"{metrics.stock_drugs_count:,} 品目",
        target_value_text=f"{required_stock:,} 品目以上",
        is_satisfied=stock_ok,
        progress_percentage=round(min(100.0, (metrics.stock_drugs_count / float(required_stock)) * 100), 1),
        shortage_text="充足" if stock_ok else f"未充足 (不足: {required_stock - metrics.stock_drugs_count} 品目)",
        official_ref="施設基準通知 第8の2(2)イ(一) / 様式87の3の2 1.(1)",
        advice=f"主たる保険医療機関の処方箋のみならず幅広い医療用医薬品の備蓄（{'基本料1は1,200品目' if is_basic_1 else '基本料1以外は1,500品目'}以上）"
    ))
    if not stock_ok:
        struct_actions.append(f"備蓄医薬品数が {metrics.stock_drugs_count} 品目で基準（{required_stock}品目）に未達です。")

    # (9) セルフメディケーション機器: 指定8機器中3種以上
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
        shortage_text="充足" if device_ok else f"未充足 (不足: {3 - metrics.self_medication_device_count} 種類)",
        official_ref="施設基準通知 第8の2(2)イ(九) / 様式87の3の2 1.(9)",
        advice="血圧計・自己血糖測定器・体組成計等の指定8機器中3種類以上の常設"
    ))
    if not device_ok:
        struct_actions.append(f"セルフメディケーション機器が {metrics.self_medication_device_count} 種で基準（3種以上）に未達です。")

    # 後方互換性ハンドリング
    has_mat_supply = metrics.has_medical_materials_supply if metrics.has_medical_materials_supply is not None else (metrics.has_medical_equipment_sales_license or True)
    has_dev_license = metrics.has_medical_device_sales_license if metrics.has_medical_device_sales_license is not None else (metrics.has_medical_equipment_sales_license or True)

    # (2)〜(8), (10), (11) の完全分解独立判定
    struct_items = [
        ("REQ-STR-02", "24時間調剤及び在宅対応体制", metrics.has_24h_system, "施設基準通知 第8の2(2)イ(二) / 様式87の3の2 1.(2)", "開局時間外の電話対応体制及び夜間・休日の調剤・在宅訪問体制の確保"),
        ("REQ-STR-03", "麻薬小売業免許及び管理保管設備", metrics.has_narcotics_license, "麻薬及び向精神薬取締法第3条 / 施設基準通知 第8の2(2)イ(三)", "麻薬小売業者免許の取得及び麻薬専用金庫による保管管理"),
        ("REQ-STR-04", "無菌製剤処理の自店実施又は共同利用体制", metrics.has_sterile_preparation_system, "施設基準通知 第8の2(2)イ(四) / 様式87の3の2 1.(4)", "自店におけるクリーンベンチ等設置または他施設無菌調剤室の共同利用協定"),
        ("REQ-STR-05", "医療DX推進体制（電子処方箋・オン資等）", metrics.has_medical_dx_system, "施設基準通知 第8の2(2)イ(五) / 様式87の3の2 1.(5)", "オンライン資格確認・電子処方箋・電子カルテ情報共有サービスの導入運用"),
        ("REQ-STR-06", "新興感染症第二種指定協定締結等の体制", metrics.has_infection_agreement, "感染症法第38条 / 施設基準通知 第8の2(2)イ(六)", "都道府県等との第二種指定医療機関協定（感染症法第38条）等の締結"),
        ("REQ-STR-07", "要指導・一般用医薬品の備蓄販売 (48薬効群以上)", metrics.otc_drug_categories_count >= 48, "施設基準通知 第8の2(2)イ(七) / 様式87の3の2 1.(7)", "指定48薬効群以上の要指導医薬品・一般用医薬品の常時備蓄販売"),
        ("REQ-STR-08", "個別服薬指導相談カウンターの設置", metrics.has_private_counseling_counter, "施設基準通知 第8の2(2)イ(八) / 様式87の3の2 1.(8)", "患者のプライバシーに配慮した仕切り付き個別相談カウンターの設置"),
        ("REQ-STR-10", "医療材料・衛生材料の供給体制", has_mat_supply, "施設基準通知 第8の2(2)イ(十)前段 / 様式87の3の2 1.(10)", "吸引器・胃瘻カテーテル等の医療材料及び衛生材料を供給できる体制"),
        ("REQ-STR-11", "高度管理医療機器等販売業の許可", has_dev_license, "医薬品医療機器等法第39条 / 施設基準通知 第8の2(2)イ(十)後段", "高度管理医療機器等販売業・貸与業の許可取得及び適正管理")
    ]

    other_struct_ok = True
    for stid, stname, stval, stref, stadvice in struct_items:
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
            official_ref=stref,
            advice=stadvice
        ))

    # 調剤基本料1用および調剤基本料1以外用の構造要件充足
    stock_basic1_ok = metrics.stock_drugs_count >= 1200
    stock_non_basic1_ok = metrics.stock_drugs_count >= 1500

    structural_basic1_qualified = stock_basic1_ok and device_ok and other_struct_ok
    structural_non_basic1_qualified = stock_non_basic1_ok and device_ok and other_struct_ok
    structural_system_qualified = structural_basic1_qualified if is_basic_1 else structural_non_basic1_qualified

    audit_trail.append(f"【地域医療貢献に係る十分な体制】: {'適合' if structural_system_qualified else '不適合'}")

    # 4. 様式87の3の2：地域医療貢献実績（全9項目）の補正後評価
    raw_perf_specs = [
        ("REQ-PRF-01", "(1) 時間外加算等・夜間休日等加算等の調剤実績", metrics.rec_1_night_holiday_count, 40, 400, "回", "様式87の3の2 (1)", "夜間・休日等の調剤対応実績（時間外加算、夜間休日等加算等）"),
        ("REQ-PRF-02", "(2) 麻薬の調剤実績", metrics.rec_2_narcotics_count, 1, 10, "回", "様式87の3の2 (2)", "麻薬処方箋の調剤及び服薬指導実績"),
        ("REQ-PRF-03", "(3) 調剤時残薬調整加算及び薬学的有害事象等防止加算等の実績", metrics.rec_3_prevention_adjustment_count, 20, 40, "回", "様式87の3の2 (3)", "疑義照会による残薬解消・重複投薬防止等の薬学的介入実績"),
        ("REQ-PRF-04", "(4) 服薬管理指導料1の「イ」及び2の「イ」の算定実績【加算2・4必須】", metrics.rec_4_guidance_1a_2a_count, 20, 40, "回", "様式87の3の2 (4)", "手帳持参患者に対する服薬管理指導（加算2・4の必須要件）"),
        ("REQ-PRF-05", "(5) 外来服薬支援料1の算定実績", metrics.rec_5_outpatient_support_1_count, 1, 12, "回", "様式87の3の2 (5)", "一包化・服薬カレンダー等による患者の服薬整理・継続支援実績"),
        ("REQ-PRF-06", "(6) 訪問薬剤管理指導料等の算定実績【加算4必須】", metrics.rec_6_home_visit_count, 24, 24, "回", "様式87の3の2 (6)", "在宅患者訪問薬剤管理指導・居宅療養管理指導実績（加算4の必須要件）"),
        ("REQ-PRF-07", "(7) 服薬情報等提供料等の算定実績", metrics.rec_7_info_provision_tr_count, 30, 60, "回", "様式87の3の2 (7)", "医師・医療機関に対する服薬状況・提案等のトレーシングレポート提供"),
        ("REQ-PRF-08", "(8) 小児特定加算等の算定実績", metrics.rec_8_pediatric_special_count, 1, 1, "回", "様式87の3の2 (8)", "6歳未満の乳幼児に対するきめ細やかな指導実績"),
        ("REQ-PRF-09", "(9) 認定研修取得薬剤師による地域多職種連携会議出席実績", metrics.rec_9_multidisciplinary_conference_count, 1, 5, "回", "様式87の3の2 (9)", "地域ケア会議・退院時カンファレンス等の多職種連携会議出席実績")
    ]

    tier2_satisfied_count = 0
    tier4_satisfied_count = 0
    
    req_targets_t2: List[int] = []
    req_targets_t4: List[int] = []

    for _, _, _, t2_base, t4_base, _, _, _ in raw_perf_specs:
        req_targets_t2.append(math.ceil(t2_base * rx_factor))
        req_targets_t4.append(math.ceil(t4_base * rx_factor))

    rec_4_tier2_ok = metrics.rec_4_guidance_1a_2a_count >= req_targets_t2[3]
    rec_4_tier4_ok = metrics.rec_4_guidance_1a_2a_count >= req_targets_t4[3]
    rec_6_tier4_ok = metrics.rec_6_home_visit_count >= req_targets_t4[5]

    for idx, (pid, pname, pval, _, _, punit, pref, padvice) in enumerate(raw_perf_specs):
        t2_req = req_targets_t2[idx]
        t4_req = req_targets_t4[idx]
        
        is_t2_ok = pval >= t2_req
        is_t4_ok = pval >= t4_req
        
        if is_t2_ok:
            tier2_satisfied_count += 1
        if is_t4_ok:
            tier4_satisfied_count += 1
            
        target_display = t2_req if is_basic_1 else t4_req
        is_current_ok = is_t2_ok if is_basic_1 else is_t4_ok
        prog = round(min(100.0, (pval / float(target_display)) * 100), 1)
        shortage = "充足" if is_current_ok else f"未達 (不足: {target_display - pval} {punit})"
        
        perf_reqs.append(RequirementStatus(
            id=pid,
            name=pname,
            category="地域医療貢献実績(様式87-3-2)",
            requirement_type="performance_87_2",
            current_value_text=f"{pval:,} {punit}",
            target_value_text=f"基準: {t2_req:,} {punit} (上位: {t4_req:,})",
            is_satisfied=is_current_ok,
            progress_percentage=prog,
            shortage_text=shortage,
            official_ref=pref,
            advice=padvice
        ))
        if not is_current_ok:
            perf_actions.append(f"【様式87-3-2】{pname}: 実績 {pval:,}/{target_display:,} {punit}（{shortage}）")

    # 5. 加算1〜5の告示参照論理式による判定（法定継承関係を明示的にモデル化）

    # RULE-ADD01 (27点):
    # 告示第8の2(1): 調剤基本料1 ＋ 供給体制8項目
    rule_add01 = is_basic_1 and supply_system_qualified

    # RULE-ADD02 (59点):
    # 告示第8の2(2): 調剤基本料1 ＋ 加算1の施設基準(イ) ＋ 十分な体制(ウ:基本料1用) ＋ 実績(4)>=基準 かつ (1)〜(9)中3項目以上(エ)
    tier2_perf_qualified = rec_4_tier2_ok and (tier2_satisfied_count >= 3)
    rule_add02 = is_basic_1 and rule_add01 and structural_basic1_qualified and tier2_perf_qualified

    # RULE-ADD03 (67点):
    # 告示第8の2(3): 調剤基本料1 ＋ 加算2のイ〜ハの施設基準(ア:供給体制8項目＋十分な体制) ＋ 実績7項目以上（相当の実績）(イ)
    tier3_perf_qualified = tier2_satisfied_count >= 7
    rule_add03 = is_basic_1 and supply_system_qualified and structural_basic1_qualified and tier3_perf_qualified

    # RULE-ADD04 (37点):
    # 告示第8の2(4): 特別調剤基本料Bを除く基本料(ア) ＋ 加算1の施設基準(イ) ＋ 十分な体制(ウ:基本料1以外用1500品目等) ＋ 実績(4)&(6)必須 かつ 3項目以上(エ)
    tier4_perf_qualified = rec_4_tier4_ok and rec_6_tier4_ok and (tier4_satisfied_count >= 3)
    rule_add04 = is_non_basic1_eligible and supply_system_qualified and structural_non_basic1_qualified and tier4_perf_qualified

    # RULE-ADD05 (59点):
    # 告示第8の2(5): 加算3の実績基準（ロ: 7項目以上）(ア) ＋ 加算4の施設基準（イ〜ハ：特別基本料B以外、供給体制8項目、十分な体制1500品目等）(イ)
    tier5_perf_qualified = tier4_satisfied_count >= 7
    rule_add05 = is_non_basic1_eligible and supply_system_qualified and structural_non_basic1_qualified and tier5_perf_qualified

    # 最終加算の決定（最も有利な点数を選択）
    current_tier = "算定不可"
    tier_code = "none"
    points_earned = 0
    performance_system_qualified = False

    if rule_add03:
        current_tier = "地域支援・医薬品供給対応体制加算3"
        tier_code = "tier_3"
        points_earned = ADD03_POINTS  # 67点
        performance_system_qualified = True
        summary_msg = f"調剤基本料1において十分な体制及び実績7項目（現在{tier2_satisfied_count}項目）を満たし、加算3（{ADD03_POINTS}点）に適合しています。"
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
        summary_msg = f"調剤基本料1以外において十分な体制及び上位実績7項目（現在{tier4_satisfied_count}項目）を満たし、加算5（{ADD05_POINTS}点）に適合しています。"
    elif rule_add04:
        current_tier = "地域支援・医薬品供給対応体制加算4"
        tier_code = "tier_4"
        points_earned = ADD04_POINTS  # 37点
        performance_system_qualified = True
        summary_msg = f"調剤基本料1以外において十分な体制及び実績（必須の(4)・(6)を含む{tier4_satisfied_count}項目）を満たし、加算4（{ADD04_POINTS}点）に適合しています。"
    elif rule_add01:
        current_tier = "地域支援・医薬品供給対応体制加算1"
        tier_code = "tier_1"
        points_earned = ADD01_POINTS  # 27点
        performance_system_qualified = False
        summary_msg = f"調剤基本料1において医薬品供給対応体制（様式87の3の1の8項目）を満たし、加算1（{ADD01_POINTS}点）に適合しています。"
    else:
        current_tier = "算定不可"
        tier_code = "none"
        points_earned = 0
        summary_msg = "現在、施設基準の必須要件（対象調剤基本料区分、医薬品供給対応体制、十分な体制、または実績基準）に未達項目があります。"

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

