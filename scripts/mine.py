#!/usr/bin/env python3
"""Claude Code·Codex·agy 세션 로그에서 "뭔 말이야"류 반응과 그 직전 답변을 뽑아 후보 목록을 만든다.

  python3 scripts/mine.py [--session-logs DIR] [--out data/candidates.local.json]

로그 파싱은 my-skills의 session-logs 스킬(sessions.py)을 import해서 쓴다.
출력에는 cwd 같은 로컬 정보가 들어가므로 .gitignore 대상인 *.local.json으로 저장한다.
후보에서 case를 골라 data/cases.jsonl에 옮기는 일은 사람이 한다 (data/README.md 참고).
"""
import argparse, json, os, re, sys
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument('--session-logs', default=os.path.expanduser('~/Desktop/my-skills/skills/in-progress/session-logs'),
                help='sessions.py가 있는 폴더')
ap.add_argument('--out', default='data/candidates.local.json')
a = ap.parse_args()
sys.path.insert(0, a.session_logs)
import sessions as S  # noqa: E402

# 사용자가 직전 설명을 이해하지 못했다는 신호. 넓게 잡고 사람이 거른다.
PAT = re.compile(r'뭔\s*말|무슨\s*말|무슨\s*뜻|뭔\s*뜻|이해가?\s*(안|잘\s*안)|이해\s*못|어렵게|쉽게\s*(설명|말)'
                 r'|못\s*알아|헷갈|뭔소리|무슨\s*소리|explain-clearly')

out = []
for s in S.selectable(S.discover('~/.claude/projects', '~/.codex/sessions')):
    try:
        ev = S.parse(s)['events']
    except Exception:
        continue
    for i, e in enumerate(ev):
        if e['kind'] != 'user' or len(e['text']) > 300 or not PAT.search(e['text']):
            continue
        prev = [x for x in ev[:i] if x['kind'] in ('assistant', 'user')]
        j = max((k for k, x in enumerate(prev) if x['kind'] == 'user'), default=-1)
        ans = '\n'.join(x['text'] for x in prev[j + 1:] if x['kind'] == 'assistant')  # 직전 user turn 이후 assistant 텍스트 전부
        if not ans or j < 0:
            continue
        out.append(dict(agent=s['agent'], sid=s['sid'][:8], cwd=s['cwd'], ev=S.eid(e), ts=e['ts'],
                        question=prev[j]['text'][:1500], answer=ans, reaction=e['text']))

os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
print(len(out), dict(Counter(o['agent'] for o in out)), '->', a.out)
