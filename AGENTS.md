# ko-prompt-eval

한국어 설명 prompt와 skill을 같은 데이터·여러 모델로 돌려 출력, 비용, 시간을 비교하는 실험 저장소다. 한국어로, 짧게 답한다.

시작할 때 `README.md`의 현재 상태를 읽는다. 구현이나 실험을 하기 전에는 `docs/implementation.md`와 `docs/test-plan.md`를 읽는다.

## 규칙

- 실험 실행은 전역 설정과 격리한다. `claude -p`는 `--safe-mode`로 돌리고, 비교할 변형만 `--append-system-prompt-file`로 넣는다. 격리를 바꾸면 canary로 다시 확인한다 (`docs/test-plan.md` T1).
- 실행 결과는 `experiments/<YYYY-MM-DD>-<이름>/`에 새 폴더로 남긴다. 이전 실험 폴더는 고치지 않는다.
- `variants/`는 실험 시점의 snapshot이다. 원본 스킬이 바뀌면 덮어쓰지 말고, 바뀐 원본을 새 이름으로 추가하거나 실험 폴더에 원본 commit을 적는다.
- `third_party/`는 외부 원본 사본이다. 수정하지 않는다. 바꿔 써야 하면 `variants/`에 사본을 만든다.
- `data/cases.jsonl`은 실제 대화 로그다. 이 repo는 public이므로 case를 추가하기 전에 비밀값, 이메일, 내부 주소가 없는지 검사한다 (`data/README.md`).
- `*.local.json`은 로컬 경로가 든 원자료라 commit하지 않는다.
