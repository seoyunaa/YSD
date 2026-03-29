#!/usr/bin/env python3
"""Rebuild the public pilot outputs from reviewed annotations only."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from phase_d_pipeline import (
    ENTITY_DIR,
    ASSERTIONS_PATH,
    REVIEWED_CHUNKS_PATH,
    DOSSIER_CHUNKS_PATH,
    GRAPH_NODES_PATH,
    GRAPH_EDGES_PATH,
    build_reviewed_entry_chunks,
    build_entity_dossier_chunks,
    generate_semantic_assertions,
    generate_graph,
    build_demo_queries,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def referenced_entity_ids() -> set[str]:
    entity_ids: set[str] = set()

    for chunk in load_jsonl(DOSSIER_CHUNKS_PATH):
        source_entity_id = chunk.get("source_entity_id")
        if source_entity_id:
            entity_ids.add(source_entity_id)
        for entity in chunk.get("entities", []):
            entity_id = entity.get("entity_id")
            if entity_id:
                entity_ids.add(entity_id)

    for assertion in load_jsonl(ASSERTIONS_PATH):
        subject_id = assertion.get("subject", {}).get("entity_id")
        object_id = assertion.get("object", {}).get("entity_id")
        if subject_id:
            entity_ids.add(subject_id)
        if object_id:
            entity_ids.add(object_id)

    return {
        entity_id
        for entity_id in entity_ids
        if entity_id.startswith(("person-", "place-", "office-", "institution-"))
    }


def authority_path_for(entity_id: str) -> Path:
    if entity_id.startswith("person-"):
        return ENTITY_DIR / "persons" / f"{entity_id}.json"
    if entity_id.startswith("place-"):
        return ENTITY_DIR / "places" / f"{entity_id}.json"
    if entity_id.startswith("office-"):
        return ENTITY_DIR / "offices" / f"{entity_id}.json"
    if entity_id.startswith("institution-"):
        return ENTITY_DIR / "institutions" / f"{entity_id}.json"
    raise ValueError(f"Unsupported entity id: {entity_id}")


def collect_authority_closure(seed_ids: set[str]) -> set[str]:
    queue: deque[str] = deque(sorted(seed_ids))
    closure: set[str] = set()

    while queue:
        entity_id = queue.popleft()
        if entity_id in closure:
            continue
        path = authority_path_for(entity_id)
        if not path.exists():
            continue
        closure.add(entity_id)
        authority = load_json(path)

        if entity_id.startswith("person-"):
            for relation in authority.get("relations", []):
                related_id = relation.get("related_entity_id")
                if related_id and related_id not in closure:
                    queue.append(related_id)
            for appointment in authority.get("appointments", []):
                for key in ("office_id", "institution_id", "place_id"):
                    related_id = appointment.get(key)
                    if related_id and related_id not in closure:
                        queue.append(related_id)
            for residence in authority.get("residences", []):
                related_id = residence.get("place_id")
                if related_id and related_id not in closure:
                    queue.append(related_id)

        if entity_id.startswith("place-"):
            parent_id = authority.get("place_info", {}).get("parent_place_id")
            if parent_id and parent_id not in closure:
                queue.append(parent_id)

        if entity_id.startswith("institution-"):
            institution_info = authority.get("institution_info", {})
            for key in ("place_id", "parent_institution_id"):
                related_id = institution_info.get(key)
                if related_id and related_id not in closure:
                    queue.append(related_id)

    return closure


def prune_authorities_to_public_subset() -> None:
    keep_ids = collect_authority_closure(referenced_entity_ids())
    keep_by_dir: dict[str, set[str]] = defaultdict(set)

    for entity_id in keep_ids:
        if entity_id.startswith("person-"):
            keep_by_dir["persons"].add(entity_id)
        elif entity_id.startswith("place-"):
            keep_by_dir["places"].add(entity_id)
        elif entity_id.startswith("office-"):
            keep_by_dir["offices"].add(entity_id)
        elif entity_id.startswith("institution-"):
            keep_by_dir["institutions"].add(entity_id)

    for directory_name in ("persons", "places", "offices", "institutions"):
        directory = ENTITY_DIR / directory_name
        if not directory.exists():
            continue
        for path in directory.glob("*.json"):
            if path.stem == "_template":
                continue
            if path.stem not in keep_by_dir[directory_name]:
                path.unlink()


def main() -> None:
    build_reviewed_entry_chunks()
    build_entity_dossier_chunks()
    generate_semantic_assertions()
    generate_graph()
    build_demo_queries()
    prune_authorities_to_public_subset()


if __name__ == "__main__":
    main()
