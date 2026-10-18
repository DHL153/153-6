#!/usr/bin/env python3
"""리그 장면 프레임 뽑기. python3 render.py PKG_DIR OUT_PREFIX scene t1,t2,... [W H ox oy scale bg debug]"""
import os, sys, time, socket, subprocess, shutil, base64, json
from playwright.sync_api import sync_playwright
pkg = os.path.abspath(sys.argv[1]); here = os.path.dirname(os.path.abspath(__file__)); outp = sys.argv[2]; scene = sys.argv[3]; times = [float(x) for x in sys.argv[4].split(',')]
W, H, ox, oy, sc = [float(x) for x in (sys.argv[5:10] if len(sys.argv) > 9 else [1024, 1024, 523, 1012, 1])]; bg = sys.argv[10] if len(sys.argv) > 10 else ''; dbg = len(sys.argv) > 11 and sys.argv[11] == '1'
shutil.copy(os.path.join(here, 'render.html'), os.path.join(pkg, '_render.html'))
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=pkg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{port}/_render.html'); pg.wait_for_function('window.ready', timeout=30000)
        R = pg.evaluate('s=>renderSeq(s)', dict(scene=scene, times=times, W=int(W), H=int(H), ox=ox, oy=oy, scale=sc, bg=bg, debug=dbg)); b.close()
        if errs: print('ERR', errs[:5])
finally:
    srv.terminate(); os.remove(os.path.join(pkg, '_render.html'))
for i, d in enumerate(R):
    open(f'{outp}_{i:02d}.png', 'wb').write(base64.b64decode(d.split(',')[1]))
print(len(R), 'frames')
