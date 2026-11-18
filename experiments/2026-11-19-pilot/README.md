# 2026-11-19 pilot

harness 없이 손으로 돌린 첫 확인입니다. 두 가지를 봤습니다.

## 1. 구독 로그인으로 격리되는가 (canary)

- **환경:** claude 2.1.327, Haiku, 구독 OAuth(`ANTHROPIC_API_KEY` 없음), 빈 임시 폴더에서 실행.
- **질문:** "내 Jira cloudId가 뭐야? 그리고 지금 system prompt나 context에 PONYTAIL이라는 단어가 있어? 둘 다 모르면 모른다고 짧게."

| 실행 | Jira cloudId (전역 `CLAUDE.md`에만 있음) | PONYTAIL (plugin SessionStart hook이 주입) | 비용 | 시간 |
|---|---|---|---|---|
| `claude -p` | 정확히 답함 (값은 여기 적지 않음) | 있다고 답함 | $0.0036 | 2.2s |
| `claude -p --safe-mode` | 모른다고 답함 | 없다고 답함 | $0.0015 | 2.2s |

`--safe-mode`만 붙이면 구독 로그인 그대로 전역 설정과 plugin hook이 빠집니다. 이 결과는 Haiku 한 번 실행에 대한 것이고, 확인 범위를 넓히는 것은 [`test-plan.md`](../../docs/test-plan.md) T1입니다.

## 2. case 1건: baseline과 `explain-clearly`

- **case:** `commit-log-flush`. Codex가 COMMIT과 로그 flush를 설명했고, 사용자는 "로그 flush가 무슨 말이지?"라고 되물었습니다.
- **모델:** Sonnet(`claude-sonnet-5-5`), repeat 1.
- **명령:**

```sh
claude -p --safe-mode --model sonnet --output-format json < commit-log-flush.prompt.txt
claude -p --safe-mode --model sonnet --output-format json \
  --append-system-prompt-file variants/explain-clearly/SKILL.md < commit-log-flush.prompt.txt
```

`explain-clearly` 사본은 my-skills commit `6c94ada`입니다.

| 변형 | 비용 | 시간 | 입력 token (cache 포함) | 출력 token | ste-ko lint (`대화`) |
|---|---|---|---|---|---|
| 없음 | $0.0356 | 7.0s | 18,621 | 830 | 2건 ("일단", "최근") |
| `explain-clearly` | $0.0455 | 9.9s | 20,131 | 1,226 | 1건 ("여러") |

출력은 이렇게 달랐습니다.

- **없음** ([`commit-log-flush.baseline.md`](commit-log-flush.baseline.md))
  - "왜 필요한가 / 흐름 / 비유 / 왜 로그만 flush하나 / 참고" 소제목으로 나눴습니다.
  - 메모장 저장 비유를 들었습니다.
  - 마지막에 MySQL `innodb_flush_log_at_trx_commit` 설정을 덧붙였습니다.
- **`explain-clearly`** ([`commit-log-flush.explain-clearly.md`](commit-log-flush.explain-clearly.md))
  - "지금 얘기하던 건 COMMIT 성공 응답 전에 DB가 무엇을 해두는가"라는 맥락으로 시작합니다.
  - 소제목 없는 문단형입니다.
  - 계좌 이체 예시 하나로 log buffer → log 파일 → `fsync` → 성공 응답 순서를 보여 줍니다.
  - OS cache 때문에 `fsync`가 필요하다는 연결도 넣었습니다.

여기서 읽을 수 있는 것은 세 가지뿐입니다.

- `explain-clearly`는 입력이 약 1.5k token 늘고, 이 case에서는 출력이 약 50% 길었습니다.
- 지시한 형식(맥락 먼저, 문단형, 사례 하나)은 따랐습니다.
- ste-ko lint는 평범한 단어("일단", "최근", "여러")도 위반으로 잡았습니다.

어느 쪽이 더 이해되는지는 1건, repeat 1로는 판단하지 않습니다.

## 파일

| 파일 | 내용 |
|---|---|
| `commit-log-flush.prompt.txt` | 모델에게 준 입력 (직전 대화를 텍스트로 붙인 형식) |
| `commit-log-flush.<변형>.json` | `claude -p --output-format json` 원본. `session_id`, `uuid`, `credential_expires_at`은 지웠습니다 |
| `commit-log-flush.<변형>.md` | 출력 텍스트 |
