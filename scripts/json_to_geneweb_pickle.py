#!/usr/bin/env python3
"""
Convert JSON dataset (data.json) into GeneWeb-compatible pickle (persons/families as dataclasses).

Usage:
  python scripts/json_to_geneweb_pickle.py --input data.json --output data/showcase.pickle
"""

import argparse
import json
import os
import pickle
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure we can import 'backend.*' like the server does (cd src && python -m ...)
ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backend.geneweb.core.definitions import (
    Calendar,
    DateMY,
    GeneDate,
    Person,
    Family,
    Descendants,
    Union,
    Precision,
    Sex,
)
from backend.geneweb.core.definitions import Death, DeathStatus
from backend.geneweb.db.driver import PersonId, FamilyId


def to_text_or_gregorian_date(d: Dict[str, Any] | None) -> GeneDate | None:
    if not d or not isinstance(d, dict):
        return None
    if d.get("text_date"):
        return GeneDate.from_text(str(d["text_date"]))
    greg = d.get("gregorian_date")
    if isinstance(greg, list) and greg:
        first = greg[0] or {}
        try:
            day = int(first.get("day", 0) or 0)
            month = int(first.get("month", 0) or 0)
            year = int(first.get("year", 0) or 0)
        except Exception:
            day = 0
            month = 0
            year = 0
        dmy = DateMY(day=day, month=month, year=year, prec=Precision.SURE, delta=0)
        return GeneDate.from_gregorian(dmy, Calendar.GREGORIAN)
    return None


def to_sex(value: Any) -> Sex:
    # Accept dict {value: "Male"/"Female"} or plain string
    if isinstance(value, dict):
        v = str(value.get("value", "")).lower()
    else:
        v = str(value or "").lower()
    if v.startswith("m"):
        return Sex.MALE
    if v.startswith("f"):
        return Sex.FEMALE
    return Sex.NEUTER


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data.json")
    parser.add_argument("--output", default="data/showcase.pickle")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    persons_json: Dict[str, Dict[str, Any]] = data.get("persons", {})

    persons: Dict[PersonId, Person] = {}
    id_map: Dict[str, PersonId] = {}
    next_id = 1

    for pid_str, pj in persons_json.items():
        # Build Person dataclass, mapping only key fields used by the app
        p = Person(
            first_name=str(pj.get("first_name", "")),
            surname=str(pj.get("surname", "")),
            occurrence=int(pj.get("occurrence", 0) or 0),
        )

        p.public_name = str(pj.get("public_name", ""))
        p.occupation = str(pj.get("occupation", ""))
        # Program expects person.sex to be a simple string "M"/"F" in some display paths
        sex_enum = to_sex(pj.get("sex"))
        p.sex = sex_enum  # keep enum in dataclass
        # also set a string mirror attribute if accessed as string elsewhere
        # This will be ignored by dataclass typing but kept in pickle
        setattr(p, "sex", "M" if sex_enum == Sex.MALE else ("F" if sex_enum == Sex.FEMALE else ""))
        p.birth_date = to_text_or_gregorian_date(pj.get("birth_date"))
        # Death is optional; if structure exists with date
        death_obj = pj.get("death")
        if isinstance(death_obj, dict):
            death_date = to_text_or_gregorian_date(death_obj.get("date"))
            p.death = Death(status=DeathStatus.DEATH, date=death_date)
            # Add compatibility attribute expected by some templates/server code
            setattr(p, "death_date", death_date)
        else:
            setattr(p, "death_date", None)

        # Assign id
        pid = PersonId(next_id)
        next_id += 1
        p.key_index = pid
        persons[pid] = p
        id_map[pid_str] = pid

    # Families
    families_json: Dict[str, Dict[str, Any]] = data.get("families", {})
    families: Dict[FamilyId, Family] = {}
    unions: Dict[PersonId, Union] = {}
    descendants: Dict[FamilyId, Descendants] = {}
    next_family_id = 1

    for fid_str, fj in families_json.items():
        fam = Family()

        # Marriage info
        marriage = fj.get("marriage")
        if isinstance(marriage, dict):
            fam.marriage_date = to_text_or_gregorian_date(marriage.get("date"))
            fam.marriage_place = str(marriage.get("place", ""))

        # Parents (store as dynamic attributes expected by API code)
        husband_key = fj.get("husband")
        wife_key = fj.get("wife")
        husband_id = id_map.get(str(husband_key)) if husband_key else None
        wife_id = id_map.get(str(wife_key)) if wife_key else None

        if husband_id is not None:
            setattr(fam, "father", husband_id)
        if wife_id is not None:
            setattr(fam, "mother", wife_id)

        # Link unions (parents -> families they are part of)
        if husband_id is not None:
            u = unions.get(husband_id) or Union()
            u.families.append(fam)
            unions[husband_id] = u
        if wife_id is not None:
            u = unions.get(wife_id) or Union()
            u.families.append(fam)
            unions[wife_id] = u

        # Children
        child_objs = []
        for child_key in fj.get("children", []) or []:
            cid = id_map.get(str(child_key))
            if cid is not None and cid in persons:
                child_objs.append(persons[cid])

        fam_id = FamilyId(next_family_id)
        next_family_id += 1
        fam.family_index = fam_id
        families[fam_id] = fam
        descendants[fam_id] = Descendants(children=child_objs)

    out = {
        "persons": persons,
        "families": families,
        "ascendants": {},
        "unions": unions,
        "descendants": descendants,
        "name_index": {},
        "next_person_id": next_id,
        "next_family_id": next_family_id,
        "update_history": [],
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "wb") as f:
        pickle.dump(out, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"✅ Wrote GeneWeb pickle: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()


