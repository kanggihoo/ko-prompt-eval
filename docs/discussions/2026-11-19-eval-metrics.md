> Claude와 Codex 토론 요약 사본입니다. 원본 turn 파일은 로컬 `.herdr-discuss/`에만 있고 git에서 제외했습니다. 토론 뒤 사용자가 바꾼 결정은 [`../decisions.md`](../decisions.md)가 우선합니다.

# Summary: ko-prompt-eval 평가 지표

- 참가: `discuss-claude`(w2G:p1), `discuss-codex`(w2G:pA)
- 6 turn(3라운드), 2026-11-19
- 쟁점 13개 모두 `agreed`, `needs user` 없음
- 사용자 검토 표시(`confirm`) 8개
- 전제: 앞선 토론(`20261119-0800-eval-automation/summary.md`)과 사용자 결정(task 둘로 분리, 주 9건, CLI 직접 runner, `--tools ""`)

## Decisions for the user

없음.

## Agreed recommendations for user review (`confirm`)

| ID | 권장 | 대안 | 근거 | 수락 turn |
|---|---|---|---|---|
| M1 | 두 task 모두 기준 질문은 "처음 이 답을 받았다면, 다시 묻게 된 부분을 이해할 수 있었겠는가". `rewrite`는 생성할 때 반응을 안 받지만 평가는 반응 기준으로 함 | 자연스러움 같은 task 고유 기준만 사용 | 사용자 목표가 "이해되는가". 고유 기준만으로는 원래 의문이 풀렸는지 알 수 없음 | 01, 02 |
| M5 | `rewrite` 고유 체크는 K-Humanizer의 `meaning_fidelity`, `edit_discipline`, naturalness. "새 사실 추가" 감점은 `rewrite`에만 적용(`reexplain`에서는 근거 없는 새 주장만 오류 후보). `business_korean` 32건은 원래 기준을 쓰고, 유지율은 보존 대상 문단의 일치로 계산 | 로그와 business에 같은 rubric 적용 | K-Humanizer Red Flags는 내용 추가를 감점하는데, 내용 추가는 `reexplain`의 목적임. `bk_landing_003`은 보존과 설명을 함께 요구함 | 01–03 |
| M6 | task 간 비교는 결과를 보기 전에 고정. 주 비교는 5줄 `rewrite` 대 5줄 `reexplain`으로, task 입력 묶음 전체(반응·질문 제공 포함)의 효과로 해석. 보조 비교는 K-Humanizer `rewrite` 대 `explain-clearly` `reexplain`(배포 후보 비교). 둘 다 같은 case·모델·repeat. 판정은 주 비교부터 | 공통 5줄만 판정 / case별 최선 출력끼리 비교(기각) | 최선 출력을 고르면 후보 수(4개 대 3개)와 같은 사람의 선택 효과가 섞임 | 02–05 |
| M7 | 자동 지표는 서술(어절, 문장, 구조, 영문 비율), 지시 준수(변형 금지 표현, lint `--no-vocab`), 실행 정보(token 성분, 지연, 비용 출처, `tool_used`)로 나누고, 품질 총점에 넣지 않음 | 품질 총점에 합산 | 금지 표현 수는 지시를 따랐는지만 보여 줌. 품질로 쓰면 순환 편향(앞선 토론 I12) | 01, 02 |
| M10 | 짝은 동시에 보여 주고 제시 순서와 A/B 위치를 기록. 출력별 이해 비율은 "재검토 판단"으로 해석 | 출력별 판정을 짝보다 먼저 받는 화면 | 한 case를 12번 읽으므로, 오염 없는 첫 노출 판정은 9건 전체에서 9개(변형당 약 2개)뿐 | 02–05 |
| M11 | case를 열 때 출력보다 먼저 "당시 막혔던 부분을 지금 설명할 수 있나: 가능 / 일부 / 어려움 / 기억 안 남"을 한 번 묻고, case 행에 출처 날짜와 함께 기록. 주 분모 9건은 유지. 익숙함별 차이는 탐색으로만. 최근 case는 사람이 골라 별도 검증 세트로 | 익숙함을 묻지 않음 | 주 9건 중 `commit-log-flush`(05-02), `rebase-shared`(06-19), `cors-origin`(06-23)은 다섯 달 전 case. 이미 아는 개념은 천장 효과로 변형 차이를 지움 | 03–06 |
| M13 | judge를 두 호출로 분리. ① 공통 이해 체크(두 task 모두): 질문·직전 답변·반응·익명 출력 → `answers_reaction`, `defines_target`, `new_unexplained`, 중요 오류. ② task 고유 체크: `rewrite`는 원문·편집 요청·익명 출력 → 의미 보존·편집 절제·자연스러움(반응 없이). `reexplain` 자연스러움은 ①에 함께 기록 | 한 호출로 합침(비용 절감) | 합치면 judge가 반응을 보고 편집 점수까지 깎을 위험. `commit-log-flush`처럼 편집은 좋지만 의문은 남는 출력은 두 결과가 다 필요 | 05, 06 |

