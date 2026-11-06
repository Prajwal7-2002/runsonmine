import json

from fastapi.testclient import TestClient

from runsonmine.service import RateLimiter, create_app
from runsonmine.validate import content_id


class FakeGitHub:
    def __init__(self, existing=()):
        self.existing, self.prs = set(existing), []

    def file_exists(self, path):
        return path in self.existing

    def open_pr(self, branch, path, content, title, body):
        self.prs.append(
            {"branch": branch, "path": path, "content": content, "title": title, "body": body}
        )
        return f"https://github.com/x/runsonmine/pull/{len(self.prs)}"


def client(gh, limit=20):
    return TestClient(create_app(github=gh, limiter=RateLimiter(limit=limit)))


def test_valid_upload_opens_a_pull_request(result):
    gh = FakeGitHub()
    r = client(gh).post("/v1/results", content=json.dumps(result))
    assert r.status_code == 201, r.text
    rid = content_id(result)
    assert r.json() == {
        "status": "submitted",
        "id": rid,
        "pull_request": "https://github.com/x/runsonmine/pull/1",
        "flags": [],
    }
    pr = gh.prs[0]
    assert pr["branch"] == f"submit/{rid}" and pr["path"] == f"data/results/{rid}.json"
    assert json.loads(pr["content"]) == result  # stored as submitted; name = content hash
    assert "qwen2.5:0.5b" in pr["title"] and "RTX 3050" in pr["title"]


def test_invalid_upload_is_rejected_without_a_pr(result):
    result["results"][0]["per_user_tok_s"] = 5000.0
    gh = FakeGitHub()
    r = client(gh).post("/v1/results", content=json.dumps(result))
    assert r.status_code == 422 and "physical ceiling" in r.json()["errors"][0]
    assert gh.prs == []


def test_private_fields_are_rejected(result):
    result["hardware"]["hostname"] = "bobs-laptop"
    r = client(FakeGitHub()).post("/v1/results", content=json.dumps(result))
    assert r.status_code == 422


def test_duplicate_is_not_reopened(result):
    gh = FakeGitHub(existing={f"data/results/{content_id(result)}.json"})
    r = client(gh).post("/v1/results", content=json.dumps(result))
    assert r.status_code == 200 and r.json()["status"] == "already-added"
    assert gh.prs == []


def test_bad_bodies(result):
    c = client(FakeGitHub())
    assert c.post("/v1/results", content=b"not json").status_code == 400
    assert c.post("/v1/results", content=b"[1, 2]").status_code == 400
    assert c.post("/v1/results", content=b"x" * 40_000).status_code == 413


def test_rate_limit(result):
    c = client(FakeGitHub(), limit=2)
    body = json.dumps(result)
    assert [c.post("/v1/results", content=body).status_code for _ in range(3)][-1] == 429


def test_unconfigured_service_fails_cleanly(result, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    r = TestClient(create_app()).post("/v1/results", content=json.dumps(result))
    assert r.status_code == 503 and "not configured" in r.json()["error"]
