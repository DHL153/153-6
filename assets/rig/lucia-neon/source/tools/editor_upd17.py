"""편집 툴(리깅 편집 툴 artifact)의 17 네온 루시아 고치기 — 받은 페이지 HTML → 새 HTML (파일 수 그대로: rigs/lucia-neon/rig.def.js 만 바꿔 올림)
python3 -I editor_upd17.py 받은.html 새.html 리그버전 시각(예 2026-10-21T12:55) 판(예 v1.1) 진행그림.jpg 비교그림.jpg "목록 메모" "진행 칸 메모(HTML)" "그림 설명"
  ① 스크립트 ?v= ② 캐릭터 목록 이름·메모·updated(맨 위로) ③ 진행 칸 제목·그림(진행 그림 바꿈 + 비교 그림 더함)·메모(맨 앞에 새 판)
"""
import sys, base64, re, os
src, dst, ver, when, tag, prog, cmp_, cnote, pnote, cap = sys.argv[1:11]
s = open(src, encoding='utf-8').read()
b64 = lambda p: base64.b64encode(open(p, 'rb').read()).decode()
# 1) 스크립트
s, n = re.subn(r'rigs/lucia-neon/rig\.def\.js\?v=[0-9a-f]+', 'rigs/lucia-neon/rig.def.js?v=' + ver, s); assert n == 1, n
# 2) 캐릭터 목록: 기존 줄을 빼서 맨 위에(이름·메모 앞·updated 바꿈)
m = re.search(r"  \{id:'lucia-neon',no:17,name:'17 네온 루시아 [^']*',note:'([^']*)',updated:'[^']*'\},\n", s); assert m
old_note = m.group(1).replace('컷인 .34', '컷인 .36')
line = "  {id:'lucia-neon',no:17,name:'17 네온 루시아 " + tag + "',note:'" + cnote + " / " + old_note + "',updated:'" + when + "'},\n"
s = s[:m.start()] + s[m.end():]
assert s.count("const CHARS=[\n") == 1; s = s.replace("const CHARS=[\n", "const CHARS=[\n" + line)
# 3) 진행 칸
a = s.index('<section class="panel prog" aria-labelledby="l17T">'); b = s.index('</section>', a)
sec = s[a:b]
sec = re.sub(r'<h2 id="l17T">17 네온 루시아 v[0-9.]+ <small>[^<]*</small></h2>',
             f'<h2 id="l17T">17 네온 루시아 {tag} <small>{when[:10]} {when[11:]} · {os.environ.get("H2SMALL", "무릎 보호대·걸음·방패 옆(DHL 12:27)")} · 게임 반영(REGISTRY 17)</small></h2>', sec)
sec = sec.replace("‘17 네온 루시아 v1’을", f"‘17 네온 루시아 {tag}’을")
i0 = sec.index('<figure><img src="data:image/jpeg;base64,'); i1 = sec.index('</figure>', i0) + len('</figure>')
if prog == '-':   # 진행 그림은 그대로 두고 비교 그림만 맨 앞에 더함
    sec = sec[:i0] + f'<figure><img src="data:image/jpeg;base64,{b64(cmp_)}" alt="17 네온 루시아 {tag} 비교" loading="lazy"><figcaption>{cap}</figcaption></figure>\n    ' + sec[i0:]
    i0 = i1 = None
if i0 is not None:
  fig = (f'<figure><img src="data:image/jpeg;base64,{b64(cmp_)}" alt="17 네온 루시아 달리기 다리 전·후 비교" loading="lazy"><figcaption>{cap}</figcaption></figure>\n'
         f'    <figure><img src="data:image/jpeg;base64,{b64(prog)}" alt="17 네온 루시아 {tag} — 원화·리그 대기·표정, 내려찍기 8장면, 달리기 8장면" loading="lazy"><figcaption>위: 원화 · 리그 서 있기 · 표정 6 + 깜빡임 2 / 가운데: 내려찍기 8장면 / 아래: 달리기 1/60초씩</figcaption></figure>')
  sec = sec[:i0] + fig + sec[i1:]
j = sec.index('<p class="note">'); sec = sec[:j] + '<p class="note">' + pnote + '</p>\n    ' + sec[j:]
s = s[:a] + sec + s[b:]
open(dst, 'w', encoding='utf-8').write(s); print('ok', len(s) // 1024, 'KB')
