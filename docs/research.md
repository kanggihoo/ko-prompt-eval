# 조사 내용

2026-11-19에 정리했습니다. 이 문서는 조사 기록이고, 그 뒤에 정한 것은 [`decisions.md`](decisions.md)가 우선합니다. 오픈소스 내용은 아래 적은 commit 기준이고, promptfoo와 prompt-optimizer는 [oss-analysis](https://github.com/kanggihoo/oss-analysis/tree/main/prompt-eval/reports)의 분석 리포트를 근거로 했습니다. 리포트 경로는 `PF` = `prompt-eval/reports/promptfoo/`, `PO` = `prompt-eval/reports/prompt-optimizer/`로 줄여 씁니다. 리포트는 코드를 읽고 쓴 것이고 실행해서 확인한 것은 아닙니다.

## 1. 출발점

Claude Code와 Codex 로그를 보면, 사용자가 직전 설명을 이해하지 못하고 "뭔 말이야"라고 되묻는 일이 자주 있습니다. 개인 프로필 정리 때 센 값은 121건이고, 불만 표본 40건 중 12건이 용어나 추상적인 표현 때문이었습니다. 이번에 `scripts/mine.py`로 다시 넓게 찾아보니 후보가 302건 나왔습니다(Claude 126, Codex 173, agy 3).

지금 이 문제에 대응하는 방법은 두 가지입니다.

1. **전역 `CLAUDE.md`의 "응답 기본값" 5줄.** 모든 답변에 항상 들어갑니다. "결론 먼저, 추상적인 설명에는 구체 예시, 기술 용어는 영어 원문 그대로" 같은 성향입니다. 사본은 [`variants/claude-md-defaults.md`](../variants/claude-md-defaults.md)입니다.
2. **`explain-clearly` 스킬.** 사용자가 직전 설명을 이해하지 못했을 때 `/explain-clearly`로 부릅니다. mattpocock의 `wait-what`에서 시작했고 여러 글쓰기 스킬의 규칙을 한국어용으로 다시 썼습니다. 원본 `wait-what`은 영어 통제 언어 ASD-STE100 규칙을 쓰는데, 한국어에는 맞지 않아 "직역투를 누가 무엇을 하는 문장으로 다시 짠다"는 규칙으로 바꿨습니다. 사본은 [`variants/explain-clearly/SKILL.md`](../variants/explain-clearly/SKILL.md)이고, 원본은 my-skills `skills/in-progress/explain-clearly`(commit `6c94ada`, 2026-11-11)입니다.

남은 의문은 이 변형이 실제로 효과가 있는지입니다. 더 단순하게 써도 결과가 같다면 매번 token을 덜 쓰는 쪽이 낫습니다. 이 의문을 사람이 출력을 직접 보고 판단하려는 것이 이 repo의 목적입니다.

## 2. 비교 후보

| 후보 | 크기 | 하는 일 | 입력 | 적용 방식 |
|---|---|---|---|---|
| 없음 (baseline) | 0 | - | - | - |
| `claude-md-defaults` | 542 bytes, 5줄 | 모든 답변의 기본 성향 | 질문 | 항상 켜짐 |
| `explain-clearly` | 4.2KB, 약 70줄. 실측 약 1.5k token | 이해 못 한 직전 설명을 다시 설명 | 질문 + 직전 답변 + 반응 | 사용자가 부를 때 |
| ste-ko | `SKILL.md` 6.7KB(119줄), 전체 규칙 `SPEC.md` 36KB | 모든 한국어 답변에 적용하는 통제 언어 규칙 | 질문 | 항상 켜짐 ("매 응답 적용한다") |
| K-Humanizer | `SKILL.md` 11KB(199줄), references 4개 63KB | 주어진 글을 자연스러운 한국어로 고쳐 쓰거나 번역 | 고칠 원문 | 사용자가 부를 때 |

네 후보는 푸는 문제가 다릅니다. 같은 데이터에 올릴 때 이 차이가 중요합니다.

- ste-ko와 5줄 규칙은 **처음 답할 때** 작용합니다.
- `explain-clearly`는 **이미 실패한 답변 뒤에** 작용합니다.
- K-Humanizer는 **이미 있는 글을 고쳐 씁니다.** 설명에서 빠진 연결을 채우는 스킬이 아니라, 같은 내용을 자연스럽게 다듬는 스킬입니다.

그래서 로그 case 하나로 두 가지 task를 만들 수 있습니다. 자세한 내용은 [`implementation.md`](implementation.md) 2절에 있습니다.

## 3. K-Humanizer

- 저장소: <https://github.com/evergreentree97/K-Humanizer> (commit `46218c5`, MIT)
- 사본: [`third_party/k-humanizer/`](../third_party/k-humanizer/)

### 스킬

`skills/k-humanizer/SKILL.md`는 영어로 쓰여 있습니다. 순서는 입력 모드 판별(한국어만 / 영어 원문 + 한국어 초안 / 영어만), 상황 읽기, 작성, 사실 보호, 멈출 시점, 결과 반환입니다. 패턴 목록, 비즈니스 한국어, 자연스러운 글쓰기, 평가 rubric은 `references/`에 따로 있고, SKILL.md가 필요할 때 읽게 합니다. 이력서용 `k-humanizer-resume`도 있지만 이번 사본에는 넣지 않았습니다.

### 데이터셋

| 파일 | 건수 | 내용 |
|---|---|---|
| `evals/fixtures/golden_set.v0.jsonl` | 220 | 합성. 10개 도메인, 그중 resume 90건. `{id, domain, input, expected_traits, must_preserve, avoid}` |
| `evals/fixtures/business_korean.v1.jsonl` | 32 | 모델이 maintainer 요구사항으로 만든 합성. `{id, domain, mode, input, grading:{expected_behavior, expected_traits, must_preserve, avoid}}` |

v1에는 설계상 쓸 만한 점이 두 가지 있습니다.

- **정답 출력 대신 채점 기준만 둡니다.** `expected_behavior`는 `produce_korean`, `keep_unchanged`, `ask_one_question` 중 하나입니다.
- **고치면 안 되는 case를 섞습니다.** 이미 자연스러운 글이라 그대로 둬야 하는 no-op case가 7건, 질문 하나만 해야 하는 case가 3건입니다. 스킬이 과하게 고치는지를 이 case로 잡습니다.

`avoid`도 v1에서 금지어 목록 대신 의미 기준으로 바꿨습니다. 이유는 "`통해`, `진행` 같은 단어 자체는 오류가 아니다. 단어만 피하려고 바꾸면 과잉 수정이다"입니다.

이 데이터셋은 비즈니스 문장 교정·번역용이라 "설명을 이해하기 쉽게" task에는 그대로 쓸 수 없습니다. schema와 no-op 발상만 가져옵니다. 사본으로 `business_korean.v1.jsonl`과 `golden_set.sample.jsonl`을 넣어 두었습니다.

### 실행과 격리

생성 스크립트는 repo에 없고, Claude Code 세션에서 직접 돌린 것으로 보입니다. `docs/validation-plan.md`의 "Business Forward Test"와 `evals/reports/2026-11-07-business-korean/runs.jsonl`에 방식이 적혀 있습니다.

- 생성 모델에는 `id`와 `input`만 보여 주고 `grading`은 숨깁니다(blind).
- case마다 새 프로세스를 띄우고 `--safe-mode`(CLAUDE.md, skill, plugin, hook 끔)와 `--restricted`(명령 실행 도구 제거)를 준 뒤 skill 파일을 명시적으로 넣습니다.
- 그 전의 run 세 번은 batch 세션 하나에서 돌려서 CLAUDE.md가 섞였을 수 있다고 `business-review.md` "Harness" 절에서 스스로 밝힙니다.
- `runs.jsonl`에는 run마다 `skill_revision`(skills 트리 전체를 정렬해 SHA-256), `fixture_sha256`, generator와 judge 모델, harness 설명을 남깁니다.

### 채점

LLM judge만 씁니다. 생성은 `claude-sonnet-5-5`, judge는 `claude-opus-5-5`입니다. judge에게는 input, grading, 출력, rubric(`references/evaluation.md`)을 주고 생성 지시문은 보여 주지 않습니다.

- 1–5점 항목 5개: `meaning_fidelity`(의미 보존), `korean_naturalness`(한국어 자연스러움), `context_fit`(맥락 적합), `edit_discipline`(편집 절제), `practical_usefulness`(그대로 쓸 수 있는가).
- 추가 판정: `expected_behavior_met`, `hard_failure`(가격·날짜 변경, 혜택 추가, 약속 강화 등), `lost_requirements`, `avoid_failures`.
- rubric의 원칙: "Do not score a translation by word overlap with a reference… Ask, 'Could someone actually use this sentence as-is?'"
- 사람 검토는 없고, 보고서에 "model-scored, not human review"라고 적습니다. 비용, 시간, token은 기록하지 않습니다.

### 보고된 결과

- v0 220건: 평균 4.765, 의미 보존 4.800, critical 실패 0건 (`evals/reports/2026-08-25/model-baseline.md`).
- business 세트 `metrics.jsonl`: initial run 26/30 통과, rerun 29/32. 질문 case는 0/2에서 2/3으로 올랐고 hard failure는 0건입니다.
- README에 스킬 적용 전후 비교가 있습니다(Sonnet 5.5, 32건, Opus 5.5 judge). 원문에 없는 내용 덧붙임 12→0건, 요구사항 누락 6→0건, no-op 유지 2/7→6/7입니다. 다만 근거라는 `evals/reports/2026-11-10-skill-vs-baseline/`이 clone에 없어서 확인하지 못했습니다.
- 짧은 규칙과 전체 규칙을 비교한 실험은 없습니다.

### 약점

데이터가 합성이고 같은 세트로 반복 수정해서 held-out set이 없습니다. judge는 모델 하나이고 사람 검토가 없습니다. 대상도 설명이 아니라 교정·번역입니다.

## 4. ste-ko

- 저장소: <https://github.com/beamonic/ste-ko> (commit `ed98bcb`, MIT)
- 사본: [`third_party/ste-ko/`](../third_party/ste-ko/)

### 규격

영어 ASD-STE100처럼 한국어 업무 글을 통제 언어로 고정하려는 시도입니다. SKILL.md 첫 줄이 "`쉽게 쓰세요`는 판단을 사람에게 되돌려주므로 작동하지 않는다"이고, 그래서 규칙을 목록으로 고정합니다.

- `skills/ste-ko/SKILL.md`(119줄): 표면 4개(`대화`, `문서`, `코딩`, `UI`)마다 문장·문단 상한, 항상 지키는 열 가지, 답변 분량, 규격을 자동으로 푸는 조건, 예문.
- `SPEC.md`(736줄): 번호 붙은 규칙 73개.
- `dictionary.md`(337줄): 비승인 표현 대응표. A절 번역투 조사, B절 이중피동, C절 빈 동사 등.
- "SKILL.md는 요약, 전체 규칙은 SPEC" 구조로 매 턴 들어가는 분량을 줄이려 했지만, 그 효과를 측정하지는 않았습니다.

### 벤치마크

`benchmarks/corpus-2026-08.md`는 모델 출력이 아니라 사내 기술 문서 8개(17,549어절)를 linter로 잰 결과입니다. 위반 55건(1000어절당 3.1건)이고, 비승인 어휘 51%, 범위 표기 물결표 36%, 같은 종결어미 3연속 11%, 어절 상한 초과 2%였습니다. 저자의 결론은 "문장 길이는 문제가 아니었다"입니다. 모델, 변형, 비용, lite와 full 비교는 없습니다.

### Linter

`scripts/lint.py`(244줄, stdlib만 사용)는 규칙 7개를 기계로 잡습니다.

- 4.1 어절 상한, 4.7 문단 문장 수, 4.8 같은 종결어절 3연속, 3.2 이중피동, 8.1 물결표, 8.5 말줄임표, 1.3 비승인 어휘.
- `대화` 표면에서는 10.4 앞 턴 되풀이(`좋은 질문`, `말씀하신`, `확인해 보겠` 등으로 시작)도 잡습니다.
- 이중피동은 어간 목록을 활용형으로 펼쳐서 잡습니다(`되어집니다`까지).
- 비승인 어휘는 `dictionary.md` 표를 파싱해서 regex로 만듭니다.
- 코드 펜스, 표, 인용, 인라인 코드는 검사하지 않습니다. 위반이 있으면 종료 코드 1을 냅니다.

이 repo에서 `--self-test`가 통과하는 것을 확인했습니다. pilot 출력 두 개에 돌려 보니 "일단", "최근", "여러" 같은 평범한 단어도 위반으로 잡았습니다([`experiments/2026-11-19-pilot/`](../experiments/2026-11-19-pilot/README.md)). 단어 금지 방식은 K-Humanizer가 과잉 수정이라며 버린 방식과 정면으로 충돌합니다. 그래서 lint 점수는 보조 지표로만 씁니다.

## 5. promptfoo

분석 리포트: [`PF/`](https://github.com/kanggihoo/oss-analysis/tree/main/prompt-eval/reports/promptfoo)

prompt 평가 CLI입니다. 이번 목적의 대부분을 기본 기능으로 처리합니다.

### 행렬 실행

설정 파일 하나에 `providers`(모델마다 `id`, `label`, `config`), `prompts`, `tests`(`vars` + `assert`), `defaultTest`를 둡니다. 결과 표의 열은 provider × prompt이고 행은 test입니다. 실행 횟수는 대략 repeat × 변수 조합 × 열 수입니다(`PF/overview.md` 2절 Q1, `PF/capabilities/eval-run.md` R-50). test는 CSV, xlsx, `file://` jsonl, HF dataset에서 불러올 수 있습니다(`PF/capabilities/config-loading.md` 1.3).

변형을 system 메시지에 넣으려면 `{{rule}}` 자리를 두고 `vars`에 `file://...`로 주입합니다. 원문을 Nunjucks로 렌더하기 때문에 SKILL.md 안의 `{{`나 `{%`가 깨질 수 있습니다(`PF/overview.md` Q1 6번).

### 비용, 시간, token

- 행마다 `latency_ms`와 `cost`가 SQLite `~/.promptfoo/promptfoo.db`의 `eval_results`에 저장됩니다. 행 단위 `tokenUsage` 컬럼은 없습니다(`PF/capabilities/eval-records.md` 1.3, R-10, R-11).
- web UI는 열마다 통과율, 총·평균 비용, 평균 지연, tok/s를 보여 줍니다. 두 eval을 Compare로 나란히 볼 수 있고 사람이 평점을 줄 수 있습니다(`PF/capabilities/web-ui.md` 1.1, R-13, R-24).
- CSV export에는 latency와 token 열이 없습니다(`PF/capabilities/results-store.md` 2.1).

### 채점 (assertion 68종)

- 결정적 채점: `regex`, `contains`, `word-count`, `javascript`, `python`. 응답 필드 채점: `cost`, `latency`(threshold 필수).
- 모델 채점: `llm-rubric`, `g-eval`.
- 열 사이 비교: `select-best`(grader를 test당 1회 호출), `max-score`(모델 호출 없음).
- `weight`와 `metric`으로 항목별 점수(`namedScores`)를 나눠 볼 수 있습니다.

근거는 `PF/capabilities/assertion-family.md` 1.3과 R-29, R-49~R-52입니다.

### Claude Code 방식으로 skill 로딩

`anthropic:claude-agent-sdk`(`anthropic:claude-code`와 같은 클래스)가 있습니다(`PF/capabilities/agent-providers.md` 표 1-A, 1-B).

- `setting_sources`의 기본값이 `[]`라서 user, project, local 설정을 읽지 않는 것이 설계 의도입니다(R-15). 실제로 홈의 skill과 설정이 안 보이는지는 리포트에서도 확인하지 못했습니다.
- skill은 `working_dir/.claude/skills/<이름>/SKILL.md`에 두고 `setting_sources: ['project']`, `skills: ['이름']`을 줍니다(R-55). 공식 예제는 `examples/claude-agent-sdk/skill-comparison`입니다.
- `custom_system_prompt`는 Claude Code 프리셋을 통째로 바꾸고, `append_system_prompt`는 뒤에 덧붙이고, `exclude_dynamic_sections`는 사용자별 동적 구간을 뺍니다(R-17).
- 비용은 SDK의 `total_cost_usd`를 씁니다. prompt token에 cache 읽기·쓰기가 합산되고 `cached` 필드는 비어 있습니다(R-27, R-28).
- `skill-used` assertion으로 skill을 실제로 불렀는지 채점할 수 있습니다(`PF/capabilities/skill-calls-metadata.md`).

### 함정

- **cache:** 응답 cache가 기본으로 켜져 있습니다(디스크, TTL 14일). cache가 적중한 행은 시간이 저장값이고 비용이 0입니다(`PF/capabilities/response-cache.md` R-01, R-16).
- **`exec` cache key:** 명령에 직접 나온 파일만 해시합니다. wrapper가 따로 읽는 SKILL.md는 key에 들어가지 않습니다(R-19).
- **grader:** `OPENAI_API_KEY`가 환경에 있으면 기본 grader가 OpenAI가 됩니다(`PF/capabilities/default-providers.md` R-04).
- **비용 기록:** 저장 단계에서 "미보고"와 "0"이 구분되지 않습니다(`PF/capabilities/eval-records.md` R-11).
- **API key:** `{{env.KEY}}` 값이 DB에 평문으로 저장됩니다(`PF/capabilities/results-store.md` R-37).
- **`view` 서버:** 인증 없이 모든 interface에 바인딩됩니다.
- **Nunjucks:** 템플릿 변수로 넣은 SKILL.md의 `{{`, `{%`가 템플릿으로 해석됩니다.

이 함정들과 "세 모델이 모두 구독 CLI라 결국 `exec` provider가 된다"는 점 때문에 promptfoo는 지금 쓰지 않습니다([`decisions.md`](decisions.md) D-10, [토론 I1](discussions/2026-11-19-eval-automation.md)).

## 6. prompt-optimizer

분석 리포트: [`PO/`](https://github.com/kanggihoo/oss-analysis/tree/main/prompt-eval/reports/prompt-optimizer)

브라우저 앱입니다. 입력 하나를 (prompt 버전 × 모델) 최대 4개 조합으로 병렬 실행해서 눈으로 비교하고, 별도 judge 모델이 0~100점, 차원 점수, 개선안을 냅니다(`PO/overview.md` 2절 Q1).

이번 목적에는 엔진으로 맞지 않습니다. 이유는 다섯 가지입니다.

- 데이터셋 일괄 실행이 없습니다.
- compare 평가가 모델별 점수가 아니라 전체 점수 하나만 냅니다.
- 비용과 지연 시간을 기록하지 않습니다.
- Claude Code의 skill 로딩을 재현할 수 없습니다.
- 키가 브라우저 저장소에 평문으로 남습니다. license는 AGPL입니다.

가져올 것은 두 가지입니다. judge가 JSON으로 답하는 계약과 파싱 실패 시 처리(`PO/capabilities/llm-evaluation.md`), 평가 결과를 재작성 입력으로 압축하는 설계(`PO/capabilities/iterate-rewrite.md`)입니다. 두 번째는 나중에 개선 루프를 만들 때 참고합니다.

## 7. Claude Code 격리 실측 (claude 2.1.327)

`claude --help`에서 확인한 격리 관련 flag는 다음과 같습니다.

| flag | 하는 일 | 인증 |
|---|---|---|
| `--bare` | hook, LSP, plugin sync, auto-memory, CLAUDE.md 자동 탐색을 끔 | `ANTHROPIC_API_KEY` 또는 apiKeyHelper만. OAuth 안 됨 |
| `--safe-mode` | CLAUDE.md, skill, plugin, hook, MCP, custom command, output style 등 모든 customization을 끔 | 구독 OAuth 그대로 됨 (실측) |
| `--restricted` | 명령 실행 도구와 WebFetch를 빼고 user/project/local 설정 파일을 무시 | - |
| `--setting-sources` | 읽을 설정 출처 지정 (user, project, local) | - |
| `--append-system-prompt-file` | 기본 system prompt 뒤에 파일 내용을 덧붙임 | - |
| `--output-format json` | 결과와 함께 `total_cost_usd`, `duration_ms`, `usage`, `modelUsage`를 돌려줌 | - |

canary 실측 결과(Haiku):

- `claude -p`로 물으면 전역 `CLAUDE.md`에만 있는 Jira cloudId를 답했고, plugin hook이 주입한 "PONYTAIL MODE" 문구도 있다고 답했습니다.
- `claude -p --safe-mode`로 물으면 둘 다 모른다고 답했습니다.

즉 `--safe-mode`만 붙이면 구독 로그인 그대로 격리됩니다. 다만 `--safe-mode`에서도 Claude Code 기본 system prompt와 도구 설명이 들어가서 입력이 약 18.6k token입니다. 변형 간 차이는 이 baseline을 빼고 봐야 합니다. 구독일 때 `total_cost_usd`는 API 가격으로 환산한 추정치이고, 실제로는 구독 사용량 한도를 씁니다.

## 8. 결론

- 처음에는 promptfoo를 실행 엔진으로 권했습니다. 이후 토론과 사용자 결정으로, CLI를 직접 부르는 얇은 Python runner로 바꿨습니다([`decisions.md`](decisions.md) D-10). 직접 만들 것은 runner, 데이터셋, 설명 task용 judge rubric, blind 판정 화면입니다.
- 한국어 오픈소스 두 곳 모두 runner, 비용과 시간 기록, 짧은 규칙 대 긴 규칙 비교가 없습니다. 이 repo가 처음 묻는 질문이 그 비교입니다.
- 데이터는 합성보다 실제 실패 로그가 낫습니다. 실제로 이해하지 못한 답변이 이미 302건 후보로 있습니다.
