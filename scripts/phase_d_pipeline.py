#!/usr/bin/env python3
"""Phase D pilot pipeline helpers for entry-0019 ~ entry-0028."""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = REPO_ROOT / "data" / "review" / "hangzhou_translation_reviews.json"
ANNOTATION_DIR = REPO_ROOT / "data" / "annotations" / "entries"
ENTITY_DIR = REPO_ROOT / "data" / "annotations" / "entities"
THIN_CHUNKS_PATH = REPO_ROOT / "data" / "rag" / "chunks" / "entry_chunks.jsonl"
REVIEWED_CHUNKS_PATH = REPO_ROOT / "data" / "rag" / "chunks" / "reviewed_entry_chunks.jsonl"
DOSSIER_CHUNKS_PATH = REPO_ROOT / "data" / "rag" / "chunks" / "entity_dossier_chunks.jsonl"
ASSERTIONS_PATH = REPO_ROOT / "data" / "semantic" / "assertions" / "assertions.jsonl"
GRAPH_NODES_PATH = REPO_ROOT / "data" / "graph" / "knowledge_graph_nodes.jsonl"
GRAPH_EDGES_PATH = REPO_ROOT / "data" / "graph" / "knowledge_graph_edges.jsonl"
DEMO_QUERIES_PATH = REPO_ROOT / "data" / "rag" / "demo_queries.json"

GOLD_ENTRY_IDS = [f"entry-{index:04d}" for index in range(19, 29)]
SELF_PERSON_ID = "person-0001"
SELF_PERSON_LABEL = "郭畀"
GENERATED_BY = "scripts/phase_d_pipeline.py"

PLACE_ALIAS_MAP = {
    "항주": "杭州",
    "항주성내": "杭州",
    "항주 성내": "杭州",
    "항주성외": "杭州城外",
    "항주 성외": "杭州城外",
    "상주": "常州",
    "평강": "平江",
    "고소": "姑蘇",
    "전당": "錢塘",
    "여성": "呂城",
    "금단": "金壇",
    "무주": "婺州",
    "단도": "丹徒",
}

TOPIC_RULES = [
    ("불교", ("佛", "寺", "觀", "經", "長老", "觀音")),
    ("이동", ("行", "航", "舟", "船", "배편", "환승", "여정")),
    ("문예", ("書", "畫", "圖", "壁", "題", "卷", "書院", "米老")),
    ("관청", ("司", "省中", "照磨所", "提舉", "禮房", "都目", "外郞", "府判")),
    ("교유", ("酒", "茶", "留宿", "款待", "小酌", "晚飯")),
]

INSTITUTION_HINTS = ("寺", "書院", "觀", "司", "所")
WORK_HINTS = ("畫", "圖", "佛像", "壁", "碑", "塔", "觀音")
DOCUMENT_HINTS = ("書", "文", "呈子", "解由", "卷", "經")
CONSUMABLE_HINTS = ("茶", "酒", "飯", "蟹", "芋", "食")
OFFICE_HINTS = (
    "山長",
    "府判",
    "提舉",
    "提點",
    "外郞",
    "都目",
    "教授",
    "學正",
    "州判",
    "同知",
    "主簿",
    "學士",
    "維那",
    "令史",
    "廉吏",
)
GENERIC_PLACE_HEADINGS = {
    "항주 체류 전체",
    "항주 성내",
    "항주 성문/경계",
    "항주 성외",
    "항주 외부 참조 공간",
    "항주 주변",
}
NON_PLACE_MOVEMENT_HINTS = {"夜航", "換舟", "小舟", "借馬", "登航", "夜間 배편", "야간 배편"}
TIME_MARKER_RULES = {"四更": "late_night", "二更": "night", "拂明": "dawn", "晡時": "afternoon", "早": "morning"}
CERTAINTY_PRIORITY = {"confirmed": 0, "probable": 1, "uncertain": 2, "unknown": 3}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def get_git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip() or None


def canonical_key(value: str | None) -> str:
    if value is None:
        return ""
    value = value.strip().strip("-:()[] ")
    value = value.replace(" ", "")
    return PLACE_ALIAS_MAP.get(value, value)


def split_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def split_label_and_note(line: str) -> tuple[str, str | None]:
    line = line.strip().lstrip("-").strip()
    if ":" in line:
        left, right = line.split(":", 1)
        return left.strip(), right.strip() or None
    return line, None


def split_surface_and_gloss(label: str) -> tuple[str, str | None]:
    if "→" in label:
        left, right = label.split("→", 1)
        return left.strip(), right.strip() or None
    return label.strip(), None


def strip_parenthetical(label: str) -> tuple[str, str | None]:
    match = re.match(r"^(.*?)\((.*?)\)\s*$", label.strip())
    if not match:
        return label.strip(), None
    return match.group(1).strip(), match.group(2).strip() or None


def split_compound_plus(label: str) -> tuple[str, str] | None:
    plus_index = label.find("+")
    if plus_index < 0:
        return None
    paren_index = label.find("(")
    if paren_index >= 0 and plus_index > paren_index:
        return None
    left, right = label.split("+", 1)
    return left.strip(), right.strip()


def infer_entity_type_from_id(entity_id: str) -> str:
    return entity_id.split("-", 1)[0]


def looks_like_office_label(label: str) -> bool:
    return any(token in label for token in OFFICE_HINTS)


def lowest_certainty(values: Iterable[str]) -> str:
    found = [value for value in values if value in CERTAINTY_PRIORITY]
    if not found:
        return "confirmed"
    return max(found, key=lambda item: CERTAINTY_PRIORITY[item])


def reviewed_chunk_certainty(values: Iterable[str]) -> str:
    lowest = lowest_certainty(values)
    return "uncertain" if lowest == "unknown" else lowest


def edge_certainty(values: Iterable[str]) -> str:
    found = [value for value in values if value in {"confirmed", "probable", "uncertain"}]
    unique = set(found)
    if not found:
        return "confirmed"
    if len(unique) > 1:
        return "mixed"
    return found[0]


class EntityRegistry:
    """Assign deterministic IDs for the pilot subset."""

    def __init__(self) -> None:
        self.maps: dict[str, dict[str, str]] = defaultdict(dict)
        self.labels: dict[str, dict[str, str]] = defaultdict(dict)
        self.counters: dict[str, int] = defaultdict(int)
        self.register("person", SELF_PERSON_LABEL, preferred_id=SELF_PERSON_ID)

    def register(self, entity_type: str, label: str, *, preferred_id: str | None = None) -> str:
        key = canonical_key(label)
        if key in self.maps[entity_type]:
            return self.maps[entity_type][key]
        if preferred_id is None:
            self.counters[entity_type] += 1
            while f"{entity_type}-{self.counters[entity_type]:04d}" == SELF_PERSON_ID:
                self.counters[entity_type] += 1
            entity_id = f"{entity_type}-{self.counters[entity_type]:04d}"
        else:
            entity_id = preferred_id
            self.counters[entity_type] = max(self.counters[entity_type], int(entity_id.split("-")[1]))
        self.maps[entity_type][key] = entity_id
        self.labels[entity_type][entity_id] = label.strip()
        return entity_id

    def resolve(self, entity_type: str, label: str | None) -> str | None:
        if not label:
            return None
        return self.maps[entity_type].get(canonical_key(label))


