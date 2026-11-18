# 데이터셋

`cases.jsonl`은 실제 Claude Code와 Codex 대화에서 사용자가 직전 설명을 이해하지 못한 장면을 뽑은 것입니다. 한 줄이 case 하나입니다.

## Schema

| 필드 | 내용 |
|---|---|
| `id` | case 이름 |
| `type` | `concept`(개념 설명), `study`(학습 문제), `design`(설계 논의), `codebase`(codebase 맥락이 필요함) |
| `source` | `agent`(claude/codex), `session`(session id 앞 8자리), `event`(`sessions.py show <session> --event <event>`로 원문을 볼 수 있는 위치), `date` |
| `question` | 직전 답변을 부른 사용자 메시지 (1500자에서 자름) |
| `prior_answer` | 사용자가 이해하지 못한 assistant 답변. 직전 user turn 이후 assistant 텍스트를 모두 이어 붙인 것이라, tool 실행 중간의 짧은 안내문이 섞여 있을 수 있음 |
| `reaction` | "뭔 말이야"류 사용자 반응. 욕설을 포함해 원문 그대로 |
| `gap` | 직전 답변이 빠뜨린 연결에 대한 사람의 판단. judge 채점 기준으로 씀. 생성 모델에는 보여 주지 않음 |

## 현재 case (9건)

| id | type | 출처 | gap 요약 |
|---|---|---|---|
| `subnet-range` | study | Claude | "바뀌는 칸", "구간 크기"를 정의 없이 씀 |
| `kafka-inbox-latest` | concept | Claude | 사용자가 생각한 흐름에서 출발하지 않고 표 2개로 넓힘 |
| `deploy-lock` | concept | Claude | 배포 작업 동시 실행과 서비스 동시 기동의 구분을 끝에 한 줄로만 말함 |
| `rust-result-guard` | study | Claude | 설명을 넓힐수록 더 이해하지 못함 |
| `agent-token-cost` | design | Claude | "매 턴 대화 전체를 다시 받는다"의 이유가 빠짐 |
| `chip-undefined` | codebase | Claude | "칩"을 정의 없이 씀. codebase 맥락이 필요함 |
| `cors-origin` | concept | Codex | Origin header와 CORS 허용이 어떻게 다른지 설명 없음 |
| `rebase-shared` | concept | Codex | 다이어그램이 많고 사용자가 막힌 지점을 짚지 않음 |
| `commit-log-flush` | concept | Codex | "로그 flush"를 정의 없이 씀 |

## 수집 방법

1. `python3 scripts/mine.py`를 실행합니다. my-skills의 session-logs 스킬(`sessions.py`)로 `~/.claude/projects`와 `~/.codex/sessions`를 읽고, 혼란을 표현한 사용자 메시지(정규식은 스크립트 안의 `PAT`)와 그 직전 답변을 `data/candidates.local.json`에 씁니다. 2026-11-19 기준 302건이 나왔습니다.
2. 사람이 고릅니다. 이번에 쓴 기준은 다섯 가지입니다.
   - 반응이 90자 이하이고 "뭔 말", "무슨 말", "뜻", "이해"를 포함합니다.
   - 직전 답변이 250~2200자입니다.
   - 반응이 직전 답변을 향합니다. 다른 일을 지시하면서 "뭔 말인지 알지?"라고 쓴 경우는 뺍니다.
   - 직전 답변과 질문만으로 상황을 대략 알 수 있어야 합니다.
   - 개념, 학습, 설계, codebase와 Claude, Codex가 섞이게 합니다.
3. 고른 case에 `gap`을 적어서 `cases.jsonl`에 추가합니다.

## Public으로 올리기 전 검사

이 repo는 public입니다. case를 추가하기 전에 아래를 확인합니다.

```sh
grep -nE '@[a-z0-9.-]+\.(com|net)|gh[opsu]_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{8,}|password\s*[:=]|/Users/' data/cases.jsonl
```

이 정규식으로 잡히지 않는 것도 눈으로 봅니다. 내부 서비스 주소, 팀원 이름, 개인 사정이 드러나는 문장이 그런 예입니다. `candidates.local.json`은 cwd 경로가 들어 있어서 commit하지 않습니다.

## 한계

- 9건은 판단의 출발점일 뿐입니다. 변형 사이의 차이가 작으면 늘려야 합니다.
- 직전 한 turn만 담았습니다. 그보다 앞의 대화를 알아야 하는 case(`kafka-inbox-latest`, `deploy-lock`, `chip-undefined`)는 모델에게도 불리합니다.
- `gap`은 한 사람의 판단입니다. 사용자가 실제로 어디서 막혔는지와 다를 수 있습니다.
- "이해하기 쉬웠던 답변" 같은 대조 case가 아직 없습니다.
