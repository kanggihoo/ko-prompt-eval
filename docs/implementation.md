# 구현 메모

실험 harness를 만들 때 참고할 구조, 결정, 주의점입니다. 근거는 [`research.md`](research.md)에 있습니다. "미확인"이라고 적은 것은 [`test-plan.md`](test-plan.md)에서 먼저 실행해서 확인합니다.

## 1. 전체 흐름

```
data/cases.jsonl ──┐
                   ├─> task별 prompt 조립 ─> 변형 × 모델 × repeat 실행 ─> 출력 + 비용·시간·token
variants/, third_party/ ┘                                                    │
                                                                             ├─> 자동 지표 (길이, 구조, ste-ko lint)
                                                                             ├─> LLM judge (설명 task rubric)
                                                                             └─> 사람이 나란히 보고 판단 (주 판정)
```

주 판정은 사람이 합니다. 이 repo의 목적이 "내가 읽고 이해되는가"이기 때문입니다. 자동 지표와 judge는 사람이 무엇부터 볼지 정하고, case가 많아졌을 때 거르는 데 씁니다.

## 2. Task 설계

로그 case 하나(`question`, `prior_answer`, `reaction`)로 task 세 개를 만들 수 있습니다. 후보마다 원래 용도에 맞는 task에 올립니다.

| task | 모델에게 주는 것 | 비교할 변형 | 보는 것 |
|---|---|---|---|
| `reexplain` | 질문 + 직전 답변 + "뭔 말이야" | 없음, `claude-md-defaults`, `explain-clearly`, ste-ko | `gap`을 채웠는가, 사용자가 잘못 이해한 지점을 짚었는가 |
| `first-answer` | 질문만 | 없음, `claude-md-defaults`, ste-ko | 로그의 실패한 답변과 비교해 처음부터 이해되게 답했는가 |
| `rewrite` | 직전 답변 + "이 글을 이해하기 쉬운 한국어로 고쳐 써 줘" | 없음, K-Humanizer, `explain-clearly` | 같은 내용을 다듬은 것만으로 이해가 되는가 |

`reexplain`부터 시작합니다. `explain-clearly`의 효과를 묻는 질문에 바로 답하기 때문입니다.

### 직전 대화를 넣는 방법

`claude -p`는 prompt 하나만 받습니다. 그래서 pilot에서는 직전 대화를 텍스트로 붙였습니다([`experiments/2026-11-19-pilot/commit-log-flush.prompt.txt`](../experiments/2026-11-19-pilot/commit-log-flush.prompt.txt)).

```
[이전 대화]
사용자: <question>

assistant: <prior_answer>

[지금 사용자 메시지]
<reaction>
```

이 방식은 실제 대화와 다릅니다. 모델은 직전 답변을 자기가 한 말이 아니라 남의 대화 기록으로 읽습니다. 실제와 같게 하려면 assistant turn을 진짜 message로 넣어야 합니다. 방법은 두 가지가 있습니다.

- Agent SDK나 API에서 messages 배열로 넣습니다.
- `claude -p --input-format stream-json`이나 session resume으로 넣습니다. 될지는 미확인입니다.

첫 실험은 텍스트 방식으로 하고, 결과가 이 차이에 민감한지는 test-plan T5에서 확인합니다.

### skill을 넣는 방법

`--safe-mode`는 skill을 꺼서 `/explain-clearly`를 실제로 부를 수 없습니다. 그래서 SKILL.md 본문을 `--append-system-prompt-file`로 system prompt 뒤에 붙입니다. 실제 사용과 다른 점은 둘입니다.

1. **들어가는 자리.** 실제로는 사용자가 slash command를 쳤을 때 skill 본문이 대화 중간에 들어갑니다. 실험에서는 처음부터 system prompt에 있습니다.
2. **frontmatter.** 실제로는 frontmatter의 `description`이 skill 목록에 따로 실립니다. 실험에서는 frontmatter가 본문과 함께 그대로 들어갑니다.

실제 로딩과 같게 하려면 promptfoo `anthropic:claude-agent-sdk`에 `working_dir/.claude/skills/`를 두는 방식을 씁니다. 이 경로가 구독 로그인으로 되는지는 미확인입니다(T3).

K-Humanizer는 SKILL.md가 `references/`를 필요할 때 읽게 되어 있습니다. system prompt 주입 방식에서는 references를 읽을 수 없습니다. 그래서 둘 중 하나를 고르고, 어느 쪽인지 실험 기록에 적습니다.

