#!/usr/bin/env python3
"""Claude Code·Codex·agy 세션 로그에서 "뭔 말이야"류 반응, 그 직전 답변, 답변을 낸 모델을 뽑아 후보 목록을 만든다.

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
ap.add_argument('--exclude-cwd', action='append',
                default=[os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'experiments')],
                help='실험 runner가 쓰는 cwd(기본: 이 repo의 experiments/). 이 아래에서 생긴 세션은 실험 호출이라 후보에서 뺀다 (반복 가능)')
a = ap.parse_args()
EXCLUDE = [os.path.realpath(p) for p in a.exclude_cwd]  # macOS는 /tmp를 /private/tmp로 기록한다


def excluded(cwd):
    if not cwd:
        return False
    p = os.path.realpath(cwd)
    return any(p == x or p.startswith(x + os.sep) for x in EXCLUDE)
sys.path.insert(0, a.session_logs)
import sessions as S  # noqa: E402

# 사용자가 직전 설명을 이해하지 못했다는 신호. 넓게 잡고 사람이 거른다.
PAT = re.compile(r'뭔\s*말|무슨\s*말|무슨\s*뜻|뭔\s*뜻|이해가?\s*(안|잘\s*안)|이해\s*못|어렵게|쉽게\s*(설명|말)'
                 r'|못\s*알아|헷갈|뭔소리|무슨\s*소리|explain-clearly')

def models_by_line(s):
    """원본 줄 번호마다 그 시점까지 마지막으로 기록된 모델. sessions.py는 모델을 버리므로 원본을 따로 읽는다.
    claude: assistant 줄의 message.model / codex: turn_context의 payload.model / agy: PLANNER_RESPONSE의 model."""
    cur, out = None, {}
    for n, l in S.lines(s['path']):
        try:
            d = json.loads(l)
        except ValueError:
            d = None
        if isinstance(d, dict):
            m = ((d.get('message') or {}).get('model') if s['agent'] == 'claude' and d.get('type') == 'assistant'
                 else (d.get('payload') or {}).get('model') if s['agent'] == 'codex' and d.get('type') == 'turn_context'
                 else d.get('model') if s['agent'] == 'agy' and d.get('type') == 'PLANNER_RESPONSE' else None)
            if m and m != '<synthetic>':
                cur = m
        out[n] = cur
    return out


out, skipped = [], 0
for s in S.selectable(S.discover('~/.claude/projects', '~/.codex/sessions')):
    if excluded(s['cwd']):
        skipped += 1
        continue
    try:
        ev = S.parse(s)['events']
    except Exception:
        continue
    models = None
    for i, e in enumerate(ev):
        if e['kind'] != 'user' or len(e['text']) > 300 or not PAT.search(e['text']):
            continue
        prev = [x for x in ev[:i] if x['kind'] in ('assistant', 'user')]
        j = max((k for k, x in enumerate(prev) if x['kind'] == 'user'), default=-1)
        ans = '\n'.join(x['text'] for x in prev[j + 1:] if x['kind'] == 'assistant')  # 직전 user turn 이후 assistant 텍스트 전부
        if not ans or j < 0:
            continue
        models = models or models_by_line(s)
        out.append(dict(agent=s['agent'], model=models.get(e['line']), sid=s['sid'][:8], cwd=s['cwd'], ev=S.eid(e), ts=e['ts'],
                        question=prev[j]['text'][:1500], answer=ans, reaction=e['text']))

os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
print(len(out), dict(Counter(o['agent'] for o in out)), f'(실험 cwd 세션 {skipped}개 제외)', '->', a.out)
