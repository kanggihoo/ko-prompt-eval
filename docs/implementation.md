# 구현 설계

실험 harness를 어떻게 만들지 정리한 문서입니다. 결정의 출처는 [`decisions.md`](decisions.md)에 있습니다. 평가 방법은 [`evaluation.md`](evaluation.md)에 따로 있습니다. 아직 확인하지 않은 사실은 "미확인"으로 표시했고, [`test-plan.md`](test-plan.md)에서 먼저 확인합니다.

## 1. 전체 흐름

```
plan.yaml ─┐
data/, variants/, third_party/ ─┴─> run ──> inputs/ (입력 사본), run.json, raw/, results.jsonl
                                              │
                         ┌────────────────────┼────────────────────┐
                         v                    v                    v
                      metrics              judge                report
                  (metrics.jsonl)       (judge.jsonl)   (report.html, blind_map.json)
                                                                   │
                                                                   v
                                                    사람 판정 export (human.jsonl)
```

- `run`만 모델을 부릅니다.
- `metrics`, `judge`, `report`는 각각 `results.jsonl`을 읽습니다. 그래서 모델을 다시 부르지 않고 다시 계산할 수 있습니다(D-15).
- `report`는 사람 판정 전에도 만들 수 있어야 합니다.

## 2. 실험 폴더 계약 (`experiments/<YYYY-MM-DD>-<이름>/`)

| 파일 | 만드는 단계 | 내용 |
|---|---|---|
| `plan.yaml` | 사람 | task, case 목록, 변형 경로, 모델(adapter와 모델 이름), repeat 수, seed |
| `inputs/` | `run` 시작 | 이번 실행에 쓸 case, prompt template, 변형, 포함한 reference의 사본. 실행은 이 사본만 읽음. 원본이 실행 중에 바뀌어도 영향 없음 (D-16) |
| `run.json` | `run` | repo HEAD, 입력 파일별 경로·SHA-256·HEAD와 일치 여부, template SHA, CLI 버전, 실행 flag 전체, 변형 주입 방식(`system`/`prefix`), 실제 호출 순서와 seed, 시작·끝 시각 |
| `raw/<case>/<variant>__<model>__r<k>.json(l)` | `run` | CLI stdout 원본. Codex는 JSONL. `session_id`, `uuid`, 인증 만료 시각 같은 식별자는 지움 |
| `results.jsonl` | `run` | 호출 1회 = 1행 (아래 필드) |
| `metrics.jsonl` | `metrics` | 자동 지표 ([`evaluation.md`](evaluation.md) 4절) |
| `judge.jsonl` | `judge` | judge 모델, judge prompt SHA, 항목별 판정, 원문 응답, 파싱 상태 |
| `blind_map.json` | `report` | review ID, 출력 ID ↔ 변형, A/B 위치, 제시 순서 |
| `report.html` | `report` | blind 짝 판정 화면. localStorage에 저장하고 JSON으로 내보냄. `gap`은 보여 주지 않음 |
| `human.jsonl` | 사람 (export) | 판정 ([`evaluation.md`](evaluation.md) 2절) |
| `README.md` | 사람 | 결론, `완료 쌍 / 계획 쌍`, 변형별 실패 수 |

### `results.jsonl` 필드

| 필드 | 내용 |
|---|---|
| `case`, `task`, `variant`, `model_requested`, `repeat`, `attempt` | 키. 재시도하면 `attempt`가 늘고 이전 시도도 남음 (D-17) |
| `status` | `ok` / `error` / `timeout` |
| `output` | 출력 텍스트 |
| `raw_ref` | `raw/` 안의 경로 |
| `model_observed` | 응답이 보고한 실제 모델 ID. alias가 아니라 `modelUsage`의 키 |
| `rendered_prompt_sha` | 모델에 실제로 보낸 prompt의 SHA-256 |
| `tokens_input_uncached`, `tokens_cache_write`, `tokens_cache_read`, `tokens_output`, `tokens_thinking` | token 성분. Claude는 `usage.input_tokens`가 cache를 뺀 값이라 성분을 따로 둠. pilot에서 `input_tokens`는 2였고 나머지는 cache였음 |
| `latency_cli_ms`, `latency_wall_ms` | CLI가 보고한 시간과 runner가 잰 시간 |
| `cost_usd`, `cost_source` | `cli_reported_api_equiv`(Claude, 구독이면 API 가격 환산 추정) / `price_table_estimate` / `null` |
| `num_turns`, `tool_calls`, `tool_denials` | 도구 사용 신호. 보고되지 않으면 `null` (D-13) |
| `call_order` | 실행 순서 번호 |

공개해도 되는 입력만 `inputs/`에 저장합니다. `third_party/`의 두 원본은 MIT라 저장해도 됩니다.