## Agreed

| ID | 명제 | 수락 turn | 검증 수준 |
|---|---|---|---|
| M2 | 사람 판정은 짝 선호(`A / B / 동률 / 둘 다 불충분`) + 출력별 3단계("의문을 설명할 수 있음 / 핵심 일부가 빠져 다시 물어야 함 / 의문이 그대로 남음") + 중요 사실 오류(문장, 근거, 확인 불가 구분)를 따로 기록. 성공 = 이해됨이면서 확인된 중요 오류 없음. 기본 검토는 task당 핵심 27쌍, 합계 54쌍·출력 108개 | 02, 03 | `deploy-lock` 원답의 "구현은 아직 없으니 확인 못 한 부분"으로 분리 필요성 확인 |
| M3 | `reexplain` judge 체크: `answers_reaction`(예/부분/아니오 + 반응·출력 근거 인용), `defines_target`(반응이 용어를 특정한 경우만), `new_unexplained`(이해에 필요한데 설명 없이 추가된 용어와 근거), 중요 오류(근거/확인 불가), naturalness(K-Humanizer 1·3·5 기준), `answer_first`(진단용). `gap_filled`는 사용자가 검토한 `gap`만 | 02, 03 | `rebase-shared` 반응에는 특정 용어가 없음을 확인 |
| M4 | 원래 `prior_answer`는 "이 설명으로 대화가 끝나지 않았다"는 참고점일 뿐 정답 실패 예시가 아님. judge 검증은 사람이 판정한 출력으로 | 02, 03 | `deploy-lock` 원답에 사용자가 다시 물은 구분이 이미 있음 |
| M8 | 보고 순서: ① case별 짝 승·패·동률·미확정 → ② 출력 수준 `이해됨 / 검토 출력`, `이해됨이면서 중요 오류 없음 / 검토 출력`, 미검토·확인 불가 수 → ③ 같은 case·repeat 집합의 시도 비용 합계 ÷ 성공 수(미보고·0성공은 생략하고 이유 표시) → ④ judge: 짝 방향·동률 일치, 사람이 표시한 중요 오류 누락, 판정 건수, `answers_reaction` × 사람 이해 판정 교차표. 단일 합격선은 강제하지 않음(6/9가 우연히 나올 확률 25.4%) | 02, 03 | 추론 |
| M9 | 원래 답변의 출처 agent·모델을 case 표에 기록(주 9건: Claude 5, Codex 3, Gemini 1 모델 미기록). 소표본이라 계열별 순위는 만들지 않음 | 01, 02 | `cases.jsonl` 확인 |
| M12 | 중요 확인 불가 표시가 있으면, 그것을 성공에서 빼고 넣은 성공 수 범위를 함께 보고(예: 검토 12, 이해됨 8, 확인된 오류 1, 확인 불가 2 → 5–7). 신뢰구간이 아니라 처리 규칙에 따른 차이 | 04, 05 | 예시 계산 확인 |

## Validation still needed

| 쟁점 | 확인 |
|---|---|
| M3, M13 | judge 프롬프트를 구현하고, 사람 판정이 끝난 출력으로 T9 일치율 확인. 양쪽 task를 포함한 같은 case·repeat 표본부터 |
| M13 | 분리 호출과 단일 호출에서 `edit_discipline` 판정이 달라지는지(지금은 추측) |
| M7 | 어절·문장 분리 규칙 구현과 pilot 출력 대조(pilot 두 파일 `--no-vocab` 0건은 확인) |
| M11 | 익숙함 질문이 실제로 case를 가르는지 E1에서 관찰 |
| M2, M10 | 판정 화면(`report.html`)에서 54쌍을 읽는 데 드는 시간. 부담이 크면 주 비교부터 |

