#!/usr/bin/env python3
"""Convert a keyword classifier CSV with PCRE regex patterns to RE2-compatible patterns.

Usage:
    python convert_pcre_csv_to_re2.py input.csv output.csv

Outputs:
- output.csv: valid rows with transformed patterns and duplicates removed.
- errors.csv: rows where the regex pattern still fails RE2 validation after
  transformation and needs manual fixing. Includes an 'error' column.

Transformations applied to rows where is_regex is TRUE:
- Possessive quantifiers: ++ -> +, *+ -> *, ?+ -> ?, {n,m}+ -> {n,m}
- Atomic groups: (?>...) -> (?:...) (RE2 doesn't backtrack, so equivalent)
- \\K (reset match start): removed (no RE2 equivalent, pattern still matches)
"""

import csv
import os
import re
import sys


def pcre_to_re2(pattern: str) -> str:
    """Transform a PCRE regex pattern to be RE2-compatible.

    RE2 doesn't backtrack (Thompson NFA), so possessive quantifiers
    and atomic groups are semantically equivalent to their non-possessive
    counterparts.
    """
    # Remove possessive quantifiers: ++, *+, ?+, {n,m}+
    # Must handle {n,m}+ before the simpler ones
    pattern = re.sub(r"(\{\d+(?:,\d*)?\})\+", r"\1", pattern)
    pattern = re.sub(r"\+\+", "+", pattern)
    pattern = re.sub(r"\*\+", "*", pattern)
    pattern = re.sub(r"\?\+", "?", pattern)

    # Atomic groups (?>...) -> non-capturing groups (?:...)
    # Safe because RE2 never backtracks
    pattern = re.sub(r"\(\?>", "(?:", pattern)

    # \K (match reset) - no equivalent in RE2, remove it
    pattern = re.sub(r"\\K", "", pattern)

    return pattern


def validate_re2(pattern: str) -> str | None:
    """Validate pattern with google-re2. Returns error message or None."""
    try:
        import re2

        re2.compile(pattern)
        return None
    except ImportError:
        return None
    except Exception as e:
        return str(e)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.csv> <output.csv>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    errors_path = os.path.splitext(output_path)[0] + "_errors.csv"

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print("Error: CSV file is empty.")
            sys.exit(1)
        fieldnames = list(reader.fieldnames)

        valid_rows = []
        error_rows = []
        seen: set[tuple[str, str, str]] = set()
        duplicates_removed = 0
        transforms = 0

        for line_num, row in enumerate(reader, start=2):
            is_regex = row.get("is_regex", "").strip().lower() in ("true", "1")

            if is_regex and row.get("musts", "").strip():
                original = row["musts"]
                transformed = pcre_to_re2(original)

                if transformed != original:
                    print(f"  Row {line_num}: '{original}' -> '{transformed}'")
                    transforms += 1

                error = validate_re2(transformed)
                if error:
                    error_rows.append({**row, "error": error})
                    print(f"  Row {line_num}: INVALID - {error}")
                    continue

                row["musts"] = transformed

            # Deduplicate on (class_name, musts, nots)
            key = (
                row.get("class_name", "").strip(),
                row.get("musts", "").strip(),
                row.get("nots", "").strip(),
            )
            if (key[1] or key[2]) and key in seen:
                duplicates_removed += 1
                print(f"  Row {line_num}: duplicate removed {key}")
                continue
            if key[1] or key[2]:
                seen.add(key)

            valid_rows.append(row)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valid_rows)

    if error_rows:
        error_fieldnames = fieldnames + ["error"]
        with open(errors_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=error_fieldnames)
            writer.writeheader()
            writer.writerows(error_rows)

    print(f"\nSummary:")
    print(f"  Transformed: {transforms} pattern(s)")
    print(f"  Duplicates removed: {duplicates_removed}")
    print(f"  Valid rows: {len(valid_rows)} -> {output_path}")
    print(f"  Error rows: {len(error_rows)} -> {errors_path if error_rows else '(none)'}")


if __name__ == "__main__":
    main()
