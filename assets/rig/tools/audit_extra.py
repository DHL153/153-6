#!/usr/bin/env python3
"""추가 검사 4종을 헤드리스로 돌려 표로 출력. python3 audit_extra.py PKG_DIR
합격(8 니콜 기준으로 보정): 이음매 빈 픽셀 ≤ 100(테두리 노이즈) / 손-자루 거리 초과 ≤ 0 / 팔꿈치 부호 뒤집힘 없음 / 팔뚝 비틀림 ≤ 15° / 천: 접힘 0, 칸 넓이비 0.25~1.6, 변 늘어남 ≤ 2.1"""
import os, sys, time, socket, subprocess, shutil, json
from playwright.sync_api import sync_playwright
pkg = os.path.abspath(sys.argv[1]); here = os.path.dirname(os.path.abspath(__file__))
shutil.copy(os.path.join(here, 'audit_extra.html'), os.path.join(pkg, 'audit_extra.html'))
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=pkg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.8)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path='/opt/pw-browsers/chromium'); pg = b.new_page()
        pg.goto(f'http://127.0.0.1:{port}/audit_extra.html'); pg.wait_for_function('window.ready', timeout=60000)
        R = pg.evaluate('audit()'); b.close()
finally:
    srv.terminate()
fail = 0
print(f"{'장면':10s} {'이음매빈px':>9s}  {'손-자루 초과(단위)':24s} {'팔꿈치 범위(F / N)':28s} {'팔뚝비틀림(F / N)'}")
for n, r in R.items():
    hs = ' '.join(f"{k}:{v:+.0f}" for k, v in r['handMax'].items()); el = r['elbow']; tw = r['twist']
    flip = any(e[0] < -10 and e[1] > 10 for e in el.values())
    bad = r['seamMax'] > 100 or any(v > 0 for v in r['handMax'].values()) or flip or any(v > 15 for v in tw.values())
    fail |= bad
    els = ' / '.join(f"{k}:{e[0]:.0f}..{e[1]:.0f}" for k, e in el.items()); tws = ' / '.join(f"{k}:{v:.0f}°" for k, v in tw.items())
    cl=r.get('cloth',{});cbad=any(c['amin']<.25 or c['amax']>1.6 or c['emax']>2.1 or c['fold']>0 for c in cl.values());bad|=cbad;fail|=cbad
    cls=' '.join(f"{k}:넓이{c['amin']:.2f}~{c['amax']:.2f} 변{c['emax']:.2f}{' 접힘'+str(c['fold']) if c['fold'] else ''}" for k,c in cl.items())
    print(f"{n:10s} {r['seamMax']:6d}@{r.get('seamT','-')!s:5s}  {hs:24s} {els:28s} {tws}{'  ← 뒤집힘' if flip else ''}{'  ✗' if bad else '  ✓'}\n{'':10s} 천: {cls}")
sys.exit(1 if fail else 0)
