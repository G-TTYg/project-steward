"""Portable schema, migrations, and invariants without filesystem mutations.

Run lifecycle, milestone acceptance, and progress events have separate semantics.
References use stable IDs; evidence provenance describes collection, never correctness.
"""

from __future__ import annotations

from copy import deepcopy
import datetime as dt
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any

RUN_STATUSES = {"active", "paused", "blocked", "complete", "cancelled"}
MILESTONE_STATUSES = {"pending", "in_progress", "verified", "failed", "skipped"}
EVIDENCE_STATUSES = {"passed", "failed", "skipped", "unavailable", "not_run"}
LEGACY_STATUS = {"active": "in_progress", "paused": "in_progress",
                 "blocked": "in_progress", "complete": "verified"}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def timestamp(value: Any) -> dt.datetime:
    require(isinstance(value, str), "timestamp must be an ISO-8601 string")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(parsed.tzinfo is not None, "timestamp must include a timezone")
        return parsed
    except ValueError:
        raise SystemExit(f"invalid timestamp: {value}") from None


def binding(project: Path, run: Path, repository: Path | None) -> dict:
    project, run = project.resolve(), run.resolve()
    repository = repository.resolve() if repository is not None else None
    require(project.is_dir() and run != project and run.is_relative_to(project),
            "run must be a subdirectory of its existing project")
    return {"root_relative": os.path.relpath(project, run).replace(os.sep, "/"),
            "run_relative": run.relative_to(project).as_posix(),
            "repository_subpath": project.relative_to(repository).as_posix() if repository else None}


def resolve_project(run: Path, state: dict) -> Path:
    run = run.resolve()
    project = state.get("project")
    require(isinstance(project, dict), "schema v3 project must be an object")
    root = project.get("root_relative")
    relative = project.get("run_relative")
    require(isinstance(root, str) and bool(re.fullmatch(r"\.\.(?:/\.\.)*", root)),
            "project root_relative must contain only parent steps relative to the run directory")
    require(isinstance(relative, str) and relative and "\\" not in relative
            and not PurePosixPath(relative).is_absolute()
            and all(p not in (".", "..") and ":" not in p for p in relative.split("/")),
            "project run_relative must be a safe project-relative path")
    resolved = (run / root).resolve()
    require(resolved.is_dir() and run != resolved and run.is_relative_to(resolved)
            and (resolved / relative).resolve() == run,
            "run path does not match its portable project binding")
    subpath = project.get("repository_subpath")
    require(subpath is None or (isinstance(subpath, str) and subpath
            and not PurePosixPath(subpath).is_absolute() and "\\" not in subpath
            and all(p != ".." and ":" not in p for p in subpath.split("/"))),
            "invalid repository_subpath")
    return resolved