- SKILL.md만 넣습니다.
- references 중 필요한 것을 이어 붙여 넣습니다. 그만큼 token이 늘어납니다.

ste-ko도 마찬가지로 `SPEC.md`와 `dictionary.md`를 참조합니다.

## 3. 실행기 선택

| 방식 | 인증 | 격리 | 장점 | 단점 |
|---|---|---|---|---|
| A. promptfoo `exec` provider로 `claude -p --safe-mode` 감싸기 | 구독 (실측 확인) | `--safe-mode` (실측 확인) | 지금 바로 됨. promptfoo UI와 assertion을 그대로 씀 | cache key에 SKILL.md 내용이 안 들어감. 비용과 token을 promptfoo 형식으로 넘겨야 함 |
| B. promptfoo `anthropic:claude-agent-sdk` | 구독 가능한지 미확인 | `setting_sources: []` (홈 설정이 안 보이는지 미확인) | 실제 skill 로딩. 비용 자동 기록. `skill-used` 채점 | 확인할 것이 많음 |
| C. promptfoo `anthropic:messages` (API 직접) | `ANTHROPIC_API_KEY`, 과금 | 완전 (Claude Code 프리셋도 없음) | 깨끗한 비교. 입력 token이 작음 | Claude Code 환경과 다름. 돈이 듦 |
| D. 직접 Python 스크립트 | A와 같음 | A와 같음 | 의존성 없음 | 결과 보기 UI를 직접 만들어야 함 |

A로 시작하는 것을 권합니다. 구독으로 되는 것을 이미 확인했고, promptfoo의 행렬 실행, 결과 DB, web UI를 그대로 쓸 수 있습니다. B가 된다는 것이 확인되면 실제 skill 로딩 비교를 B로 옮깁니다.

### A의 모양 (미확인 초안)

```yaml
# promptfooconfig.yaml (초안. exec provider 인자 형식은 T4에서 확인)
prompts:
  - file://prompts/reexplain.txt          # {{question}}, {{prior_answer}}, {{reaction}}
providers:
  - id: 'exec: python3 scripts/run_claude.py --model sonnet --variant none'
    label: sonnet/none
  - id: 'exec: python3 scripts/run_claude.py --model sonnet --variant variants/claude-md-defaults.md'
    label: sonnet/defaults
  - id: 'exec: python3 scripts/run_claude.py --model sonnet --variant variants/explain-clearly/SKILL.md'
    label: sonnet/explain-clearly
  - id: 'exec: python3 scripts/run_claude.py --model sonnet --variant third_party/ste-ko/skills/ste-ko/SKILL.md'
    label: sonnet/ste-ko
tests: file://data/cases.jsonl
defaultTest:
  assert:
    - type: python
      value: file://scripts/assert_lint.py    # ste-ko lint, 1000어절당 위반 수
      metric: lint
    - type: llm-rubric
      provider: ...                            # judge 모델을 명시 (5절 참고)
      value: file://rubrics/reexplain.md
      metric: judge
```

`scripts/run_claude.py`가 할 일은 이렇습니다.

1. `claude -p --safe-mode --model <m> --output-format json [--append-system-prompt-file <variant>]`를 실행합니다.
2. stdout JSON에서 `result`를 출력으로 넘깁니다.
3. 비용과 token은 promptfoo가 읽을 수 있는 형식으로 넘깁니다. 형식은 T4에서 확인합니다.
4. 원본 JSON은 실험 폴더에도 따로 저장합니다. promptfoo DB에는 행 단위 token 컬럼이 없기 때문입니다.

### 모델

| 모델 | 실행 | 비고 |
|---|---|---|
| Haiku, Sonnet, Opus | `claude -p --model haiku|sonnet|opus` | alias는 최신 모델로 풀리므로 기록에는 JSON `modelUsage`의 정확한 모델 ID를 남깁니다 |
| Codex (GPT) | `codex exec -m <model>` | 전역 `~/.codex/AGENTS.md` 격리 방법이 미확인입니다(T6). promptfoo Codex provider는 cache가 없고 비용을 가격표로 추정하며, `model`을 지정하지 않으면 비용이 undefined입니다 |

## 4. 채점

### 자동 지표 (모델 호출 없음)

