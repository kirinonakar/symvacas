"""Extract searchable bilingual signatures, descriptions and examples from web help."""
import json
import re


def help_entries(path):
    entries = []
    category = ""
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            category = line[3:].strip()
            current = None
        match = re.match(r"^`([^`]+)`\s*[—–-]\s*(.*)$", line)
        if match:
            signature, description = match.groups()
            current = dict(name=signature.split("(")[0].strip(), signature=signature,
                           category=category, description=description.replace("`", ""), examples=[])
            entries.append(current)
        elif current is not None and re.match(r"^(Example:|예(?:시|제):)", line):
            example = line.split(":", 1)[1].strip().replace("`", "")
            current["examples"].append({"text": example, "expression": example.split("→")[0].strip()})
    return entries


def build_catalog(web, output):
    import runpy
    contracts=runpy.run_path(str(web.parent / "app/src/main/python/calc_survival_contract.py"))["CONTRACTS"]
    english = help_entries(web / "catalog_help.md")
    translated_entries = help_entries(web / "catalog_help_ko.md")
    korean = {(item["category"], item["signature"]): item for item in translated_entries}
    from collections import defaultdict, Counter
    translations = defaultdict(list)
    for item in translated_entries:
        translations[item["name"]].append(item)
    counts = Counter(item["name"] for item in english)
    positions = Counter()
    templates = {}
    for category, items in json.loads((web / "catalog.json").read_text(encoding="utf-8")).items():
        for template in items:
            templates.setdefault(template.split("(")[0].strip(), []).append(dict(category=category, template=template))
    for entry in english:
        translated = korean.get((entry["category"], entry["signature"]))
        # The bilingual help keeps overload order; parameter names can be localized.
        choices = translations[entry["name"]]
        if translated is None and len(choices) == counts[entry["name"]]:
            translated = choices[positions[entry["name"]]]
        positions[entry["name"]] += 1
        entry["descriptionKo"] = translated["description"] if translated else ""
        entry["examplesKo"] = translated["examples"] if translated else []
        choices = templates.get(entry["name"], [])
        words = set(re.findall(r"\w+", entry["signature"].lower()))
        entry["templates"] = sorted(choices, key=lambda item: -len(words & set(re.findall(r"\w+", item["template"].lower()))))[:3]
        entry["templateCount"] = len(choices)
        if entry['name'] in contracts:
            contract=contracts[entry['name']]
            for key in ('signature','minimumArguments','arguments','rowLayouts'):
                entry[key]=contract[key]
    covered = {entry["name"] for entry in english}
    for name, items in templates.items():
        if name not in covered:
            english.append(dict(name=name, signature=items[0]["template"], category=items[0]["category"],
                                description="", descriptionKo="", examples=[], examplesKo=[], templates=items))
    output.write_text(json.dumps(english, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
