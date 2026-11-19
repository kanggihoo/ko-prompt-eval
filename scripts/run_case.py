"""case를 변형별로 `claude -p`에 돌려 실험 폴더에 저장하고 요약을 출력한다.

koeval harness를 만들기 전의 임시 runner다. `reexplain` task만 돌린다.

    uv run scripts/run_case.py --case commit-log-flush \\
        --variant none --variant variants/explain-clearly/SKILL.md \\
        --model sonnet --out experiments/2026-11-19-rerun

- 호출은 결과를 남기는 실험 폴더(--out)를 cwd로 해서 하고, AGENTS.md의 격리 flag를 쓴다.
- `gap`은 prompt에 넣지 않는다 (docs/decisions.md D-6).
- 결과 폴더: inputs/(변형 사본), raw/, outputs/, results.jsonl, run.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = ROOT / "data" / "cases.jsonl"
CLAUDE_FLAGS = [
    "--safe-mode",
    "--tools",
    "",
    "--strict-mcp-config",
    "--no-session-persistence",
    # repo 안에서 호출하면 git branch와 최근 commit 메시지가 system prompt에 들어간다.
    # commit 메시지에 실험 설계가 적혀 있어서 끈다 (2026-11-19 canary, docs/test-plan.md T1).
    "--settings",
    '{"includeGitInstructions":false}',
    "--output-format",
    "json",
]
# raw JSON에서 지울 식별자 (docs/implementation.md 2절)
SCRUB_KEYS = ("session_id", "uuid", "credential_expires_at")
NO_VARIANT = "none"


@dataclass(frozen=True)
class Case:
    id: str
    context_ok: bool
    question: str
    prior_answer: str
    reaction: str

    def render_prompt(self) -> str:
        """직전 대화를 텍스트로 붙인다. 형식은 pilot과 같다 (docs/implementation.md 3절)."""
        return (
            f"[이전 대화]\n사용자: {self.question}\n\n"
            f"assistant: {self.prior_answer}\n\n"
            f"[지금 사용자 메시지]\n{self.reaction}"
        )


@dataclass(frozen=True)
class Variant:
    name: str
    path: Path | None  # None이면 변형 없음


@dataclass
class Result:
    """results.jsonl 한 행. 필드는 docs/implementation.md 2절을 따른다."""

    case: str
    task: str
    variant: str
    model_requested: str
    repeat: int
    attempt: int
    status: str
    output: str | None
    raw_ref: str
    model_observed: str | None
    rendered_prompt_sha: str
    tokens_input_uncached: int | None
    tokens_cache_write: int | None
    tokens_cache_read: int | None
    tokens_output: int | None
    latency_cli_ms: int | None
    latency_wall_ms: int
    cost_usd: float | None
    cost_source: str | None
    num_turns: int | None
    call_order: int

    @property
    def tokens_input_total(self) -> int:
        parts = (self.tokens_input_uncached, self.tokens_cache_write, self.tokens_cache_read)
        return sum(p or 0 for p in parts)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--case",
        action="append",
        required=True,
        help="case id (반복 가능). all이면 12건 전부, main이면 context_ok인 case만",
    )
    ap.add_argument("--variant", action="append", required=True, help=f"{NO_VARIANT} 또는 변형 파일 경로 (반복 가능)")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--out", type=Path, required=True, help="experiments/<YYYY-MM-DD>-<이름>")
    return ap.parse_args()


def load_cases() -> list[Case]:
    cases: list[Case] = []
    for line in CASES_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        cases.append(Case(d["id"], d["context_ok"], d["question"], d["prior_answer"], d["reaction"]))
    return cases


def select_cases(cases: list[Case], ids: list[str]) -> list[Case]:
    if ids == ["all"]:
        return cases
    if ids == ["main"]:
        return [c for c in cases if c.context_ok]
    by_id = {c.id: c for c in cases}
    missing = [i for i in ids if i not in by_id]
    if missing:
        sys.exit(f"없는 case: {missing}")
    return [by_id[i] for i in ids]


def resolve_from_root(p: Path) -> Path:
    return p if p.is_absolute() else ROOT / p


def copy_variants(specs: list[str], inputs_dir: Path) -> list[Variant]:
    """변형 파일을 inputs/에 복사하고, 실행은 사본만 읽게 한다 (D-16)."""
    variants: list[Variant] = []
    for spec in specs:
        if spec == NO_VARIANT:
            variants.append(Variant(NO_VARIANT, None))
            continue
        src = resolve_from_root(Path(spec))
        name = src.parent.name if src.name == "SKILL.md" else src.stem
        dst = inputs_dir / f"{name}.md"
        shutil.copyfile(src, dst)
        variants.append(Variant(name, dst.resolve()))
    return variants


def call_claude(
    claude: str, prompt: str, variant: Variant, model: str, cwd: Path
) -> tuple[subprocess.CompletedProcess[str], int]:
    cmd = [claude, "-p", *CLAUDE_FLAGS, "--model", model]
    if variant.path is not None:
        cmd += ["--append-system-prompt-file", str(variant.path)]
    cmd += ["--", prompt]  # --tools가 뒤따르는 인자를 도구 이름으로 먹지 않게 한다
    start = time.monotonic()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=False)
    return proc, int((time.monotonic() - start) * 1000)


def parse_cli_json(stdout: str) -> dict[str, Any] | None:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    d = cast(dict[str, Any], data)
    for key in SCRUB_KEYS:
        d.pop(key, None)
    return d


def build_result(
    *,
    case: Case,
    variant: Variant,
    model: str,
    repeat: int,
    order: int,
    prompt: str,
    proc: subprocess.CompletedProcess[str],
    data: dict[str, Any] | None,
    wall_ms: int,
    raw_ref: Path,
) -> Result:
    d = data or {}
    usage = cast(dict[str, Any], d.get("usage") or {})
    model_usage = cast(dict[str, Any], d.get("modelUsage") or {})
    ok = data is not None and proc.returncode == 0 and not d.get("is_error")
    return Result(
        case=case.id,
        task="reexplain",
        variant=variant.name,
        model_requested=model,
        repeat=repeat,
        attempt=1,
        status="ok" if ok else "error",
        output=d.get("result"),
        raw_ref=raw_ref.as_posix(),
        model_observed=next(iter(model_usage), None),
        rendered_prompt_sha=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        tokens_input_uncached=usage.get("input_tokens"),
        tokens_cache_write=usage.get("cache_creation_input_tokens"),
        tokens_cache_read=usage.get("cache_read_input_tokens"),
        tokens_output=usage.get("output_tokens"),
        latency_cli_ms=d.get("duration_ms"),
        latency_wall_ms=wall_ms,
        cost_usd=d.get("total_cost_usd"),
        cost_source="cli_reported_api_equiv" if data is not None else None,
        num_turns=d.get("num_turns"),
        call_order=order,
    )


def write_raw(out: Path, raw_ref: Path, proc: subprocess.CompletedProcess[str], data: dict[str, Any] | None) -> None:
    path = out / raw_ref
    path.parent.mkdir(parents=True, exist_ok=True)
    if data is not None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        path.write_text(f"{proc.stdout}\n--- stderr ---\n{proc.stderr}", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out = resolve_from_root(args.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out}가 이미 있습니다. 이전 실험 폴더는 고치지 않습니다 (AGENTS.md).")
    claude = shutil.which("claude")
    if claude is None:
        sys.exit("claude CLI를 찾지 못했습니다")

    cases = select_cases(load_cases(), args.case)
    (out / "inputs").mkdir(parents=True)
    variants = copy_variants(args.variant, out / "inputs")

    version = subprocess.run([claude, "--version"], capture_output=True, text=True, check=False).stdout.strip()
    started = datetime.now().isoformat(timespec="seconds")
    results: list[Result] = []
    order = 0

    with (out / "results.jsonl").open("a", encoding="utf-8") as results_file:
        for case in cases:
            prompt = case.render_prompt()
            for repeat in range(1, args.repeat + 1):
                for variant in variants:
                    order += 1
                    proc, wall_ms = call_claude(claude, prompt, variant, args.model, out)
                    data = parse_cli_json(proc.stdout)
                    stem = f"{variant.name}__{args.model}__r{repeat}"
                    raw_ref = Path("raw") / case.id / f"{stem}.json"
                    write_raw(out, raw_ref, proc, data)
                    result = build_result(
                        case=case,
                        variant=variant,
                        model=args.model,
                        repeat=repeat,
                        order=order,
                        prompt=prompt,
                        proc=proc,
                        data=data,
                        wall_ms=wall_ms,
                        raw_ref=raw_ref,
                    )
                    results_file.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")
                    results_file.flush()
                    if result.status == "ok" and result.output is not None:
                        md = out / "outputs" / case.id / f"{stem}.md"
                        md.parent.mkdir(parents=True, exist_ok=True)
                        md.write_text(result.output, encoding="utf-8")
                    results.append(result)
                    print(
                        f"[{order}] {case.id} {variant.name} r{repeat}: {result.status} "
                        f"${result.cost_usd} {wall_ms}ms in={result.tokens_input_total} out={result.tokens_output}",
                        flush=True,
                    )

    run_info = {
        "cli_version": version,
        "flags": CLAUDE_FLAGS,
        "model": args.model,
        "cwd": out.relative_to(ROOT).as_posix() if out.is_relative_to(ROOT) else str(out),
        "injection": "system",
        "cases": [c.id for c in cases],
        "variants": {v.name: (v.path.relative_to(out).as_posix() if v.path else None) for v in variants},
        "repeat": args.repeat,
        "started": started,
        "finished": datetime.now().isoformat(timespec="seconds"),
    }
    (out / "run.json").write_text(json.dumps(run_info, ensure_ascii=False, indent=1), encoding="utf-8")

    failed = sum(r.status != "ok" for r in results)
    total_cost = sum(r.cost_usd or 0 for r in results)
    print(f"\n{len(results)}회 호출, 실패 {failed}, 합계 ${total_cost:.4f} -> {out}")


if __name__ == "__main__":
    main()
