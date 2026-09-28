#!/usr/bin/env python3
"""Validate traceability and digest-bound plan reviews; never authorize execution."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from common import InvalidPlan, REVISION, file_bytes, file_hashes, load_json, markdown_links, need, safe_path, string_list, text, verify_snapshot


def records(plan: dict[str, Any], name: str, prefix: str, required: bool = False) -> dict[str, dict[str, Any]]:
    values = plan.get(name)
    need(isinstance(values, list), f"{name}: array required")
    need(not required or bool(values), f"{name}: cannot be empty")
    result: dict[str, dict[str, Any]] = {}
    for record in values:
        need(isinstance(record, dict), f"{name}: object required")
        ident = record.get("id")
        need(isinstance(ident, str) and bool(re.fullmatch(re.escape(prefix) + r"[A-Z0-9-]+", ident)),
             f"{name}: invalid ID {ident!r}; expected {prefix}...")
        need(ident not in result, f"{name}: duplicate ID {ident}")
        result[ident] = record
    return result


def refs(record: dict[str, Any], key: str, target: dict[str, Any], required: bool = False) -> list[str]:
    values = string_list(record.get(key), f"{record.get('id', '?')}.{key}", required)
    need(set(values) <= set(target), f"{record.get('id', '?')}.{key}: unknown references {sorted(set(values) - set(target))}")
    return values


def validate_review_options(policy: dict[str, Any]) -> None:
    """Optional v1 extensions. Legacy packets remain valid; strict runs opt in."""
    need(type(policy.get("per_file_verdicts", False)) is bool,
         "review_policy.per_file_verdicts must be boolean")
    constraints = policy.get("reviewer_constraints", {})
    need(isinstance(constraints, dict), "reviewer_constraints must be an object")
    need(set(constraints) <= set(policy["roles"]), "Constraints refer to an unconfigured reviewer role")
    for role, values in constraints.items():
        need(isinstance(values, dict) and bool(values), f"{role}: nonempty reviewer constraints required")
        need(set(values) <= {"provider", "model", "model_alias", "effort"},
             f"{role}: unsupported reviewer constraint")
        for key, value in values.items():
            text(value, f"{role}.{key} constraint")


def validate_file_verdicts(report: dict[str, Any], manifest: dict[str, Any],
                           plan: dict[str, Any], findings: dict[str, Any]) -> None:
    """Check per-file declarations, not reviewer identity or semantic adequacy."""
    values = report.get("file_verdicts")
    if values is None and not plan["review_policy"].get("per_file_verdicts", False):
        return
    need(isinstance(values, dict), "Per-file verdicts are required for this run")
    need(set(values) == set(manifest["files"]), "Per-file verdicts must cover exactly every packet file")
    prereqs = {p["id"]: p for p in plan["prerequisites"]}
    attributed: set[str] = set()
    for name, entry in values.items():
        need(isinstance(entry, dict), f"{name}: file verdict must be an object")
        need(entry.get("sha256") == manifest["files"][name], f"{name}: stale per-file verdict hash")
        verdict = entry.get("verdict")
        need(verdict in {"accept", "watch", "request_changes"}, f"{name}: invalid per-file verdict")
        selected = refs({"id": name, **entry}, "finding_ids", findings)
        gates = refs({"id": name, **entry}, "prerequisite_ids", prereqs)
        attributed.update(selected)
        open_material = any(findings[i]["severity"] in {"blocker", "major"}
                            and findings[i]["status"] != "resolved" for i in selected)
        open_notes = any(findings[i]["status"] != "resolved" for i in selected)
        open_gates = any(prereqs[i]["status"] == "open" for i in gates)
        need(verdict == "request_changes" or not open_material,
             f"{name}: accepting file has an open material finding")
        if verdict == "accept":
            need(not open_notes and not open_gates,
                 f"{name}: open notes or conditions must remain visible as watch/request_changes")
        if verdict == "watch":
            need(open_notes or open_gates, f"{name}: watch needs an explicit unresolved note or prerequisite")
        if report.get("verdict") == "accept":
            need(verdict != "request_changes", f"{name}: file rejects an accepting packet")
    # Resolved historical findings may refer only to deleted files. Open ones may not disappear.
    need({i for i, f in findings.items() if f["status"] != "resolved"} <= attributed,
         "Every unresolved finding must be attributed to at least one file")


def validate_content(root: Path, ready: bool = False) -> dict[str, Any]:
    plan = load_json(root / "plan.json")
    need(type(plan.get("schema_version")) is int and plan["schema_version"] == 1, "Unsupported plan schema")
    text(plan.get("task_id"), "task_id")
    need(plan.get("profile") in {"generic", "bff-crud"}, "Unknown profile")
    string_list(plan.get("authors"), "authors", True)
    policy = plan.get("review_policy")
    need(isinstance(policy, dict), "review_policy required")
    roles = string_list(policy.get("roles"), "review_policy.roles", True)
    need(all(re.fullmatch(r"[a-z][a-z0-9-]*", role) for role in roles), "Unsafe reviewer role")
    need("critic" in roles, "An independent critic is required")
    if plan["profile"] == "bff-crud":
        need("architect" in roles, "bff-crud requires architect and critic")
    need(type(policy.get("max_rounds")) is int and 1 <= policy["max_rounds"] <= 10, "max_rounds must be 1..10")
    need(type(policy.get("require_model_diversity")) is bool, "require_model_diversity must be boolean")
    validate_review_options(policy)
    council = plan.get("council")
    need(isinstance(council, dict) and type(council.get("enabled")) is bool, "council.enabled must be boolean")
    topics = string_list(council.get("allowed_topics"), "council.allowed_topics")
    if council["enabled"]:
        text(council.get("delegation_ref"), "Council requires explicit user delegation")
        need(bool(topics), "Council delegation must name allowed topics")
    repos = records(plan, "repositories", "REPO-", True)
    for repo in repos.values():
        need(repo.get("working_tree") in {"clean", "dirty", "unavailable"}, "Unknown working-tree state")
        text(repo.get("scope"), f"{repo['id']}.scope")
        if repo["working_tree"] != "unavailable":
            need(isinstance(repo.get("revision"), str) and bool(re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", repo["revision"])),
                 f"{repo['id']}: full Git commit hash required")
        if repo["working_tree"] == "dirty":
            text(repo.get("worktree_snapshot_ref"), "Dirty tree requires separately identified snapshot evidence")
    capabilities = plan.get("capabilities")
    need(isinstance(capabilities, list), "capabilities: array required")
    capability_names: set[str] = set()
    for cap in capabilities:
        need(isinstance(cap, dict), "Capability must be an object")
        name = text(cap.get("name"), "capability name")
        need(name not in capability_names, "Duplicate capability")
        capability_names.add(name)
        need(cap.get("status") in {"available", "unavailable", "unverified"}, "Unknown capability status")
        text(cap.get("evidence"), f"Capability {name} needs evidence or an explanation of unavailability")
    need({"native-analysis", "user-interaction", "native-planning", "native-council", "independent-review"} <= capability_names,
         "Preflight must record native-analysis, user-interaction, native-planning, native-council and independent-review")

    reqs = records(plan, "requirements", "REQ-", True)
    evidence = records(plan, "evidence", "EVD-", True)
    decisions = records(plan, "decisions", "DEC-", True)
    tasks = records(plan, "tasks", "TASK-", True)
    tests = records(plan, "tests", "TEST-", True)
    apis = records(plan, "api_inventory", "API-", plan["profile"] == "bff-crud")
    questions = records(plan, "open_questions", "Q-")
    prereqs = records(plan, "prerequisites", "PRE-")
    for ev in evidence.values():
        need(ev.get("kind") in {"source", "runtime", "user", "contract", "inference", "artifact"}, f"{ev['id']}: unknown evidence kind")
        text(ev.get("ref"), f"{ev['id']}.ref")
        text(ev.get("claim"), f"{ev['id']}.claim")
        if ev["kind"] in {"source", "contract"}:
            need(ev.get("repository_id") in repos, f"{ev['id']}: unknown repository")
            repo = repos[ev["repository_id"]]
            need(repo["working_tree"] != "unavailable" and ev.get("revision") == repo.get("revision"),
                 f"{ev['id']}: source evidence must match an accessible pinned revision")
        if ev["kind"] == "artifact":
            need(isinstance(ev.get("artifact_sha256"), str)
                 and bool(re.fullmatch(r"[a-f0-9]{64}", ev["artifact_sha256"])),
                 f"{ev['id']}: imported artifact needs its captured byte hash")
            text(ev.get("observed_at"), f"{ev['id']}.observed_at")
        if ev["kind"] == "runtime":
            text(ev.get("environment"), f"{ev['id']}.environment")
            text(ev.get("observed_at"), f"{ev['id']}.observed_at")
            text(ev.get("build_ref"), f"{ev['id']}.build_ref")
    for req in reqs.values():
        text(req.get("text"), f"{req['id']}.text")
        need(type(req.get("in_scope")) is bool, "in_scope must be boolean")
        if not req["in_scope"]:
            text(req.get("exclusion_reason"), f"{req['id']}: excluded requirement needs a reason")
    for decision in decisions.values():
        text(decision.get("decision"), f"{decision['id']}.decision")
        need(decision.get("origin") in {"user", "council", "code", "assumption"}, "Unknown decision origin")
        need(decision.get("category") in {"architecture", "product", "security", "local"}, "Unknown decision category")
        need(type(decision.get("accepted")) is bool, "accepted must be boolean")
        refs(decision, "evidence_ids", evidence, True)
        if decision["accepted"]:
            text(decision.get("authority_ref"), f"{decision['id']}: accepted decision needs its authority/provenance")
            if decision["origin"] == "council":
                need(council["enabled"] and decision.get("topic") in topics,
                     f"{decision['id']}: council decision exceeds user delegation")
                need(decision["category"] != "security", "Council cannot waive security requirements")
            if decision["origin"] == "assumption":
                need(decision["category"] == "local" and decision.get("reversible") is True,
                     "Only reversible local technical assumptions may be accepted without authority")
    for test in tests.values():
        refs(test, "requirement_ids", reqs, True)
        need(test.get("stage") in {"test-first", "regression", "manual", "contract"}, "Unknown test stage")
        need(test.get("level") in {"unit", "integration", "contract", "e2e", "manual"}, "Unknown test level")
        text(test.get("method"), f"{test['id']}.method")
        text(test.get("expected"), f"{test['id']}.expected")
        if test["stage"] == "test-first":
            text(test.get("red_oracle"), f"{test['id']}.red_oracle")
        need(test.get("status") == "planned", "This registry describes planned tests, not executed results")
    if plan["profile"] == "bff-crud":
        need(any(t["stage"] == "test-first" for t in tests.values()), "bff-crud requires a test-first scenario")
        need(any(t["stage"] == "regression" and t["level"] == "unit" for t in tests.values()),
             "bff-crud requires planned unit regression expansion")
    for task in tasks.values():
        task_reqs = refs(task, "requirement_ids", reqs, True)
        need(all(reqs[x]["in_scope"] for x in task_reqs), f"{task['id']}: cannot implement excluded requirements")
        selected = refs(task, "decision_ids", decisions, True)
        if ready:
            need(all(decisions[x]["accepted"] for x in selected), f"{task['id']}: unresolved decision")
        refs(task, "depends_on", tasks)
        selected_tests = refs(task, "test_ids", tests, True)
        covered = {r for test_id in selected_tests for r in tests[test_id]["requirement_ids"]}
        need(set(task_reqs) <= covered, f"{task['id']}: task requirements are not covered by its tests")
        for key in ["title", "owner", "outcome"]:
            text(task.get(key), f"{task['id']}.{key}")
        string_list(task.get("files"), f"{task['id']}.files", True)
    # Kahn's algorithm: no recursion limit on large plans.
    remaining = {key: set(value["depends_on"]) for key, value in tasks.items()}
    while remaining:
        free = {key for key, dependencies in remaining.items() if not dependencies}
        need(bool(free), f"Task dependency cycle: {sorted(remaining)}")
        remaining = {key: value - free for key, value in remaining.items() if key not in free}
    for req in reqs.values():
        if req["in_scope"]:
            need(any(req["id"] in task["requirement_ids"] for task in tasks.values()), f"{req['id']}: no task")
    if apis:
        text(plan.get("api_inventory_scope"), "API inventory scope/method required")
        refs({"id": "inventory", "evidence_ids": plan.get("api_inventory_evidence_ids")}, "evidence_ids", evidence, True)
    layers = {"contract", "handler", "persistence", "execution", "ui"}
    for api in apis.values():
        text(api.get("operation"), f"{api['id']}.operation")
        refs(api, "requirement_ids", reqs, True)
        need(api.get("disposition") in {"planned", "existing", "excluded"}, f"{api['id']}: unknown disposition")
        linked_tasks = refs(api, "task_ids", tasks, api["disposition"] == "planned")
        if api["disposition"] == "planned":
            covered_requirements = {r for t in linked_tasks for r in tasks[t]["requirement_ids"]}
            need(set(api["requirement_ids"]) <= covered_requirements,
                 f"{api['id']}: planned tasks do not cover API requirements")
        if api["disposition"] in {"excluded", "existing"}:
            text(api.get("reason"), f"{api['id']}: disposition needs a reason")
        coverage = api.get("coverage")
        need(isinstance(coverage, dict) and set(coverage) == layers, f"{api['id']}: all five evidence layers are required")
        unresolved = False
        for layer, entry in coverage.items():
            need(isinstance(entry, dict), "Coverage entry must be an object")
            state = entry.get("state")
            need(state in {"source-confirmed", "runtime-confirmed", "missing", "unknown", "not-applicable"}, "Unknown evidence state")
            ev_ids = refs({"id": f"{api['id']}.{layer}", **entry}, "evidence_ids", evidence)
            if state == "runtime-confirmed":
                need(bool(ev_ids) and any(evidence[e]["kind"] == "runtime" for e in ev_ids),
                     f"{api['id']}.{layer}: runtime claim needs observed runtime evidence")
            if state == "source-confirmed":
                need(bool(ev_ids) and any(evidence[e]["kind"] in {"source", "contract"} for e in ev_ids),
                     f"{api['id']}.{layer}: source claim needs pinned source evidence")
            if state in {"missing", "unknown", "not-applicable"}:
                text(entry.get("reason"), f"{api['id']}.{layer}: reason required")
            unresolved |= state in {"missing", "unknown"}
        refs(api, "resolution_task_ids", tasks, unresolved and api["disposition"] != "excluded")
    for question in questions.values():
        text(question.get("question"), f"{question['id']}.question")
        need(type(question.get("blocking")) is bool, "Question blocking must be boolean")
        need(question.get("status") in {"open", "answered", "delegated"}, "Unknown question status")
        selected = refs(question, "decision_ids", decisions, question["status"] == "answered")
        if ready and question["blocking"]:
            need(question["status"] == "answered" and all(decisions[x]["accepted"] for x in selected),
                 f"{question['id']}: unresolved material product question")
    for prereq in prereqs.values():
        text(prereq.get("condition"), f"{prereq['id']}.condition")
        text(prereq.get("owner"), f"{prereq['id']}.owner")
        need(prereq.get("status") in {"open", "satisfied"}, "Unknown prerequisite status")
        refs(prereq, "blocks_task_ids", tasks, True)
        resolution = refs(prereq, "resolution_task_ids", tasks, prereq["status"] == "open")
        if prereq["status"] == "open":
            for blocked in prereq["blocks_task_ids"]:
                ancestors: set[str] = set()
                pending = list(tasks[blocked]["depends_on"])
                while pending:
                    ancestor = pending.pop()
                    if ancestor not in ancestors:
                        ancestors.add(ancestor)
                        pending.extend(tasks[ancestor]["depends_on"])
                need(set(resolution) <= ancestors,
                     f"{prereq['id']}: resolution tasks must precede blocked tasks in the dependency graph")
        refs(prereq, "evidence_ids", evidence, prereq["status"] == "satisfied")
    if ready:
        available = {c["name"] for c in capabilities if c["status"] == "available"}
        need("independent-review" in available, "No available independent review capability")
        if council["enabled"]:
            need("native-council" in available, "Requested native council is unavailable or unverified")
        for name, data in file_bytes(root).items():
            if name.endswith(".md"):
                need(not re.search(r"\b(TODO|TBD|REPLACE_ME)\b|\{\{", data.decode("utf-8")),
                     f"{name}: unresolved placeholder in ready packet")
    markdown_links(root)
    return plan


def review_for(run: Path, revision: str, role: str, seen: set[str] | None = None) -> dict[str, Any]:
    seen = set() if seen is None else set(seen)
    need(revision not in seen, "Review inheritance cycle")
    seen.add(revision)
    manifest, root = verify_snapshot(run, revision)
    plan = validate_content(root)
    report = load_json(safe_path(run, f"reviews/{revision}.{role}.json"))
    need(type(report.get("schema_version")) is int and report["schema_version"] == 1, "Invalid review schema")
    need(report.get("role") == role and report.get("revision") == revision, "Reviewer role/revision mismatch")
    need(report.get("packet_digest") == manifest["packet_digest"], f"{role}: stale review digest")
    reviewer = text(report.get("reviewer_id"), f"{role}.reviewer_id")
    need(reviewer not in plan["authors"], f"{role}: author cannot independently review their own plan")
    text(report.get("provider"), f"{role}.provider")
    text(report.get("model"), f"{role}.model")
    for key, expected in plan["review_policy"].get("reviewer_constraints", {}).get(role, {}).items():
        need(report.get(key) == expected, f"{role}: reviewer {key} does not match configured constraint")
    text(report.get("summary"), f"{role}.summary")
    text(report.get("completed_at"), f"{role}.completed_at")
    all_files = set(manifest["files"])
    read = set(string_list(report.get("reviewed_files"), f"{role}.reviewed_files", True))
    inherited = set(string_list(report.get("inherited_files"), f"{role}.inherited_files"))
    deleted = set(string_list(report.get("acknowledged_deletions"), f"{role}.acknowledged_deletions"))
    need(read.isdisjoint(inherited) and read | inherited == all_files, f"{role}: review scope must partition the entire packet")
    mode = manifest.get("review_mode")
    need(report.get("mode") == mode and mode in {"full", "delta"}, f"{role}: review mode mismatch")
    if mode == "full":
        need(read == all_files and not inherited, f"{role}: full review must read every packet file")
    else:
        need(set(manifest.get("required_review_files", [])) <= read, f"{role}: changed/impacted files not reviewed")
    findings = records({"findings": report.get("findings")}, "findings", "F-")
    for finding in findings.values():
        need(finding.get("severity") in {"blocker", "major", "minor"}, "Unknown finding severity")
        need(finding.get("status") in {"open", "resolved", "accepted-risk"}, "Unknown finding status")
        text(finding.get("message"), f"{finding['id']}.message")
        if finding["status"] != "open":
            text(finding.get("resolution"), f"{finding['id']}.resolution")
        need(not (finding["status"] == "accepted-risk" and finding["severity"] != "minor"),
             "Major/blocking findings cannot be waived as minor accepted risk")
    validate_file_verdicts(report, manifest, plan, findings)
    base = manifest.get("base_revision")
    if base:
        base_manifest, _ = verify_snapshot(run, base)
        need(manifest.get("base_digest") == base_manifest["packet_digest"], "Wrong base digest")
        old = review_for(run, base, role, seen)
        old_findings = {finding["id"]: finding for finding in old["findings"]}
        if plan["review_policy"].get("per_file_verdicts", False):
            for name in inherited:
                need(report["file_verdicts"][name] == old["file_verdicts"][name],
                     f"{role}: inherited file verdict changed without re-review: {name}")
                need(all(findings.get(ident) == old_findings[ident]
                         for ident in old["file_verdicts"][name]["finding_ids"]),
                     f"{role}: inherited file finding changed without re-review: {name}")
        need(set(old_findings) <= set(findings), f"{role}: findings disappeared from the cumulative ledger")
        for ident, previous in old_findings.items():
            need(findings[ident]["severity"] == previous["severity"], f"{ident}: cannot reduce severity to bypass closure")
        changed = {name for name, sha in manifest["files"].items() if base_manifest["files"].get(name) != sha}
        need(changed <= read, f"{role}: changed files inherited without review")
        need(deleted == set(base_manifest["files"]) - all_files, f"{role}: deleted files not acknowledged")
    else:
        need(mode == "full" and not deleted, "First review must be full and have no inherited deletions")
    need(report.get("verdict") in {"accept", "request_changes"}, f"{role}: invalid verdict")
    blocking = [f for f in findings.values() if f["severity"] in {"major", "blocker"} and f["status"] != "resolved"]
    need(not (report["verdict"] == "accept" and blocking), f"{role}: accept contradicts open material findings")
    return report


def validate_run(run: Path, revision: str) -> dict[str, Any]:
    manifest, root = verify_snapshot(run, revision)
    plan = validate_content(root, ready=True)
    policy = plan["review_policy"]
    revision_names = [p.name for p in (run / "revisions").iterdir() if p.is_dir() and REVISION.fullmatch(p.name)]
    need(revision == max(revision_names, key=lambda x: int(x[1:])), "Final closure must use the latest revision")
    need(file_hashes(run / "draft") == manifest["files"],
         "Working draft differs from the reviewed packet; freeze and review a new revision")
    need(int(revision[1:]) <= policy["max_rounds"], "Review budget exhausted")
    reports = [review_for(run, revision, role) for role in policy["roles"]]
    need(all(r["verdict"] == "accept" for r in reports), "Independent reviewers have not accepted this revision")
    need(len({r["reviewer_id"] for r in reports}) == len(reports), "Roles require separate reviewer instances")
    if policy["require_model_diversity"]:
        need(len({(r["provider"], r["model"]) for r in reports}) >= 2, "Requested model diversity is missing")
    open_prereqs = [p["id"] for p in plan["prerequisites"] if p["status"] == "open"]
    return {"status": "READY_WITH_PREREQUISITES" if open_prereqs else "READY", "revision": revision,
            "packet_digest": manifest["packet_digest"], "open_prerequisites": open_prereqs,
            "implementation_authorized": False,
            "assurance": "Structural checks and recorded review declarations; not semantic proof or authenticated signatures."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--draft", action="store_true")
    group.add_argument("--revision")
    args = parser.parse_args()
    try:
        if args.draft:
            validate_content(args.run / "draft")
            result = {"status": "DRAFT_STRUCTURALLY_VALID", "implementation_authorized": False}
        else:
            result = validate_run(args.run, args.revision)
        code = 0
    except (InvalidPlan, OSError, ValueError, TypeError, KeyError) as exc:
        result = {"status": "NEEDS_WORK", "errors": [str(exc)], "implementation_authorized": False}
        code = 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
