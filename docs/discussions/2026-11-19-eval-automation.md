> Claude와 Codex 토론 요약 사본입니다. 원본 turn 파일은 로컬 `.herdr-discuss/`에만 있고 git에서 제외했습니다. 토론 뒤 사용자가 바꾼 결정은 [`../decisions.md`](../decisions.md)가 우선합니다.

# Summary: ko-prompt-eval 평가·증거·자동화 설계

- 참가: `discuss-claude`(w2G:p1), `discuss-codex`(w2G:p9, gpt-6.2-sol high)
- 8 turn(4라운드), 2026-11-19
- 쟁점 16개 모두 `agreed`, `needs user` 없음
- 사용자 검토 표시(`confirm`) 10개

## Decisions for the user

없음. 논쟁 끝에 합의하지 못한 쟁점은 없습니다. 아래 `confirm` 항목은 사용자 결정 없이 두 참가자가 정한 선택이라 검토가 필요합니다.

## Agreed recommendations for user review (`confirm`)

| ID | 권장 | 대안 | 근거·가정 | 수락 turn |
|---|---|---|---|---|
| I1 | 실험 파일을 증거 정본으로 두고, 직접 만든 얇은 Python runner로 실행. promptfoo는 쓰지 않거나 보기 도구로만 | promptfoo를 실행 엔진으로(`implementation.md` 3절 A) | 세 모델 모두 구독 CLI라 promptfoo에서도 `exec` provider가 됨. 결과 DB가 repo 밖(`~/.promptfoo`)에 있고 행 단위 token이 없음. blind 판정과 CLI raw 기록은 어차피 직접 만들어야 함 | 01, 02, 03 |
| I4 | CLI 버전이나 flag가 바뀔 때 양성 대조, 매 실행 전 음성 canary, 누출이면 중단. 전역 설정 파일은 고치지 않음(project 층은 임시 cwd의 표식 파일, 전역 층은 기존 고유 문자열 검출 여부만, agy는 skill 목록 노출 검출) | 설정이 바뀔 때만 확인 | pilot canary, T12 agy skill 노출 | 02, 03, 04, 05 |
| I5 | 5줄 대 `explain-clearly`를 같은 case·repeat의 짝으로 blind 판정(`A/B/동률/둘 다 불충분` + 사실 오류 표시). A/B 위치는 seed로 섞고 기록. repeat 과반으로 case 승리. 판정 기준은 6/9 또는 승·패·동률과 비용을 함께 보는 방식 중 사용자가 선택 | 4개 변형을 한 번에 비교(case당 4개 읽기) | 읽을 양: 짝 판정은 72개 출력, 전체는 144개 | 02, 03, 04, 05 |
| I8 | CI는 모델 호출 없이 schema, 비밀값 패턴, fake adapter, `lint.py --self-test`만. 구독을 쓰는 회귀 실행은 로컬에서 | CI에서 실제 호출 | 구독 인증은 GitHub Actions에서 못 씀, 사용량 한도 | 01, 02 |
| I9 | 모델 간 비교는 격리를 통과한 무변형 baseline부터, "CLI 프리셋 포함 성능"으로 해석. 주입 위치 통일은 T6·T12 후 | 모든 모델에 변형을 prompt 앞에 붙여 통일 | prefix로 맞춰도 프리셋 차이가 남고, Claude에 prefix를 쓰려면 `AGENTS.md` 주입 규칙 변경 필요 | 02, 03 |
| I11 | 주 승률은 맥락 충족 9건(`subnet-range`, `kafka-inbox-latest`, `deploy-lock`, `rust-result-guard`, `agent-token-cost`, `cors-origin`, `rebase-shared`, `commit-log-flush`, `gemini-supply-terms`)으로, 12건 전체 결과도 공개. 생성 전에 목록 고정 | 부족한 3건(`chip-undefined`, `gemini-demo-step`, `gemini-demo-story`)에 원본 세션에서 최소 context를 발췌해 추가 | 기준: 질문 + 직전 답변 + 반응만으로 오해 지점을 특정할 수 있는가. Gemini 출처는 세션 1개 | 02, 03, 04, 05 |
| I12 | `gap_author: claude`, `gap_reviewed: false` 기록. 사람 판정은 `gap`을 보지 않고 먼저. 판정 뒤 사용자가 `gap`을 검토할지 선택. judge의 `gap_filled`는 검토된 `gap`에만 | E1 전에 사용자가 `gap` 검토 | `gap` 12개는 Claude가 `explain-clearly`의 bridge 개념으로 썼음(순환 편향). blind 전에 읽으면 사용자 판정을 유도 | 03, 04, 05 |
| I16 | 생성 호출은 text-only(Claude `--tools ""`, Codex·agy는 sandbox + 빈 cwd, T6·T12에서 확인). `num_turns`, 도구 호출, 거부를 기록하고 `tool_used`로 표시 | CLI 기본 도구 유지 | 전용 빈 cwd에서 codebase를 묻는 case가 도구를 시도하면 출력·비용이 변형과 무관하게 달라짐. `claude --help`에 `"" for none` 확인 | 07, 08 |

