# 테스트 계획

harness를 만들기 전과 만드는 중에 실행해서 확인할 사실(T)과, 그 위에서 돌릴 실험(E)입니다. 확인이 끝나면 결과를 해당 항목 아래에 날짜와 함께 적고, 결과 파일은 `experiments/`에 둡니다. 설계는 [`implementation.md`](implementation.md), 평가는 [`evaluation.md`](evaluation.md), 결정은 [`decisions.md`](decisions.md)에 있습니다.

## 확인할 사실

### T1. 격리가 유지되는가

- **상태:** 2026-11-19 한 번 확인했습니다(Haiku, [pilot](../experiments/2026-11-19-pilot/README.md)). 매 실행 전 확인은 하지 않기로 했습니다(D-12).
- **방법:** 전역 `CLAUDE.md`에만 있는 값(Jira cloudId 같은 것)과, plugin hook이 주입하는 문구("PONYTAIL")를 아는지 묻습니다. `claude -p`와 `claude -p --safe-mode`를 비교합니다.
- **통과 기준:** `--safe-mode`에서는 둘 다 모른다고 답합니다. 응답에는 값을 기록하지 않고 검출 여부만 남깁니다.
- **다시 할 때:**
  - 결과가 이상할 때. 예: baseline이 5줄 규칙을 따르는 것처럼 보이거나, 출력에 skill 이름이나 hook 문구가 나올 때.
  - Claude Code를 업데이트한 뒤 `-p` 기본 동작이 바뀌었을 수 있을 때. 문서상 `-p`가 bare로 바뀔 예정입니다.
- **같이 볼 것:**
  - skill 목록이 비어 있는지.
  - 현재 폴더의 `CLAUDE.md`, `AGENTS.md`를 읽지 않는지. 실험 cwd는 `/tmp/koeval-run`이지만 확인해 둡니다.

### T2. 변형이 들어가고, 도구가 꺼지는가

- **상태:**
  - 2026-11-19에 `--safe-mode --tools ""`로 "ok"를 보내 입력 2,815 token($0.0005, Haiku)을 측정했습니다. `--tools` 없이는 18,388 token입니다.
  - pilot에서 `--append-system-prompt-file`로 `explain-clearly`를 넣으면 입력이 약 1.5k token 늘었습니다. 이것은 `--tools` 없이 잰 값입니다.
- **방법:** 실제 실행 조합(`--safe-mode --tools "" --strict-mcp-config --no-session-persistence`)에 변형을 하나씩 넣고 묻습니다. 질문은 "system prompt 끝에 덧붙은 지시의 첫 제목을 그대로 말해"입니다.
- **통과 기준:**
  - 변형 파일의 첫 제목을 답합니다.
  - 입력 token이 baseline보다 대략 변형 크기만큼 늘어납니다.
  - `num_turns`가 1이고, 도구 호출이 없습니다.
- **추가로 볼 것:** frontmatter(`---` 블록)가 들어가는 것이 결과에 영향을 주는지. frontmatter를 뺀 사본과 비교합니다.

### T3. Agent SDK로 실제 skill 로딩을 재현할 수 있는가 (보류)

promptfoo를 쓰지 않기로 해서 보류합니다(D-10). 실험에서는 `/explain-clearly`를 실제로 부르지 않고 SKILL.md를 system prompt에 붙입니다. 실제 호출 방식과 결과가 다른지 확인이 필요해지면 다시 엽니다. 방법 후보는 Agent SDK에서 `setting_sources: ['project']`와 `working_dir/.claude/skills/`를 쓰는 것입니다.

### T4. promptfoo `exec` 연결 (보류)

D-10으로 보류합니다. 나중에 promptfoo로 옮길 때 [`research.md`](research.md) 5절과 앞선 토론의 I1을 다시 봅니다.

### T5. 직전 대화를 텍스트로 넣어도 되는가

- **방법:** case 3건으로 두 방식을 비교합니다.
  - (a) `[이전 대화]` 텍스트로 넣습니다.
  - (b) 직전 답변을 실제 assistant turn으로 넣습니다. 방법은 `--input-format stream-json`이나 session resume인데, 둘 다 되는지 미확인입니다.
