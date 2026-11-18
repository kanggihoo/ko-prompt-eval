---
name: explain-clearly
description: Re-explain your last explanation in development work so the user gets it on the first read, in natural Korean with developer terms kept as typed. Use when the user did not follow what you just said, or points at the part they did not follow.
disable-model-invocation: true
---

# Explain clearly

The user did not follow your last explanation. They are not slow; the explanation left something out. Find what was missing and put it back.

## What to explain

- With an argument (`/explain-clearly 두 번째 단락`, `/explain-clearly 왜 cache를 비워?`), explain that part only.
- Without one, re-explain your last explanation whole.

Keep the question and scope of the earlier answer. If part of it was wrong, say so plainly and give the correct version.

## The shape

1. **Context first, when it helps.** One or two sentences on what we are working on and how this answer serves it. "지금은 logout 뒤에 이전 사용자의 화면이 보이는 문제를 고치고 있습니다. 그래서 logout할 때 cache를 비우자는 뜻입니다."
2. **Then the answer.** The first sentence is the answer or the goal it serves.
3. **The bridge.** Name the actor, cause, or condition the earlier answer skipped. This is the repair; a rewrite without it is the same confusion in easier words.
4. **A concrete case, when it makes the bridge clearer.** Real values from this codebase: the file, the command, the output.

Write prose. Keep a table or list only when its structure is the help; a table usually hides the "because" between rows. Number items only when the order is real, such as steps to run in sequence.

Stop when the bridge is in place. A two-sentence repair can end there.

## Korean

Write Korean the way a Korean developer explains to a colleague. Keep developer terms and identifiers exactly as typed: `commit`, `branch`, `rebase`, `cache`, file and function names. Korean particles attach to them (`commit을`, `branch에서`).

Rebuild the sentence around who does what:

| Translationese | Rebuilt |
|---|---|
| 이 값은 `getUser`에 의해 반환됩니다. | `getUser`가 이 값을 반환합니다. |
| 캐시의 무효화를 수행한 후 재요청이 이루어집니다. | cache를 비운 다음 다시 요청합니다. |
| 이 컴포넌트가 상태를 들고 있어서 터집니다. | 이 컴포넌트가 이전 user 값을 계속 갖고 있어서, logout 뒤에도 그 값으로 화면을 그립니다. |

## Words

- Explain a term only when this user likely does not know it. Then call it by that one name throughout.
- One thought per sentence. Put the condition before the instruction: "conflict가 나면, 먼저 `git status`로 파일을 확인합니다."
- Name the mechanism. Write "transaction이 실패하면 DB가 두 변경을 모두 되돌립니다" instead of "안전하게 처리됩니다".
- Call a thing by the name the user or the code already uses. Do not coin a label for it, and do not wrap a made-up label in quotes ("그 '유령 cache' 문제").
- Keep the sentences plain, the way you would say it to a colleague. Leave out these devices: an aside set off by dashes (—), the "A가 아니라 B입니다" contrast, a colon followed by a reveal ("핵심은 이겁니다: …"), and stock phrases such as "참고로", "솔직히 말하면", "짚고 넘어갈 점은".
- Give a number a baseline only when its size matters ("200ms, 지금 응답 시간의 두 배"). Line numbers, status codes and ports stand alone.
- Write as if the point was not obvious, because it was not. Drop "그냥", "간단히", "당연히", "simply", "just" wherever they imply the reader should already know.
- If you are unsure of a part, say so in one line where it comes up.

## Terms from the repo

If the repo has a `GLOSSARY.md` (or several, routed by `GLOSSARY-MAP.md`), use its domain terms for meaning. Use exact identifiers when pointing at code. If the user names something differently, their name wins.

## Before sending

Read it as the person who was just confused. Check: did you add the missing context, actor, cause, or condition, or did you only reword the earlier answer? If only reworded, find the gap and fill it.
