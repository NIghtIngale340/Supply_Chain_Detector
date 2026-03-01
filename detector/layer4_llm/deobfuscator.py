import re
import base64
from typing import Any

def _safe_b64decode(b64_string: str) -> str | None:
    try:
        decoded_bytes = base64.b64decode(b64_string)
        return decoded_bytes.decode("utf-8")
    except Exception:
        return None

def deobfuscate_source(source_code: str) -> dict[str, Any]:
    cleaned_source = source_code
    transformations: list[str] = []
    warnings: list[str] = []

    b64_pattern = r"['\"]([A-Za-z0-9+/=]{16,})['\"]"
    for match in re.finditer(b64_pattern, source_code):
        raw_b64 = match.group(1)
        decoded_text = _safe_b64decode(raw_b64)
        if decoded_text:
            replacement = f"/* DEOBFUSCATED_B64: {decoded_text} */"
            cleaned_source = cleaned_source.replace(match.group(0), replacement)
            transformations.append(f"Decoded B64 length {len(raw_b64)}")

    hex_pattern = r"(?:\\x[0-9a-fA-F]{2}){4,}"
    for match in re.finditer(hex_pattern, source_code):
        raw_hex = match.group(0)
        try:
            encoded_bytes = bytes([int(x, 16) for x in raw_hex.split(r"\x") if x])
            decoded_text = encoded_bytes.decode("utf-8")
            replacement = f"/* DEOBFUSCATED_HEX: {decoded_text} */"
            cleaned_source = cleaned_source.replace(raw_hex, replacement)
            transformations.append(f"Decoded hex to: {decoded_text[:20]}...")
        except Exception as e:
            warnings.append(f"Failed to decode hex sequence: {e}")

    return {
        "cleaned_source": cleaned_source,
        "transformations_applied": transformations,
        "warnings": warnings,
    }