## 3. Task와 prompt

두 task는 서로 비교하지 않고 각각 평가합니다(D-4).

| task | 모델이 받는 입력 | 변형 | 데이터 |
|---|---|---|---|
| `reexplain` | 질문 + 직전 답변 + 사용자 반응 | 없음, `claude-md-defaults`, `explain-clearly`, ste-ko | 로그 9건 (`context_ok: true`) |
| `rewrite` | 직전 답변 + "이해하기 쉬운 한국어로 고쳐 써 줘" | 없음, `claude-md-defaults`, K-Humanizer | 로그 9건. 뒤에 `business_korean.v1` 32건 |

### 직전 대화를 넣는 방법

`claude -p`는 prompt 하나만 받으므로, 직전 대화를 텍스트로 붙입니다. 형식은 pilot과 같습니다([`experiments/2026-11-19-pilot/commit-log-flush.prompt.txt`](../experiments/2026-11-19-pilot/commit-log-flush.prompt.txt)).

```
[이전 대화]
사용자: <question>

assistant: <prior_answer>

[지금 사용자 메시지]
<reaction>
```

이렇게 하면 모델은 직전 답변을 자기가 한 말이 아니라 남의 대화 기록으로 읽습니다. 실제 assistant turn으로 넣는 방식과 결과가 다른지는 T5에서 봅니다.

### 변형을 넣는 방법

- **Claude:** `--append-system-prompt-file <inputs/…>`로 system prompt 뒤에 붙입니다. `--safe-mode`가 skill을 끄기 때문에 `/explain-clearly`를 실제로 부를 수는 없습니다. 실제 사용과 두 가지가 다릅니다.
  - 실제로는 skill 본문이 대화 중간에 들어가지만, 실험에서는 처음부터 system prompt에 있습니다.
  - 실제로는 frontmatter의 `description`이 skill 목록에 따로 실리지만, 실험에서는 frontmatter가 본문과 함께 들어갑니다.
- **Codex, agy:** system prompt 자리에 넣는 flag가 없거나 미확인입니다. 그래서 prompt 앞에 붙이고 `injection: prefix`로 기록합니다(T6, T12).
- **reference를 참조하는 skill:** K-Humanizer는 SKILL.md가 `references/`를, ste-ko는 `SPEC.md`와 `dictionary.md`를 필요할 때 읽게 되어 있습니다. 주입 방식에서는 이 파일을 읽을 수 없습니다. 그래서 SKILL.md만 넣을지, 필요한 reference를 이어 붙일지 `plan.yaml`에서 정하고 기록합니다.

## 4. Runner와 adapter

- 진입점은 `python3 -m koeval run|metrics|judge|report experiments/<dir>`입니다(D-15).
- 패키지는 `koeval/`이고, adapter는 `koeval/adapters/{claude,codex,agy}.py`입니다.
- 공통 계약은 `run(prompt, variant_path|None, model) → 정규화된 행 + raw + injection`입니다. 순수 JSON이나 이벤트 스트림 파싱은 adapter 안에 둡니다.
- 실행은 직렬로 합니다. 같은 case, 모델, repeat 안에서 변형 순서는 seed로 섞고 실제 순서를 기록합니다(D-18).
- 모든 호출은 그 실험 폴더를 cwd로 해서 합니다(D-14). harness 전까지는 `scripts/run_case.py`가 임시 runner입니다.

### Adapter별 명령

| adapter | 명령 | 상태 |
|---|---|---|
| Claude | `claude -p --safe-mode --tools "" --strict-mcp-config --no-session-persistence --settings '{"includeGitInstructions":false}' --output-format json --model <m> [--append-system-prompt-file <변형>] -- "<prompt>"` | `--safe-mode`, `--tools ""`, JSON 출력 확인. `--strict-mcp-config`는 안전장치(5절) |
| Codex | `codex exec --ephemeral --ignore-user-config --sandbox read-only --skip-git-repo-check -m <m> --json …` (빈 cwd) | flag가 있는지는 `codex exec --help`로 확인. 격리와 text-only 여부는 미확인 (T6) |
| agy | `agy -p --output-format json --model gemini-3.8-flash-<level> --print-timeout <t> …` (빈 cwd, `--sandbox`) | print mode와 JSON 확인. 격리와 skill 목록 노출은 미확인 (T12) |

### Claude 실측 (2026-11-19, Haiku, prompt "ok")

| 조건 | 입력 token | 비용 |
|---|---|---|
| `--safe-mode` | 18,388 | $0.0015 |
| `--safe-mode --tools ""` | 2,815 | $0.0005 |

입력의 약 85%가 도구 설명이었습니다. 도구를 끄면 비용이 약 1/3로 줄고, baseline이 작아져서 변형(`explain-clearly` 약 1.5k token)의 영향이 더 또렷해집니다.