def validate(state: Any) -> None:
    require(isinstance(state, dict), "run state must be an object")
    require(type(state.get("schema_version")) is int and state["schema_version"] == 3,
            "expected run-state schema v3")
    for key in ("run_id", "task", "summary", "next", "verification"):
        require(isinstance(state.get(key), str), f"run-state {key} must be text")
    require(bool(state["run_id"]) and bool(state["task"].strip()), "run identity/task cannot be empty")
    require(state.get("status") in RUN_STATUSES, "invalid run lifecycle status")
    require(type(state.get("revision")) is int and state["revision"] >= 1, "invalid revision")
    created, updated = timestamp(state.get("created_at")), timestamp(state.get("updated_at"))
    require(created <= updated, "updated_at precedes created_at")
    require(isinstance(state.get("workflow"), dict) and isinstance(state.get("git"), dict),
            "workflow and git must be objects")
    items = state.get("milestones")
    require(isinstance(items, list), "milestones must be a list")
    ids = set()
    verified = []
    for item in items:
        require(isinstance(item, dict), "milestone must be an object")
        mid = item.get("id")
        require(isinstance(mid, str) and bool(re.fullmatch(r"M-\d{3,}", mid)) and mid not in ids,
                "milestone IDs must be unique M-001 identifiers")
        ids.add(mid)
        require(isinstance(item.get("name"), str) and bool(item["name"].strip()), "milestone needs a name")
        require(item.get("status") in MILESTONE_STATUSES, "invalid milestone status")
        recorded = timestamp(item.get("recorded_at"))
        require(created <= recorded <= updated, "milestone time outside run lifetime")
        require(isinstance(item.get("verification"), str), "milestone verification must be text")
        if item["status"] == "verified":
            require(bool(item["verification"].strip()), "verified milestone requires explicit evidence")
            completed = timestamp(item.get("completed_at"))
            require(recorded <= completed <= updated, "invalid milestone completion time")
            require(type(item.get("verified_revision")) is int
                    and 1 <= item["verified_revision"] <= state["revision"], "invalid milestone verification revision")
            verified.append(item)
        if "commit" in item:
            require(isinstance(item["commit"], str) and bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", item["commit"])),
                    "implementation commit must be a full SHA")
            require(item.get("commit_relationship") == "caller_attached", "commit relationship must be explicit")
    require(state.get("current_milestone") is None or state["current_milestone"] in ids,
            "current_milestone must reference a real milestone ID")
    last = state.get("last_verified")
    expected = max(verified, key=lambda m: (m["verified_revision"], timestamp(m["completed_at"]), items.index(m)))["id"] if verified else None
    require(last == expected, "last_verified must reference the latest real verified milestone")
    events = state.get("events")
    require(isinstance(events, list) and len(events) == state["revision"], "event/revision mismatch")
    previous = created
    for revision, event in enumerate(events, 1):
        require(isinstance(event, dict) and type(event.get("revision")) is int
                and event["revision"] == revision and isinstance(event.get("text"), str),
                "invalid ordered event journal")
        stamp = timestamp(event.get("recorded_at"))
        require(previous <= stamp <= updated, "event times must be ordered within run lifetime")
        previous = stamp
    require(isinstance(state.get("log_prefix"), str), "log_prefix must be text")
    evidence = state.get("evidence")
    require(isinstance(evidence, list), "evidence must be a list")
    evidence_ids = set()
    for record in evidence:
        require(isinstance(record, dict), "evidence record must be an object")
        eid = record.get("id")
        require(isinstance(eid, str) and bool(re.fullmatch(r"V-\d{3,}", eid)) and eid not in evidence_ids,
                "evidence IDs must be unique V-001 identifiers")
        evidence_ids.add(eid)
        require(record.get("milestone_id") in ids, "evidence milestone reference is invalid")
        require(record.get("source") in {"reported", "observed", "independently_confirmed"}, "invalid evidence source")
        if record["source"] != "reported":
            provenance = record.get("provenance")
            require(isinstance(provenance, dict), "collected evidence requires adapter provenance")
            timestamp(provenance.get("observed_at"))
            if record["source"] == "observed":
                require(provenance.get("adapter") == "explicit-argv-v1", "invalid observed adapter")
                for key in ("before", "after"):
                    snap = provenance.get(key)
                    require(isinstance(snap, dict) and isinstance(snap.get("head"), str)
                            and bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", snap["head"]))
                            and isinstance(snap.get("files_sha256"), str)
                            and bool(re.fullmatch(r"[0-9a-f]{64}", snap["files_sha256"])), "invalid code snapshot")
                require(record.get("revision") == provenance["before"]["head"]
                        and provenance.get("source_changed") == (provenance["before"] != provenance["after"]), "inconsistent source observation")
                require(type(record.get("exit_code")) is int and type(record.get("timed_out")) is bool
                        and type(record.get("duration_seconds")) in (int, float)
                        and 0 <= record["duration_seconds"] < float("inf"), "invalid execution observation")
            else:
                require(provenance.get("adapter") == "github-actions-api-v1"
                        and isinstance(provenance.get("repository"), str)
                        and type(provenance.get("run_id")) is int and provenance["run_id"] > 0
                        and isinstance(provenance.get("jobs"), list) and provenance["jobs"]
                        and isinstance(record.get("revision"), str)
                        and bool(re.fullmatch(r"[0-9a-f]{40}", record["revision"])), "invalid CI provenance")
        require(record.get("claimed_source") in {"reported", "observed", "independently_confirmed"},
                "invalid claimed evidence source")
        require(record.get("status") in EVIDENCE_STATUSES, "invalid verification outcome")
        require(isinstance(record.get("summary"), str) and record["summary"].strip(), "evidence summary required")
        stamp = timestamp(record.get("recorded_at"))
        require(created <= stamp <= updated, "evidence time outside run lifetime")
        code = record.get("exit_code")
        require(code is None or type(code) is int, "exit_code must be an integer or null")
        if code is not None:
            require(record["status"] in {"passed", "failed"}
                    and ((code == 0) == (record["status"] == "passed")), "exit code contradicts outcome")
        for key in ("command", "environment", "revision", "scope"):
            require(record.get(key) is None or isinstance(record[key], str), f"evidence {key} must be text or null")
    for event in events:
        if event.get("milestone_id") is not None:
            require(event["milestone_id"] in ids, "checkpoint milestone reference is invalid")