def validate_annotation(annotation: dict[str, Any]) -> None:
    required = {
        "entry_id",
        "summary_ko",
        "persons",
        "places",
        "offices",
        "institutions",
        "documents",
        "works",
        "consumables",
        "topics",
        "notes",
        "status",
        "provenance",
    }
    missing = required - set(annotation)
    if missing:
        raise ValueError(f"annotation missing keys: {sorted(missing)}")


def validate_authority(authority: dict[str, Any]) -> None:
    required = {"id", "entity_type", "label_original", "status"}
    missing = required - set(authority)
    if missing:
        raise ValueError(f"authority missing keys: {sorted(missing)}")


def validate_rag_chunk(chunk: dict[str, Any]) -> None:
    required = {
        "chunk_id",
        "chunk_type",
        "source_entry_ids",
        "text_ko",
        "evidence_raw",
        "certainty",
        "review_status",
        "provenance",
    }
    missing = required - set(chunk)
    if missing:
        raise ValueError(f"chunk missing keys: {sorted(missing)}")


def validate_assertion(assertion: dict[str, Any]) -> None:
    required = {
        "assertion_id",
        "assertion_type",
        "subject",
        "predicate",
        "object",
        "source_entry_ids",
        "evidence_raw",
        "certainty",
        "provenance",
    }
    missing = required - set(assertion)
    if missing:
        raise ValueError(f"assertion missing keys: {sorted(missing)}")


def validate_node(node: dict[str, Any]) -> None:
    required = {"node_id", "node_type", "label", "source_entity_id", "provenance"}
    missing = required - set(node)
    if missing:
        raise ValueError(f"node missing keys: {sorted(missing)}")


def validate_edge(edge: dict[str, Any]) -> None:
    required = {
        "edge_id",
        "source_node",
        "target_node",
        "edge_type",
        "source_assertion_ids",
        "certainty",
        "provenance",
    }
    missing = required - set(edge)
    if missing:
        raise ValueError(f"edge missing keys: {sorted(missing)}")


def classify_item_type(label: str) -> str:
    if any(token in label for token in CONSUMABLE_HINTS):
        return "consumable"
    if any(token in label for token in WORK_HINTS):
        return "work"
    if any(token in label for token in DOCUMENT_HINTS):
        return "document"
    return "document"


def looks_like_institution(label: str) -> bool:
    return any(token in label for token in INSTITUTION_HINTS)


def infer_place_type(label: str) -> str:
    if label in {"杭州", "常州", "平江", "錢塘"}:
        return "city"
    if "寺" in label or "觀" in label:
        return "temple"
    if "書院" in label:
        return "academy"
    if "省" in label or "司" in label or "所" in label or "房" in label:
        return "office_building"
    if "鎮" in label or "壩" in label:
        return "town"
    return "other"


def infer_institution_type(label: str) -> str:
    if "書院" in label:
        return "academy"
    if "寺" in label or "觀" in label:
        return "temple"
    if "司" in label or "所" in label or "省" in label:
        return "government"
    return "other"


def infer_transport_mode(text: str) -> str | None:
    if any(token in text for token in ("舟", "船", "배", "航")):
        return "boat"
    if any(token in text for token in ("馬", "말")):
        return "horse"
    if any(token in text for token in ("徒", "步", "걸어")):
        return "walk"
    return None


def split_route(route_text: str) -> list[str]:
    if not route_text:
        return []
    cleaned = route_text.replace("(", "|").replace(")", "|")
    cleaned = cleaned.replace("→", "|").replace("->", "|").replace("—", "|")
    if "→" not in route_text:
        cleaned = cleaned.replace(" - ", "|").replace("-", "|")
    results: list[str] = []
    seen: set[str] = set()
    for part in cleaned.split("|"):
        piece = part.strip()
        if not piece:
            continue
        candidates = [canonical_key(piece)]
        candidates.extend(canonical_key(token) for token in re.findall(r"[一-龥]{2,}", piece))
        for alias in PLACE_ALIAS_MAP:
            if alias in piece:
                candidates.append(canonical_key(alias))
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            results.append(candidate)
    return results


def infer_topics(review_entry: dict[str, Any]) -> list[str]:
    corpus = "\n".join(
        str(review_entry.get(field, ""))
        for field in (
            "name_office_corrections",
            "place_movement_corrections",
            "document_item",
            "weather",
            "transport",
            "route",
            "food_hospitality",
            "other_factual_notes",
            "short_comment",
            "suggested_revised_translation",
        )
    )
    topics: list[str] = []
    for topic, hints in TOPIC_RULES:
        if any(hint in corpus for hint in hints):
            topics.append(topic)
    return topics


def extract_time_markers(review_entry: dict[str, Any]) -> list[dict[str, str]]:
    corpus = "\n".join(str(review_entry.get(field, "")) for field in ("other_factual_notes", "suggested_revised_translation"))
    markers: list[dict[str, str]] = []
    for raw, position in TIME_MARKER_RULES.items():
        if raw in corpus:
            markers.append({"position": position, "raw": raw})
    return markers