| 지표 | 얻는 곳 | 해석 |
|---|---|---|
| 비용 | `total_cost_usd` | 구독이면 API 가격 환산 추정치. 변형끼리 상대 비교에만 씀 |
| 시간 | `duration_ms` | cache를 끄고 잰 값만 비교 |
| 입력·출력 token | `usage` | 입력 차이는 곧 변형의 크기. 출력 token은 길이 |
| 구조 비율 | 출력 텍스트 | 소제목, bullet, 표, 코드 블록 수. `explain-clearly`는 문단형을 지시하므로 이 차이가 드러나야 함 |
| ste-ko lint | `third_party/ste-ko/scripts/lint.py --surface 대화` | 1000어절당 위반 수, 규칙별 수. 평범한 단어도 잡으므로 보조 지표 |

### LLM judge

K-Humanizer의 방식을 따르되, rubric은 설명 task용으로 바꿉니다.

- **judge 모델.** 생성 모델과 다른 모델을 씁니다. 예를 들어 생성이 Sonnet이면 judge는 Opus나 GPT입니다.
- **숨길 것.** 어느 변형의 출력인지와 변형의 지시문은 judge에게 보여 주지 않습니다.
- **judge에게 주는 것.** `question`, `prior_answer`, `reaction`, `gap`, 출력.
- **항목** (1–5점):
  - `gap_filled`: `gap`에 적은 빠진 연결을 채웠는가.
  - `addresses_reaction`: 사용자 반응에 드러난 오해를 짚었는가(예: `kafka-inbox-latest`에서 "E2가 먼저 와서 inbox에 넣고 offset 커밋을 한다는 거 아니야?").
  - `meaning_fidelity`: 직전 답변의 맞는 내용을 틀리게 바꾸지 않았는가.
  - `korean_naturalness`: K-Humanizer rubric을 그대로 가져옵니다.
  - `length_fit`: 이해에 필요한 만큼만 썼는가. 길이 자체가 아니라 사용자가 다시 막힐 만한 확장이 있는지를 봅니다. `rust-result-guard`처럼 설명이 늘수록 더 이해하지 못하는 경우가 있기 때문입니다.
- **빼는 항목.** K-Humanizer의 `edit_discipline`(원문을 덜 고칠수록 좋음)은 교정 task 기준입니다. `reexplain`에는 빼고 `rewrite` task에서만 씁니다.
- **출력 형식.** judge는 JSON으로 답하게 하고, 파싱이 실패하면 그 행을 실패로 표시합니다(prompt-optimizer 방식). 판정은 judge의 요약문이 아니라 항목별 점수 행에서 셉니다.
- **열 사이 비교.** `select-best`로 case마다 변형 중 하나를 고르게 하면 사람 판단과 비교하기 쉽습니다.

### 사람

1. 판정은 사람이 직접 읽고 합니다. promptfoo `view`의 사람 평점이나, 실험 폴더에 HTML 비교표를 만들어 씁니다.
2. 변형 이름을 가리고 읽어야 선입견이 줄어듭니다. 열 label을 무작위 문자로 바꾼 사본을 만듭니다.
3. 마지막에 사람 판정과 judge 판정이 얼마나 맞는지 봅니다. 많이 맞으면 judge로 case를 늘려도 됩니다.

## 5. 주의할 점

promptfoo 리포트(`PF/`)에서 이번 실험에 영향을 주는 것만 모았습니다.

