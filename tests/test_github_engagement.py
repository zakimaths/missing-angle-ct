"""Guard the report against false counts, missing-data inflation and duplicate adoption."""

import importlib.util
import math
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "github_engagement", Path(__file__).parents[1] / "scripts/github_engagement.py"
)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def test_zero_missing_and_invalid_counts_are_distinct():
    assert report.log_count(0) == 0
    assert report.log_count(None) is None
    assert report.log_count(9) == pytest.approx(math.log(10))
    for value in [-1, True, 1.5]:
        with pytest.raises(ValueError):
            report.log_count(value)


def test_contributors_deduplicate_accounts_and_separate_owner():
    records = [{"login": "Owner", "type": "User"},
               {"login": "External", "type": "User"},
               {"login": "external", "type": "User"},
               {"login": "automation[bot]", "type": "Bot"}]
    assert report.contributor_counts(records, "owner") == (2, 1)


def test_adoption_deduplicates_evidence_and_rejects_self_use():
    entry = {"repository": "owner/project", "project_key": "external/course",
             "independent_owner": "external", "evidence_url": "https://example.org/course",
             "description": "Public course uses the reconstruction exercise",
             "reviewed_on": "2026-09-08"}
    ledger = {"schema": 1, "entries": [entry, dict(entry)]}
    assert report.adoption_counts(ledger, ["owner/project"], "owner") == {"owner/project": 1}
    assert report.adoption_counts({"schema": 1, "entries": []}, ["owner/project"], "owner") == {
        "owner/project": 0}
    ledger["entries"][0] = dict(entry, independent_owner="OWNER")
    with pytest.raises(ValueError):
        report.adoption_counts(ledger, ["owner/project"], "owner")


def test_collection_is_public_owned_paginated_and_missing_is_not_zero(monkeypatch):
    base = {"private": False, "fork": False, "owner": {"login": "owner"},
            "full_name": "owner/public", "html_url": "https://github.com/owner/public",
            "url": "https://api.github.com/repos/owner/public", "archived": False,
            "stargazers_count": 0, "forks_count": 0}

    def api(endpoint, paginate=False):
        assert paginate
        if endpoint.startswith("users/"):
            return [base, dict(base, private=True), dict(base, fork=True),
                    dict(base, owner={"login": "someone-else"})]
        raise ValueError("Unavailable contributor endpoint")

    monkeypatch.setattr(report, "api", api)
    snapshot = report.collect("owner", {"schema": 1, "entries": []})
    assert len(snapshot["repositories"]) == 1
    row = snapshot["repositories"][0]
    assert row["raw"]["contributors"] is None
    assert row["log1p"]["contributors"] is None
    assert row["raw"]["stars"] == 0
    chart = report.render(snapshot)
    assert "Unavailable" in chart
    assert "0 documented" in chart
