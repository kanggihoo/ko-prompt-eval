# 데이터셋

`cases.jsonl`은 실제 Claude Code, Codex, Antigravity CLI(agy, Gemini) 대화에서 사용자가 직전 설명을 이해하지 못한 장면을 뽑은 것입니다. 한 줄이 case 하나입니다.

## Schema

| 필드 | 내용 |
|---|---|
| `id` | case 이름 |
| `context_ok` | 질문 + 직전 답변 + 반응만으로 사용자가 무엇을 잘못 이해했는지 특정할 수 있는가. `true` 9건이 주 평가 대상 (D-5). 실험 전에 고정 |
| `type` | `concept`(개념 설명), `study`(학습 문제), `design`(설계 논의), `codebase`(codebase 맥락이 필요함), `domain`(프로젝트 도메인과 화면 맥락이 필요함) |
| `source` | `agent`(claude/codex/agy), `session`(session id 앞 8자리), `event`(`sessions.py show <session> --event <event>`로 원문을 볼 수 있는 위치), `date`, `model`(직전 답변을 낸 모델. 로그에 없으면 `null`) |
| `question` | 직전 답변을 부른 사용자 메시지 (1500자에서 자름) |
| `prior_answer` | 사용자가 이해하지 못한 assistant 답변. 직전 user turn 이후 assistant 텍스트를 모두 이어 붙인 것이라, tool 실행 중간의 짧은 안내문이 섞여 있을 수 있음 |
| `reaction` | "뭔 말이야"류 사용자 반응. 욕설을 포함해 원문 그대로 |
| `gap` | 직전 답변이 빠뜨린 연결에 대한 해석. 채점용 AI의 평가 기준(`gap_filled`)으로만 쓰고, 생성 모델과 사람 판정 화면에는 보여 주지 않음 (`docs/decisions.md` D-6) |
| `gap_author` | `gap`을 쓴 쪽. 현재 12건 모두 `claude`. `explain-clearly`의 "빠진 연결" 관점으로 썼기 때문에 `gap_filled` 점수는 `explain-clearly`에 조금 유리할 수 있음. 해석할 때 감안 |
| `gap_reviewed` | 사용자가 `gap`을 검토했는지. 검토는 필수가 아님. 고치고 싶으면 사람 판정이 끝난 뒤에 함 (판정 전에 읽으면 해석이 판정을 끌고 감) |

## 현재 case (12건)

| id | type | 출처 (모델) | gap 요약 |
|---|---|---|---|
| `subnet-range` | study | Claude (sonnet-5-5) | "바뀌는 칸", "구간 크기"를 정의 없이 씀 |
| `kafka-inbox-latest` | concept | Claude (sonnet-5-5) | 사용자가 생각한 흐름에서 출발하지 않고 표 2개로 넓힘 |
| `deploy-lock` | concept | Claude (sonnet-5-5) | 배포 작업 동시 실행과 서비스 동시 기동의 구분을 끝에 한 줄로만 말함 |
| `rust-result-guard` | study | Claude (sonnet-5-5) | 설명을 넓힐수록 더 이해하지 못함 |
| `agent-token-cost` | design | Claude (opus-5-5) | "매 턴 대화 전체를 다시 받는다"의 이유가 빠짐 |
| `chip-undefined` | codebase | Claude (opus-5-5) | "칩"을 정의 없이 씀. codebase 맥락이 필요함 |
| `cors-origin` | concept | Codex (gpt-5.5) | Origin header와 CORS 허용이 어떻게 다른지 설명 없음 |
| `rebase-shared` | concept | Codex (gpt-5.5) | 다이어그램이 많고 사용자가 막힌 지점을 짚지 않음 |
| `commit-log-flush` | concept | Codex (gpt-5.4-mini) | "로그 flush"를 정의 없이 씀 |
| `gemini-supply-terms` | domain | agy (모델 미기록) | 용어는 정의했지만 사용자가 가진 모델(제조사는 검사 끝난 재고를 보낸다)에서 출발하지 않음 |
| `gemini-demo-step` | domain | agy (모델 미기록) | 데모 단계 이름(a2-accept, A2, SBL)을 정의 없이 나열 |
| `gemini-demo-story` | domain | agy (모델 미기록) | 직전 설명을 "스토리"로 다시 했지만 실패한 재설명. 사용자가 막힌 곳은 화면에서 무엇을 봐야 하는가 |

