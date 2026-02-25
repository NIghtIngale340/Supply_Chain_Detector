import json
import os
from datetime import datetime

REQUIRED_FIELD = ["package_name", "registry", "label"]

VALID_REGISTERS = {"npm", "pypi"}

def validate_record(record: dict) -> tuple[bool, str]:
    for field in REQUIRED_FIELD:
        if field not in record or not record[field]:
            return False, f"Missing required field: {field}"
    
    if record["registry"] not in VALID_REGISTERS:
        return False, f"Invalid registry: {record['registry']}"
    
    if record["label"] not in ["benign", "malicious"]:
        return False, f"Invalid label: {record['label']}"
    
    return True, "Valid record"

def normalize_records(record: dict) -> dict:
    return {
        "package_name": record.get("package_name", "").strip().lower(),
        "registry":     record.get("registry", "").strip().lower(),
        "label":        record.get("label", "").strip().lower(),
        "version":      record.get("version", "").strip(),
        "source_url":   record.get("source_url") or record.get("source_reference", "").strip(),
        "collected_at": record.get("collected_at", datetime.now().isoformat()),
    }

def normalize_dataset(input_file: str, output_file: str) -> dict:
    with open(input_file, "r", encoding="utf-8") as f:
        raw_records = json.load(f)
    valid_records = []
    quarantined = []

    for record in raw_records:
        normalized = normalize_records(record)
        is_valid, reason = validate_record(normalized)
        if is_valid:
            valid_records.append(normalized)
        else:
            quarantined.append({
                "record": normalized,
                "reason": reason
            })

    valid_records.sort(key=lambda r: r["package_name"])


    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)
    
    stats = {
        "input_count": len(raw_records),
        "valid_count": len(valid_records),
        "quarantined_count": len(quarantined),
    }

    print(f"  {stats['valid_count']}/{stats['input_count']} valid, "
          f"{stats['quarantined_count']} quarantined → {output_file}")
    return stats


if __name__ == "__main__":
    print("Normalizing malicious datasets...")
    normalize_dataset(
        "data/processed/backstabbers_seed.json", "data/processed/malicious_normalized.json")  

    print("Normalizing benign dataset...")
    normalize_dataset(
        "data/processed/benign_sample.json",
        "data/processed/benign_normalized.json",
    )
  
    print("\nDone! Both normalized files created.")



    
    


