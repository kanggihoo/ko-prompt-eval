# 테스트 계획

harness를 만들기 전에 실행해서 확인해야 할 사실(T)과, 그 위에서 돌릴 첫 실험(E)입니다. 확인이 끝나면 결과를 해당 항목 아래에 날짜와 함께 적고, 결과 파일은 `experiments/`에 둡니다.

## 확인할 사실

### T1. 격리가 유지되는가

- **상태:** 2026-11-19 한 번 확인 (Haiku, [pilot](../experiments/2026-11-19-pilot/README.md)).
- **방법:** 전역 `CLAUDE.md`에만 있는 값(Jira cloudId 같은 것)과 plugin hook이 주입하는 문구("PONYTAIL")를 아는지 묻습니다. `claude -p`와 `claude -p --safe-mode`를 비교합니다.
- **통과 기준:** `--safe-mode`에서는 둘 다 모른다고 답합니다.
- **추가로 볼 것:**
  - `--safe-mode`에서 skill 목록이 비어 있는지. "사용할 수 있는 skill을 나열해"로 확인합니다.
  - output style이 꺼지는지.
  - 현재 작업 폴더의 `CLAUDE.md`나 `AGENTS.md`도 읽지 않는지. 실험 repo 안에서 실행할 것이므로 중요합니다.
- **다시 할 때:** Claude Code를 업데이트하거나 실행 flag를 바꿀 때마다 반복합니다. 매 실험에 canary case 하나를 넣는 것도 방법입니다.

### T2. 변형이 실제로 모델에 들어가는가

- **방법:** `--safe-mode --append-system-prompt-file <변형>`으로 실행하고 "system prompt 끝에 덧붙은 지시의 첫 제목을 그대로 말해"라고 묻습니다. 변형마다 한 번씩 합니다.
- **통과 기준:** 변형 파일의 첫 제목을 답하고, 입력 token이 baseline보다 변형 크기만큼 늘어납니다. pilot에서 `explain-clearly`는 약 1.5k token 늘었습니다.
- **추가로 볼 것:** frontmatter(`---` 블록)가 그대로 들어가는 것이 결과에 영향을 주는지. frontmatter를 뺀 사본과 비교합니다.

### T3. promptfoo Agent SDK provider가 구독으로 되는가

- **방법:** `anthropic:claude-agent-sdk` provider를 `ANTHROPIC_API_KEY` 없이 실행합니다.
- **볼 것:**
  1. 구독 OAuth로 인증되는지.
  2. `setting_sources: []`일 때 홈의 skill과 `CLAUDE.md`가 안 보이는지(T1과 같은 canary).
  3. `working_dir/.claude/skills/explain-clearly/SKILL.md`와 `setting_sources: ['project']`, `skills: ['explain-clearly']`로 skill이 실제 skill로 로드되는지.
  4. 사용자 메시지에 `/explain-clearly`를 넣으면 실제로 호출되는지(`skill-used` assertion).
- **판단:** 되면 실제 skill 로딩 비교를 이 provider로 합니다. 안 되면 `exec` 방식(T4)만 씁니다.

### T4. promptfoo `exec` provider 연결 방식

- **방법:** `exec:` provider로 `scripts/run_claude.py`를 감쌉니다.
- **볼 것:**
  1. prompt와 test vars가 스크립트에 어떤 인자 형식으로 들어오는지.
  2. 스크립트가 출력 외에 cost, latency, tokenUsage를 promptfoo에 넘길 수 있는지(JSON 반환 형식).
  3. `--no-cache`를 주면 매번 실제로 실행되는지.
  4. `promptfoo view`에 비용과 시간이 열별로 나오는지.
- **안 될 때:** 비용과 token은 실험 폴더의 원본 JSON에서 직접 집계하고, promptfoo는 출력 비교와 assertion에만 씁니다.

### T5. 직전 대화를 텍스트로 넣어도 되는가

- **방법:** case 3건으로 두 방식을 비교합니다.
  - (a) pilot처럼 `[이전 대화]` 텍스트로 넣습니다.
  - (b) 직전 답변을 실제 assistant turn으로 넣습니다. Agent SDK messages, API, 또는 `--input-format stream-json`을 씁니다.
- **볼 것:**
  - (a)에서 모델이 직전 답변을 "남이 한 설명"으로 다루는지. 예: "위 assistant의 설명은…"처럼 3인칭으로 말합니다.
  - (b)처럼 "제가 앞에서…"로 자기 설명을 고치는지.
  - 출력 품질이 달라지는지.
- **판단:** 차이가 크면 (b) 방식으로 harness를 만듭니다.

### T6. Codex를 격리해서 돌릴 수 있는가

- **방법:** `codex exec`로 T1 canary를 돌립니다. 전역 `~/.codex/AGENTS.md`의 내용을 아는지 확인합니다.
- **볼 것:**
  1. `codex exec`에 전역 지침을 끄는 옵션이 있는지.
  2. 없으면 `CODEX_HOME`을 임시 폴더로 바꾸고 인증 파일만 복사해서 되는지.
  3. 출력에서 token 수를 얻을 수 있는지. Codex는 비용을 보고하지 않으므로 가격표로 추정해야 합니다.