def parse_ambiguity_map(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in split_lines(text):
        label, note = split_label_and_note(line)
        result[canonical_key(label)] = note or "review ambiguity noted"
    return result


def extract_place_candidates(place_text: str) -> list[tuple[str, str | None]]:
    candidates: list[tuple[str, str | None]] = []
    seen: set[str] = set()

    for raw_line in split_lines(place_text):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped in GENERIC_PLACE_HEADINGS:
            continue
        if " " in stripped and ":" not in stripped and not stripped.startswith("-"):
            continue

        parts = [part.strip() for part in stripped.split(",") if part.strip()]
        if not parts:
            parts = [stripped]

        for part in parts:
            label, note = split_label_and_note(part)
            label, gloss = split_surface_and_gloss(label)
            note = note or gloss
            normalized = canonical_key(label)
            if not normalized or normalized in GENERIC_PLACE_HEADINGS:
                continue
            if len(normalized) <= 1:
                continue
            if normalized in NON_PLACE_MOVEMENT_HINTS:
                continue
            if any(token in normalized for token in ("현재", "본", "소재", "출신", "방문한", "수식")):
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            candidates.append((normalized, note))

    return candidates


def mention_payload(
    entity_id: str,
    surface: str,
    normalized: str,
    role: str,
    *,
    mention_type: str | None = None,
    certainty: str = "confirmed",
    certainty_reason: str | None = None,
    compound_surface: bool = False,
    compound_components: list[dict[str, str]] | None = None,
    register_context: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "entity_id": entity_id,
        "surface": surface,
        "normalized": normalized,
        "role": role,
    }
    if mention_type is not None:
        payload["mention_type"] = mention_type
    if certainty != "confirmed":
        payload["certainty"] = certainty
    if certainty_reason:
        payload["certainty_reason"] = certainty_reason
    if compound_surface:
        payload["compound_surface"] = True
    if compound_components:
        payload["compound_components"] = compound_components
    if register_context is not None:
        payload["register_context"] = register_context
    return payload


def build_review_registry(review_entries: dict[str, dict[str, Any]]) -> EntityRegistry:
    registry = EntityRegistry()
    for entry_id in GOLD_ENTRY_IDS:
        entry = review_entries[entry_id]
        for line in split_lines(entry.get("name_office_corrections", "")):
            label, _note = split_label_and_note(line)
            label, _gloss = split_surface_and_gloss(label)
            if "=" in label:
                _, right = [part.strip() for part in label.split("=", 1)]
                label = right
            compound = split_compound_plus(label)
            if compound:
                left, right = compound
                left, _left_note = strip_parenthetical(left)
                right, _right_note = strip_parenthetical(right)
                if looks_like_office_label(right):
                    registry.register("person", left)
                    registry.register("office", right)
                else:
                    registry.register("person", right)
            elif label:
                label, _label_note = strip_parenthetical(label)
                registry.register("person", label)
        for normalized, _note in extract_place_candidates(str(entry.get("place_movement_corrections", ""))):
            registry.register("place", normalized)
            if looks_like_institution(normalized):
                registry.register("institution", normalized)
        for value in split_lines(entry.get("document_item", "")) + split_lines(entry.get("food_hospitality", "")):
            label, _note = split_label_and_note(value)
            registry.register(classify_item_type(label), label)
        for route_label in split_route(str(entry.get("route", ""))):
            registry.register("place", route_label)
        for raw_line in split_lines(entry.get("place_movement_corrections", "")):
            normalized = canonical_key(raw_line.strip())
            if normalized in {"杭州", "杭州城外", "平江", "常州", "呂城", "錢塘"}:
                registry.register("place", normalized)
        if registry.resolve("place", "杭州城外"):
            registry.register("place", "杭州")
    return registry


def convert_reviews_to_annotations() -> list[dict[str, Any]]:
    review_payload = load_json(REVIEW_PATH)
    review_entries = review_payload["entries"]
    registry = build_review_registry(review_entries)
    annotations: list[dict[str, Any]] = []
    generated_at = iso_now()

    for entry_id in GOLD_ENTRY_IDS:
        review_entry = review_entries[entry_id]
        ambiguity_map = parse_ambiguity_map(str(review_entry.get("ambiguities_to_keep", "")))

        persons: list[dict[str, Any]] = []
        offices: list[dict[str, Any]] = []
        places: list[dict[str, Any]] = []
        institutions: list[dict[str, Any]] = []
        documents: list[dict[str, Any]] = []
        works: list[dict[str, Any]] = []
        consumables: list[dict[str, Any]] = []

        for line in split_lines(review_entry.get("name_office_corrections", "")):
            label, note = split_label_and_note(line)
            label, gloss = split_surface_and_gloss(label)
            certainty = "uncertain" if canonical_key(label) in ambiguity_map else "confirmed"
            certainty_reason = ambiguity_map.get(canonical_key(label)) or note or gloss
            if "=" in label:
                left, right = [part.strip() for part in label.split("=", 1)]
                label = right
                persons.append(
                    mention_payload(
                        registry.register("person", label),
                        left,
                        label,
                        "mentioned_person",
                        mention_type="alias",
                        certainty=certainty,
                        certainty_reason=certainty_reason,
                    )
                )
                continue
            compound = split_compound_plus(label)
            if compound:
                left, right = compound
                left_base, left_note = strip_parenthetical(left)
                right_base, right_note = strip_parenthetical(right)
                certainty_reason = certainty_reason or left_note or right_note
                if looks_like_office_label(right):
                    person_id = registry.register("person", left_base)
                    office_id = registry.register("office", right_base)
                    persons.append(
                        mention_payload(
                            person_id,
                            label,
                            left_base,
                            "mentioned_person",
                            mention_type="office",
                            certainty=certainty,
                            certainty_reason=certainty_reason,
                            compound_surface=True,
                            compound_components=[
                                {"kind": "person", "surface": left_base, "entity_id": person_id},
                                {"kind": "office", "surface": right_base, "entity_id": office_id},
                            ],
                            register_context="administrative",
                        )
                    )
                    offices.append(
                        mention_payload(
                            office_id,
                            right_base,
                            right_base,
                            "title",
                            mention_type="office",
                            certainty=certainty,
                            certainty_reason=certainty_reason,
                            register_context="administrative",
                        )
                    )
                else:
                    person_id = registry.register("person", right_base)
                    persons.append(
                        mention_payload(
                            person_id,
                            label,
                            right_base,
                            "mentioned_person",
                            mention_type="descriptor",
                            certainty=certainty,
                            certainty_reason=certainty_reason,
                        )
                    )
            else:
                label_base, label_note = strip_parenthetical(label)
                certainty_reason = certainty_reason or label_note
                persons.append(
                    mention_payload(
                        registry.register("person", label_base),
                        label,
                        label_base,
                        "mentioned_person",
                        certainty=certainty,
                        certainty_reason=certainty_reason,
                    )
                )

        seen_place_ids: set[str] = set()
        for normalized, note in extract_place_candidates(str(review_entry.get("place_movement_corrections", ""))):
            certainty = "uncertain" if normalized in ambiguity_map else "confirmed"
            certainty_reason = ambiguity_map.get(normalized) or note
            place_id = registry.register("place", normalized)
            if place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)
            places.append(
                mention_payload(
                    place_id,
                    normalized,
                    normalized,
                    "location",
                    certainty=certainty,
                    certainty_reason=certainty_reason,
                    register_context="administrative",
                )
            )
            if looks_like_institution(normalized):
                institution_id = registry.register("institution", normalized)
                institutions.append(
                    mention_payload(
                        institution_id,
                        normalized,
                        normalized,
                        "mentioned_institution",
                        certainty=certainty,
                        certainty_reason=certainty_reason,
                        register_context="administrative",
                    )
                )

        for route_label in split_route(str(review_entry.get("route", ""))):
            place_id = registry.register("place", route_label)
            if place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)
            places.append(
                mention_payload(
                    place_id,
                    route_label,
                    route_label,
                    "location",
                    register_context="journey",
                )
            )

        for line in split_lines(review_entry.get("document_item", "")):
            label, note = split_label_and_note(line)
            item_type = classify_item_type(label)
            entity_id = registry.register(item_type, label)
            payload = mention_payload(entity_id, label, label, "mentioned_item", certainty_reason=note)
            if item_type == "document":
                documents.append(payload)
            elif item_type == "work":
                works.append(payload)
            else:
                consumables.append(payload)

        for line in split_lines(review_entry.get("food_hospitality", "")):
            label, note = split_label_and_note(line)
            entity_id = registry.register("consumable", label)
            consumables.append(mention_payload(entity_id, label, label, "hospitality_item", certainty_reason=note))

        route_labels = split_route(str(review_entry.get("route", "")))
        journey = None
        if len(route_labels) >= 2:
            route_ids = [registry.register("place", label) for label in route_labels]
            journey = {
                "from": route_ids[0],
                "to": route_ids[-1],
                "via": route_ids[1:-1],
                "mode": infer_transport_mode(str(review_entry.get("transport", ""))),
                "distance_raw": str(review_entry.get("route", "")),
            }

        notes: list[dict[str, Any]] = []
        if review_entry.get("weather"):
            notes.append({"type": "editorial", "text": f"weather: {review_entry['weather']}"})
        for line in split_lines(review_entry.get("other_factual_notes", "")):
            notes.append({"type": "editorial", "text": line})
        for reason in ambiguity_map.values():
            notes.append({"type": "uncertainty", "text": reason})

        translation_notes = []
        for field in ("name_office_corrections", "place_movement_corrections", "food_hospitality"):
            if review_entry.get(field):
                translation_notes.append({"type": "editorial", "text": f"{field}: {review_entry[field]}"})

        interactions = []
        seq = 1
        location_id = places[0]["entity_id"] if places else None
        for person in persons:
            reason = (person.get("certainty_reason") or "") + " " + str(review_entry.get("short_comment", ""))
            action = "visit"
            result = "met"
            if any(token in reason for token in ("만나지 못함", "찾았으나 만나지 못함", "부재중")):
                result = "not_met"
            elif "동행" in reason:
                action = "travel_with"
            interactions.append(
                {
                    "seq": seq,
                    "action": action,
                    "agent": SELF_PERSON_ID,
                    "target": person["entity_id"],
                    "companions": [],
                    "result": result,
                    "location": location_id,
                    "notes": person.get("certainty_reason"),
                }
            )
            seq += 1
        if review_entry.get("food_hospitality") and persons:
            interactions.append(
                {
                    "seq": seq,
                    "action": "dined_with",
                    "agent": SELF_PERSON_ID,
                    "target": persons[0]["entity_id"],
                    "companions": [],
                    "result": "met",
                    "location": location_id,
                    "notes": str(review_entry.get("food_hospitality", "")),
                }
            )

        summary = str(review_entry.get("short_comment", "")).strip()
        if not summary:
            summary = str(review_entry.get("suggested_revised_translation", "")).strip().split(".")[0].strip()
        if not summary:
            summary = f"{entry_id} reviewed entry"

        annotation = {
            "entry_id": entry_id,
            "summary_ko": summary,
            "text_corrections": [],
            "translation_revised": str(review_entry.get("suggested_revised_translation", "")).strip() or None,
            "translation_notes": translation_notes,
            "persons": persons,
            "places": places,
            "offices": offices,
            "institutions": institutions,
            "documents": documents,
            "works": works,
            "consumables": consumables,
            "interactions": interactions,
            "exchanges": [],
            "artworks": [],
            "journey": journey,
            "time_markers": extract_time_markers(review_entry),
            "emotional_markers": [],
            "costs": [],
            "topics": infer_topics(review_entry),
            "notes": notes,
            "status": {
                "summary": "done" if review_entry.get("short_comment") else "partial",
                "entities": "done" if persons or places or offices else "partial",
                "review": "reviewed",
            },
            "provenance": {
                "annotated_by": "codex",
                "updated_at": str(review_entry.get("updated_at", "")).strip() or generated_at,
                "reviewed_by": "seo_yuna",
                "review_method": "translation_assisted",
            },
        }
        validate_annotation(annotation)
        annotations.append(annotation)

    for annotation in annotations:
        write_json(ANNOTATION_DIR / f"{annotation['entry_id']}.annotation.json", annotation)
    return annotations