## Change list or proposed solution

### 1. 사람 판정

1. **case를 열 때 (M11):** 원래 질문과 반응을 보여 주고, "당시 막혔던 부분을 지금 설명할 수 있나"를 한 번 묻습니다. 답은 가능 / 일부 / 어려움 / 기억 안 남입니다. `gap`은 보여 주지 않습니다.
2. **짝마다 (M2, M10):** 두 출력을 동시에 보여 줍니다. A/B 위치는 무작위로 하고 기록합니다.
   - 각 출력에 3단계 이해 판정을 남깁니다. "의문을 설명할 수 있음 / 핵심 일부가 빠져 다시 물어야 함 / 의문이 그대로 남음".
   - 중요 사실 오류가 있으면 문장, 근거, 확인 불가 여부를 표시합니다.
   - 짝 선호를 고릅니다. `A / B / 동률 / 둘 다 불충분`.
3. **읽을 양:**
   - 기본은 task당 핵심 27쌍입니다. `reexplain`은 5줄 대 `explain-clearly`, `rewrite`는 5줄 대 K-Humanizer입니다. 합계 54쌍, 출력 108개입니다.
   - task 사이 짝 판정(M6)은 같은 출력을 재사용합니다. 주 비교 27쌍, 보조 비교 27쌍입니다. 이때는 짝 선호만 받습니다.
   - 부담이 크면 주 비교부터 합니다.

### 2. LLM judge (M3, M4, M5, M13)

- **① 공통 이해 체크**(두 task의 모든 출력)
  - 입력: 질문, 직전 답변, 반응, 익명 출력. 검토된 `gap`이 있으면 양쪽에 같게 줍니다. 변형 이름과 task label은 숨깁니다.
  - 항목: `answers_reaction`(예/부분/아니오 + 근거), `defines_target`(해당 시), `new_unexplained`(목록 + 근거), 중요 오류(근거 / 확인 불가). `reexplain`이면 naturalness(1·3·5)와 `answer_first`(진단용)도 매깁니다.
- **② `rewrite` 고유 체크**
  - 입력: 원문, 편집 요청, 익명 출력. 반응은 주지 않습니다.
  - 항목: `meaning_fidelity`, `edit_discipline`, naturalness. 원문에 없던 실질 주장은 감점하지만, 원문에서 도출되는 쉬운 풀이는 허용합니다.
- **`business_korean` 32건:** `grading`은 judge에만 줍니다. K-Humanizer 원래 기준을 씁니다(`expected_behavior_met`, `hard_failure`, 5개 항목). 유지율은 보존 대상 문단이 일치하는지로 셉니다.
- **K-Humanizer에서 가져올 것:** `meaning_fidelity`, `edit_discipline`, naturalness 기준. Red Flags 중 조건·불확실성 삭제와 근거 없는 용어 대체. 내용 추가 감점은 `rewrite`에만 씁니다.
- **K-Humanizer에서 버릴 것:** 내용 추가 감점을 `reexplain`에 적용하는 것. 도메인 체크 중 비즈니스 외 항목.
- **judge 검증:** 원답을 정답 실패 예시로 쓰지 않습니다. 사람이 판정한 출력과 대조합니다(M4, M8 ④).

### 3. 자동 지표 (M7)

| 종류 | 지표 | 계산 |
|---|---|---|
| 서술 | 산문 어절 수 | Markdown 표식, 코드, URL을 빼고 공백으로 분할 |
| 서술 | 문장 수 | 명시한 분리 규칙의 추정치 |
| 서술 | 구조 | heading, list item, table, code fence 개수 |
| 서술 | 영문 비율 | 영문 문자 비율(분모가 재현되는 방식) |
| 지시 준수 | 변형 금지 표현 | 줄표 부연, "A가 아니라 B", 콜론 반전, 오프너, 공감 멘트. 탐지 건수와 짧은 예시 |
| 지시 준수 | ste-ko lint | `--no-vocab` 규칙별 경고 |
| 실행 정보 | token 성분, 지연, `cost_usd` + `cost_source`, `tool_used` | 앞선 토론 I2, I16 |