## Agreed

| ID | 명제 | 수락 turn | 검증 수준 |
|---|---|---|---|
| I2 | 실험 파일 계약(아래 2절)과 필드: token 성분 분리, CLI 지연과 실측 wall time, `cost_source`, 요청 모델과 관측 모델, 렌더된 prompt SHA, canary는 검출 여부만 | 02, 03 | pilot `usage`로 token 성분 확인. 계약 자체는 추론 |
| I3 | 공통 adapter 계약과 `injection`(system/prefix) 기록 | 01, 02 | 각 CLI 도움말 확인. 동작은 미검증 |
| I6 | 사람 판정이 우선. judge는 첫 실험에서 사람과의 일치율을 잰 뒤에만 쓰고, 그 전에는 거르는 용도로도 쓰지 않음 | 02, 03 | 추론 |
| I7 | `run` 뒤 `metrics`/`judge`/`report`가 각각 `results.jsonl`을 읽는 분기 구조. `report`는 사람 판정 전에도 만들 수 있음. 구현 순서는 아래 4절 | 02, 03 | 추론 |
| I10 | 전용 cwd, Claude `--no-session-persistence`, Codex `--ephemeral`, `mine.py`는 realpath로 그 cwd를 제외 | 01–05 | agy print 호출이 `/tmp/agy-test`로 기록됨을 DB에서 확인. Claude canary가 `/private/tmp/iso-test` session으로 남은 것도 확인. runner 연동 뒤 제외 동작은 미검증 |
| I13 | 변형 순서를 seed로 섞고 cache 성분을 기록. 비용은 같은 repeat 번호끼리 비교. warm-up은 기본으로 하지 않고 T7 결과 뒤 별도 조건으로 | 04–07 | pilot cache 수치(읽기 12,106/12,115, 쓰기 6,513/8,014) 확인. 재사용 효과는 미확인 |
| I14 | 실행 시작 시 선택한 case, template, 변형, 포함한 reference의 사본을 `inputs/`에 만들고 실행은 사본만 읽음. `run.json`에 HEAD, 입력별 경로, 해시, HEAD와의 일치 여부 | 05–07 | third_party MIT 확인. 사본 고정 동작은 미검증 |
| I15 | 실행 실패와 품질 판정을 분리. 성공 출력이 둘 다 있는 repeat만 사람에게 보여 줌. `완료 쌍 / 계획 쌍`, 변형별 실패 수 보고. 과반을 판정할 수 없으면 미확정. 재시도는 별도 시도로 보존 | 06, 07 | E1 구성에 대입한 추론 |

## Validation still needed

| 쟁점 | 확인 |
|---|---|
| I4, I16 | T1·T2를 `--safe-mode --tools ""` 조합으로 다시: canary 음성, 변형 주입, 입력 token 구성 변화 |
| I4 | adapter별 양성 대조: 임시 cwd의 project 표식이 flag 없이 검출되고 격리 flag로 사라지는가 |
| I3, I9, I16 | T6(Codex), T12(agy): 격리, text-only, 주입 위치 |
| I13 | T7: 같은 case·변형 연속 3회와, case만 바꾼 1회의 cache 쓰기·읽기량. 출력 분산으로 repeat 수 결정 |
| I14 | fake CLI: 사본을 만든 뒤 원본을 고쳐도 호출 내용과 해시가 유지되는가 |
| I15 | fake adapter로 실패를 주입: 완료 쌍 집계와 미확정 처리 |
| I10 | runner 호출 뒤 `mine.py` 후보에서 실험 호출이 빠지는가 |
| I6 | T9: E1 사람 판정과 judge 일치율, 사실 오류 누락 |
| I11 | T11: 직렬 실행의 rate limit과 전체 시간 |

## Change list or proposed solution

### 1. 평가 방법

1. **E1 주 질문은 5줄 규칙 대 `explain-clearly`입니다.**
   - 같은 case, 같은 repeat의 두 출력을 blind 짝으로 봅니다.
   - 판정은 `A / B / 동률 / 둘 다 불충분`과 사실 오류 표시입니다.
   - A/B 위치는 seed로 섞고 기록합니다.
   - repeat 과반으로 case 승리를 셉니다. 실패 때문에 과반을 판정할 수 없으면 미확정입니다(I5, I15).
