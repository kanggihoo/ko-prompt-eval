# 외부 파일

비교 후보와 채점 도구로 쓰려고 복사한 파일입니다. 둘 다 MIT license이고, 각 폴더에 원본 `LICENSE`를 두었습니다. 수정하지 않습니다. 바꿔 써야 하면 `variants/`에 사본을 만듭니다.

| 폴더 | 원본 | commit | 가져온 것 |
|---|---|---|---|
| `ste-ko/` | <https://github.com/beamonic/ste-ko> | `ed98bcb249c6a5b129e983a5df8a761b520e0bb3` | `skills/ste-ko/`, `SPEC.md`, `dictionary.md`, `scripts/lint.py`, `LICENSE` |
| `k-humanizer/` | <https://github.com/evergreentree97/K-Humanizer> | `46218c5a4512423a759ca905966b59764e7ebb3c` | `skills/k-humanizer/`(references 포함), `evals/fixtures/business_korean.v1.jsonl`, `evals/fixtures/golden_set.sample.jsonl`, `LICENSE` |

`ste-ko/scripts/lint.py`는 상위 폴더의 `dictionary.md`를 읽으므로, 폴더 구조를 원본과 같게 두었습니다.

```sh
python3 third_party/ste-ko/scripts/lint.py <파일.md> --surface 대화
python3 third_party/ste-ko/scripts/lint.py --self-test
```
