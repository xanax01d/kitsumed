#!/usr/bin/env python3
"""
KitsuMed Localization Validator
Validates JSON structure, required keys, placeholders, and formatting of locale files.
Usage:
    python scripts/validate_locale.py                  # Validates all locales in locales/
    python scripts/validate_locale.py locales/de.json  # Validates specific locale file
"""

import sys
import json
import re
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

REFERENCE_LOCALE = "locales/en.json"
REQUIRED_SECTIONS = [
    "messages",
    "location_map",
    "pain_type_map",
    "symptoms_map",
    "medication_map",
    "triggers_map",
]

def load_json(filepath: Path):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"JSON Syntax Error: {e.msg} (line {e.lineno}, col {e.colno})"
    except Exception as e:
        return None, f"Error reading file: {e}"

def extract_placeholders(text: str):
    return set(re.findall(r"\{[a-zA-Z0-9_]+\}", text))

def validate_locale(target_path: Path, ref_data: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)"""
    errors = []
    warnings = []

    target_data, err = load_json(target_path)
    if err:
        return [err], []

    # Check top-level sections
    for sec in REQUIRED_SECTIONS:
        if sec not in target_data:
            errors.append(f"Missing required top-level section: '{sec}'")
        elif not isinstance(target_data[sec], dict):
            errors.append(f"Section '{sec}' must be a dictionary/object")

    if errors:
        return errors, warnings

    # Validate each section against reference
    for sec in REQUIRED_SECTIONS:
        ref_sec = ref_data.get(sec, {})
        target_sec = target_data.get(sec, {})

        missing_keys = set(ref_sec.keys()) - set(target_sec.keys())
        extra_keys = set(target_sec.keys()) - set(ref_sec.keys())

        if missing_keys:
            errors.append(f"[{sec}] Missing {len(missing_keys)} key(s): {', '.join(sorted(missing_keys)[:5])}{'...' if len(missing_keys) > 5 else ''}")
        
        if extra_keys:
            warnings.append(f"[{sec}] {len(extra_keys)} unknown/extra key(s): {', '.join(sorted(extra_keys)[:5])}{'...' if len(extra_keys) > 5 else ''}")

        # Check values
        for key, ref_val in ref_sec.items():
            if key in target_sec:
                target_val = target_sec[key]
                if not isinstance(target_val, str):
                    errors.append(f"[{sec}.{key}] Value must be a string, got {type(target_val).__name__}")
                    continue

                if not target_val.strip() and ref_val.strip():
                    errors.append(f"[{sec}.{key}] Translation is empty")

                # Check placeholders (e.g. {time}, {id})
                if isinstance(ref_val, str):
                    ref_placeholders = extract_placeholders(ref_val)
                    target_placeholders = extract_placeholders(target_val)
                    missing_placeholders = ref_placeholders - target_placeholders
                    if missing_placeholders:
                        errors.append(f"[{sec}.{key}] Missing placeholder variables: {', '.join(missing_placeholders)}")

    return errors, warnings

def main():
    repo_root = Path(__file__).resolve().parent.parent
    ref_path = repo_root / REFERENCE_LOCALE

    if not ref_path.exists():
        print(f"{RED}{BOLD}Error:{RESET} Reference file {ref_path} not found.")
        sys.exit(1)

    ref_data, err = load_json(ref_path)
    if err:
        print(f"{RED}{BOLD}Error loading reference {REFERENCE_LOCALE}:{RESET} {err}")
        sys.exit(1)

    # Determine files to validate
    if len(sys.argv) > 1:
        target_files = [Path(p) for p in sys.argv[1:]]
    else:
        locales_dir = repo_root / "locales"
        target_files = sorted(locales_dir.glob("*.json"))

    print(f"\n{BOLD}{CYAN}🔍 KitsuMed Locale Validator{RESET}")
    print(f"{BLUE}Reference:{RESET} {ref_path.name} ({len(ref_data.get('messages', {}))} message keys)\n")

    overall_success = True
    tested = 0

    for path in target_files:
        if path.name == "template.json":
            continue
        tested += 1
        errors, warnings = validate_locale(path, ref_data)
        
        rel_path = path.relative_to(repo_root) if path.is_relative_to(repo_root) else path
        if not errors:
            if warnings:
                print(f"  {YELLOW}⚠{RESET}  {BOLD}{rel_path}{RESET} - {YELLOW}VALID with {len(warnings)} warning(s){RESET}")
                for w in warnings:
                    print(f"      {YELLOW}↳ {w}{RESET}")
            else:
                print(f"  {GREEN}✔{RESET}  {BOLD}{rel_path}{RESET} - {GREEN}VALID (100% matched){RESET}")
        else:
            overall_success = False
            print(f"  {RED}✖{RESET}  {BOLD}{rel_path}{RESET} - {RED}FAILED with {len(errors)} error(s){RESET}")
            for e in errors[:10]:
                print(f"      {RED}↳ {e}{RESET}")
            if len(errors) > 10:
                print(f"      {RED}↳ ... and {len(errors) - 10} more errors{RESET}")

    print(f"\n{BOLD}Results:{RESET} {tested} file(s) checked.")
    if overall_success:
        print(f"{GREEN}{BOLD}🎉 All validated locales are compliant!{RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}❌ Some locale files failed validation. Please fix the errors above.{RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
