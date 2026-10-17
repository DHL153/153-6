#!/usr/bin/env python3
"""달리기 걸음새(gait)를 동작 시트 달리기 8장에 맞춤. python3 fitrun.py PKG out.json"""
import os, sys, time, socket, subprocess, json, shutil, glob
from playwright.sync_api import sync_playwright
pkg = os.path.abspath(sys.argv[1]); here = os.path.dirname(os.path.abspath(__file__))
shutil.copy(os.path.join(here, 'fit.html'), os.path.join(pkg, '_fit.html')); os.makedirs(os.path.join(pkg, '_m'), exist_ok=True)
for f in glob.glob(os.path.join(here, '..', 'motion', 'frames', 's*.png')): shutil.copy(f, os.path.join(pkg, '_m', os.path.basename(f)))
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=pkg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.5)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path='/opt/pw-browsers/chromium'); pg = b.new_page()
        pg.goto(f'http://127.0.0.1:{port}/_fit.html'); pg.wait_for_function('window.ready', timeout=30000)
        for i in range(8): pg.evaluate(f"loadMask({i},'_m/s{i:02d}.png')")
        base = pg.evaluate("()=>Object.assign({},RunAnimator.GAIT_DEFAULTS,rig.def.gait||{})")
        P = ['lean', 'bob', 'hipBase', 'kneeLift', 'heelKick', 'armSwing', 'armBias', 'strideBase']
        ST = {'lean': .06, 'bob': 6, 'hipBase': 10, 'kneeLift': .2, 'heelKick': .2, 'armSwing': .15, 'armBias': .1, 'strideBase': 15}
        r = pg.evaluate('([b,f,p,s,n])=>fitRun(b,f,p,s,n)', [base, list(range(8)), P, ST, 8]); b.close()
finally: srv.terminate(); os.remove(os.path.join(pkg, '_fit.html')); shutil.rmtree(os.path.join(pkg, '_m'))
print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != 'gait'})); print({k: round(v, 3) for k, v in r['gait'].items()})
json.dump(r, open(sys.argv[2], 'w'), indent=1)
