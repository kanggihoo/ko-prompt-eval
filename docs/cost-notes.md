# 실행 비용 측정 기록

이 repo를 만들기 전에 따로 측정하고 정리해 둔 Claude Code와 Codex의 비용 기록을 옮긴 문서입니다. 실험 harness의 flag와 비용 해석에 직접 쓰입니다.

- **1절, 2절:** 2026-11-13~16에 실제로 실행해서 잰 값입니다. Claude Code는 `-p`로, Codex는 0.169.0 `exec`과 인터랙티브로 쟀습니다.
- **3절:** 2026-07 시점에 설정과 문서를 보고 점검한 것입니다. 측정값이 아니고, 지금 버전과 기본값이 다를 수 있습니다.
- **비용 값:** 구독 로그인 상태에서 CLI가 보고한 API 가격 환산 추정치입니다. 실제 청구액이 아니라 구독 사용량에서 나간 것입니다.

이 repo에서 새로 잰 값은 4절에 따로 적었습니다.

## 1. Claude Code `claude -p` 시작 비용

### 결론

구독 로그인을 유지한 채 시작 context를 줄일 수 있습니다. 기준은 flag 없이 `claude -p "ok"`를 보냈을 때의 **36,323 token**입니다.

| 용도 | flag | 시작 token |
|---|---|---|
| 리뷰용 (읽기 도구만) | `--strict-mcp-config --setting-sources project,local --disable-slash-commands --tools "Read,Grep,Glob,Bash" --settings '{"autoMemoryEnabled":false}'` | 6,273 (−83%) |
| 수정용 | `--strict-mcp-config --setting-sources project,local --settings '{"autoMemoryEnabled":false}'` | 17,445 (−52%) |

### 품질

- 버그 5개를 심은 파일을 같은 방식으로 리뷰시켰습니다. 줄인 조합도 baseline처럼 5개를 모두 찾았습니다.
- 프로젝트 `CLAUDE.md` 규칙도 지켰습니다.
- 호출당 추정 비용은 약 $0.24에서 $0.02–0.04로 줄었습니다.
- 달라진 점: 사용자 `~/.claude/CLAUDE.md`가 빠지자 **응답이 영어로** 나왔습니다. 이 repo의 실험도 전역 설정을 빼고 돌리므로, 한국어 prompt에 영어로 답하는 경우가 있는지 봐야 합니다. pilot에서는 한국어 prompt에 한국어로 답했습니다.

### 함정

- **`--tools`와 MCP:** MCP가 켜진 상태에서 `--tools`에 `ToolSearch`가 없으면, MCP 도구 정의가 처음부터 전부 실립니다. 406k token, 첫 호출 $3.26이 나갔습니다. 문서에 적힌 동작입니다. 그래서 `--tools`는 `--strict-mcp-config`와 함께만 씁니다.
- **`--max-budget-usd`:** 요청 한 번이 상한을 넘는 것은 막지 못합니다. 상한 $1인데 $3.26과 $3.56이 그대로 나갔습니다. 측정 전체의 추정 지출은 약 $10.7(list 가격 기준, 구독 사용량)이었고, 그중 $6.8이 이 두 호출이었습니다.
- **`--setting-sources project,local`:** 사용자 `~/.claude/CLAUDE.md`, user skills, plugin, MCP가 함께 빠집니다. 문서에는 없는 동작이라, 직접 묻는 probe로 확인했습니다. 프로젝트 `CLAUDE.md`는 남습니다.
- **`--safe-mode`, `CLAUDE_CODE_DISABLE_CLAUDE_MDS`:** 프로젝트 규칙까지 뺍니다. 테스트용 `[INV]` 접두어 규칙을 놓쳤습니다. 서브에이전트 용도에서는 피할 것으로 분류했습니다. 이 repo에서는 프로젝트 규칙도 빼는 것이 목적이라 `--safe-mode`를 씁니다.
- **`CLAUDE_CODE_DISABLE_BUNDLED_SKILLS`:** 오히려 4.3k token 늘었습니다. 원인은 확인하지 못했습니다.

### `--bare`