def load_annotations() -> list[dict[str, Any]]:
    return [load_json(ANNOTATION_DIR / f"{entry_id}.annotation.json") for entry_id in GOLD_ENTRY_IDS]


def build_aliases_for_entity(entity_id: str, mentions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aliases: list[dict[str, Any]] = []
    seen: set[str] = set()
    for mention in mentions:
        if mention["entity_id"] != entity_id:
            continue
        surface = mention["surface"]
        normalized = mention.get("normalized")
        if surface == normalized or surface in seen:
            continue
        aliases.append(
            {
                "surface": surface,
                "alias_type": mention.get("mention_type", "alias"),
                "ambiguous": mention.get("certainty") == "uncertain",
                "notes": mention.get("certainty_reason"),
            }
        )
        seen.add(surface)
    return aliases


def create_authority_files() -> dict[str, dict[str, dict[str, Any]]]:
    annotations = load_annotations()
    review_entries = load_json(REVIEW_PATH)["entries"]
    mention_index: dict[str, dict[str, Any]] = {
        SELF_PERSON_ID: mention_payload(SELF_PERSON_ID, SELF_PERSON_LABEL, SELF_PERSON_LABEL, "self")
    }
    mentions_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    mentions_by_type["person"].append(mention_index[SELF_PERSON_ID])
    first_seen: dict[str, str] = {SELF_PERSON_ID: GOLD_ENTRY_IDS[0]}

    hierarchy: dict[str, str | None] = {}
    registry = build_review_registry(review_entries)
    for entry_id in GOLD_ENTRY_IDS:
        heading_place: str | None = None
        stack: list[tuple[int, str]] = []
        for raw_line in split_lines(review_entries[entry_id].get("place_movement_corrections", "")):
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            stripped = raw_line.strip()
            if stripped.startswith("-"):
                label, _note = split_label_and_note(stripped)
                label, _gloss = split_surface_and_gloss(label)
                normalized = canonical_key(label)
                place_id = registry.resolve("place", normalized)
                while stack and stack[-1][0] >= indent:
                    stack.pop()
                parent_id = None
                if stack:
                    parent_id = registry.resolve("place", stack[-1][1])
                elif heading_place and heading_place != normalized:
                    parent_id = registry.resolve("place", heading_place)
                if place_id:
                    hierarchy[place_id] = parent_id
                stack.append((indent, normalized))
            else:
                normalized = canonical_key(stripped)
                heading_place = normalized if normalized in {"杭州", "杭州城外", "平江", "常州", "呂城", "錢塘"} else None
                stack.clear()

    for annotation in annotations:
        entry_id = annotation["entry_id"]
        for field in ("persons", "places", "offices", "institutions"):
            entity_type = field[:-1] if field != "places" else "place"
            if field == "persons":
                entity_type = "person"
            if field == "offices":
                entity_type = "office"
            if field == "institutions":
                entity_type = "institution"
            for mention in annotation[field]:
                entity_id = mention["entity_id"]
                mention_index.setdefault(entity_id, mention)
                mentions_by_type[entity_type].append(mention)
                first_seen.setdefault(entity_id, entry_id)

    for entity_id, parent_id in hierarchy.items():
        if not parent_id or parent_id in mention_index:
            continue
        mention_index[parent_id] = mention_payload(parent_id, registry.labels["place"].get(parent_id, parent_id), registry.labels["place"].get(parent_id, parent_id), "location")
        mentions_by_type["place"].append(mention_index[parent_id])
        first_seen.setdefault(parent_id, GOLD_ENTRY_IDS[0])

    authorities: dict[str, dict[str, dict[str, Any]]] = {"person": {}, "place": {}, "office": {}, "institution": {}}

    for entity_id, mention in sorted(mention_index.items()):
        entity_type = infer_entity_type_from_id(entity_id)
        if entity_type not in authorities:
            continue
        label = mention.get("normalized") or mention["surface"]
        authority: dict[str, Any] = {
            "id": entity_id,
            "entity_type": entity_type,
            "label_original": label,
            "label_normalized": mention.get("normalized"),
            "first_seen_entry_id": first_seen[entity_id],
            "aliases": build_aliases_for_entity(entity_id, mentions_by_type[entity_type]),
            "notes": mention.get("certainty_reason"),
            "status": "active",
        }
        if entity_type == "person":
            appointments = []
            for annotation in annotations:
                for person in annotation["persons"]:
                    if person["entity_id"] != entity_id or not person.get("compound_surface"):
                        continue
                    for component in person.get("compound_components", []):
                        if component["kind"] != "office":
                            continue
                        appointments.append(
                            {
                                "office_id": component["entity_id"],
                                "institution_id": annotation["institutions"][0]["entity_id"] if annotation["institutions"] else None,
                                "place_id": annotation["places"][0]["entity_id"] if annotation["places"] else None,
                                "period_raw": annotation["entry_id"],
                                "period_start": None,
                                "period_end": None,
                                "source_entry_ids": [annotation["entry_id"]],
                                "source_external": None,
                                "grade": "confirmed",
                                "notes": person.get("certainty_reason"),
                            }
                        )
            authority["relations"] = []
            authority["appointments"] = appointments
            authority["residences"] = []
            authority["external_ids"] = {"cbdb": {"id": None, "grade": "unresolved", "notes": "pilot placeholder"}}
        elif entity_type == "place":
            authority["place_info"] = {
                "place_type": infer_place_type(label),
                "admin_level": "zhou" if label in {"杭州", "常州", "平江"} else None,
                "parent_place_id": hierarchy.get(entity_id),
                "coordinates": None,
                "period_names": [],
            }
            authority["external_ids"] = {"chgis": {"id": None, "grade": "unresolved", "notes": "pilot placeholder"}}
        elif entity_type == "office":
            authority["external_ids"] = {"inindex": {"url": None, "grade": "unresolved", "notes": "pilot placeholder"}}
        elif entity_type == "institution":
            authority["institution_info"] = {
                "institution_type": infer_institution_type(label),
                "place_id": registry.resolve("place", label),
                "parent_institution_id": None,
            }
            authority["external_ids"] = {"inindex": {"url": None, "grade": "unresolved", "notes": "pilot placeholder"}}

        validate_authority(authority)
        authorities[entity_type][entity_id] = authority

    path_map = {
        "person": ENTITY_DIR / "persons",
        "place": ENTITY_DIR / "places",
        "office": ENTITY_DIR / "offices",
        "institution": ENTITY_DIR / "institutions",
    }
    for entity_type, entity_map in authorities.items():
        for authority in entity_map.values():
            write_json(path_map[entity_type] / f"{authority['id']}.json", authority)

    return authorities


def load_authorities() -> dict[str, dict[str, dict[str, Any]]]:
    path_map = {
        "person": ENTITY_DIR / "persons",
        "place": ENTITY_DIR / "places",
        "office": ENTITY_DIR / "offices",
        "institution": ENTITY_DIR / "institutions",
    }
    result: dict[str, dict[str, dict[str, Any]]] = {"person": {}, "place": {}, "office": {}, "institution": {}}
    for entity_type, directory in path_map.items():
        for path in sorted(directory.glob(f"{entity_type}-*.json")):
            result[entity_type][path.stem] = load_json(path)
    return result


def build_reviewed_entry_chunks() -> list[dict[str, Any]]:
    annotations = {item["entry_id"]: item for item in load_annotations()}
    thin_chunks = {
        row["source_entry_ids"][0]: row
        for row in load_jsonl(THIN_CHUNKS_PATH)
        if row.get("source_entry_ids")
    }
    generated_at = iso_now()
    data_commit = get_git_commit()
    reviewed_chunks: list[dict[str, Any]] = []

    for entry_id in GOLD_ENTRY_IDS:
        annotation = annotations[entry_id]
        thin = thin_chunks[entry_id]
        all_mentions = (
            annotation["persons"]
            + annotation["places"]
            + annotation["offices"]
            + annotation["institutions"]
            + annotation["documents"]
            + annotation["works"]
            + annotation["consumables"]
        )
        has_revised = bool(annotation.get("translation_revised"))
        seen_entities: set[str] = set()
        entities = []
        for mention in all_mentions:
            entity_id = mention["entity_id"]
            if entity_id in seen_entities:
                continue
            seen_entities.add(entity_id)
            entities.append(
                {
                    "entity_id": entity_id,
                    "entity_type": infer_entity_type_from_id(entity_id),
                    "label": mention.get("normalized") or mention["surface"],
                }
            )
        chunk = {
            "chunk_id": thin["chunk_id"],
            "chunk_type": "entry",
            "source_entry_ids": [entry_id],
            "source_sequence_id": None,
            "source_entity_id": None,
            "sequence_type": None,
            "source_text_pointer": thin.get("source_text_pointer"),
            "text_ko": annotation["translation_revised"] if has_revised else thin["text_ko"],
            "text_lzh": thin.get("text_lzh"),
            "translation_basis": "human_revised_translation" if has_revised else thin.get("translation_basis"),
            "sequence_source": None,
            "evidence_raw": thin.get("evidence_raw") or thin.get("text_lzh") or "",
            "certainty": reviewed_chunk_certainty(item.get("certainty", "confirmed") for item in all_mentions),
            "review_status": "reviewed",
            "entities": entities,
            "topics": annotation.get("topics", []),
            "places": list(dict.fromkeys(item["entity_id"] for item in annotation["places"])),
            "temporal_range": thin.get("temporal_range"),
            "metadata": thin.get("metadata", {}),
            "provenance": {
                "generated_by": GENERATED_BY,
                "generated_at": generated_at,
                "data_commit": data_commit,
            },
        }
        validate_rag_chunk(chunk)
        reviewed_chunks.append(chunk)

    write_jsonl(REVIEWED_CHUNKS_PATH, reviewed_chunks)
    return reviewed_chunks


def build_entity_dossier_chunks() -> list[dict[str, Any]]:
    authorities = load_authorities()
    annotations = load_annotations()
    generated_at = iso_now()
    data_commit = get_git_commit()
    thin_chunks = {
        row["source_entry_ids"][0]: row
        for row in load_jsonl(THIN_CHUNKS_PATH)
        if row.get("source_entry_ids")
    }

    preferred_targets = [
        ("person", "郭畀"),
        ("person", "龔子敬"),
        ("person", "潘伯起"),
        ("person", "張德輝"),
        ("person", "李叔義"),
        ("person", "趙子昂"),
        ("place", "杭州"),
        ("place", "平江"),
    ]
    selected_ids: list[str] = []
    for entity_type, label in preferred_targets:
        for authority in authorities[entity_type].values():
            if authority["label_original"] == label:
                selected_ids.append(authority["id"])
                break
    if len(selected_ids) < 8:
        for entity_type in ("person", "place"):
            for authority in sorted(authorities[entity_type].values(), key=lambda item: item["id"]):
                if authority["id"] in selected_ids:
                    continue
                selected_ids.append(authority["id"])
                if len(selected_ids) >= 8:
                    break
            if len(selected_ids) >= 8:
                break

    dossier_chunks: list[dict[str, Any]] = []
    for entity_id in selected_ids:
        entity_type = infer_entity_type_from_id(entity_id)
        authority = authorities[entity_type][entity_id]
        source_entry_ids = sorted(
            {
                annotation["entry_id"]
                for annotation in annotations
                for field in ("persons", "places", "offices", "institutions")
                if any(item["entity_id"] == entity_id for item in annotation[field])
            }
        ) or [authority["first_seen_entry_id"]]
        evidence_raw = thin_chunks[source_entry_ids[0]].get("evidence_raw") or thin_chunks[source_entry_ids[0]].get("text_lzh") or ""
        text_ko = (
            f"{authority['label_original']}는 항주 gold-set에서 {len(source_entry_ids)}개 entry에 등장한다. "
            f"첫 등장은 {authority['first_seen_entry_id']}이며, 관련 entry는 {', '.join(source_entry_ids)}이다."
        )
        if entity_type == "person" and authority.get("appointments"):
            office_labels = ", ".join(
                dict.fromkeys(
                    authorities["office"].get(item["office_id"], {}).get("label_original", item["office_id"])
                    for item in authority["appointments"]
                )
            )
            text_ko += f" 확인된 직함 기록은 {office_labels}이다."
        if entity_type == "place" and authority.get("place_info", {}).get("parent_place_id"):
            parent_label = authorities["place"].get(authority["place_info"]["parent_place_id"], {}).get(
                "label_original", authority["place_info"]["parent_place_id"]
            )
            text_ko += f" 상위 장소는 {parent_label}이다."
        if entity_type == "person" and authority["id"] == SELF_PERSON_ID:
            text_ko += " 이 일기 gold-set의 서술 주체이자 이동·방문·교유 행위의 중심 인물이다."

        chunk = {
            "chunk_id": f"chunk-dossier-{entity_id}",
            "chunk_type": "entity_dossier",
            "source_entry_ids": source_entry_ids,
            "source_sequence_id": None,
            "source_entity_id": entity_id,
            "sequence_type": None,
            "source_text_pointer": None,
            "text_ko": text_ko,
            "text_lzh": None,
            "translation_basis": "researcher_summary",
            "sequence_source": None,
            "evidence_raw": evidence_raw,
            "certainty": "confirmed",
            "review_status": "reviewed",
            "entities": [{"entity_id": entity_id, "entity_type": entity_type, "label": authority["label_original"]}],
            "topics": [],
            "places": [entity_id] if entity_type == "place" else [],
            "temporal_range": None,
            "metadata": {},
            "provenance": {
                "generated_by": GENERATED_BY,
                "generated_at": generated_at,
                "data_commit": data_commit,
            },
        }
        validate_rag_chunk(chunk)
        dossier_chunks.append(chunk)

    write_jsonl(DOSSIER_CHUNKS_PATH, dossier_chunks)
    return dossier_chunks


def generate_semantic_assertions() -> list[dict[str, Any]]:
    authorities = load_authorities()
    annotations = load_annotations()
    thin_chunks = {
        row["source_entry_ids"][0]: row
        for row in load_jsonl(THIN_CHUNKS_PATH)
        if row.get("source_entry_ids")
    }
    generated_at = iso_now()
    assertions: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str, str]] = set()

    def find_entity(label: str, entity_type: str) -> str | None:
        for authority in authorities[entity_type].values():
            if authority["label_original"] == label:
                return authority["id"]
            if any(alias["surface"] == label for alias in authority.get("aliases", [])):
                return authority["id"]
        return None

    def label_of(entity_id: str) -> str:
        if entity_id == SELF_PERSON_ID:
            return SELF_PERSON_LABEL
        entity_type = infer_entity_type_from_id(entity_id)
        authority = authorities.get(entity_type, {}).get(entity_id)
        return authority["label_original"] if authority else entity_id

    def add(assertion_type: str, subject_id: str, predicate: str, object_id: str, entry_id: str, *, certainty: str = "confirmed", qualifiers: dict[str, Any] | None = None, certainty_reason: str | None = None) -> None:
        key = (assertion_type, subject_id, predicate, object_id)
        if key in seen_keys:
            return
        seen_keys.add(key)
        assertion = {
            "assertion_id": f"assert-{len(assertions)+1:05d}",
            "assertion_type": assertion_type,
            "subject": {"entity_id": subject_id, "label": label_of(subject_id)},
            "predicate": predicate,
            "object": {"entity_id": object_id, "value": label_of(object_id), "value_type": "entity"},
            "qualifiers": qualifiers or {},
            "source_entry_ids": [entry_id],
            "source_action": None,
            "evidence_raw": thin_chunks[entry_id].get("text_lzh") or thin_chunks[entry_id].get("evidence_raw") or "",
            "evidence_translation_ko": None,
            "certainty": certainty,
            "certainty_reason": certainty_reason,
            "negated": bool((qualifiers or {}).get("result") == "not_met"),
            "provenance": {"generated_by": GENERATED_BY, "generated_at": generated_at, "source_annotation_review": "reviewed"},
        }
        validate_assertion(assertion)
        assertions.append(assertion)

    # Curated pilot assertions.
    qiantang = find_entity("錢塘", "place")
    bai = find_entity("白湛淵", "person")
    cai = find_entity("蔡德甫", "person")
    bai_wujiu = find_entity("白无咎", "person")
    gong = find_entity("龔子敬", "person")
    hangzhou = find_entity("杭州", "place")
    zhang_yunxin = find_entity("張雲心", "person")
    xuantong = find_entity("玄同觀", "place")
    miaoxing = find_entity("妙行寺", "place") or find_entity("湖州市妙行寺", "place")
    zhaoziang = find_entity("趙子昂", "person")
    lishuyi = find_entity("李叔義", "person")
    shishui = find_entity("施水坊橋", "place")
    zhang_songjian = find_entity("張松㵎", "person")
    wu_linqing = find_entity("武臨淸", "person")
    shanzhang = find_entity("山長", "office")
    fupan = find_entity("府判", "office")
    tiju = find_entity("提舉", "office")

    if qiantang:
        add("person_action", SELF_PERSON_ID, "traveled_to", qiantang, "entry-0019")
    if bai:
        add("person_action", SELF_PERSON_ID, "visited", bai, "entry-0020", certainty="uncertain", qualifiers={"result": "not_met"}, certainty_reason="review notes mark the visit as unsuccessful")
    if cai:
        add("person_action", SELF_PERSON_ID, "visited", cai, "entry-0021")
    if bai_wujiu:
        add("person_action", SELF_PERSON_ID, "dined_with", bai_wujiu, "entry-0021")
    if gong:
        add("person_action", SELF_PERSON_ID, "visited", gong, "entry-0022")
        add("person_action", gong, "welcomed", SELF_PERSON_ID, "entry-0022")
    if hangzhou:
        add("person_action", SELF_PERSON_ID, "traveled_to", hangzhou, "entry-0025")
    if zhang_yunxin:
        add("person_action", SELF_PERSON_ID, "visited", zhang_yunxin, "entry-0026")
    if xuantong:
        add("person_action", SELF_PERSON_ID, "visited", xuantong, "entry-0026")
    if miaoxing:
        add("person_action", SELF_PERSON_ID, "visited", miaoxing, "entry-0026")
    if zhaoziang:
        add("person_action", SELF_PERSON_ID, "visited", zhaoziang, "entry-0027", certainty="uncertain", qualifiers={"result": "not_met"}, certainty_reason="review notes mark the attempt as unsuccessful")
    if lishuyi:
        add("person_action", SELF_PERSON_ID, "visited", lishuyi, "entry-0028")
    if gong and shanzhang:
        add("person_appointment", gong, "held_office", shanzhang, "entry-0022")
    if zhang_songjian and fupan:
        add("person_appointment", zhang_songjian, "held_office", fupan, "entry-0025")
    if wu_linqing and tiju:
        add("person_appointment", wu_linqing, "held_office", tiju, "entry-0025")
    if bai_wujiu and bai:
        add("person_relation", bai_wujiu, "son_of", bai, "entry-0021", certainty="probable", certainty_reason="review notes identify 白无咎 as 白湛淵의 아들")
    if shishui and hangzhou:
        add("place_relation", shishui, "located_in", hangzhou, "entry-0025")
    if xuantong and hangzhou:
        add("place_relation", xuantong, "located_in", hangzhou, "entry-0026")
    if miaoxing and hangzhou:
        add("place_relation", miaoxing, "located_in", hangzhou, "entry-0026")

    # Top up with a few annotation-derived assertions so the pilot remains within the spec range.
    for annotation in annotations:
        entry_id = annotation["entry_id"]
        if annotation.get("journey"):
            add("person_action", SELF_PERSON_ID, "traveled_to", annotation["journey"]["to"], entry_id)
            for via_id in annotation["journey"].get("via", []):
                add("person_action", SELF_PERSON_ID, "traveled_via", via_id, entry_id, certainty="probable")
        for interaction in annotation.get("interactions", [])[:2]:
            target_id = interaction.get("target")
            if not target_id:
                continue
            predicate = "visited"
            if interaction.get("action") == "dined_with":
                predicate = "dined_with"
            elif interaction.get("action") == "travel_with":
                predicate = "friend_of"
            elif interaction.get("action") == "welcome":
                predicate = "welcomed"
            result = interaction.get("result")
            add(
                "person_action" if predicate not in {"friend_of"} else "person_relation",
                SELF_PERSON_ID,
                predicate,
                target_id,
                entry_id,
                certainty="uncertain" if result == "not_met" else "confirmed",
                qualifiers={"result": result} if result == "not_met" else None,
                certainty_reason=interaction.get("notes"),
            )
        if len(assertions) >= 22:
            break

    assertions = assertions[:25]
    write_jsonl(ASSERTIONS_PATH, assertions)
    return assertions