- **판단:** 격리가 안 되면 Codex는 비교에서 빼거나, "전역 지침 포함"이라고 표시하고 따로 봅니다.

### T7. 같은 조건에서 출력이 얼마나 흔들리는가

- **방법:** case 2건 × 변형 2개(없음, `explain-clearly`) × Sonnet × 5회.
- **볼 것:** 같은 변형 안의 5개 출력이 서로 얼마나 다른지. 길이, 구조, judge 점수, 그리고 사람이 읽었을 때의 차이를 봅니다.
- **판단:** 같은 변형 안의 차이가 변형 사이의 차이만큼 크면 repeat를 늘려야 합니다. 이 결과로 E1의 repeat 수를 정합니다.

### T8. ste-ko lint가 AI 답변에 쓸 만한가

- **상태:** pilot 출력 2개에서 "일단", "최근", "여러"가 비승인 어휘로 잡혔습니다.
- **방법:** 로그의 실제 답변 20개 정도에 `--surface 대화`로 돌리고, 위반을 규칙별로 셉니다.
- **볼 것:** 사람이 보기에 실제로 읽기 어렵게 만드는 위반이 몇 %인지. 어휘 규칙(1.3)을 끈 `--no-vocab` 점수와 비교합니다.
- **판단:** 오탐이 많으면 `--no-vocab`(문장 길이, 이중피동, 종결어미 반복만)으로 씁니다.

### T9. judge를 믿을 수 있는가

- **방법:** E1 결과에서 사람이 case마다 가장 이해되는 출력을 고르고, judge(`select-best`와 항목 점수)의 선택과 비교합니다.
- **볼 것:**
  - 일치율.
  - judge가 긴 답이나 표가 많은 답을 선호하는지.
  - 생성 모델과 같은 계열의 judge가 자기 계열 출력을 선호하는지. 예를 들어 Sonnet이 생성하고 Opus가 판정할 때입니다.
- **판단:** 일치율이 낮으면 judge는 거르는 용도로만 쓰고 판정은 사람이 합니다.

### T10. judge도 구독으로 돌릴 수 있는가

- **방법:** `llm-rubric`과 `select-best`의 `provider`를 T4의 `exec` provider(`claude -p --safe-mode --model opus`)로 지정합니다.
- **볼 것:** promptfoo가 judge 응답을 파싱하는지, judge 비용이 어디에 남는지.

### T11. 구독 사용량 한도와 실행 시간

- **방법:** E1 규모(100회 안팎)를 동시 실행 수 1, 2, 4로 나눠 돌립니다.
- **볼 것:** rate limit 오류가 나는지, 전체 시간이 얼마인지.
- **판단:** promptfoo `-j`(동시 실행 수)를 정합니다.

## 첫 실험

### E1. `reexplain`: 긴 skill이 짧은 규칙보다 나은가

- **전제:** T1, T2, T4(또는 대안), T7을 먼저 끝냅니다.
- **구성:** case 9건 × 변형 4개(없음, `claude-md-defaults`, `explain-clearly`, ste-ko) × Sonnet × repeat 3 = 108회. judge 호출은 따로 셉니다.
- **기록:** 출력, 비용, 시간, 입력·출력 token, 구조 비율, lint, judge 항목 점수, 사람 선택.
- **보는 순서:**
  1. 변형 이름을 가린 채 case마다 출력 4개를 읽고, 가장 이해되는 것 하나와 이해되지 않는 것을 고릅니다.
  2. 이름을 열고 변형별로 선택 횟수를 셉니다.
  3. 비용과 시간 차이를 같이 봅니다.
- **판단 기준 (제안):**
  - `explain-clearly`가 `claude-md-defaults`보다 9건 중 6건 이상에서 선택되면, 추가 token(약 1.5k 입력, 출력 증가분)을 쓸 만하다고 봅니다.
  - 비슷하면 짧은 규칙을 쓰고, `explain-clearly`에서 차이를 만든 규칙만 짧은 규칙으로 옮겨 다시 비교합니다.

### E2. 모델 비교

- **구성:** E1에서 남은 변형 2개 × Haiku, Sonnet, Opus(× Codex, T6이 되면).
- **볼 것:** 작은 모델에 긴 skill을 주는 것이 큰 모델에 짧은 규칙을 주는 것보다 싸고 나은 경우가 있는지.

### E3. `rewrite`와 `first-answer`

- **rewrite:** K-Humanizer와 `explain-clearly`를 "직전 답변을 고쳐 쓰기" task에서 비교합니다. 다듬기만으로 이해가 되는지, 빠진 연결을 채워야 하는지가 갈립니다.
- **first-answer:** 질문만 주고 없음, `claude-md-defaults`, ste-ko를 비교합니다. 로그의 원래 답변(실제로 실패한 것)도 같이 놓고 봅니다.