- **볼 것:**
  - (a)에서 모델이 직전 답변을 남의 설명처럼 다루는지. 예: "위 assistant의 설명은…".
  - (b)처럼 "제가 앞에서…"로 자기 설명을 고치는지.
  - 사람이 읽기에 품질 차이가 있는지.
- **판단:** 차이가 크면 (b) 방식으로 바꿉니다.

### T6. Codex를 격리해서 text-only로 돌릴 수 있는가

- **방법:** `codex exec --ephemeral --ignore-user-config --sandbox read-only --skip-git-repo-check --json`을 빈 cwd에서 실행하고 T1 canary를 돌립니다.
- **볼 것:**
  1. 전역 `~/.codex/AGENTS.md` 내용을 모르는지. [`cost-notes.md`](cost-notes.md) 2절에 따르면 `project_doc_max_bytes=0`으로는 전역 `AGENTS.md`가 꺼지지 않습니다.
  2. skills 목록과 plugins가 빠지는지. 후보는 `--disable plugins`, `-c skills.include_instructions=false -c skills.max_context_tokens=1`입니다.
  3. 명령 실행 없이 텍스트만 답하는지.
  4. JSONL에서 token 수를 얻을 수 있는지. 비용은 가격표로 추정합니다.
- **판단:** 격리가 안 되면 Codex는 비교에서 빼거나 "전역 지침 포함"으로 표시해서 따로 봅니다.

### T7. 같은 조건에서 출력과 cache가 얼마나 흔들리는가

- **방법:** case 2건 × 변형 2개(없음, `explain-clearly`) × Sonnet × 5회.
- **같이 잴 것:**
  - 같은 case·변형을 연속 3회 돌릴 때와, case만 바꾼 1회의 cache 쓰기·읽기량.
  - 변형 본문이 첫 호출 뒤에 cache 읽기로 바뀌는지.
- **볼 것:** 같은 변형 안의 출력 차이가 변형 사이 차이만큼 큰지. 길이, 구조, 사람이 읽은 인상을 봅니다.
- **판단:**
  - E1의 repeat 수(기본 3)를 정합니다.
  - warm-up 호출을 둘지 정합니다(D-18).

### T8. ste-ko lint를 어떤 설정으로 쓸까

- **상태:**
  - pilot 출력 2개에서 어휘 규칙이 "일단", "최근", "여러"를 잡았습니다.
  - `--no-vocab`에서는 0건이었습니다.
  - 기본은 `--no-vocab`으로 정했습니다([`evaluation.md`](evaluation.md) 4절).
- **방법:** 로그의 실제 답변 20개 정도에 `--surface 대화`로 돌려 규칙별 경고를 셉니다.
- **볼 것:** 남은 규칙(문장 길이, 문단 길이, 이중피동, 종결어미 반복)의 경고가 사람이 보기에 실제로 읽기 어려운 곳을 가리키는지.

### T9. judge를 믿을 수 있는가

- **방법:** E1 사람 판정이 끝난 출력으로 judge를 돌립니다. 양쪽 task를 포함한 같은 case·repeat 표본부터 합니다.
- **볼 것:**
  - 짝 방향·동률 일치.
  - 사람이 표시한 중요 오류를 judge가 놓친 수.
  - `answers_reaction` × 사람 이해 판정 교차표.
  - 긴 답이나 표가 많은 답을 선호하는지.
  - 같은 계열 출력을 선호하는지.
- **판단:** 일치가 낮으면 judge는 쓰지 않고 사람이 판정합니다(D-36).

### T10. judge를 구독으로 돌릴 수 있고, 한 번에 채점해도 되는가

- **방법:** judge도 `claude -p --safe-mode --tools ""`(또는 다른 계열 adapter)로 부르고, JSON 출력을 파싱합니다.
- **볼 것:**
  - `rewrite` 답을 한 번에 채점할 때 `edit_discipline`이 반응 때문에 깎이는지(D-35). 그렇게 보이면 반응을 뺀 호출을 따로 해서 비교합니다.
  - judge 비용이 어디에 남는지.