def generate_graph() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    assertions = load_jsonl(ASSERTIONS_PATH)
    authorities = load_authorities()
    generated_at = iso_now()
    nodes: dict[str, dict[str, Any]] = {}
    edge_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    def ensure_node(entity_id: str) -> None:
        if entity_id in nodes:
            return
        entity_type = infer_entity_type_from_id(entity_id)
        authority = authorities.get(entity_type, {}).get(entity_id)
        label = authority["label_original"] if authority else entity_id
        node = {
            "node_id": entity_id,
            "node_type": entity_type,
            "label": label,
            "label_lzh": label,
            "label_ko": authority.get("label_normalized") if authority else None,
            "source_entity_id": entity_id,
            "source_event_id": None,
            "source_sequence_id": None,
            "attributes": {
                "entity_type": entity_type,
                "place_type": authority.get("place_info", {}).get("place_type") if authority else None,
                "admin_level": authority.get("place_info", {}).get("admin_level") if authority else None,
                "institution_type": authority.get("institution_info", {}).get("institution_type") if authority else None,
                "first_seen_entry": authority.get("first_seen_entry_id") if authority else None,
                "entry_count": None,
                "certainty_summary": "confirmed" if authority else "unresolved",
            },
            "provenance": {"generated_by": GENERATED_BY, "generated_at": generated_at},
        }
        validate_node(node)
        nodes[entity_id] = node

    for assertion in assertions:
        ensure_node(assertion["subject"]["entity_id"])
        if assertion["object"].get("entity_id"):
            ensure_node(assertion["object"]["entity_id"])
            edge_type = "visited_not_met" if assertion["predicate"] == "visited" and assertion.get("qualifiers", {}).get("result") == "not_met" else assertion["predicate"]
            edge_groups[(assertion["subject"]["entity_id"], assertion["object"]["entity_id"], edge_type)].append(assertion)

    edges: list[dict[str, Any]] = []
    for index, ((source_node, target_node, edge_type), bucket) in enumerate(sorted(edge_groups.items()), start=1):
        edge = {
            "edge_id": f"edge-{index:05d}",
            "source_node": source_node,
            "target_node": target_node,
            "edge_type": edge_type,
            "weight": len(bucket),
            "temporal_range": None,
            "source_assertion_ids": [item["assertion_id"] for item in bucket],
            "source_entry_ids": sorted({entry_id for item in bucket for entry_id in item["source_entry_ids"]}),
            "certainty": edge_certainty(item["certainty"] for item in bucket),
            "review_status": "reviewed",
            "provenance": {"generated_by": GENERATED_BY, "generated_at": generated_at},
        }
        validate_edge(edge)
        edges.append(edge)

    write_jsonl(GRAPH_NODES_PATH, nodes.values())
    write_jsonl(GRAPH_EDGES_PATH, edges)
    return list(nodes.values()), edges