`chip-undefined`, `gemini-demo-step`, `gemini-demo-story` 3건은 `context_ok: false`입니다. 칩의 정의나 화면 자료처럼 직전 대화 밖의 맥락이 있어야 답할 수 있어서, 결과는 참고용으로만 공개합니다.

### Gemini(agy) case에 대해

- 2026-11-19 기준 agy 대화는 9개뿐이고, 혼란 반응 후보 3건이 모두 대화 하나(`ecb5ed6b`, 2026-11-14, 공급망 데모 프로젝트)에서 나왔습니다.
- 이 대화의 transcript에는 `model` 필드가 없습니다. agy 기본 설정은 현재 `Gemini 3.8 Flash (Low)`이지만, 그 무렵 같은 workspace에서 `/model` 명령을 친 기록이 있어 모델을 확정하지 않았습니다. 그래서 `model`은 `null`입니다. 11-16 이후 대화는 `PLANNER_RESPONSE.model`에 `gemini-3.8-flash-low`가 남습니다.
- 세 case 모두 프로젝트 도메인(가상의 회사, 화면, 단계 이름)을 알아야 해서 직전 한 turn만으로는 모델에게 불리합니다.
- `gemini-demo-story`는 L51의 답에 사용자가 이해하지 못하자 Gemini가 다시 설명한 답이고, 그것도 실패했습니다. 실제 재설명이 실패한 사례라 `reexplain` task의 비교 기준으로 쓸 수 있습니다.
- 답변 안의 로컬 경로(`file:///Users/...`)는 `file://~/`로 바꿨습니다.

Gemini를 실험 대상 모델로 쓰는 것은 로그가 아니라 직접 호출입니다(`agy -p --output-format json --model gemini-3.8-flash-high`). 확인한 내용은 `docs/test-plan.md` T12에 있습니다.

## 수집 방법

1. `python3 scripts/mine.py`를 실행합니다. my-skills의 session-logs 스킬(`sessions.py`)로 `~/.claude/projects`, `~/.codex/sessions`, `~/.gemini/antigravity-cli`를 읽고, 혼란을 표현한 사용자 메시지(정규식은 스크립트 안의 `PAT`)와 그 직전 답변, 그 답변을 낸 모델을 `data/candidates.local.json`에 씁니다. 모델은 `sessions.py`가 버리므로 `mine.py`가 원본 줄을 따로 읽습니다. 2026-11-19 기준 302건이 나왔습니다. 실험 runner의 cwd(`/tmp/koeval-run`)에서 생긴 세션은 실험 호출이라 기본으로 제외합니다(`--exclude-cwd`로 추가).
2. 사람이 고릅니다. 이번에 쓴 기준은 다섯 가지입니다.
   - 반응이 90자 이하이고 "뭔 말", "무슨 말", "뜻", "이해"를 포함합니다.
   - 직전 답변이 250~2200자입니다.
   - 반응이 직전 답변을 향합니다. 다른 일을 지시하면서 "뭔 말인지 알지?"라고 쓴 경우는 뺍니다.
   - 직전 답변과 질문만으로 상황을 대략 알 수 있어야 합니다.
   - 개념, 학습, 설계, codebase와 Claude, Codex가 섞이게 합니다.
3. 고른 case에 `context_ok`, `gap`, `gap_author`, `gap_reviewed`를 적어서 `cases.jsonl`에 추가합니다. `context_ok`는 결과를 보기 전에 정합니다.

## Public으로 올리기 전 검사

이 repo는 public입니다. case를 추가하기 전에 아래를 확인합니다.

```sh
grep -nE '@[a-z0-9.-]+\.(com|net)|gh[opsu]_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{8,}|password\s*[:=]|/Users/' data/cases.jsonl
```

이 정규식으로 잡히지 않는 것도 눈으로 봅니다. 내부 서비스 주소, 팀원 이름, 개인 사정이 드러나는 문장이 그런 예입니다. `candidates.local.json`은 cwd 경로가 들어 있어서 commit하지 않습니다.

## 한계

- 12건은 판단의 출발점일 뿐입니다. 변형 사이의 차이가 작으면 늘려야 합니다.
- 직전 한 turn만 담았습니다. 그보다 앞의 대화를 알아야 하는 case(`kafka-inbox-latest`, `deploy-lock`, `chip-undefined`, `gemini-*` 3건)는 모델에게도 불리합니다.
- `gap`은 Claude가 쓴 해석입니다. 사용자가 실제로 어디서 막혔는지와 다를 수 있습니다.
- "이해하기 쉬웠던 답변" 같은 대조 case가 아직 없습니다.
