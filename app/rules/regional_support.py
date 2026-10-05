import math
from typing import List
from app.models.schemas import (
    PharmacyMetrics, RegionalEvaluationResult, RequirementStatus,
    ADD01_POINTS, ADD02_POINTS, ADD03_POINTS, ADD04_POINTS, ADD05_POINTS,
    BASIC_FEE_MASTER
)

def get_default_metrics() -> PharmacyMetrics:
    return PharmacyMetrics()

# 令和8年度 告示規定の対象調剤基本料マスター
# 加算1は特別調剤基本料Bを除く「全区分共通（医薬品安定供給の体制のみ）」
ADD01_ELIGIBLE_FEES = {"basic_1", "basic_2", "basic_3_a", "basic_3_b", "basic_3_c", "special_a"}
ADD02_ELIGIBLE_FEES = {"basic_1"}
ADD03_ELIGIBLE_FEES = {"basic_1"}
ADD04_ELIGIBLE_FEES = {"basic_2", "basic_3_a", "basic_3_b", "basic_3_c", "special_a"}
ADD05_ELIGIBLE_FEES = {"basic_2", "basic_3_a", "basic_3_b", "basic_3_c", "special_a"}

def evaluate_regional_support(metrics: PharmacyMetrics) -> RegionalEvaluationResult:
    """
    厚生労働省 令和8年度（2026年6月1日施行）調剤報酬点数表・告示・施設基準通知
    「地域支援・医薬品供給対応体制加算1〜5」完全適合判定エンジン (v2.4)
    """
    audit_trail: List[str] = []
    supply_reqs: List[RequirementStatus] = []
    struct_reqs: List[RequirementStatus] = []
    perf_reqs: List[RequirementStatus] = []
    
    supply_actions: List[str] = []
    struct_actions: List[str] = []
    perf_actions: List[str] = []

    fee_type = metrics.dispensing_basic_fee_type
    is_basic_1 = (fee_type == "basic_1")
    is_special_b = (fee_type == "special_b")
    is_special_a = (fee_type == "special_a")
    is_non_basic1_eligible = fee_type in ADD04_ELIGIBLE_FEES and not is_basic_1

    # 1. 処方箋受付回数1万回当たりの補正係数算出（様式87の3の2: 最低1万回適用）
    annual_rx = metrics.annual_prescriptions or (metrics.monthly_prescriptions * 12)
    effective_rx = max(10000, annual_rx)
    rx_factor = effective_rx / 10000.0

    eval_mode_text = "定例報告（継続判定: 前年5/1〜当年4/30）" if metrics.evaluation_mode == "continuous" else "新規届出（直近1年間）"
    audit_trail.append(f"・調剤基本料区分: {fee_type} ({'調剤基本料1' if is_basic_1 else ('特別調剤基本料B' if is_special_b else '調剤基本料1以外')})")
    audit_trail.append(f"・判定モード: {eval_mode_text}")
    scale_note = "（※1万回未満のため最低1万回・1.00倍適用）" if annual_rx < 10000 else ""
    audit_trail.append(f"・直近1年間の総処方箋受付回数: {annual_rx:,} 枚（1万回当たり補正係数: {rx_factor:.2f}倍{scale_note}）")
    audit_trail.append(f"・後発品割合 評価期間: {metrics.generic_ratio_period} (規格単位数量ベース)")

    # 特別調剤基本料Bの事前チェック
    if is_special_b:
        audit_trail.append("【基本料制限】特別調剤基本料Bは告示上、加算1〜5のすべての対象外（算定不可: 0点）となります。")

    # 2. 様式87の3の1：医薬品供給対応体制（全加算共通 基礎要件）の判定
    ge_rate = metrics.generic_percentage_special_applied if metrics.temporary_exclusion_enabled else metrics.generic_percentage
    ge_ok = ge_rate >= 85.0
    ge_progress = round((ge_rate / 85.0) * 100, 1)
    ge_shortage = "充足" if ge_ok else f"未達 (不足: {(85.0 - ge_rate):.1f}%)"
    
    supply_reqs.append(RequirementStatus(
        id="REQ-SUP-01",
        name="後発医薬品調剤割合 85%以上（規格単位数量ベース）",
        category="医薬品安定供給要件(様式87-3-1)",
        requirement_type="supply_87_1",
        current_value_text=f"{ge_rate:.1f} % (直近3か月)",
        target_value_text="85.0 %以上",
        is_satisfied=ge_ok,
        progress_percentage=ge_progress,
        shortage_text=ge_shortage,
        official_ref="施設基準告示 第8の2(1)イ / 様式87の3の1 (8)",
        advice="直近3か月間の調剤数量（規格単位数量）に基づく算出（経過措置あり）"
    ))
    if not ge_ok:
        supply_actions.append(f"後発医薬品調剤割合が {ge_rate:.1f}%（基準: 85.0%）で未達です。")

    supply_items = [
        ("REQ-SUP-02", "計画的な調達及び在庫管理の実施", metrics.has_planned_procurement, "様式87の3の1 (1)", "需要予測に基づく計画的発注及び適正な在庫管理体制の確保"),
        ("REQ-SUP-03", "近隣保険薬局への医薬品分譲実績", metrics.has_drug_distribution_record, "様式87の3の1 (2)", "別紙様式4-1等を用いた他薬局（別グループ）への分譲実績・伝票2年間保管"),
        ("REQ-SUP-04", "供給不安時の代替調剤・他薬局案内手順", metrics.has_shortage_response_protocol, "様式87の3の1 (3)", "別紙様式4-2を用いた他薬局案内体制及び処方医への疑義照会・処方変更対応"),
        ("REQ-SUP-05", "重要供給確保医薬品（内・外）の1か月備蓄努力", metrics.has_critical_drugs_stock, "様式87の3の1 (4)", "重要供給確保医薬品のうち内用薬・外用薬の1か月程度備蓄努力"),
        ("REQ-SUP-06", "医薬品卸との原則単品単価交渉", metrics.has_single_item_negotiation, "様式87の3の1 (5)", "医薬品卸売業者との品目ごとの単品単価契約交渉の実施"),
        ("REQ-SUP-07", "過度な頻回配送・急配の依頼自粛", metrics.has_rush_delivery_prevention, "様式87の3の1 (6)", "配送効率化に配慮し、卸への過度な頻回配送・休日夜間配送依頼の抑制"),
        ("REQ-SUP-08", "在庫調整目的の返品自粛", metrics.has_return_suppression, "様式87の3の1 (7)", "温度管理品や在庫調整目的での卸への医薬品返品自粛"),
        ("REQ-SUP-09", "後発医薬品調剤の積極的推進の周知・掲示", metrics.has_generic_promotion_notice, "様式87の3の1 (8)", "薬局内における後発医薬品使用促進の趣旨・体制の患者への周知・掲示"),
        ("REQ-SUP-10", "地域の医療機関・薬局との品目情報共有・連携", metrics.has_regional_drug_collaboration, "様式87の3の1 (9)", "地域医療機関・保険薬局との取扱品目情報共有および事前連携の取り決め")
    ]

    supply_bools_ok = True
    for sid, sname, sval, sref, sadvice in supply_items:
        s_ok = bool(sval)
        if not s_ok:
            supply_bools_ok = False
            supply_actions.append(f"【医薬品供給体制】{sname} が未確認です。")
        supply_reqs.append(RequirementStatus(
            id=sid,
            name=sname,
            category="医薬品安定供給要件(様式87-3-1)",
            requirement_type="supply_87_1",
            current_value_text="適合" if s_ok else "未確認",
            target_value_text="必須",
            is_satisfied=s_ok,
            progress_percentage=100.0 if s_ok else 0.0,
            shortage_text="充足" if s_ok else "未確認",
            official_ref=sref,
            advice=sadvice
        ))

    supply_system_qualified = ge_ok and supply_bools_ok
    audit_trail.append(f"【様式87の3の1 医薬品供給安定体制】: {'適合 (全項目充足)' if supply_system_qualified else '不適合'}")

    # 3. 地域医療への貢献に係る十分な体制（加算2〜5共通の体制要件）
    # (1) 備蓄品目数: 全基本料共通 1,200品目以上
    required_stock = 1200
    stock_ok = metrics.stock_drugs_count >= required_stock
    struct_reqs.append(RequirementStatus(
        id="REQ-STR-01",
        name="医療用医薬品の備蓄品目数（基準: 1,200品目以上）",
        category="十分な体制要件(加算2〜5)",
        requirement_type="structural",
        current_value_text=f"{metrics.stock_drugs_count:,} 品目",
        target_value_text=f"{required_stock:,} 品目以上",
        is_satisfied=stock_ok,
        progress_percentage=round(min(100.0, (metrics.stock_drugs_count / float(required_stock)) * 100), 1),
        shortage_text="充足" if stock_ok else f"未充足 (不足: {required_stock - metrics.stock_drugs_count} 品目)",
        official_ref="施設基準通知 第8の2(2)イ(1) / 様式87の3の2 1.(1)",
        advice="主たる保険医療機関の処方箋のみならず幅広い医療用医薬品の備蓄（1,200品目以上）"
    ))
    if not stock_ok:
        struct_actions.append(f"備蓄医薬品数が {metrics.stock_drugs_count} 品目で基準（{required_stock}品目）に未達です。")

    # (2) 薬局としての年間在宅実績 24回以上 (体制要件: 実績9項目とは別枠)
    home_care_24_ok = bool(metrics.has_pharmacy_home_care_24)
    struct_reqs.append(RequirementStatus(
        id="REQ-STR-02",
        name="薬局としての在宅患者訪問指導実績 年間24回以上",
        category="十分な体制要件(加算2〜5)",
        requirement_type="structural",
        current_value_text="適合 (24回以上/年)" if home_care_24_ok else "未達 (24回未満)",
        target_value_text="年間24回以上",
        is_satisfied=home_care_24_ok,
        progress_percentage=100.0 if home_care_24_ok else 0.0,
        shortage_text="充足" if home_care_24_ok else "要実績確保",
        official_ref="施設基準通知 第8の2(2)イ(3) / 様式87の3の2 1.(3)",
        advice="直近1年間の薬局全体の在宅薬学的管理指導実績（在宅協力薬局としての連携を含む）"
    ))
    if not home_care_24_ok:
        struct_actions.append("薬局全体の在宅実績（年間24回以上）が未達です。")

    # (9) セルフメディケーション機器: 指定機器中3種以上
    device_ok = metrics.self_medication_device_count >= 3
    struct_reqs.append(RequirementStatus(
        id="REQ-STR-09",
        name="セルフメディケーション関連機器設置 (3種類以上)",
        category="十分な体制要件(加算2〜5)",
        requirement_type="structural",
        current_value_text=f"{metrics.self_medication_device_count} 種類",
        target_value_text="3 種類以上",
        is_satisfied=device_ok,
        progress_percentage=round(min(100.0, (metrics.self_medication_device_count / 3.0) * 100), 1),
        shortage_text="充足" if device_ok else f"未充足 (不足: {3 - metrics.self_medication_device_count} 種類)",
        official_ref="施設基準通知 第8の2(2)イ(10) / 様式87の3の2 1.(10)",
        advice="体重計・体温計・血圧計・体組成計・パルスオキシメータ・握力計・骨密度計等の指定機器中3種常設"
    ))
    if not device_ok:
        struct_actions.append(f"セルフメディケーション機器が {metrics.self_medication_device_count} 種で基準（3種以上）に未達です。")

    # 後方互換性ハンドリング
    has_mat_supply = metrics.has_medical_materials_supply if metrics.has_medical_materials_supply is not None else (metrics.has_medical_equipment_sales_license or True)
    has_dev_license = metrics.has_medical_device_sales_license if metrics.has_medical_device_sales_license is not None else (metrics.has_medical_equipment_sales_license or True)

    struct_items = [
        ("REQ-STR-03", "24時間調剤及び在宅対応体制（週45時間以上開局）", metrics.has_24h_system, "施設基準通知 第8の2(2)イ(2) / 様式87の3の2 1.(2)", "開局時間外の調剤・在宅対応体制及び週45時間以上の開局"),
        ("REQ-STR-04", "麻薬小売業者免許及び管理保管設備", metrics.has_narcotics_license, "麻薬及び向精神薬取締法第3条 / 施設基準通知 第8の2(2)イ(1)", "麻薬小売業者免許の取得及び麻薬専用金庫による適正保管"),
        ("REQ-STR-05", "無菌製剤処理の自店実施又は共同利用体制", metrics.has_sterile_preparation_system, "施設基準通知 第8の2(2)イ(1) / 様式87の3の2 1.(1)", "自店クリーンベンチ設置又は他施設無菌調剤室の共同利用体制"),
        ("REQ-STR-06", "医療DX推進体制（電子処方箋・オン資等）", metrics.has_medical_dx_system, "施設基準通知 第8の2(2)イ(5) / 様式87の3の2 1.(5)", "オンライン資格確認・電子処方箋・電子カルテ情報共有サービスの運用"),
        ("REQ-STR-07", "新興感染症第二種指定協定締結等の体制", metrics.has_infection_agreement, "感染症法第38条 / 施設基準通知 第8の2(2)イ(6)", "都道府県との第二種指定医療機関協定（感染症法第38条）等の締結"),
        ("REQ-STR-08", "要指導・一般用医薬品の備蓄販売 (48薬効群を参考に多種取扱)", metrics.otc_drug_categories_count >= 48, "施設基準通知 第8の2(2)イ(10) / 様式87の3の2 1.(10)", "指定48薬効群を参考にした要指導医薬品・一般用医薬品の常時多種備蓄販売"),
        ("REQ-STR-10", "個別服薬指導相談カウンターの設置", metrics.has_private_counseling_counter, "施設基準通知 第8の2(2)イ(9) / 様式87の3の2 1.(9)", "プライバシーに配慮した仕切り付き個別相談カウンターおよび着座対応"),
        ("REQ-STR-11", "医療材料・衛生材料の供給体制", has_mat_supply, "施設基準通知 第8の2(2)イ(1) / 様式87の3の2 1.(1)", "吸引器・胃瘻カテーテル等の医療材料及び衛生材料を供給できる体制"),
        ("REQ-STR-12", "高度管理医療機器等販売業・貸与業の許可", has_dev_license, "医薬品医療機器等法第39条 / 施設基準通知 第8の2(2)イ(1)", "高度管理医療機器等販売業・貸与業の許可取得及び適正管理"),
        ("REQ-STR-13", "敷地内禁煙・たばこ販売禁止・未承認研究用試薬非提供", metrics.has_clean_environment, "施設基準通知 第8の2(2)イ(10)", "敷地内全面禁煙、たばこ販売禁止、薬事未承認の研究用試薬・検査サービスの非提供"),
        ("REQ-STR-14", "管理薬剤師要件（勤務5年・週31h・在籍1年以上）", metrics.has_managing_pharmacist_req, "施設基準通知 第8の2(2)イ(7)", "管理薬剤師の保険薬剤師歴5年以上、週31時間以上勤務、継続在籍1年以上")
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
            category="十分な体制要件(加算2〜5)",
            requirement_type="structural",
            current_value_text="適合" if st_ok else "未整備",
            target_value_text="必須",
            is_satisfied=st_ok,
            progress_percentage=100.0 if st_ok else 0.0,
            shortage_text="充足" if st_ok else "要整備",
            official_ref=stref,
            advice=stadvice
        ))

    # 構造要件：備蓄品目数（全基本料共通で1,200品目以上）
    stock_ok = metrics.stock_drugs_count >= 1200
    structural_system_qualified = stock_ok and home_care_24_ok and device_ok and other_struct_ok

    audit_trail.append(f"【地域医療貢献に係る十分な体制】: {'適合' if structural_system_qualified else '不適合'}")

    # 4. 様式87の3の2：地域医療貢献実績（全9項目）の評価
    # (1)〜(8)は処方箋受付1万回当たり比例（rx_factor）、(9)のみ薬局当たり年間回数（固定）
    raw_perf_specs = [
        ("REQ-PRF-01", "(1) 時間外加算等・夜間休日等加算等の調剤実績", metrics.rec_1_night_holiday_count, 40, 400, "回", "様式87の3の2 (1)", "夜間・休日等の調剤対応実績（処方箋1万回当たり）", True),
        ("REQ-PRF-02", "(2) 麻薬の調剤実績", metrics.rec_2_narcotics_count, 1, 10, "回", "様式87の3の2 (2)", "麻薬処方箋の調剤及び服薬指導実績（処方箋1万回当たり）", True),
        ("REQ-PRF-03", "(3) 調剤時残薬調整加算及び薬学的有害事象等防止加算の実績", metrics.rec_3_prevention_adjustment_count, 20, 40, "回", "様式87の3の2 (3)", "疑義照会による残薬解消・副作用等防止の薬学的介入実績（処方箋1万回当たり）", True),
        ("REQ-PRF-04", "(4) 服薬管理指導料1の「イ」及び2の「イ」の算定実績【加算2・4で必須】", metrics.rec_4_guidance_1a_2a_count, 20, 40, "回", "様式87の3の2 (4)", "手帳持参・かかりつけ薬剤師による服薬指導（処方箋1万回当たり）", True),
        ("REQ-PRF-05", "(5) 外来服薬支援料1の算定実績", metrics.rec_5_outpatient_support_1_count, 1, 12, "回", "様式87の3の2 (5)", "一包化・服薬カレンダー等による服薬整理支援実績（処方箋1万回当たり）", True),
        ("REQ-PRF-06", "(6) 単一建物診療患者1人の在宅薬剤管理の実績【加算4で必須】", metrics.rec_6_home_visit_count, 24, 24, "回", "様式87の3の2 (6)", "単一建物1人に対する在宅訪問指導等の実績（処方箋1万回当たり）", True),
        ("REQ-PRF-07", "(7) 服薬情報等提供料等の算定実績", metrics.rec_7_info_provision_tr_count, 30, 60, "回", "様式87の3の2 (7)", "医師への情報提供・提案（トレーシングレポート等）（処方箋1万回当たり）", True),
        ("REQ-PRF-08", "(8) 小児特定加算等の算定実績", metrics.rec_8_pediatric_special_count, 1, 1, "回", "様式87の3の2 (8)", "6歳未満乳幼児に対するきめ細やかな指導実績（処方箋1万回当たり）", True),
        ("REQ-PRF-09", "(9) 認定研修取得薬剤師による地域多職種連携会議出席実績", metrics.rec_9_multidisciplinary_conference_count, 1, 5, "回", "様式87の3の2 (9)", "地域ケア会議等の多職種連携会議出席（薬局当たり年間実績・比例なし）", False)
    ]

    tier2_satisfied_count = 0
    tier4_satisfied_count = 0
    
    req_targets_t2: List[int] = []
    req_targets_t4: List[int] = []

    for _, _, _, t2_base, t4_base, _, _, _, is_scaled in raw_perf_specs:
        if is_scaled:
            req_targets_t2.append(math.ceil(t2_base * rx_factor))
            req_targets_t4.append(math.ceil(t4_base * rx_factor))
        else:
            # (9) 多職種連携会議は薬局当たり固定
            req_targets_t2.append(t2_base)
            req_targets_t4.append(t4_base)

    rec_4_tier2_ok = metrics.rec_4_guidance_1a_2a_count >= req_targets_t2[3]
    rec_4_tier4_ok = metrics.rec_4_guidance_1a_2a_count >= req_targets_t4[3]
    rec_6_tier4_ok = metrics.rec_6_home_visit_count >= req_targets_t4[5]

    for idx, (pid, pname, pval, _, _, punit, pref, padvice, is_scaled) in enumerate(raw_perf_specs):
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
        prog = round(min(100.0, (pval / float(target_display)) * 100), 1) if target_display > 0 else 100.0
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

    # 5. 加算1〜5の告示参照論理式による判定
    
    # 加算1 (27点): 特別調剤基本料Bを除く全基本料 ＋ 医薬品供給対応体制（様式87の3の1）充足
    rule_add01 = (not is_special_b) and supply_system_qualified

    # 加算2 (59点): 調剤基本料1 ＋ 加算1の施設基準 ＋ 十分な体制（1200品目等） ＋ (4)を含む3項目以上
    tier2_perf_qualified = rec_4_tier2_ok and (tier2_satisfied_count >= 3)
    rule_add02 = is_basic_1 and supply_system_qualified and structural_system_qualified and tier2_perf_qualified

    # 加算3 (67点): 調剤基本料1 ＋ 加算1の施設基準 ＋ 十分な体制（1200品目等） ＋ 7項目以上（(4)は単独必須ではない）
    tier3_perf_qualified = (tier2_satisfied_count >= 7)
    rule_add03 = is_basic_1 and supply_system_qualified and structural_system_qualified and tier3_perf_qualified

    # 加算4 (37点): 調剤基本料1以外（特別B除く） ＋ 加算1の施設基準 ＋ 十分な体制（1200品目等） ＋ (4)及び(6)を含む3項目以上
    tier4_perf_qualified = rec_4_tier4_ok and rec_6_tier4_ok and (tier4_satisfied_count >= 3)
    rule_add04 = is_non_basic1_eligible and supply_system_qualified and structural_system_qualified and tier4_perf_qualified

    # 加算5 (59点): 調剤基本料1以外（特別B除く） ＋ 加算1の施設基準 ＋ 十分な体制（1200品目等） ＋ 7項目以上（(4)(6)は単独必須ではない）
    tier5_perf_qualified = (tier4_satisfied_count >= 7)
    rule_add05 = is_non_basic1_eligible and supply_system_qualified and structural_system_qualified and tier5_perf_qualified

    # 最終加算の決定（最も有利な点数を選択）
    current_tier = "算定不可"
    tier_code = "none"
    points_earned = 0
    performance_system_qualified = False

    if is_special_b:
        current_tier = "算定不可"
        tier_code = "none"
        points_earned = 0
        summary_msg = "特別調剤基本料Bを算定している保険薬局は、告示規定により加算1〜5のいずれも算定できません。"
    elif is_basic_1:
        if rule_add03:
            current_tier = "地域支援・医薬品供給対応体制加算3"
            tier_code = "tier_3"
            points_earned = ADD03_POINTS  # 67点
            performance_system_qualified = True
            summary_msg = f"調剤基本料1において医薬品供給体制・十分な体制（1,200品目等）及び実績7項目（現在{tier2_satisfied_count}項目）を満たし、加算3（{ADD03_POINTS}点）に適合しています。"
        elif rule_add02:
            current_tier = "地域支援・医薬品供給対応体制加算2"
            tier_code = "tier_2"
            points_earned = ADD02_POINTS  # 59点
            performance_system_qualified = True
            summary_msg = f"調剤基本料1において医薬品供給体制・十分な体制（1,200品目等）及び実績（項目(4)を含む{tier2_satisfied_count}項目）を満たし、加算2（{ADD02_POINTS}点）に適合しています。"
        elif rule_add01:
            current_tier = "地域支援・医薬品供給対応体制加算1"
            tier_code = "tier_1"
            points_earned = ADD01_POINTS  # 27点
            performance_system_qualified = False
            summary_msg = f"調剤基本料1において医薬品供給対応体制（様式87の3の1）を満たし、加算1（{ADD01_POINTS}点）に適合しています。"
        else:
            current_tier = "算定不可"
            tier_code = "none"
            points_earned = 0
            summary_msg = "現在、医薬品供給対応体制（後発品85%以上および供給8項目）に未達項目があります。"
    else: # 基本料1以外 (basic_2, basic_3, special_a等)
        pts_add05 = round(ADD05_POINTS * 0.1) if is_special_a else ADD05_POINTS
        pts_add04 = round(ADD04_POINTS * 0.1) if is_special_a else ADD04_POINTS
        pts_add01 = round(ADD01_POINTS * 0.1) if is_special_a else ADD01_POINTS

        if rule_add05:
            current_tier = "地域支援・医薬品供給対応体制加算5"
            tier_code = "tier_5"
            points_earned = pts_add05  # 59点 (特別Aは6点)
            performance_system_qualified = True
            summary_msg = f"調剤基本料1以外において医薬品供給体制・十分な体制（1,200品目等）及び上位実績7項目（現在{tier4_satisfied_count}項目）を満たし、加算5（{pts_add05}点）に適合しています。"
        elif rule_add04:
            current_tier = "地域支援・医薬品供給対応体制加算4"
            tier_code = "tier_4"
            points_earned = pts_add04  # 37点 (特別Aは4点)
            performance_system_qualified = True
            summary_msg = f"調剤基本料1以外において医薬品供給体制・十分な体制（1,200品目等）及び実績（(4)及び(6)を含む{tier4_satisfied_count}項目）を満たし、加算4（{pts_add04}点）に適合しています。"
        elif rule_add01:
            current_tier = "地域支援・医薬品供給対応体制加算1"
            tier_code = "tier_1"
            points_earned = pts_add01  # 27点 (特別Aは3点)
            performance_system_qualified = False
            summary_msg = f"調剤基本料1以外において医薬品供給対応体制（様式87の3の1）を満たし、加算1（{pts_add01}点）に適合しています。"
        else:
            current_tier = "算定不可"
            tier_code = "none"
            points_earned = 0
            summary_msg = "現在、医薬品供給対応体制（後発品85%以上および供給8項目）に未達項目があります。"

    # 調剤基本料 基礎点数および減算の精密判定（注3, 注4, 注8, 注15, 下限3点ルール）
    fee_info = BASIC_FEE_MASTER.get(fee_type, {"name": "調剤基本料1", "points": 47})
    b_name = fee_info.get("name", "調剤基本料1")
    b_base_pts = fee_info.get("points", 47)
    current_fee_pts = float(b_base_pts)
    deductions_applied: List[str] = []

    # (1) 注4：未妥結・かかりつけ機能未実施減算（50/100）
    service_threshold = 100 if (is_special_a or is_special_b) else 10
    is_basic_services_insufficient = (metrics.basic_services_count < service_threshold)
    is_note4_applicable = metrics.has_unsettled_or_unreported_discount or is_basic_services_insufficient

    if is_note4_applicable:
        current_fee_pts = round(current_fee_pts * 0.5)
        reason = "未妥結/未報告" if metrics.has_unsettled_or_unreported_discount else f"基本的業務実績不足({metrics.basic_services_count}回 < 基準{service_threshold}回)"
        deductions_applied.append(f"注4減算 (50/100算定: {reason})")
        audit_trail.append(f"・【調剤基本料減算】注4適用: 所定点数の50/100に減算 → {int(current_fee_pts)}点 ({reason})")

    # (2) 注3：複数医療機関処方箋同時受付（2回目以降受付: 80/100）
    if metrics.is_multiple_reception_second:
        current_fee_pts = round(current_fee_pts * 0.8)
        deductions_applied.append("注3減算 (複数医療機関同時受付2回目以降: 80/100算定)")
        audit_trail.append(f"・【調剤基本料減算】注3適用: 2回目以降受付80/100に減算 → {int(current_fee_pts)}点")

    # (3) 注15：門前薬局等立地依存減算（▲15点）
    if metrics.is_new_location_dependent_pharmacy:
        current_fee_pts = current_fee_pts - 15.0
        deductions_applied.append("注15減算 (新設立地依存/門前薬局減算: ▲15点)")
        audit_trail.append(f"・【調剤基本料減算】注15適用: 新設立地依存減算 ▲15点 → {int(current_fee_pts)}点")

    # (4) 注8：後発医薬品調剤割合減算（50%以下かつ月600回超: ▲5点）
    is_monthly_rx_over_600 = (metrics.monthly_prescriptions > 600 or annual_rx > 7200)
    if ge_rate <= 50.0 and is_monthly_rx_over_600:
        current_fee_pts = current_fee_pts - 5.0
        deductions_applied.append(f"注8減算 (後発品調剤割合5割以下({ge_rate:.1f}%): ▲5点)")
        audit_trail.append(f"・【調剤基本料減算】注8適用: 後発医薬品調剤割合50%以下 ▲5点 → {int(current_fee_pts)}点")

    # (5) 下限ルール：減算適用後の点数が3点未満の場合は最低3点を算定
    if current_fee_pts < 3.0:
        current_fee_pts = 3.0
        audit_trail.append("・【調剤基本料下限】減算適用後の点数が3点未満のため、告示規定に基づき最低保障 3点 を算定します。")

    b_final_pts = int(current_fee_pts)
    total_pts = b_final_pts + points_earned

    audit_trail.append(f"【最終判定結果】: {current_tier} ({points_earned}点 / 処方箋)")
    fee_desc = f"{b_name} [基礎{b_base_pts}点 → 最終{b_final_pts}点]" if deductions_applied else f"{b_name} ({b_final_pts}点)"
    audit_trail.append(f"【基本料＋加算合計】: {fee_desc} ＋ {current_tier} ({points_earned}点) ＝ 合計 {total_pts}点 / 処方箋")

    return RegionalEvaluationResult(
        current_tier=current_tier,
        tier_code=tier_code,
        points_earned=points_earned,
        basic_fee_name=b_name,
        basic_fee_base_points=b_base_pts,
        basic_fee_final_points=b_final_pts,
        basic_fee_deductions_applied=deductions_applied,
        total_basic_and_regional_points=total_pts,
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


