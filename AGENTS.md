# ko-prompt-eval

한국어 설명 prompt와 skill을 같은 데이터·여러 모델로 돌려 출력, 비용, 시간을 비교하는 실험 저장소다. 한국어로, 짧게 답한다.

시작할 때 `README.md`의 현재 상태와 `docs/decisions.md`를 읽는다. 구현이나 실험 전에는 `docs/implementation.md`와 `docs/test-plan.md`를, 채점이나 판정 화면을 만들기 전에는 `docs/evaluation.md`를 읽는다. 결정을 새로 하거나 바꾸면 `docs/decisions.md`에 출처와 함께 적는다.

## 규칙

- 실험 호출은 `/tmp/koeval-run`에서 하고, `claude -p`는 `--safe-mode --tools "" --strict-mcp-config --no-session-persistence`로 돌린다. 비교할 변형만 `--append-system-prompt-file`로 넣고, prompt 앞에는 `--`를 둔다. 결과가 이상하거나 flag를 바꾸면 canary로 확인한다 (`docs/test-plan.md` T1).
- `data/cases.jsonl`의 `gap`은 생성 모델과 사람 판정 화면에 보여 주지 않는다. `context_ok`는 결과를 보기 전에 정한다.
- 실행 결과는 `experiments/<YYYY-MM-DD>-<이름>/`에 새 폴더로 남긴다. 이전 실험 폴더는 고치지 않는다.
- `variants/`는 실험 시점의 snapshot이다. 원본 스킬이 바뀌면 덮어쓰지 말고, 바뀐 원본을 새 이름으로 추가하거나 실험 폴더에 원본 commit을 적는다.
- `third_party/`는 외부 원본 사본이다. 수정하지 않는다. 바꿔 써야 하면 `variants/`에 사본을 만든다.
- `data/cases.jsonl`은 실제 대화 로그다. 이 repo는 public이므로 case를 추가하기 전에 비밀값, 이메일, 내부 주소가 없는지 검사한다 (`data/README.md`).
- `*.local.json`은 로컬 경로가 든 원자료라 commit하지 않는다.
