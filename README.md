# ko-prompt-eval

Claude가 한국어로 어렵게 설명하는 문제를 고치려고 만든 prompt와 skill이 실제로 효과가 있는지, 같은 데이터에서 출력을 나란히 놓고 직접 보며 판단하기 위한 실험 저장소입니다.

비교하려는 질문은 이렇습니다.

- 70줄짜리 `explain-clearly` 스킬이 5줄짜리 전역 규칙보다 실제로 나은가, 아니면 짧은 규칙으로도 충분해서 token만 더 쓰는가.
- 한국어 글쓰기 오픈소스 스킬(ste-ko, K-Humanizer)을 같은 데이터에 올리면 어떻게 다른가.
- 모델(Haiku, Sonnet, Opus, 필요하면 Codex와 Gemini)마다 결과, 비용, 시간이 어떻게 다른가.
- 이 모든 실행이 전역 `~/.claude/CLAUDE.md`나 plugin hook의 영향을 받지 않는가.

## 현재 상태 (2026-11-19)

설계와 평가 방법을 정했고, 실행 harness는 아직 없습니다.

- 평가 case 12건(주 평가 9건): [`data/cases.jsonl`](data/cases.jsonl). 로그에서 뽑았고 Claude 6, Codex 3, Gemini 3건입니다.
- task는 `reexplain`(다시 설명)과 `rewrite`(고쳐 쓰기) 두 개이고, 각각 독립적으로 평가합니다.
- 실행기는 CLI(`claude -p --safe-mode --tools ""` 등)를 직접 부르는 Python runner입니다. promptfoo는 쓰지 않습니다.
- 구독 로그인으로 격리 실행이 되는 것과, case 1건을 baseline과 `explain-clearly`로 돌린 결과: [`experiments/2026-11-19-pilot/`](experiments/2026-11-19-pilot/README.md)
- 다음 작업은 [`docs/implementation.md`](docs/implementation.md) 6절의 구현 단계 1(runner 뼈대와 Claude adapter)입니다.

## 문서

| 문서 | 내용 |
|---|---|
| [`docs/research.md`](docs/research.md) | 출발점, 비교 후보, 참고한 오픈소스 4개(K-Humanizer, ste-ko, promptfoo, prompt-optimizer)를 조사한 내용 |
| [`docs/decisions.md`](docs/decisions.md) | 지금까지 정한 것과 출처(사용자 / 토론) |
| [`docs/implementation.md`](docs/implementation.md) | 실행 흐름, 실험 폴더 계약, task와 prompt, runner와 adapter 명령, 주의할 점, 구현 단계 |
| [`docs/evaluation.md`](docs/evaluation.md) | 평가 기준 질문, 사람 판정 절차, LLM judge 항목, 자동 지표, 집계와 보고 |
| [`docs/cost-notes.md`](docs/cost-notes.md) | Claude Code·Codex 실행 비용 측정 기록(시작 context, flag 함정)과 이 repo에서 잰 값 |
| [`docs/test-plan.md`](docs/test-plan.md) | 실행해서 확인할 사실(T1–T12)과 실험(E1–E3) |
| [`docs/discussions/`](docs/discussions/) | Claude와 Codex 토론 요약 2개(실행·증거·자동화, 평가 지표) |
| [`data/README.md`](data/README.md) | 데이터셋 schema, 수집 방법, 한계 |
| [`third_party/README.md`](third_party/README.md) | 복사해 온 외부 파일의 출처, commit, license |

## 구조

```
data/cases.jsonl          평가 case (질문, 직전 답변, "뭔 말이야" 반응, 빠진 연결)
scripts/mine.py           세션 로그에서 case 후보를 뽑는 스크립트
variants/                 비교할 내 prompt와 skill의 snapshot
third_party/              비교 후보와 채점 도구로 쓰는 외부 MIT 파일
experiments/<날짜>-<이름>/ 실행 결과
docs/                     조사, 결정, 구현 설계, 평가 방법, 테스트 계획, 토론 요약
```