- **cache가 시간을 가립니다.** 응답 cache가 기본으로 켜져 있습니다(디스크, TTL 14일). cache가 적중한 행은 시간이 저장값이거나 조회 시간이고, 비용이 0입니다(`PF/capabilities/response-cache.md` R-01, R-16; `PF/capabilities/eval-records.md` R-10). 시간과 비용을 비교하는 실험은 `--no-cache`로 돌립니다.
- **cache 때문에 스킬 수정이 반영되지 않을 수 있습니다.** `exec` provider는 cache key에 SKILL.md 내용이 들어가지 않습니다(R-19, R-33). Agent SDK에서도 mtime을 보존하는 수정, symlink, `working_dir` 밖의 skill은 cache를 무효화하지 않습니다(R-22, R-30). 변형을 고친 뒤에는 `--no-cache`로 돌리거나 cache를 지웁니다.
- **grader가 바뀔 수 있습니다.** `OPENAI_API_KEY`가 환경에 있으면 대상이 Claude여도 기본 grader가 OpenAI가 됩니다(`PF/capabilities/default-providers.md` R-04). `llm-rubric`마다 `provider`를 명시합니다.
- **비용이 빠지는 경우가 있습니다.** 비용이 undefined인 provider에 `cost` assertion을 쓰면 throw합니다. 저장 단계에서 "미보고"와 "0"이 구분되지 않습니다(R-11). judge 비용은 기록되지 않아서 직접 합산해야 합니다.
- **API key가 DB에 남습니다.** `{{env.KEY}}`로 넣은 값이 렌더된 채로 DB에 저장됩니다(`PF/capabilities/results-store.md` R-37).
- **`view` 서버는 인증이 없습니다.** 모든 interface에 바인딩됩니다(`PF/capabilities/web-ui.md`). 같은 네트워크에서 열리지 않게 주의합니다.
- **agent provider에는 자체 타임아웃이 없습니다.** `max_turns`, `max_budget_usd`, `timeoutMs`를 설정합니다(`PF/capabilities/agent-providers.md` R-30). `claude -p`에는 `--max-budget-usd`가 있습니다.
- **Nunjucks가 SKILL.md를 깨뜨릴 수 있습니다.** 변형을 `{{rule}}` 변수로 넣으면 SKILL.md 안의 `{{`나 `{%`가 템플릿으로 해석됩니다. 이 위험 때문에 A 방식에서는 변형을 provider 인자(파일 경로)로 넘깁니다.
- **입력 token에 기본 프리셋이 깔립니다.** `--safe-mode`에서도 Claude Code 기본 system prompt와 도구 설명으로 입력이 약 18.6k token입니다. 이 중 상당 부분이 cache 읽기로 처리되어 비용이 줄어듭니다. 변형의 순수 비용은 baseline과의 차이로 봅니다.
- **모델 출력에는 편차가 있습니다.** 한 번만 돌린 결과로 판단하지 않습니다. 최소 `repeat: 3`으로 돌리고, 점수의 평균과 표준편차는 promptfoo가 내주지 않으므로 직접 계산합니다.

## 6. 실행 기록

K-Humanizer의 `runs.jsonl` 방식을 따릅니다. 실험 폴더마다 `run.json`을 남깁니다.

- 날짜, 실행한 사람이나 agent
- `claude --version`, 실행 flag 전체
- 변형마다 파일 경로와 SHA-256
- `data/cases.jsonl`의 SHA-256과 사용한 case id
- 모델 ID(alias가 아니라 `modelUsage`의 실제 ID), judge 모델
- repeat 수, cache 사용 여부

공통 기록 키는 `(실행 id, 모델, 변형 SHA, case id, repeat)`입니다. oss-analysis `prompt-eval/GUIDE.md`의 제안을 따른 것입니다.

## 7. 오픈소스별 활용 정리

| 출처 | 이 repo에서 쓰는 곳 |
|---|---|
| K-Humanizer | 비교 후보(`rewrite` task), 데이터셋 schema(`must_preserve`, `avoid`, no-op case), judge 항목 일부(`meaning_fidelity`, `korean_naturalness`), blind judge, `runs.jsonl` 기록 방식, `--safe-mode` 격리 |
| ste-ko | 비교 후보(`reexplain`, `first-answer`), `lint.py` 자동 지표, `dictionary.md` 번역투 사전(사람이 읽을 때 참고) |
| promptfoo | 행렬 실행, 결과 DB, web UI, assertion, `select-best`, (확인되면) Agent SDK skill 로딩 |
| prompt-optimizer | judge JSON 계약과 파싱 실패 처리. 나중에 개선 루프를 만들 때 재작성 설계 |

## 8. 데이터셋 확장

- 후보는 `python3 scripts/mine.py`로 다시 뽑습니다. 원자료 302건은 `data/candidates.local.json`(git 제외)에 저장됩니다.
- 고르는 기준은 [`data/README.md`](../data/README.md)에 있습니다. 15~30건이면 첫 판단에는 충분합니다. 변형이 비슷한 결과를 낸다면 늘리기 전에 case 종류(개념, 학습, codebase, 설계)를 넓히는 편이 낫습니다.
- K-Humanizer처럼 "이미 이해하기 쉬운 답변"도 몇 건 넣어 두면, `explain-clearly`가 필요 없는 확장을 하는지 볼 수 있습니다. 로그에서 사용자가 "오케이", "이해됨"이라고 한 답변이 후보입니다.
- codebase를 알아야 답할 수 있는 case(`chip-undefined`)는 맥락 없이 돌리면 모든 변형이 실패합니다. 이런 case는 관련 파일 발췌를 `context` 필드로 넣거나, 따로 표시해서 결과를 구분해 봅니다.
