import csv
import io
from typing import Dict, Any

def parse_csv_content(content: str) -> Dict[str, Any]:
    """
    レセコン集計CSVを解析し、調剤報酬実績の数値を抽出する。
    """
    reader = csv.reader(io.StringIO(content))
    
    metrics = {
        "monthly_prescriptions": 1200,
        "narcotics_count": 4,
        "home_visit_count": 24,
        "family_pharmacist_count": 42,
        "info_provision_count": 16,
        "preavoid_count": 2,
        "generic_percentage": 85.0
    }
    
    found_keys = []
    
    for row in reader:
        if not row or len(row) < 2:
            continue
        header = row[0].strip()
        val_str = row[1].strip().replace(',', '').replace('%', '').replace('回', '').replace('件', '')
        
        try:
            val = float(val_str)
        except ValueError:
            continue
            
        if '処方箋' in header or '受付回数' in header or '枚数' in header:
            metrics["monthly_prescriptions"] = int(val)
            found_keys.append('処方箋枚数')
        elif '麻薬' in header:
            metrics["narcotics_count"] = int(val)
            found_keys.append('麻薬実績')
        elif '在宅' in header or '訪問' in header or '居宅' in header:
            metrics["home_visit_count"] = int(val)
            found_keys.append('在宅訪問実績')
        elif 'かかりつけ' in header:
            metrics["family_pharmacist_count"] = int(val)
            found_keys.append('かかりつけ指導実績')
        elif '服薬情報' in header or '情報提供' in header or 'トレーシング' in header:
            metrics["info_provision_count"] = int(val)
            found_keys.append('情報提供料実績')
        elif 'プレアボイド' in header or '副作用報告' in header:
            metrics["preavoid_count"] = int(val)
            found_keys.append('プレアボイド実績')
        elif '後発' in header or 'ジェネリック' in header or 'GE' in header:
            metrics["generic_percentage"] = float(val)
            found_keys.append('後発品割合')
            
    return {
        "format": "レセコン月次集計CSV",
        "monthly_prescriptions": metrics["monthly_prescriptions"],
        "narcotics_count": metrics["narcotics_count"],
        "home_visit_count": metrics["home_visit_count"],
        "family_pharmacist_count": metrics["family_pharmacist_count"],
        "info_provision_count": metrics["info_provision_count"],
        "preavoid_count": metrics["preavoid_count"],
        "generic_percentage": metrics["generic_percentage"],
        "detected_items": found_keys
    }