- 이 머신에서는 `Not logged in`으로 바로 종료됐습니다. bare는 `ANTHROPIC_API_KEY`나 `apiKeyHelper`만 읽고, 구독 로그인과 `setup-token` 토큰은 읽지 않습니다.
- 쓰려면 API key가 필요하고, 그러면 구독 대신 Console API 종량 과금이 됩니다.
- 문서상 앞으로 `-p` 기본값이 bare가 될 예정입니다. 그대로 바뀌면 구독 로그인만으로 돌리는 `-p` 호출이 깨질 수 있습니다.

### 문서와 로컬 CLI의 차이

- `--max-turns`: 로컬 `--help`에는 없지만 실행하면 받아들입니다.
- `--effort`: `ultracode` 값은 문서에만 있습니다.
- 측정 당시 후보로 본 flag 중 실제로 없는 것은 없었습니다.

## 2. Codex 시작 비용 (0.169.0)

### 결론

- 첫 입력이 `exec` 평균 18,859에서 13,282로, 인터랙티브 18,895에서 13,300으로 줄었습니다. 둘 다 **−29.6%**입니다. 인터랙티브는 조건당 1회라 재현성은 약합니다.
- 줄어든 원인은 두 가지입니다.
  - **skills 목록:** `skills.include_instructions=false`와 `skills.max_context_tokens=1` 조합으로 −23.9%. 두 설정을 각각 켰을 때의 기여는 나누지 못했습니다.
  - **plugins:** `--disable plugins`로 −8.9%. skills 쪽과 겹칩니다.
- 직접 설정한 MCP 3개를 끈 효과는 −0.45%뿐이었습니다. memories는 이미 꺼져 있어서 추가 절감이 없었습니다.
- 작은 리뷰는 baseline과 줄인 조합 모두 버그 4/4를 찾았습니다.

### 읽기 전용 리뷰용 조합 (측정함)

```sh
--disable plugins \
-c mcp_servers.<서버>.enabled=false \
--disable memories -c memories.use_memories=false -c memories.generate_memories=false \
--disable hooks \
-c skills.include_instructions=false -c skills.max_context_tokens=1 \
-c project_doc_max_bytes=0
```

- 코드 수정용은 위에서 `--disable hooks`, skills 두 키, `project_doc_max_bytes=0`을 뺀 조합입니다. 이 조합은 따로 재지 않았습니다.
- 프로젝트 규칙이 중요한 작업이면 `project_doc_max_bytes=0`과 `--disable plugins`를 뺍니다.

### 함정

- `--ephemeral`, `--ignore-user-config`, `--ignore-rules`는 **`exec` 전용**입니다. 인터랙티브에서는 exit 2로 거부됩니다. `--ignore-rules`는 `AGENTS.md`를 무시하는 옵션이 아닙니다.
- `project_doc_max_bytes=0`은 **전역 `AGENTS.md`를 끄지 못합니다.** 프로젝트 문서만 끕니다.
- `exec`는 `-a`와 `--no-alt-screen`을 받지 않습니다. approval은 `-c 'approval_policy="never"'`로 줍니다.
- `--disable skills`는 존재하지 않습니다.
- `skills.include_instructions`는 일반 가이드에 없고 schema와 source에서만 확인했습니다. 앞으로도 유지될지는 모릅니다.
- cache를 쓰지 않은 입력이 −76.8% 줄었다고 해서 요금이 그만큼 줄었다고 읽으면 안 됩니다.

### 확인하지 못한 것

- profile 파일(`-p`)을 실제로 선택한 실행.
- read-only sandbox에서 다른 agent에게 회신이 되는지.
- 어려운 리뷰나, 프로젝트 `AGENTS.md`와 skill 절차가 필요한 작업에서의 품질.

## 3. 설정 점검 (2026-07 스냅샷, 측정 아님)

당시 설정 파일과 문서를 보고 token을 쓰는 항목을 점검한 것입니다. 이 repo와 관련 있는 부분만 옮겼습니다.

### non-interactive 실행에 쓸 만한 flag

