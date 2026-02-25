import json
import os
from datetime import datetime



MALICIOUS_SEED = [
    {
        "package_name": "colourama",
        "registry": "pypi",
        "source_reference": "https://github.com/IQTLabs/Backstabbers-Knife-Collection",
        "label": "malicious",
        "notes": "Typosquatting of colorama",
    },
    {
        "package_name": "python-dateutils",
        "registry": "pypi",
        "source_reference": "https://github.com/IQTLabs/Backstabbers-Knife-Collection",
        "label": "malicious",
        "notes": "Typosquatting of python-dateutil",
    },
    {
        "package_name": "jeIlyfish",
        "registry": "pypi",
        "source_reference": "https://github.com/IQTLabs/Backstabbers-Knife-Collection",
        "label": "malicious",
        "notes": "Typosquatting of jellyfish (capital I instead of l)",
    },
    {
        "package_name": "event-stream",
        "registry": "npm",
        "source_reference": "https://blog.npmjs.org/post/180565383195",
        "label": "malicious",
        "notes": "Compromised dependency flatmap-stream injected",
    },
    {
        "package_name": "ua-parser-js",
        "registry": "npm",
        "source_reference": "https://github.com/nicedoc/ua-parser-js-compromised",
        "label": "malicious",
        "notes": "Hijacked maintainer account published crypto-miner",
    },
]



def download_backstabbers_dataset() -> None:

    output_dir = "data/processed"
    output_file = os.path.join(output_dir, "backstabbers_seed.json")

    os.makedirs(output_dir, exist_ok=True)

    collected_At = datetime.utcnow().isoformat()

    records = []
    seen = set()

    for entry in MALICIOUS_SEED:
        key = (entry["package_name"], entry["registry"])
        if key in seen:
            continue
        seen.add(key)
        record = {
            **entry,
            "collected_at": collected_At,
        }
        records.append(record)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        
    print(f"Wrote {len(records)} records to {output_file}")



if __name__ == "__main__":
    download_backstabbers_dataset()

    