"""Check a result: schema, the physical ceiling, and conditions that make a run unrepresentative.

See docs/format.md ("Checks applied to every result").
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from functools import cache
from importlib import resources
from pathlib import Path

import jsonschema

from .gpus import peak_bandwidth

CEILING_TOLERANCE = 1.15  # measurement noise and spec rounding


@cache
def _schema() -> dict:
    text = (
        resources.files("runsonmine")
        .joinpath("schema/result-v1.schema.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


@dataclass
class Verdict:
    errors: list[str] = field(default_factory=list)  # any error: the result is rejected
    flags: list[str] = field(default_factory=list)  # kept, but shown and left out of "best"
    ceiling_tok_s: float | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


def content_id(result: dict) -> str:
    """First 12 hex characters of the SHA-256 of the canonical JSON (the file's name)."""
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def _level(result: dict, users: int) -> dict | None:
    return next((r for r in result.get("results", []) if r.get("users") == users), None)


def _throttled(cond: dict) -> bool:
    """Busy GPU held far below its clock by something other than its normal power budget.

    A GPU running at its power limit normally clocks down under heavy load (e.g. a 70 W
    Tesla T4 at ~650 of 1590 MHz): that is how the card works, not a fault. A clock below
    25% of maximum is flagged regardless (e.g. a laptop GPU left capped at 10 W after running
    on battery: 210 of 2100 MHz), and below 50% when the GPU is *not* at its power limit.
    """
    clock, clock_max = cond.get("gpu_clock_avg_mhz"), cond.get("gpu_clock_max_mhz")
    util = cond.get("gpu_util_avg_pct")
    if not (clock and clock_max and util is not None and util >= 50):
        return False
    ratio = clock / clock_max
    power, limit = cond.get("gpu_power_avg_w"), cond.get("gpu_power_limit_w")
    at_power_limit = bool(power and limit and power >= 0.9 * limit)
    return ratio < 0.25 or (ratio < 0.5 and not at_power_limit)


def check(result: dict) -> Verdict:
    v = Verdict()
    errors = sorted(
        jsonschema.Draft202012Validator(_schema()).iter_errors(result), key=lambda e: e.path
    )
    if errors:
        v.errors += [
            f"schema: {'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
            for e in errors
        ]
        return v

    if sorted(r["users"] for r in result["results"]) != [1, 2, 4]:
        v.errors.append("results must have exactly one entry each for 1, 2 and 4 users")
        return v

    gpus = result["hardware"]["gpus"]
    serving = result["hardware"].get("serving_gpu", 0)
    if gpus and serving >= len(gpus):
        v.errors.append(f"serving_gpu {serving} but only {len(gpus)} GPU(s) listed")
        return v
    bandwidth = peak_bandwidth(gpus[serving]["name"]) if gpus else None
    weights_gb = result["model"].get("weights_gb")
    if bandwidth is None:
        v.flags.append("unknown-gpu")
    if weights_gb is None:
        v.flags.append("size-unknown")
    if bandwidth and weights_gb:
        v.ceiling_tok_s = round(bandwidth / weights_gb, 1)
        one = _level(result, 1)
        speed = one.get("per_user_tok_s") if one else None
        if speed and speed > v.ceiling_tok_s * CEILING_TOLERANCE:
            v.errors.append(
                f"single-user speed {speed} tok/s is above the physical ceiling "
                f"{v.ceiling_tok_s} tok/s ({bandwidth:g} GB/s / {weights_gb:g} GB): "
                "the run or its model metadata is wrong"
            )

    cond = result["conditions"]
    if cond.get("power_source") == "battery":
        v.flags.append("battery")
    if _throttled(cond):
        v.flags.append("throttled")
    on_gpu = result["model"].get("on_gpu")
    if on_gpu and on_gpu != "100%":
        v.flags.append("partial-offload")
    if any(r["failed"] for r in result["results"]):
        v.flags.append("failed-requests")
    return v


def check_file(path: Path) -> Verdict:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return Verdict(errors=[f"cannot read JSON: {e}"])
    v = check(result)
    if v.ok and path.parent.name == "results" and path.stem != content_id(result):
        v.errors.append(f"file name should be {content_id(result)}.json (content hash)")
    return v
