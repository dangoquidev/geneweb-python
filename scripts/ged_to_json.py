#!/usr/bin/env python3
"""
Convert a GEDCOM (5.5/5.5.1) file into a JSON structure suitable for
subsequent conversion to GeneWeb pickle.

Output schema (high level):
{
  "persons": {
    "I1": {
      "first_name": "Jean",
      "surname": "Dupont",
      "occurrence": 0,
      "public_name": "Jean Dupont",
      "aliases": [],
      "sex": "Male",
      "birth_date": { "text_date": "12 JAN 1940" },
      "birth_place": "...",
      "death": { "date": { "text_date": "21 MAY 2026" } },
      "death_place": "...",
      "occupation": "Journalist",
      "education": "...",
      "refn": "REF1",
      "uid": "I1",
      "objects": [{"file": "photos/xxx.jpg", "title": "..."}],
      "notes": []
    },
    ...
  },
  "families": {
    "F1": {
      "husband": "I1",
      "wife": "I2",
      "children": ["I9", ...],
      "marriage": { "date": { "text_date": "12 JUN 1962" }, "place": "Parish Church, Testland" },
      "divorce": { "date": { "text_date": "12 DEC 1998" }, "place": "Court, Testville" }
    }
  }
}
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def parse_line(raw: str) -> Tuple[int, List[str]]:
    raw = raw.rstrip("\n\r")
    if not raw:
        return 0, []
    parts = raw.split(maxsplit=2)
    if len(parts) == 1:
        return int(parts[0]), []
    if len(parts) == 2:
        return int(parts[0]), [parts[1]]
    return int(parts[0]), [parts[1], parts[2]]


def collect_block(lines: List[str], start: int) -> Tuple[int, int]:
    """Return (start_level, end_index_exclusive) for a record block starting at index 'start'."""
    level, _ = parse_line(lines[start])
    i = start + 1
    n = len(lines)
    while i < n:
        l, _ = parse_line(lines[i])
        if l == 0:
            break
        i += 1
    return level, i


def parse_event_block(lines: List[str], start: int) -> Tuple[Dict[str, Any], int]:
    """Parse a level-1 event block (e.g., BIRT/DEAT/MARR) until leaving the block."""
    level1, parts = parse_line(lines[start])
    assert level1 >= 1
    event: Dict[str, Any] = {}
    i = start + 1
    n = len(lines)
    while i < n:
        lvl, rest = parse_line(lines[i])
        if lvl <= level1:
            break
        tag = rest[0] if rest else ""
        value = rest[1] if len(rest) > 1 else ""
        if tag == "DATE":
            event.setdefault("date", {})["text_date"] = value
        elif tag == "PLAC":
            event["place"] = value
        i += 1
    return event, i


def parse_person(lines: List[str], start: int) -> Tuple[str, Dict[str, Any], int]:
    level0, rest = parse_line(lines[start])
    xref = rest[0] if rest else ""
    if xref.startswith("@"):  # @I1@
        xref = xref.strip("@")
    data: Dict[str, Any] = {
        "first_name": "",
        "surname": "",
        "occurrence": 0,
        "public_name": "",
        "aliases": [],
        "sex": "Unknown",
        "birth_date": None,
        "birth_place": "",
        "death": None,
        "death_place": "",
        "occupation": "",
        "education": "",
        "refn": "",
        "uid": "",
        "objects": [],
        "notes": [],
    }

    i = start + 1
    n = len(lines)
    while i < n:
        lvl, rest = parse_line(lines[i])
        if lvl == 0:
            break
        tag = rest[0] if rest else ""
        value = rest[1] if len(rest) > 1 else ""

        if lvl == 1 and tag == "NAME":
            full = value
            given, sur = full, ""
            if "/" in full:
                before, after = full.split("/", 1)
                sur = after.split("/")[0]
                given = before.strip()
            data["first_name"] = given.strip()
            data["surname"] = sur.strip()
            data["public_name"] = f"{data['first_name']} {data['surname']}".strip()
        elif lvl == 1 and tag == "SEX":
            if value == "M":
                data["sex"] = "Male"
            elif value == "F":
                data["sex"] = "Female"
            else:
                data["sex"] = "Unknown"
        elif lvl == 1 and tag == "BIRT":
            evt, i2 = parse_event_block(lines, i)
            if evt:
                data["birth_date"] = evt.get("date")
                data["birth_place"] = evt.get("place", "")
            i = i2
            continue
        elif lvl == 1 and tag == "DEAT":
            evt, i2 = parse_event_block(lines, i)
            if evt:
                data["death"] = {"date": evt.get("date")}
                data["death_place"] = evt.get("place", "")
            i = i2
            continue
        elif lvl == 1 and tag == "OCCU":
            data["occupation"] = value
        elif lvl == 1 and tag == "EDUC":
            data["education"] = value
        elif lvl == 1 and tag == "REFN":
            data["refn"] = value
        elif lvl == 1 and tag == "_AKA":
            data["aliases"].append(value.strip('"'))
        elif lvl == 1 and tag == "_UID":
            data["uid"] = value
        elif lvl == 1 and tag == "NOTE":
            data["notes"].append(value)
        elif lvl == 1 and tag == "OBJE":
            obj = {}
            i += 1
            while i < n:
                l2, r2 = parse_line(lines[i])
                if l2 <= 1:
                    i -= 1
                    break
                t2 = r2[0] if r2 else ""
                v2 = r2[1] if len(r2) > 1 else ""
                if t2 == "FILE":
                    obj["file"] = v2
                elif t2 == "TITL":
                    obj["title"] = v2
                i += 1
            if obj:
                data["objects"].append(obj)
        i += 1

    return xref, data, i


def parse_family(lines: List[str], start: int) -> Tuple[str, Dict[str, Any], int]:
    level0, rest = parse_line(lines[start])
    xref = rest[0] if rest else ""
    if xref.startswith("@"):  # @F1@
        xref = xref.strip("@")
    data: Dict[str, Any] = {
        "husband": None,
        "wife": None,
        "children": [],
        "marriage": None,
        "divorce": None,
    }

    i = start + 1
    n = len(lines)
    while i < n:
        lvl, rest = parse_line(lines[i])
        if lvl == 0:
            break
        tag = rest[0] if rest else ""
        value = rest[1] if len(rest) > 1 else ""

        if lvl == 1 and tag == "HUSB":
            data["husband"] = value.strip("@")
        elif lvl == 1 and tag == "WIFE":
            data["wife"] = value.strip("@")
        elif lvl == 1 and tag == "CHIL":
            data["children"].append(value.strip("@"))
        elif lvl == 1 and tag == "MARR":
            evt, i2 = parse_event_block(lines, i)
            if evt:
                data["marriage"] = {
                    "date": evt.get("date"),
                    "place": evt.get("place", ""),
                }
            i = i2
            continue
        elif lvl == 1 and tag == "DIV":
            evt, i2 = parse_event_block(lines, i)
            if evt:
                data["divorce"] = {
                    "date": evt.get("date"),
                    "place": evt.get("place", ""),
                }
            i = i2
            continue
        i += 1

    return xref, data, i


def ged_to_json(ged_path: Path) -> Dict[str, Any]:
    lines = ged_path.read_text(encoding="utf-8").splitlines()
    i = 0
    n = len(lines)
    persons: Dict[str, Any] = {}
    families: Dict[str, Any] = {}

    while i < n:
        lvl, rest = parse_line(lines[i])
        if lvl == 0 and rest:
            # 0 @X@ TAG or 0 TAG
            if len(rest) >= 2:
                xref, tag = rest[0], rest[1]
                if tag == "INDI":
                    key, pdata, i = parse_person(lines, i)
                    persons[key] = pdata
                    continue
                elif tag == "FAM":
                    key, fdata, i = parse_family(lines, i)
                    families[key] = fdata
                    continue
        i += 1

    return {"persons": persons, "families": families}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "--ged", dest="ged", default="genewebsample.ged")
    parser.add_argument("--output", dest="output", default="data/ged.json")
    args = parser.parse_args()

    src = Path(args.ged)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    result = ged_to_json(src)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Wrote JSON: {out.resolve()}")


if __name__ == "__main__":
    main()