### T11. 구독 사용량 한도와 실행 시간

- **방법:** 직렬 실행으로 E1 규모를 소량부터 늘립니다.
- **볼 것:** rate limit 오류가 나는지, 전체 시간이 얼마나 걸리는지.

### T12. Gemini(agy)를 실험 모델로 쓸 수 있는가

- **상태:** 2026-11-19 일부 확인.
  - `agy -p --output-format json`이 `response`, `duration_seconds`, `usage`(input, output, thinking, cache_read token)를 줍니다. 비용 필드는 없습니다.
  - 쓸 수 있는 모델(`agy models`)은 `gemini-3.8-flash-high|medium|low`, `claude-sonnet-4-6`, `claude-opus-4-6-thinking`, `gpt-oss-120b-medium`입니다.
  - canary 결과:
    - 전역 `CLAUDE.md`와 PONYTAIL hook은 모른다고 답했습니다. `~/.gemini/GEMINI.md`는 없습니다.
    - 설치된 skill 목록 25개가 context에 들어가 있었습니다.
    - 입력은 17.5k token, cache read는 25.7k token이었습니다.
  - print 호출은 agy DB에 cwd(`workspace_uris`)와 함께 기록됩니다. 그래서 `mine.py`의 cwd 제외로 거를 수 있습니다.
- **남은 확인:**
  1. skill 목록과 `~/.gemini/hooks`를 끄는 방법. 후보는 `--settings`, `--sandbox`, 빈 HOME입니다.
  2. 변형을 system prompt 자리에 넣는 방법. 없으면 prompt 앞에 붙이고 `injection: prefix`로 기록합니다.
  3. 도구 없이 텍스트만 답하는지.
- **판단:** 주입 위치가 Claude와 다르면 Gemini 결과는 그 조건으로 표시하고 따로 봅니다.

## 실험

### E1. 로그 9건, 두 task, Sonnet

- **전제:** 구현 단계 1–3([`implementation.md`](implementation.md) 6절), T2, T7을 먼저 끝냅니다.
- **구성:**

| task | 변형 | 호출 수 (9건 × repeat 3) |
|---|---|---|
| `reexplain` | 없음, `claude-md-defaults`, `explain-clearly`, ste-ko | 108 |
| `rewrite` | 없음, `claude-md-defaults`, K-Humanizer | 81 |

- **사람 판정:** task마다 핵심 27쌍입니다. `reexplain`은 5줄 대 `explain-clearly`, `rewrite`는 5줄 대 K-Humanizer입니다. 두 task는 서로 비교하지 않습니다(D-4).
- **판정 절차와 보고:** [`evaluation.md`](evaluation.md) 2절과 5절을 따릅니다. 단일 합격선은 두지 않습니다(D-37).
- **기록:** 실험 폴더 계약을 따릅니다([`implementation.md`](implementation.md) 2절).

### E2. 모델 비교

- **구성:** E1에서 남긴 변형과 변형 없는 baseline. 모델은 Haiku, Sonnet, Opus이고, T6과 T12를 통과하면 Codex와 Gemini도 넣습니다.
- **볼 것:**
  - 작은 모델에 긴 skill을 주는 것이, 큰 모델에 짧은 규칙을 주는 것보다 싸고 나은 경우가 있는지.
  - Gemini가 한국어 설명에서 실제로 나은지. 사용자의 가설입니다.
- **해석:** "CLI 기본 설정 포함 성능"으로 해석합니다(D-20).

### E3. `rewrite` 과잉 수정 (`business_korean.v1` 32건)

- **구성:** 없음, `claude-md-defaults`, K-Humanizer. 필요하면 `explain-clearly`도 넣습니다.
- **볼 것:** `keep_unchanged` 7건의 보존 대상 문단 유지율과 `expected_behavior_met`([`evaluation.md`](evaluation.md) 3절).