2. **주 승률은 맥락 충족 9건으로 냅니다.** 목록은 생성 전에 고정하고, 12건 전체 결과와 출처별 세션 수를 함께 공개합니다(I11).
3. **판정 기준은 사용자가 고릅니다.** 6/9로 정하거나, 승·패·동률을 비용과 함께 봅니다(I5 `confirm`).
4. **baseline과 ste-ko는 짝 판정 뒤 선택으로 봅니다.** 같은 repeat의 4개를 추가로 읽습니다(I5).
5. **신호를 보는 순서**(I6, I12)
   1. 사람 blind 판정을 합니다. 이때 `gap`은 숨깁니다.
   2. 자동 지표를 봅니다. 비용과 시간은 같은 repeat 번호끼리 cache 성분과 함께 봅니다. 길이, 구조, lint, `tool_used`도 봅니다.
   3. judge를 사람 판정과 비교합니다.
   4. `gap` 검토는 선택입니다.
6. **judge 조건:** 생성과 다른 계열을 쓰고, 변형 이름과 지시문을 숨깁니다. JSON으로 답하게 하고, 파싱에 실패하면 그 행을 실패로 둡니다. 검토된 `gap`이 있을 때만 `gap_filled`를 매깁니다. 사람과의 일치율을 잰 뒤에만 판정 근거로 씁니다. E2처럼 계열이 섞이면 judge를 빼거나 계열별 일치율을 냅니다(I6).
7. **모델 비교:** 격리를 통과한 무변형 baseline으로 하고, "CLI 프리셋 포함"으로 해석합니다(I9).

### 2. 증거 형태 (`experiments/<YYYY-MM-DD>-<이름>/`)

| 파일 | 만드는 단계 | 내용 |
|---|---|---|
| `plan.yaml` | 사람 | task, case 목록(주 분모 표시), 변형 경로, 모델(adapter + 모델), repeat, seed |
| `inputs/` | `run` 시작 | 고정한 case, template, 변형, reference 사본. 실행은 이것만 읽음 (I14) |
| `run.json` | `run` | HEAD, 입력별 경로·SHA-256·HEAD 일치 여부, prompt template SHA, CLI 버전, 실행 flag 전체, `injection`, canary 검출 여부(양성·음성), 실제 호출 순서와 seed, 시작·끝 시각 (I2, I4, I13, I14) |
| `raw/<case>/<variant>__<model>__r<k>.json(l)` | `run` | CLI stdout 원본. Codex는 JSONL. session id 같은 식별자는 지움 |
| `results.jsonl` | `run` | 호출 1회 = 1행. 키 `(case, variant, model, repeat, attempt)`. `status`, 출력 텍스트, `raw_ref`, `model_requested`/`model_observed`, `tokens_input_uncached`/`tokens_cache_write`/`tokens_cache_read`/`tokens_output`/`tokens_thinking`, `latency_cli_ms`/`latency_wall_ms`, `cost_usd` + `cost_source`(`cli_reported_api_equiv`/`price_table_estimate`/null), 렌더된 prompt SHA, `num_turns`, 도구 호출·거부 수(미보고는 null) |
| `metrics.jsonl` | `metrics` | 길이, 구조 비율, ste-ko lint, `tool_used` |
| `judge.jsonl` | `judge` | judge 모델, judge prompt SHA, 항목 점수, 원문 응답, 파싱 상태 |
| `blind_map.json` | `report` | review ID, opaque 출력 ID ↔ 변형, A/B 위치 |
| `report.html` | `report` | blind 짝 보기와 판정 입력(localStorage + JSON export), `gap` 숨김. 이름을 연 보기는 판정 뒤 |
| `human.jsonl` | 사람(export) | review ID, opaque 출력 ID, 판정, 사실 오류 표시, 메모 |
| `README.md` | 사람 | 결론, `완료 쌍 / 계획 쌍`, 변형별 실패 수, 비교 가능한 case 수 |

공개 원칙: canary는 값 대신 검출 여부만 남기고, 공개해도 되는 입력만 `inputs/`에 저장합니다.

### 3. 자동화와 코드 관리

- **runner:** 직접 만든 Python 패키지 `koeval/`입니다. promptfoo는 쓰지 않거나 보기 도구로만 씁니다(I1).
- **진입점:** `python3 -m koeval run|metrics|judge|report experiments/<dir>`.
  - `run`이 `inputs/`, `run.json`, `raw/`, `results.jsonl`을 만듭니다.
  - 나머지 셋은 각각 `results.jsonl`을 읽으므로, 모델을 다시 부르지 않고 다시 계산할 수 있습니다(I7).