def build_demo_queries() -> list[dict[str, Any]]:
    reviewed_chunks = {row["chunk_id"]: row for row in load_jsonl(REVIEWED_CHUNKS_PATH)}
    dossier_chunks = {row["chunk_id"]: row for row in load_jsonl(DOSSIER_CHUNKS_PATH)}
    gong_chunk_id = next((chunk_id for chunk_id, row in dossier_chunks.items() if row["source_entity_id"].startswith("person-") and "龔子敬" in row["text_ko"]), None)
    demo_queries = [
        {
            "query_id": "demo-q01",
            "question_ko": "곽비가 항주에 도착한 과정은?",
            "expected_chunks": ["chunk-entry-0025"],
            "expected_chunk_types": ["entry"],
            "design_principle_demonstrated": "route 구조화, reviewed chunk의 translation_basis 추적",
            "sample_answer_ko": reviewed_chunks["chunk-entry-0025"]["text_ko"][:180],
            "answer_evidence_raw": reviewed_chunks["chunk-entry-0025"]["evidence_raw"],
            "answer_certainty": reviewed_chunks["chunk-entry-0025"]["certainty"],
            "answer_review_status": reviewed_chunks["chunk-entry-0025"]["review_status"],
        },
        {
            "query_id": "demo-q02",
            "question_ko": "龔子敬은 누구인가?",
            "expected_chunks": [gong_chunk_id] if gong_chunk_id else [],
            "expected_chunk_types": ["entity_dossier"],
            "design_principle_demonstrated": "entity dossier, person/office 분리",
            "sample_answer_ko": dossier_chunks[gong_chunk_id]["text_ko"] if gong_chunk_id else "",
            "answer_evidence_raw": dossier_chunks[gong_chunk_id]["evidence_raw"] if gong_chunk_id else "",
            "answer_certainty": dossier_chunks[gong_chunk_id]["certainty"] if gong_chunk_id else "confirmed",
            "answer_review_status": dossier_chunks[gong_chunk_id]["review_status"] if gong_chunk_id else "reviewed",
        },
        {
            "query_id": "demo-q03",
            "question_ko": "곽비가 방문했으나 만나지 못한 사람은?",
            "expected_chunks": ["chunk-entry-0020", "chunk-entry-0027"],
            "expected_chunk_types": ["entry", "entry"],
            "design_principle_demonstrated": "ambiguity 보존, not_met assertion 처리",
            "sample_answer_ko": "곽비는 白湛淵과 趙子昂을 찾아갔으나 만나지 못했다.",
            "answer_evidence_raw": reviewed_chunks["chunk-entry-0027"]["evidence_raw"],
            "answer_certainty": "uncertain",
            "answer_review_status": "reviewed",
        },
        {
            "query_id": "demo-q04",
            "question_ko": "항주 성내에서 방문한 장소들은?",
            "expected_chunks": ["chunk-entry-0026"],
            "expected_chunk_types": ["entry"],
            "design_principle_demonstrated": "spatial hierarchy, reviewed entry chunk의 places 배열",
            "sample_answer_ko": reviewed_chunks["chunk-entry-0026"]["text_ko"][:180],
            "answer_evidence_raw": reviewed_chunks["chunk-entry-0026"]["evidence_raw"],
            "answer_certainty": reviewed_chunks["chunk-entry-0026"]["certainty"],
            "answer_review_status": reviewed_chunks["chunk-entry-0026"]["review_status"],
        },
        {
            "query_id": "demo-q05",
            "question_ko": "조맹부(趙子昂)와의 만남은?",
            "expected_chunks": ["chunk-entry-0027"],
            "expected_chunk_types": ["entry"],
            "design_principle_demonstrated": "rewrite_needed entry의 reviewed annotation과 not_met assertion 연결",
            "sample_answer_ko": reviewed_chunks["chunk-entry-0027"]["text_ko"][:180],
            "answer_evidence_raw": reviewed_chunks["chunk-entry-0027"]["evidence_raw"],
            "answer_certainty": "uncertain",
            "answer_review_status": reviewed_chunks["chunk-entry-0027"]["review_status"],
        },
    ]
    write_json(DEMO_QUERIES_PATH, demo_queries)
    return demo_queries


def run_all() -> None:
    convert_reviews_to_annotations()
    create_authority_files()
    build_reviewed_entry_chunks()
    build_entity_dossier_chunks()
    generate_semantic_assertions()
    generate_graph()
    build_demo_queries()


__all__ = [
    "build_demo_queries",
    "build_entity_dossier_chunks",
    "build_reviewed_entry_chunks",
    "convert_reviews_to_annotations",
    "create_authority_files",
    "generate_graph",
    "generate_semantic_assertions",
    "run_all",
]


if __name__ == "__main__":
    run_all()