def refresh_verified(state: dict) -> None:
    verified = [m for m in state["milestones"] if m["status"] == "verified"]
    state["last_verified"] = max(verified, key=lambda m: (m["verified_revision"], timestamp(m["completed_at"]),
                                   state["milestones"].index(m)))["id"] if verified else None


def next_id(items: list[dict], prefix: str) -> str:
    return f"{prefix}-{max((int(item['id'].split('-')[1]) for item in items), default=0) + 1:03d}"


def migrate(legacy: dict, project: Path, run: Path, repository: Path | None,
            old_log: str) -> tuple[dict, dict[str, str]]:
    """Normalize legacy data without inventing verification or commit ownership."""
    require(isinstance(legacy, dict), "run state must be an object")
    version = legacy.get("schema_version", 1)
    require(type(version) is int and version in (1, 2), f"unsupported run-state schema: {version}")
    require(isinstance(legacy.get("task"), str) and isinstance(legacy.get("project"), str),
            "legacy state requires project path and task")
    replacements = {legacy["project"]: "."} if legacy["project"] else {}
    old_repo = legacy.get("git", {}).get("repository") if isinstance(legacy.get("git", {}), dict) else None
    if isinstance(old_repo, str) and old_repo:
        replacements[old_repo] = "."

    def scrub(value):
        if isinstance(value, str):
            for old, new in sorted(replacements.items(), key=lambda p: -len(p[0])):
                for spelling in {old, old.replace("\\", "/"), old.replace("/", "\\")}:
                    value = value.replace(spelling, new)
            return value
        if isinstance(value, dict):
            return {key: scrub(val) for key, val in value.items()}
        if isinstance(value, list):
            return [scrub(val) for val in value]
        return value

    state = scrub(deepcopy(legacy))
    stamp = now_utc()
    created = state.get("created_at", stamp)
    timestamp(created)
    state.update(schema_version=3, revision=1, run_id=state.get("run_id", run.name),
                 project=binding(project, run, repository), updated_at=stamp, created_at=created,
                 log_prefix=scrub(old_log), events=[{"revision": 1, "recorded_at": stamp,
                 "text": "\n- Migrated legacy state; original files preserved in a local backup.\n"}], evidence=[])
    require(isinstance(state.get("milestones", []), list), "legacy milestones must be a list")
    for i, item in enumerate(state.setdefault("milestones", []), 1):
        require(isinstance(item, dict), "legacy milestone must be an object")
        item["id"] = f"M-{i:03d}"
        item["status"] = LEGACY_STATUS.get(item.get("status"), item.get("status"))
        item.setdefault("recorded_at", created)
        report = item.get("verification")
        if item["status"] == "verified" and not (isinstance(report, str) and report.strip()):
            item["legacy_status"] = item["status"]
            item["status"] = "in_progress"
            item.pop("completed_at", None)
        item.setdefault("verification", "Legacy verification report unavailable.")
        if item["status"] == "verified":
            item.setdefault("completed_at", item["recorded_at"])
            item["verified_revision"] = 1
        if "commit" in item:
            if isinstance(item["commit"], str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", item["commit"]):
                item["commit_relationship"] = "caller_attached"
            else:
                item["legacy_commit_report"] = item.pop("commit")
    current = state.get("current_milestone")
    matches = [m["id"] for m in state["milestones"] if m.get("name") == current]
    state["current_slice_name"] = current or ""
    state["current_milestone"] = matches[0] if len(matches) == 1 else None
    state.setdefault("workflow", {})
    state.setdefault("git", {})
    state.setdefault("summary", "Legacy progress")
    state.setdefault("next", "Reobserve the current project before continuing.")
    state.setdefault("verification", "Not reported.")
    state["status"] = "active" if state.get("status") == "verified" else state.get("status", "active")
    state["migration"] = {"from_schema": version, "legacy_status": legacy.get("status"),
                          "last_verified_recomputed": True}
    refresh_verified(state)
    validate(state)
    return state, replacements