## 5. 주의할 점

- **`--tools ""` 뒤 prompt:** `--tools`는 값을 여러 개 받아서, 바로 뒤에 오는 prompt까지 도구 이름으로 먹습니다. 2026-11-19 첫 시도가 이것으로 실패했습니다. prompt 앞에 `--`를 붙입니다.
- **`--tools`와 MCP:** [`cost-notes.md`](cost-notes.md) 1절에 따르면, MCP가 켜진 상태에서 `--tools`에 `ToolSearch`가 없으면 MCP 도구 정의가 처음부터 전부 실립니다. 그때 406k token, 첫 호출 $3.26이 나갔습니다. `--safe-mode`는 MCP를 끄므로 이번 측정에서는 문제가 없었지만, 안전장치로 `--strict-mcp-config`를 함께 줍니다.
- **`--max-budget-usd`:** [`cost-notes.md`](cost-notes.md) 1절에서 상한 $1인데 요청 한 번에 $3.26이 그대로 나갔습니다. 요청 하나가 상한을 넘는 것은 막지 못하므로 비용 보호 장치로 믿지 않습니다.
- **`--bare`:** `ANTHROPIC_API_KEY`나 apiKeyHelper만 읽고 구독 로그인을 읽지 않아서 쓰지 않습니다. 문서상 앞으로 `-p` 기본값이 bare가 될 예정입니다. 그렇게 바뀌면 이 harness가 깨질 수 있으니 CLI를 업데이트한 뒤에는 한 번 확인합니다.
- **Codex 격리 flag:** `--ephemeral`과 `--ignore-user-config`는 `codex exec` 전용입니다. `project_doc_max_bytes=0`은 전역 `AGENTS.md`를 끄지 못합니다([`cost-notes.md`](cost-notes.md) 2절). skills 목록과 plugins를 끄는 설정 조합은 T6에서 확인합니다.
- **cache와 비용 해석:** cache 쓰기와 읽기는 가격이 다릅니다. pilot에서 `explain-clearly` 본문 약 1.5k token은 cache 쓰기로 처리됐습니다. 그래서 변형 사이 비용은 같은 repeat 번호끼리 비교하고, cache 성분을 함께 봅니다. cache를 쓰지 않은 입력이 줄었다고 요금이 그만큼 줄었다고 읽지 않습니다.
- **로그 오염:** `agy -p`는 호출마다 agy 로그에 대화를 남깁니다. `claude -p`도 `--no-session-persistence` 없이는 세션을 남깁니다. 2026-11-19 canary 호출이 `/private/tmp/iso-test` 세션으로 남은 것을 확인했습니다. `mine.py`는 기본으로 이 repo의 `experiments/`를 realpath로 비교해 제외합니다(`--exclude-cwd`로 추가 가능).
- **격리 확인은 매번 하지 않습니다(D-12).** 결과가 이상하면 먼저 확인할 것은 이렇습니다.
  - baseline 출력이 전역 규칙(예: 5줄의 "결론 먼저")을 따르는 것처럼 보이는가.
  - 출력에 skill 이름이나 hook 문구가 나오는가.
  - 그러면 T1 canary를 다시 돌립니다.

## 6. 첫 구현 단계

| 순서 | 할 일 | 완료 기준 | 먼저 확인할 것 |
|---|---|---|---|
| 1 | `koeval/`과 Claude adapter. pilot JSON과 fake CLI로 호출, 실패, 집계를 확인 | `python3 -m koeval run`이 예상 행 수와 누락·실패를 보여 줌. 사본을 만든 뒤 원본을 고쳐도 호출 내용과 해시가 유지됨. 주입한 실패가 완료 쌍 집계와 미확정에 반영됨 | - |
| 2 | 실제 Claude 호출로 주입과 분산 확인 | `--tools ""` 조합에서 변형이 들어가고 입력 token이 기록됨. T7로 repeat 수와 cache 재사용 확인. 실험 호출이 `mine.py` 후보에서 빠짐 | T2, T7, T11 소량 |
| 3 | `metrics`와 blind `report` | 판정 export가 출력 ID에 연결되고, 같은 데이터로 보고서를 다시 만들 수 있음 | T8 |
| 4 | E1 실행과 사람 판정 | 두 task를 9건으로 실행. `README.md`에 완료 쌍, 실패, 결론 | - |
| 5 | `judge`와 일치율 확인 | 같은 출력으로 judge를 돌려 사람과 일치율, 중요 오류 누락 비교 | T9, T10 |
| 6 | Codex·agy adapter, E2 | T6, T12 통과 뒤 변형 없이 모델 비교 | T6, T12 |
