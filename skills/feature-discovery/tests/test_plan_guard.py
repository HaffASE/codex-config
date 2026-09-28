"""Synthetic fixtures only: these reports are NOT actual model reviews."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from common import InvalidPlan, load_json, verify_snapshot
from freeze_plan import freeze
from validate_plan import validate_content, validate_run


def fixture() -> dict:
    """Invented example used solely to exercise mechanical validation."""
    return {
        "schema_version": 1, "task_id": "SYNTHETIC-001", "profile": "bff-crud",
        "authors": ["synthetic-author"],
        "repositories": [{"id": "REPO-BACKEND", "revision": "a" * 40, "working_tree": "clean", "scope": "Synthetic fixture"}],
        "capabilities": [{"name": name, "status": "available" if name != "native-council" else "unavailable",
                          "evidence": "Synthetic fixture capability; not a real host check."}
                         for name in ["native-analysis", "user-interaction", "native-planning", "native-council", "independent-review"]],
        "council": {"enabled": False, "delegation_ref": "", "allowed_topics": []},
        "review_policy": {"roles": ["architect", "critic"], "max_rounds": 3, "require_model_diversity": False},
        "requirements": [{"id": "REQ-001", "text": "Resolve the saved reference in the consumer.", "in_scope": True}],
        "evidence": [{"id": "EVD-001", "kind": "source", "repository_id": "REPO-BACKEND", "revision": "a" * 40,
                      "ref": "synthetic/resolver.go:Resolve:1", "claim": "Synthetic source claim for test purposes."}],
        "decisions": [{"id": "DEC-001", "decision": "Keep secret resolution on the backend.", "origin": "user",
                       "category": "architecture", "accepted": True, "authority_ref": "Synthetic user authority",
                       "evidence_ids": ["EVD-001"]}],
        "tasks": [
            {"id": "TASK-001", "title": "Add resolver behavior", "owner": "backend", "files": ["synthetic/resolver.go"],
             "outcome": "Consumer resolves fake provider reference", "requirement_ids": ["REQ-001"],
             "decision_ids": ["DEC-001"], "depends_on": [], "test_ids": ["TEST-001"]},
            {"id": "TASK-002", "title": "Verify UI integration", "owner": "frontend", "files": ["synthetic/view.tsx"],
             "outcome": "Integration uses agreed contract", "requirement_ids": ["REQ-001"],
             "decision_ids": ["DEC-001"], "depends_on": ["TASK-001"], "test_ids": ["TEST-002"]}],
        "tests": [
            {"id": "TEST-001", "requirement_ids": ["REQ-001"], "stage": "test-first", "level": "integration",
             "method": "Exercise synthetic consumer", "red_oracle": "Missing behavior assertion fails",
             "expected": "Fake secret reference is resolved", "status": "planned"},
            {"id": "TEST-002", "requirement_ids": ["REQ-001"], "stage": "regression", "level": "unit",
             "method": "Round-trip reference DTO", "expected": "Reference identity preserved", "status": "planned"}],
        "api_inventory_scope": "Synthetic route and variant inventory", "api_inventory_evidence_ids": ["EVD-001"],
        "api_inventory": [{"id": "API-001", "operation": "Synthetic create-reference variant", "disposition": "planned",
                           "requirement_ids": ["REQ-001"], "task_ids": ["TASK-001", "TASK-002"],
                           "coverage": {layer: {"state": "source-confirmed", "evidence_ids": ["EVD-001"]}
                                        for layer in ["contract", "handler", "persistence", "execution", "ui"]},
                           "resolution_task_ids": []}],
        "open_questions": [], "prerequisites": []}


class PlanGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name)
        (self.run / "draft").mkdir()
        (self.run / "reviews").mkdir()
        self.plan = fixture()
        self.save()
        for name in ["brief", "analysis", "implementation", "tests"]:
            (self.run / "draft" / f"{name}.md").write_text(f"# {name.title()}\n\nSynthetic test packet only.\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        (self.run / "draft/plan.json").write_text(json.dumps(self.plan, indent=2), encoding="utf-8")

    def draft_rejected(self):
        self.save()
        with self.assertRaises(InvalidPlan):
            validate_content(self.run / "draft")

    def write_reports(self, revision="r01", findings=None, verdict="accept"):
        manifest, _ = verify_snapshot(self.run, revision)
        files = set(manifest["files"])
        reviewed = files if manifest["review_mode"] == "full" else set(manifest["required_review_files"])
        for role in self.plan["review_policy"]["roles"]:
            self.report_save(revision, role, {
                "schema_version": 1, "revision": revision, "role": role,
                "reviewer_id": f"synthetic-{role}", "provider": "synthetic-provider", "model": "synthetic-model",
                "completed_at": "2026-09-18T00:00:00Z", "packet_digest": manifest["packet_digest"],
                "mode": manifest["review_mode"], "reviewed_files": sorted(reviewed),
                "inherited_files": sorted(files-reviewed), "acknowledged_deletions": manifest["deleted_files"],
                "summary": "Synthetic test declaration, not a model review.", "verdict": verdict,
                "findings": copy.deepcopy(findings or [])})

    def report(self, revision="r01", role="architect"):
        return load_json(self.run / f"reviews/{revision}.{role}.json")

    def report_save(self, revision, role, report):
        (self.run / f"reviews/{revision}.{role}.json").write_text(json.dumps(report), encoding="utf-8")

    def ready(self):
        self.save()
        freeze(self.run, "r01")
        self.write_reports()
        return validate_run(self.run, "r01")

    def test_valid_draft_is_not_approval(self):
        self.assertEqual(validate_content(self.run / "draft")["task_id"], "SYNTHETIC-001")

    def test_valid_full_review_ready_but_no_execution_authority(self):
        result = self.ready()
        self.assertEqual(result["status"], "READY")
        self.assertIs(result["implementation_authorized"], False)

    def test_no_reports_not_ready(self):
        freeze(self.run, "r01")
        with self.assertRaises(InvalidPlan): validate_run(self.run, "r01")

    def test_duplicate_test_id(self):
        self.plan["tests"].append(copy.deepcopy(self.plan["tests"][0]))
        self.draft_rejected()

    def test_unknown_decision_reference(self):
        self.plan["tasks"][0]["decision_ids"] = ["DEC-404"]
        self.draft_rejected()

    def test_uncovered_requirement(self):
        self.plan["requirements"].append({"id":"REQ-002", "text":"Uncovered", "in_scope":True})
        self.draft_rejected()

    def test_task_test_mismatch(self):
        self.plan["requirements"].append({"id":"REQ-002", "text":"Different", "in_scope":True})
        self.plan["tasks"][0]["requirement_ids"] = ["REQ-002"]
        self.draft_rejected()

    def test_dependency_cycle(self):
        self.plan["tasks"][0]["depends_on"] = ["TASK-002"]
        self.draft_rejected()

    def test_runtime_claim_requires_runtime_evidence(self):
        self.plan["api_inventory"][0]["coverage"]["execution"]["state"] = "runtime-confirmed"
        self.draft_rejected()

    def test_observed_runtime_evidence(self):
        self.plan["evidence"].append({"id":"EVD-002", "kind":"runtime", "ref":"synthetic observation",
            "claim":"Synthetic runtime", "environment":"test-fixture", "observed_at":"2026-09-18T00:00:00Z", "build_ref":"synthetic-build"})
        self.plan["api_inventory"][0]["coverage"]["execution"] = {"state":"runtime-confirmed", "evidence_ids":["EVD-002"]}
        self.assertEqual(self.ready()["status"], "READY")

    def test_missing_execution_requires_resolution_task(self):
        self.plan["api_inventory"][0]["coverage"]["execution"] = {"state":"missing", "evidence_ids":[], "reason":"Missing resolver"}
        self.draft_rejected()

    def test_known_backend_gap_is_plannable(self):
        self.plan["api_inventory"][0]["coverage"]["execution"] = {"state":"missing", "evidence_ids":[], "reason":"Missing resolver"}
        self.plan["api_inventory"][0]["resolution_task_ids"] = ["TASK-001"]
        self.assertEqual(self.ready()["status"], "READY")

    def test_prerequisites_separate_from_plan_readiness(self):
        self.plan["prerequisites"] = [{"id":"PRE-001", "condition":"Resolver verified", "owner":"backend",
            "status":"open", "blocks_task_ids":["TASK-002"], "resolution_task_ids":["TASK-001"], "evidence_ids":[]}]
        self.assertEqual(self.ready()["status"], "READY_WITH_PREREQUISITES")

    def test_prerequisite_must_precede_blocked_task(self):
        self.plan["prerequisites"] = [{"id":"PRE-001", "condition":"Reverse order", "owner":"backend",
            "status":"open", "blocks_task_ids":["TASK-001"], "resolution_task_ids":["TASK-002"], "evidence_ids":[]}]
        self.draft_rejected()

    def test_source_revision_mismatch(self):
        self.plan["evidence"][0]["revision"] = "b"*40
        self.draft_rejected()

    def test_dirty_tree_requires_snapshot(self):
        self.plan["repositories"][0]["working_tree"] = "dirty"
        self.draft_rejected()

    def test_unavailable_repo_cannot_confirm_source(self):
        self.plan["repositories"][0]["working_tree"] = "unavailable"
        self.draft_rejected()

    def test_test_first_requires_specific_red_oracle(self):
        del self.plan["tests"][0]["red_oracle"]
        self.draft_rejected()

    def test_no_false_executed_tests(self):
        self.plan["tests"][0]["status"] = "passed"
        self.draft_rejected()

    def test_post_review_content_change(self):
        self.ready()
        (self.run / "revisions/r01/packet/analysis.md").write_text("Changed")
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_post_review_added_file(self):
        self.ready()
        (self.run / "revisions/r01/packet/extra.md").write_text("Added")
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_post_review_deleted_file(self):
        self.ready()
        (self.run / "revisions/r01/packet/tests.md").unlink()
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_stale_review_digest(self):
        self.ready()
        report = self.report(); report["packet_digest"] = "0"*64
        self.report_save("r01","architect",report)
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_author_is_not_independent_reviewer(self):
        self.ready()
        report = self.report(); report["reviewer_id"] = "synthetic-author"
        self.report_save("r01","architect",report)
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_roles_require_separate_instances(self):
        self.ready()
        report = self.report(role="critic"); report["reviewer_id"] = "synthetic-architect"
        self.report_save("r01","critic",report)
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_requested_model_diversity_missing(self):
        self.plan["review_policy"]["require_model_diversity"] = True
        self.save(); freeze(self.run,"r01"); self.write_reports()
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_requested_model_diversity_present(self):
        self.plan["review_policy"]["require_model_diversity"] = True
        self.save(); freeze(self.run,"r01"); self.write_reports()
        report = self.report(role="critic"); report["provider"] = "synthetic-other-provider"
        self.report_save("r01","critic",report)
        self.assertEqual(validate_run(self.run,"r01")["status"],"READY")

    def test_accept_cannot_hide_major_finding(self):
        freeze(self.run,"r01")
        self.write_reports(findings=[{"id":"F-001", "severity":"major", "status":"open", "message":"Missing contract", "resolution":""}])
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_minor_finding_does_not_force_loop(self):
        freeze(self.run,"r01")
        self.write_reports(findings=[{"id":"F-001", "severity":"minor", "status":"open", "message":"Minor wording", "resolution":""}])
        self.assertEqual(validate_run(self.run,"r01")["status"],"READY")

    def test_major_risk_cannot_be_waived(self):
        freeze(self.run,"r01")
        self.write_reports(findings=[{"id":"F-001", "severity":"major", "status":"accepted-risk", "message":"Missing contract", "resolution":"Waived"}])
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_unaccepted_decision_blocks_close_not_candidate(self):
        self.plan["decisions"][0]["accepted"] = False
        self.save(); freeze(self.run,"r01"); self.write_reports()
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_material_question_blocks_close(self):
        self.plan["open_questions"] = [{"id":"Q-001", "question":"Define destructive behavior", "blocking":True, "status":"open", "decision_ids":[]}]
        self.save(); freeze(self.run,"r01"); self.write_reports()
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_council_requires_delegation(self):
        self.plan["council"]["enabled"] = True
        self.draft_rejected()

    def test_council_cannot_silently_accept_out_of_scope(self):
        self.plan["council"] = {"enabled":True,"delegation_ref":"Synthetic user permission", "allowed_topics":["ux"]}
        self.plan["decisions"][0].update(origin="council", topic="security")
        self.draft_rejected()

    def test_council_missing_advisor_blocks_close(self):
        self.plan["council"] = {"enabled":True,"delegation_ref":"Synthetic user permission", "allowed_topics":["ux"]}
        self.save(); freeze(self.run,"r01"); self.write_reports()
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_unavailable_independent_review_blocks_close(self):
        self.plan["capabilities"][-1]["status"] = "unavailable"
        self.save(); freeze(self.run,"r01"); self.write_reports()
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_delta_carries_unchanged_files(self):
        self.ready()
        (self.run/"draft/tests.md").write_text("# Tests\nNew specific scenario.\n")
        freeze(self.run,"r02","delta",["tests.md","implementation.md"],"Test change affects implementation checks")
        self.write_reports("r02")
        self.assertEqual(validate_run(self.run,"r02")["status"],"READY")

    def test_delta_cannot_inherit_changed_file(self):
        self.test_delta_carries_unchanged_files()
        report = self.report("r02"); report["reviewed_files"].remove("tests.md"); report["inherited_files"].append("tests.md")
        self.report_save("r02","architect",report)
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r02")

    def test_delta_cannot_forget_findings(self):
        freeze(self.run,"r01")
        self.write_reports(findings=[{"id":"F-001","severity":"major","status":"open","message":"Add case","resolution":""}], verdict="request_changes")
        (self.run/"draft/tests.md").write_text("# Tests\nAdded the missing case.\n")
        freeze(self.run,"r02","delta",["tests.md"],"Fix reported case")
        self.write_reports("r02")
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r02")

    def test_delta_can_resolve_prior_major(self):
        freeze(self.run,"r01")
        finding = {"id":"F-001","severity":"major","status":"open","message":"Add case","resolution":""}
        self.write_reports(findings=[finding], verdict="request_changes")
        (self.run/"draft/tests.md").write_text("# Tests\nAdded the missing case.\n")
        freeze(self.run,"r02","delta",["tests.md"],"Fix reported case")
        finding.update(status="resolved",resolution="tests.md specifies the missing acceptance case")
        self.write_reports("r02",findings=[finding])
        self.assertEqual(validate_run(self.run,"r02")["status"],"READY")

    def test_deleted_file_requires_acknowledgment(self):
        (self.run/"draft/optional.md").write_text("# Optional\nExtra explanation\n")
        self.ready(); (self.run/"draft/optional.md").unlink()
        freeze(self.run,"r02","delta",["analysis.md"],"Remove redundant explanation")
        self.write_reports("r02")
        report = self.report("r02"); report["acknowledged_deletions"] = []
        self.report_save("r02","architect",report)
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r02")

    def test_architecture_change_requires_full_review(self):
        self.ready(); self.plan["decisions"][0]["decision"] += " Change cache ownership."
        self.save()
        with self.assertRaises(InvalidPlan): freeze(self.run,"r02","delta",["analysis.md"],"Change architecture")

    def test_policy_change_rejected(self):
        self.ready(); self.plan["review_policy"]["max_rounds"] = 9; self.save()
        with self.assertRaises(InvalidPlan): freeze(self.run,"r02")

    def test_budget_exhaustion(self):
        self.plan["review_policy"]["max_rounds"] = 1; self.ready()
        with self.assertRaises(InvalidPlan): freeze(self.run,"r02")

    def test_cannot_overwrite_snapshot(self):
        self.ready()
        with self.assertRaises(InvalidPlan): freeze(self.run,"r01")

    def test_first_round_cannot_be_delta(self):
        with self.assertRaises(InvalidPlan): freeze(self.run,"r01","delta",["tests.md"],"No baseline")

    def test_broken_markdown_link(self):
        (self.run/"draft/brief.md").write_text("[Missing](missing.md)")
        with self.assertRaises(InvalidPlan): validate_content(self.run/"draft")

    def test_markdown_anchor_valid(self):
        (self.run/"draft/brief.md").write_text("[Analysis](analysis.md#analysis)")
        self.assertEqual(validate_content(self.run/"draft")["schema_version"],1)

    def test_markdown_anchor_missing(self):
        (self.run/"draft/brief.md").write_text("[Missing](analysis.md#no-such-section)")
        with self.assertRaises(InvalidPlan): validate_content(self.run/"draft")

    def test_link_escape(self):
        (self.run/"outside.md").write_text("Outside")
        (self.run/"draft/brief.md").write_text("[Escape](../outside.md)")
        with self.assertRaises(InvalidPlan): validate_content(self.run/"draft")

    def test_symlink_rejected(self):
        (self.run/"draft/link.md").symlink_to(self.run/"draft/tests.md")
        with self.assertRaises(InvalidPlan): validate_content(self.run/"draft")

    def test_duplicate_json_keys(self):
        (self.run/"draft/plan.json").write_text('{"schema_version":1,"schema_version":2}')
        with self.assertRaises(InvalidPlan): validate_content(self.run/"draft")

    def test_ready_markdown_cannot_contain_placeholders(self):
        (self.run/"draft/brief.md").write_text("# Brief\nTODO: define scope.\n")
        freeze(self.run,"r01"); self.write_reports()
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_missing_test_array_type_fails_cleanly_via_cli(self):
        self.plan["tests"] = None; self.save()
        result = subprocess.run([sys.executable,str(SCRIPTS/"validate_plan.py"),str(self.run),"--draft"],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertEqual(json.loads(result.stdout)["status"],"NEEDS_WORK")
        self.assertNotIn("Traceback",result.stderr)

    def test_changed_working_draft_cannot_close_old_packet(self):
        self.ready()
        (self.run/"draft/analysis.md").write_text("# Analysis\nNew unreviewed conclusion.\n")
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")

    def test_final_closure_requires_latest_revision(self):
        self.ready()
        freeze(self.run,"r02"); self.write_reports("r02")
        with self.assertRaises(InvalidPlan): validate_run(self.run,"r01")
        self.assertEqual(validate_run(self.run,"r02")["status"],"READY")

    def test_existing_lock_is_not_deleted(self):
        lock = self.run/".freeze.lock"; lock.write_text("Other coordinator")
        with self.assertRaises(FileExistsError): freeze(self.run,"r01")
        self.assertEqual(lock.read_text(),"Other coordinator")


if __name__ == "__main__":
    unittest.main()