| flag | 효과 |
|---|---|
| `--no-session-persistence` | 세션을 저장하지 않음. 이 repo에서는 로그 오염 방지용으로 씀 |
| `--exclude-dynamic-system-prompt-sections` | cwd, 환경, git status 같은 기기별 구간을 system prompt에서 빼고 첫 사용자 메시지로 옮김. 기본 system prompt를 쓸 때만 적용 |

### token을 많이 쓰는 Claude Code 기본값 (당시 문서 기준)

| 항목 | 기본값 | 영향 |
|---|---|---|
| `includeGitInstructions` | true | git 작업 지침을 매 세션 system prompt에 넣음 |
| `ENABLE_CLAUDEAI_MCP_SERVERS` | true | claude.ai MCP 서버를 자동으로 켬 |
| `MAX_MCP_OUTPUT_TOKENS` | 25000 | MCP 도구 응답 1회 최대 token |
| `TASK_MAX_OUTPUT_LENGTH` | 32000 | 서브에이전트 출력 최대 길이 |
| auto memory | 켜짐 | 메모리를 매 세션 context에 넣음 |

### Codex 기본값 (당시)

| 항목 | 기본값 | 영향 |
|---|---|---|
| `web_search` | `"cached"` | 쓰지 않아도 검색 도구 정의가 context에 들어감 |
| `features.multi_agent` | 켜짐 | `spawn_agent` 등 도구 5개 정의가 항상 들어감 |
| `tool_output_token_limit` | 미공개 | 도구 출력이 기록에 계속 쌓임 |

### 권하지 않는 변경

| 변경 | 이유 |
|---|---|
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` (일상 작업에서) | 프로젝트 지침이 빠져 품질이 크게 떨어짐 |
| `MAX_MCP_OUTPUT_TOKENS` 1000 이하 | 검색 결과가 잘려 재질의가 늘고, 오히려 총 token이 늘어남 |
| `BASH_MAX_OUTPUT_LENGTH` 3000 이하 | 컴파일 에러와 스택트레이스가 잘려 디버깅 반복이 늘어남 |
| `effortLevel: "low"` | 복잡한 분석과 여러 단계 계획의 품질이 떨어짐 |

## 4. 이 repo에서 잰 값 (2026-11-19)

| 조건 | 모델 | prompt | 입력 token | 비용 |
|---|---|---|---|---|
| `claude -p --safe-mode` | Haiku | "ok" | 18,388 | $0.0015 |
| `claude -p --safe-mode --tools ""` | Haiku | "ok" | 2,815 | $0.0005 |
| `claude -p --safe-mode` (pilot baseline) | Sonnet | `commit-log-flush` | 18,621 (cache 제외 2 + cache 쓰기 6,513 + 읽기 12,106) | $0.0356 |
| `claude -p --safe-mode` + `explain-clearly` (pilot) | Sonnet | `commit-log-flush` | 20,131 (2 + 8,014 + 12,115) | $0.0455 |
| `agy -p` | `gemini-3.8-flash-low` | canary 질문 | 17,511 + cache read 25,704 | 보고 안 함 |

이 기록에서 harness에 반영한 것은 다음과 같습니다([`implementation.md`](implementation.md) 4절, 5절).

- **text-only 실행:** `--safe-mode --tools ""`로 입력의 약 85%(도구 설명)를 덜어 냅니다.
- **MCP 안전장치:** `--tools`를 쓰므로 `--strict-mcp-config`를 함께 줍니다(1절 함정).
- **비용 상한:** `--max-budget-usd`는 비용 보호로 믿지 않습니다(1절 함정).
- **`--bare`:** 구독 로그인이 안 돼서 쓰지 않습니다. CLI를 업데이트한 뒤 `-p` 기본 동작이 바뀌었는지 확인합니다.
- **Codex 격리:** `--ephemeral`, `--ignore-user-config`(`exec` 전용)에 skills와 plugins 끄기 조합을 써 봅니다. 전역 `AGENTS.md`가 빠지는지는 T6에서 확인합니다(2절).
- **비용 해석:** cache 쓰기와 읽기를 나눠 기록하고, cache를 쓰지 않은 입력의 감소를 요금 감소로 읽지 않습니다.