- **adapter:** `koeval/adapters/{claude,codex,agy}.py`. 공통 계약은 `run(prompt, variant_path|None, model) → 정규화 행 + raw + injection`입니다. JSON과 이벤트 스트림 파싱은 adapter 안에 둡니다(I3).
  - **Claude:** `claude -p --safe-mode --tools "" --no-session-persistence --output-format json --model <m> [--append-system-prompt-file <inputs/…>]`.
  - **Codex:** `codex exec --ephemeral` + sandbox + 빈 cwd.
  - **agy:** `agy -p --output-format json` + sandbox + 빈 cwd.
  - Codex와 agy는 T6, T12를 통과한 뒤에 넣습니다.
- **격리와 위생**(I4, I10, I16)
  - 실행은 전용 cwd에서 합니다.
  - preflight canary가 실패하면 중단합니다.
  - 실행은 직렬로 하고, 변형 순서는 seed로 섞습니다(I13).
  - `mine.py`는 전용 cwd를 realpath로 제외합니다.
- **버전 관리**(I14)
  - commit을 강제하지 않습니다. 대신 `inputs/` 사본과 해시, HEAD 일치 여부로 복원할 수 있게 합니다.
  - `variants/`는 snapshot 규칙(`AGENTS.md`)을 유지합니다.
  - `data/cases.jsonl`에 `gap_author`와 `gap_reviewed`를 추가합니다(I12).
- **CI**(I8): 모델 호출 없이 cases schema, 비밀값 grep, fake adapter 단위 테스트, `lint.py --self-test`만 돌립니다.

### 4. 첫 구현 단계

| 순서 | 할 일 | 완료 기준 | 먼저 확인할 test-plan |
|---|---|---|---|
| 1 | `koeval/`과 `adapters/claude.py`. pilot JSON 두 개와 fake CLI로 호출, 실패, 집계를 확인 | `python3 -m koeval run <새 실험>`이 예상 행 수와 누락·실패를 보여 줌. 사본을 만든 뒤 원본을 고쳐도 호출 내용과 해시가 유지됨(I14). 주입한 실패가 완료 쌍 집계와 미확정에 반영됨(I15). CI 검사 통과 | — |
| 2 | 실제 Claude 호출로 격리, 주입, 분산 확인 | `--safe-mode --tools ""`에서 canary 음성과 project 표식 양성 대조 통과. 변형 주입과 입력 token 기록. T7에서 repeat 수와 cache 재사용 확인. 실험 호출이 `mine.py` 후보에서 빠짐 | T1, T2, T7, T11(소량) |
| 3 | `metrics`와 blind `report` | 판정 export가 원래 출력 ID에 연결되고, 같은 데이터로 보고서를 다시 만들 수 있음. lint 오탐을 확인해 `--no-vocab` 사용 여부 결정 | T8 |
| 4 | E1 실행, 사람 판정 | 9건 목록 고정, 판정 기준(6/9 또는 승·패·동률 + 비용) 결정 뒤 실행. `README.md`에 완료 쌍, 실패, 결론 | — |
| 5 | `judge`와 보정 | 같은 출력으로 judge를 돌려 사람과 일치율, 사실 오류 누락 비교 | T9, T10 |
| 6 | Codex·agy adapter, E2 | T6, T12 통과 뒤 무변형 baseline으로 모델 비교 | T6, T12 |

실제 skill 로딩 비교가 필요해지면 T3(Agent SDK)을 확인합니다. T5(직전 대화를 실제 assistant turn으로 넣는 방식)는 비교할 수 있는 경로가 열릴 때 3건으로 대조합니다.

## Raised by one side, missed by the other

| 내용 | 낸 쪽 (turn) |
|---|---|
| pilot `usage.input_tokens`는 2이고, 18.6k는 cache 성분의 합 | Codex (02) |
| `exec` cache key는 명령에 나온 파일을 해시하므로, 01의 cache 지적은 wrapper가 따로 읽는 파일에만 해당 | Codex (02) |
| Claude 표식으로는 agy의 skill 노출을 못 잡음 | Codex (02) |
| case당 4개 비교보다 핵심 짝 비교가 주 질문에 맞음 | Codex (02) |
| context가 부족한 case의 분모 처리와 출처 세션 집중 | Codex (02) |
| 양성 대조 표식을 전역 설정 파일에 쓰지 않기 | Claude (03) |
| `gap`이 Claude 저작이라 생기는 순환 편향 | Claude (03) |
| blind 판정 전에 `gap`을 읽으면 사용자 판정이 유도됨 | Codex (04) |
| 호출 순서와 cache 상태가 비용 비교에 섞임 | Codex (04) |
| commit 검사가 `third_party/` 변형과 실행 중 변경을 놓침 | Codex (06) |
| 실행 실패를 품질 패배로 세는 왜곡 | Codex (06) |
| `--safe-mode`에서도 기본 도구가 남아 출력·비용을 흔듦 | Claude (07) |
| macOS `/tmp`와 `/private/tmp` realpath 처리 | Claude (03) |
