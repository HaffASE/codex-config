"""Synthetic regression cases derived from the reference-run failure modes.

No records here are real provider responses or project runtime evidence.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import test_plan_guard as legacy
from check_source_bundle import audit
from common import InvalidPlan, verify_snapshot
from freeze_plan import freeze
from validate_plan import validate_content, validate_run


class SourceAwareReviewTests(unittest.TestCase):
    setUp = legacy.PlanGuardTests.setUp
    tearDown = legacy.PlanGuardTests.tearDown
    save = legacy.PlanGuardTests.save
    report = legacy.PlanGuardTests.report
    report_save = legacy.PlanGuardTests.report_save

    def configure(self):
        self.plan["review_policy"]["per_file_verdicts"] = True
        self.plan["review_policy"]["reviewer_constraints"] = {
            "architect": {"provider": "synthetic-provider", "model_alias": "fixture-architect", "effort": "fixture-high"}}
        self.save()

    def reports(self, revision="r01", findings=None):
        legacy.PlanGuardTests.write_reports(self, revision, findings=findings)
        manifest, _ = verify_snapshot(self.run, revision)
        for role in self.plan["review_policy"]["roles"]:
            report = self.report(revision, role)
            report["model_alias"] = "fixture-architect" if role == "architect" else "fixture-critic"
            report["effort"] = "fixture-high"
            report["file_verdicts"] = {
                name: {"sha256": sha, "verdict": "accept", "finding_ids": [], "prerequisite_ids": []}
                for name, sha in manifest["files"].items()}
            if findings:
                report["file_verdicts"]["analysis.md"].update(
                    verdict="watch", finding_ids=[f["id"] for f in findings])
            self.report_save(revision, role, report)

    def prepared(self, findings=None):
        self.configure()
        freeze(self.run, "r01")
        self.reports(findings=findings)

    def rejected_report(self, mutate):
        self.prepared()
        report = self.report()
        mutate(report)
        self.report_save("r01", "architect", report)
        with self.assertRaises(InvalidPlan):
            validate_run(self.run, "r01")

    def test_strict_full_review_has_per_file_verdicts_without_execution(self):
        self.prepared()
        result = validate_run(self.run, "r01")
        self.assertEqual(result["status"], "READY")
        self.assertIs(result["implementation_authorized"], False)

    def test_missing_per_file_map_rejected(self):
        self.rejected_report(lambda r: r.pop("file_verdicts"))

    def test_one_file_verdict_missing_rejected(self):
        self.rejected_report(lambda r: r["file_verdicts"].pop("analysis.md"))

    def test_extra_file_verdict_rejected(self):
        self.rejected_report(lambda r: r["file_verdicts"].update({"not-in-packet.md": {}}))

    def test_stale_file_hash_rejected(self):
        self.rejected_report(lambda r: r["file_verdicts"]["analysis.md"].update(sha256="0" * 64))

    def test_file_request_changes_cannot_hide_under_accept(self):
        self.rejected_report(lambda r: r["file_verdicts"]["analysis.md"].update(verdict="request_changes"))

    def test_unexplained_watch_rejected(self):
        self.rejected_report(lambda r: r["file_verdicts"]["analysis.md"].update(verdict="watch"))

    def test_unknown_finding_rejected(self):
        self.rejected_report(lambda r: r["file_verdicts"]["analysis.md"].update(finding_ids=["F-404"]))

    def test_unknown_prerequisite_rejected(self):
        self.rejected_report(lambda r: r["file_verdicts"]["analysis.md"].update(prerequisite_ids=["PRE-404"]))

    def test_model_alias_constraint_rejected_on_fallback(self):
        self.rejected_report(lambda r: r.update(model_alias="fallback-model"))

    def test_effort_constraint_rejected_on_downgrade(self):
        self.rejected_report(lambda r: r.update(effort="fixture-low"))

    def test_constraint_unknown_role_rejected(self):
        self.configure()
        self.plan["review_policy"]["reviewer_constraints"]["absent"] = {"effort": "fixture-high"}
        self.save()
        with self.assertRaises(InvalidPlan): validate_content(self.run / "draft")

    def test_constraint_unknown_key_rejected(self):
        self.configure()
        self.plan["review_policy"]["reviewer_constraints"]["architect"]["temperature"] = "high"
        self.save()
        with self.assertRaises(InvalidPlan): validate_content(self.run / "draft")

    def test_minor_watch_is_not_blocking(self):
        finding = {"id": "F-NOTE", "severity": "minor", "status": "accepted-risk",
                   "message": "Synthetic wording issue", "resolution": "Recorded as nonblocking wording debt"}
        self.prepared([finding])
        self.assertEqual(validate_run(self.run, "r01")["status"], "READY")

    def test_watch_open_prerequisite_remains_conditional(self):
        self.plan["prerequisites"] = [{"id": "PRE-001", "owner": "backend", "status": "open",
            "condition": "Synthetic backend resolver contract is implemented", "resolution_task_ids": ["TASK-001"],
            "blocks_task_ids": ["TASK-002"], "evidence_ids": []}]
        self.prepared()
        for role in self.plan["review_policy"]["roles"]:
            report = self.report(role=role)
            report["file_verdicts"]["implementation.md"].update(verdict="watch", prerequisite_ids=["PRE-001"])
            self.report_save("r01", role, report)
        result = validate_run(self.run, "r01")
        self.assertEqual(result["status"], "READY_WITH_PREREQUISITES")
        self.assertIs(result["implementation_authorized"], False)

    def test_open_finding_cannot_disappear_from_file_map(self):
        finding = {"id": "F-NOTE", "severity": "minor", "status": "open",
                   "message": "Synthetic issue", "resolution": ""}
        self.prepared([finding])
        report = self.report()
        report["file_verdicts"]["analysis.md"].update(verdict="accept", finding_ids=[])
        self.report_save("r01", "architect", report)
        with self.assertRaises(InvalidPlan): validate_run(self.run, "r01")

    def test_inherited_watch_cannot_be_silently_cleared(self):
        finding = {"id": "F-NOTE", "severity": "minor", "status": "accepted-risk",
                   "message": "Synthetic issue", "resolution": "Documented note"}
        self.prepared([finding])
        with (self.run / "draft/tests.md").open("a") as handle:
            handle.write("\nChanged test instructions.\n")
        freeze(self.run, "r02", mode="delta", impact=["tests.md"], reason="Test-only synthetic delta")
        self.reports("r02", [finding])
        report = self.report("r02")
        report["findings"][0].update(status="resolved", resolution="Synthetic claimed correction")
        report["file_verdicts"]["analysis.md"].update(verdict="accept")
        self.report_save("r02", "architect", report)
        with self.assertRaisesRegex(InvalidPlan, "inherited file verdict changed"):
            validate_run(self.run, "r02")

    def test_strict_delta_with_unchanged_inherited_verdicts_passes(self):
        self.prepared()
        with (self.run / "draft/tests.md").open("a") as handle:
            handle.write("\nChanged synthetic test detail.\n")
        freeze(self.run, "r02", mode="delta", impact=["tests.md"], reason="Synthetic test-only change")
        self.reports("r02")
        self.assertEqual(validate_run(self.run, "r02")["status"], "READY")

    def test_inherited_finding_cannot_change_inside_unchanged_watch(self):
        findings = [
            {"id": "F-NOTE-1", "severity": "minor", "status": "open", "message": "Synthetic note 1", "resolution": ""},
            {"id": "F-NOTE-2", "severity": "minor", "status": "open", "message": "Synthetic note 2", "resolution": ""}]
        self.prepared(findings)
        with (self.run / "draft/tests.md").open("a") as handle:
            handle.write("\nChanged synthetic test detail.\n")
        freeze(self.run, "r02", mode="delta", impact=["tests.md"], reason="Synthetic test-only change")
        self.reports("r02", findings)
        report = self.report("r02")
        report["findings"][0].update(status="resolved", resolution="Claimed fix in an inherited file")
        self.report_save("r02", "architect", report)
        with self.assertRaisesRegex(InvalidPlan, "inherited file finding changed"):
            validate_run(self.run, "r02")

    def test_imported_artifact_is_valid_as_reported_evidence(self):
        self.plan["evidence"].append({"id": "EVD-REPORTED", "kind": "artifact", "ref": "imported/index.md:5",
            "claim": "The supplied index reports an earlier review outcome.",
            "artifact_sha256": "b" * 64, "observed_at": "2026-09-18T00:00:00Z"})
        self.save()
        self.assertEqual(validate_content(self.run / "draft")["evidence"][-1]["kind"], "artifact")

    def test_imported_artifact_is_not_source_confirmation(self):
        self.plan["evidence"][0].update(kind="artifact", artifact_sha256="b" * 64,
                                        observed_at="2026-09-18T00:00:00Z")
        self.save()
        with self.assertRaisesRegex(InvalidPlan, "source claim needs pinned source evidence"):
            validate_content(self.run / "draft")

    def test_imported_artifact_needs_captured_hash(self):
        self.plan["evidence"][0].update(kind="artifact", observed_at="2026-09-18T00:00:00Z")
        self.save()
        with self.assertRaisesRegex(InvalidPlan, "captured byte hash"):
            validate_content(self.run / "draft")


class SourceBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.logical = ".omx/artifacts/sample/index.md"
        (self.root / "index.md").write_text("# Supplied index\n", encoding="utf-8")
        self.mapping = {"schema_version": 1, "entrypoint": self.logical,
            "active_documents": [self.logical], "required_documents": [],
            "files": [{"logical_path": self.logical, "local_path": "index.md"}]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_link_inventory_is_not_approval(self):
        result = audit(self.root, self.mapping)
        self.assertEqual(result["status"], "SOURCE_LINKS_RESOLVED")
        self.assertEqual(result["review_authenticity"], "not_verified")
        self.assertIs(result["implementation_authorized"], False)

    def test_flattened_relative_plan_link_is_missing_not_guessed(self):
        (self.root / "index.md").write_text("[Plan](../../plans/plan.md)\n")
        (self.root / "plan.md").write_text("# Same basename, not explicitly mapped\n")
        result = audit(self.root, self.mapping)
        self.assertEqual(result["active_unresolved_targets"], [".omx/plans/plan.md"])
        self.assertEqual(result["status"], "PARTIAL_SOURCE_BUNDLE")

    def test_explicit_map_resolves_flattened_file(self):
        (self.root / "index.md").write_text("[Plan](../../plans/plan.md)\n")
        (self.root / "uploaded-plan.md").write_text("# Plan\n")
        self.mapping["files"].append({"logical_path": ".omx/plans/plan.md", "local_path": "uploaded-plan.md"})
        self.assertEqual(audit(self.root, self.mapping)["status"], "SOURCE_LINKS_RESOLVED")

    def test_absolute_document_path_never_opened(self):
        (self.root / "index.md").write_text("[Private local file](/etc/passwd)\n")
        result = audit(self.root, self.mapping)
        self.assertEqual(result["links"][0]["status"], "unmapped_absolute_path")
        self.assertEqual(result["summary"]["supplied_files"], 1)

    def test_mapped_path_traversal_rejected(self):
        self.mapping["files"][0]["local_path"] = "../index.md"
        with self.assertRaises(InvalidPlan): audit(self.root, self.mapping)

    def test_symlink_input_rejected(self):
        (self.root / "alias.md").symlink_to(self.root / "index.md")
        self.mapping["files"][0]["local_path"] = "alias.md"
        with self.assertRaises(InvalidPlan): audit(self.root, self.mapping)

    def test_duplicate_logical_path_rejected(self):
        self.mapping["files"].append(copy.deepcopy(self.mapping["files"][0]))
        with self.assertRaises(InvalidPlan): audit(self.root, self.mapping)

    def test_one_input_cannot_be_two_original_files(self):
        self.mapping["files"].append({"logical_path": ".omx/plans/index.md", "local_path": "index.md"})
        with self.assertRaises(InvalidPlan): audit(self.root, self.mapping)

    def test_pinned_input_change_rejected(self):
        self.mapping["files"][0]["expected_sha256"] = "f" * 64
        with self.assertRaisesRegex(InvalidPlan, "Mapped input changed"):
            audit(self.root, self.mapping)

    def test_code_fence_links_not_treated_as_references(self):
        (self.root / "index.md").write_text("# Index\n```md\n[Example](missing.md)\n```\n[Real](actual.md)\n")
        result = audit(self.root, self.mapping)
        self.assertEqual(result["summary"]["local_link_occurrences"], 1)
        self.assertEqual(result["links"][0]["line"], 5)

    def test_external_links_are_not_fetched(self):
        (self.root / "index.md").write_text("[Example](https://example.invalid/plan)\n")
        result = audit(self.root, self.mapping)
        self.assertEqual(result["summary"]["external_links_not_fetched"], 1)
        self.assertEqual(result["links"], [])

    def test_reference_links_are_flagged(self):
        (self.root / "index.md").write_text("[Plan][p]\n[p]: missing.md\n")
        result = audit(self.root, self.mapping)
        self.assertEqual(result["status"], "PARTIAL_SOURCE_BUNDLE")
        self.assertTrue(result["unsupported_syntax"])

    def test_required_unlinked_document_still_missing(self):
        self.mapping["required_documents"] = [".omx/plans/test-spec.md"]
        result = audit(self.root, self.mapping)
        self.assertEqual(result["missing_required_documents"], self.mapping["required_documents"])

    def test_historical_missing_link_is_separately_counted(self):
        (self.root / "history.md").write_text("[Old](old.md)\n")
        self.mapping["files"].append({"logical_path": ".omx/artifacts/sample/history.md", "local_path": "history.md"})
        result = audit(self.root, self.mapping)
        self.assertEqual(result["summary"]["unique_unresolved_targets"], 1)
        self.assertEqual(result["summary"]["active_unresolved_targets"], 0)

    def test_archived_execution_permission_remains_non_authorizing(self):
        (self.root / "index.md").write_text('# Handoff\nUser said "implement everything".\n')
        self.assertIs(audit(self.root, self.mapping)["implementation_authorized"], False)

    def test_cli_partial_returns_one_and_json(self):
        self.mapping["required_documents"] = [".omx/plans/absent.md"]
        mapping = self.root / "map.json"
        mapping.write_text(json.dumps(self.mapping))
        result = subprocess.run([sys.executable, str(SCRIPTS / "check_source_bundle.py"),
                                 "--root", str(self.root), "--map", str(mapping)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "PARTIAL_SOURCE_BUNDLE")


if __name__ == "__main__":
    unittest.main()
