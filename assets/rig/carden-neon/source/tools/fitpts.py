#!/usr/bin/env python3
"""찌르기 관절점 맞춤 실행. python3 fitpts.py PKG out.json [start.json]
start.json: {트랙이름: [[t,v,ease],...]} 시작 트랙(덮어씀). 결과: 키별 오차·값 + 최종 thrust 트랙 전체"""
import os, sys, time, socket, subprocess, json, shutil
from playwright.sync_api import sync_playwright
pkg = os.path.abspath(sys.argv[1]); here = os.path.dirname(os.path.abspath(__file__))
TG = json.load(open(os.path.join(here, '..', 'motion', 'pts_thrust.json')))
START = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
shutil.copy(os.path.join(here, 'fitpts.html'), os.path.join(pkg, '_fitpts.html'))
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=pkg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.5)
PARAMS = os.environ.get('PARAMS', 'hipX,hipY,lean,head,thF,nearDx,gap').split(',')   # 뒷발(먼 발)은 디딘 채, 앞발(가까운 발)만 내딛음
STEP = {'sh': .15, 'gx': 30, 'gy': 20, 'gap': 40, 'hipX': 30, 'hipY': 20, 'lean': .06, 'head': .05, 'thF': .1, 'farDx': 40, 'nearDx': 40, 'ang': .05}
res = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path='/opt/pw-browsers/chromium'); pg = b.new_page()
        pg.goto(f'http://127.0.0.1:{port}/_fitpts.html'); pg.wait_for_function('window.ready', timeout=30000)
        pg.evaluate('o=>setTargets(o)', TG)
        for n, v in START.items(): pg.evaluate('([n,v])=>setTrack(n,v)', [n, v])
        keys = sorted(float(k) for k in TG if k != 'idle' and (not os.environ.get('KEYS') or k in os.environ['KEYS'].split(',')))
        for t in keys:
            r0 = pg.evaluate('t=>err(t)', t); print('before', t, round(r0['e'], 2), r0['d'], flush=True)
        if os.environ.get('NOFIT') != '1':
            for t in keys:
                r = pg.evaluate('([t,p,s])=>fit(t,p,s,18)', [t, PARAMS, STEP]); res[str(t)] = r
                print('fit', t, round(r['e'], 3), r['d'], r['vals'], flush=True)
            for t in keys:
                r1 = pg.evaluate('t=>err(t)', t); print('after', t, round(r1['e'], 3), 'pen', r1['pen'], r1['d'], flush=True)
        res['_action'] = pg.evaluate('()=>rig.def.actions.thrust'); b.close()
finally: srv.terminate(); os.remove(os.path.join(pkg, '_fitpts.html'))
json.dump(res, open(sys.argv[2], 'w'), indent=0)