어느 것도 품질 총점에 넣지 않습니다.

### 4. task 사이 비교와 과잉 수정 (M6, M5)

- **주 비교:** 5줄 `rewrite` 대 5줄 `reexplain`. 같은 case, 모델, repeat로 맞추고 짝 선호로 판정합니다. 해석은 "반응과 질문을 함께 받는 입력 묶음과 task 지시의 효과"입니다.
- **보조 비교:** K-Humanizer `rewrite` 대 `explain-clearly` `reexplain`. 배포 후보끼리의 비교입니다.
- 두 비교 모두 E1 전에 고정합니다. judge 쪽 대조는 ① 공통 체크로 합니다.
- **과잉 수정:** `business_korean` `keep_unchanged` 7건의 보존 대상 문단 유지율과 `expected_behavior_met`으로 봅니다. 로그 `rewrite`에서는 ② `edit_discipline`으로 봅니다.

### 5. 집계와 보고 (M8, M9, M12)

1. **case 표:** case별 짝 승·패·동률·미확정을 냅니다. 출처 agent·모델, 출처 날짜, 익숙함 응답을 붙입니다.
2. **변형 표:** `이해됨 / 검토 출력`, `이해됨이면서 중요 오류 없음 / 검토 출력`, 미검토 수, 확인 불가 수를 냅니다. 확인 불가가 있으면 성공 수 범위도 냅니다.
3. **비용:** 같은 case·repeat 집합에서 시도 비용 합계를 성공 수로 나눕니다. `cost_source`를 표시합니다. 미보고나 0성공이면 생략하고 이유를 적습니다.
4. **judge 신뢰도:** 짝 방향·동률 일치, 사람이 표시한 중요 오류의 누락, 판정 건수, `answers_reaction` × 사람 이해 판정 교차표를 냅니다. 일치율이 확인되기 전에는 judge 수치를 판정 근거로 쓰지 않습니다.
5. **해석 문구:**
   - 단일 합격선은 두지 않습니다.
   - 출력별 비율은 "재검토 판단"이라고 적습니다.
   - 계열별 순위는 만들지 않습니다(소표본).
   - 익숙함별 차이는 탐색으로만 봅니다.

## Raised by one side, missed by the other

| 내용 | 낸 쪽 (turn) |
|---|---|
| 사실 오류가 이해 판정을 덮어쓰면, 읽기 쉬움과 정확성 중 어느 쪽 문제인지 잃음(`deploy-lock`) | Codex (02) |
| `defines_target`은 반응이 용어를 특정하지 않은 case(`rebase-shared`)에 적용할 수 없음 | Codex (02) |
| 원답을 일괄 실패로 두면 안 되는 반례(`deploy-lock` 원답에 이미 구분이 있음) | Codex (02) |
| case별 최선 출력 비교의 선택 효과와 후보 수 차이 | Codex (02) |
| business 유지율의 분자는 응답 전체가 아니라 보존 대상 문단(`bk_landing_003`) | Codex (02) |
| 같은 case를 여러 번 읽는 학습 효과 | Codex (02) |
| `rewrite`는 반응뿐 아니라 원래 질문도 받지 않음 | Codex (04) |
| 확인 불가 주장을 처리하는 규칙에 따른 성공 수 범위 | Codex (04) |
| 판정자가 원래 혼란을 겪던 시점의 사용자가 아님(천장 효과), 출처 날짜 차이 | Claude (03) |
| 첫 노출 판정은 9개뿐이라 출력별 선행 화면의 이득이 작음 | Claude (03) |
| 주 비교(5줄 대 5줄)와 별도로 배포 후보 비교(K-Humanizer 대 `explain-clearly`)를 사전 고정 | Claude (03) |
| `rewrite`에도 반응 기준 judge가 필요하고, 고유 체크와 호출을 분리해야 함 | Claude (05) |
| `answer_first`는 두 변형이 모두 지시하는 것이라 지시 준수 지표에 가까움 | Claude (03) |
