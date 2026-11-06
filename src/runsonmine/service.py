"""Upload service: receive a result, validate it, open a GitHub pull request adding it.

Runs on a free Hugging Face Space (see space/). Every accepted upload becomes a pull request on
the RunsOnMine repo, where CI validates it again and a maintainer merges it; nothing is
published without that review. The service stores nothing: no database, no logs of results or
IP addresses (IPs are only counted in memory for rate limiting).

Environment:
    GITHUB_TOKEN     fine-grained token for the RunsOnMine repo only
                     (Contents: read/write, Pull requests: read/write)
    RUNSONMINE_REPO  owner/name, default Prajwal7-2002/runsonmine
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import __version__
from .validate import check, content_id

MAX_BYTES = 32_000
RATE_LIMIT = 20  # uploads per IP per hour
RESULTS_PATH = "data/results"


class GitHubError(RuntimeError):
    pass


class GitHub:
    """The four GitHub REST calls the service needs (stdlib only)."""

    def __init__(self, token: str, repo: str):
        self.token, self.repo = token, repo

    def _call(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict | list]:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{self.repo}{path}",
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "runsonmine-upload",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            try:
                payload = json.load(e)
            except ValueError:
                payload = {}
            return e.code, payload

    def file_exists(self, path: str) -> bool:
        status, _ = self._call("GET", f"/contents/{path}?ref=main")
        return status == 200

    def open_pr(self, branch: str, path: str, content: str, title: str, body: str) -> str:
        """Create branch, add the file, open the PR; reuse an existing PR for the branch."""
        status, ref = self._call("GET", "/git/ref/heads/main")
        if status != 200:
            raise GitHubError(f"cannot read main ({status})")
        status, _ = self._call(
            "POST", "/git/refs", {"ref": f"refs/heads/{branch}", "sha": ref["object"]["sha"]}
        )
        if status == 422:  # branch exists: this result was already uploaded
            owner = self.repo.split("/")[0]
            _, pulls = self._call("GET", f"/pulls?head={owner}:{branch}&state=all")
            if pulls:
                return pulls[0]["html_url"]
            raise GitHubError("branch exists but has no pull request")
        if status != 201:
            raise GitHubError(f"cannot create branch ({status})")
        status, _ = self._call(
            "PUT",
            f"/contents/{path}",
            {
                "message": title,
                "content": base64.b64encode(content.encode("utf-8")).decode(),
                "branch": branch,
            },
        )
        if status not in (200, 201):
            raise GitHubError(f"cannot add file ({status})")
        status, pr = self._call(
            "POST", "/pulls", {"title": title, "head": branch, "base": "main", "body": body}
        )
        if status != 201:
            raise GitHubError(f"cannot open pull request ({status})")
        return pr["html_url"]


def _summary(result: dict, flags: list[str]) -> tuple[str, str]:
    gpus = result["hardware"]["gpus"]
    gpu = gpus[0]["name"] if gpus else "CPU only"
    model = result["model"]["name"]
    by_users = {r["users"]: r for r in result["results"]}
    title = f"result: {model} on {gpu}"[:120]
    body = "\n".join(
        [
            "Submitted through the RunsOnMine upload service.",
            "",
            f"- GPU: {gpu}",
            f"- Engine: {result['engine'].get('name')} {result['engine'].get('version') or ''}",
            f"- Model: {model} {result['model'].get('quantization', '')}",
            f"- 1 user: {by_users[1]['per_user_tok_s']} tok/s, "
            f"TTFT {by_users[1]['ttft_ms_p50']} ms",
            f"- 4 users: {by_users[4]['output_tok_s']} tok/s total",
            f"- Flags: {', '.join(flags) or 'none'}",
            "",
            "CI validates the file again; merge to publish it on the site.",
        ]
    )
    return title, body


class RateLimiter:
    def __init__(self, limit: int = RATE_LIMIT, window_s: float = 3600.0):
        self.limit, self.window = limit, window_s
        self.hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now, q = time.monotonic(), self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True


def create_app(github: GitHub | None = None, limiter: RateLimiter | None = None) -> FastAPI:
    app = FastAPI(title="RunsOnMine upload", version=__version__, docs_url=None, redoc_url=None)
    limiter = limiter or RateLimiter()

    def gh() -> GitHub:
        if github is not None:
            return github
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise GitHubError("service is not configured (no GITHUB_TOKEN)")
        return GitHub(token, os.environ.get("RUNSONMINE_REPO", "Prajwal7-2002/runsonmine"))

    @app.get("/")
    def info() -> dict:
        return {
            "service": "RunsOnMine upload",
            "version": __version__,
            "submit": "POST /v1/results with a result file from `servebench submit`",
            "site": "https://prajwal7-2002.github.io/runsonmine/",
        }

    @app.post("/v1/results")
    async def upload(request: Request) -> JSONResponse:
        forwarded = request.headers.get("x-forwarded-for", "")
        client = forwarded.split(",")[0].strip() or (request.client.host if request.client else "")
        if not limiter.allow(client):
            return JSONResponse({"error": "too many uploads, try again in an hour"}, 429)
        raw = await request.body()
        if len(raw) > MAX_BYTES:
            return JSONResponse({"error": f"result larger than {MAX_BYTES} bytes"}, 413)
        try:
            result = json.loads(raw)
        except ValueError:
            return JSONResponse({"error": "body is not JSON"}, 400)
        if not isinstance(result, dict):
            return JSONResponse({"error": "body must be a JSON object"}, 400)
        verdict = check(result)
        if not verdict.ok:
            return JSONResponse({"status": "rejected", "errors": verdict.errors}, 422)
        rid = content_id(result)
        path = f"{RESULTS_PATH}/{rid}.json"
        try:
            client_gh = gh()
            if client_gh.file_exists(path):
                return JSONResponse({"status": "already-added", "id": rid}, 200)
            title, body = _summary(result, verdict.flags)
            url = client_gh.open_pr(
                f"submit/{rid}", path, json.dumps(result, indent=2) + "\n", title, body
            )
        except GitHubError as e:
            return JSONResponse({"error": str(e)}, 503)
        return JSONResponse(
            {"status": "submitted", "id": rid, "pull_request": url, "flags": verdict.flags}, 201
        )

    return app
