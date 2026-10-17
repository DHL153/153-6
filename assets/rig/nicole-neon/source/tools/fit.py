#!/usr/bin/env python3
"""동작 시트 맞춤 실행. python3 fit.py PKG plan.json out.json  (plan: [{act,t,frame,params,step}])"""
import os, sys, time, socket, subprocess, json, shutil, glob
from playwright.sync_api import sync_playwright
pkg = os.path.abspath(sys.argv[1]); plan = json.load(open(sys.argv[2])); here = os.path.dirname(os.path.abspath(__file__))
shutil.copy(os.path.join(here, 'fit.html'), os.path.join(pkg, '_fit.html')); os.makedirs(os.path.join(pkg, '_m'), exist_ok=True)
for f in glob.glob(os.path.join(here, '..', 'motion', 'frames', 's*.png')): shutil.copy(f, os.path.join(pkg, '_m', os.path.basename(f)))
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=pkg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.5)
res = {}
META = json.load(open(os.path.join(here, '..', 'motion', 'scaled_meta.json')))
try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path='/opt/pw-browsers/chromium'); pg = b.new_page()
        pg.goto(f'http://127.0.0.1:{port}/_fit.html'); pg.wait_for_function('window.ready', timeout=30000)
        for step in plan:
            pg.evaluate(f"loadMask({step['frame']},'_m/s{step['frame']:02d}.png')")
            sm = META[str(step['frame'])]
            if sm['spear'] and step.get('spear', True):
                (x1, y1), (x2, y2) = sm['spear']['p1'], sm['spear']['p2']; pg.evaluate('([i,a,y])=>setSpear(i,a,y)', [step['frame'], sm['spear']['ang'], sm['h'] - (y1 + y2) / 2])
            if 'target' in step: pg.evaluate('([i,t])=>setTarget(i,t)', [step['frame'], step['target']])
            for n, v in step.get('init', {}).items(): pg.evaluate('([a,t,n,v])=>{const A=rig.def.actions[a][n];const k=A.find(x=>Math.abs(x[0]-t)<1e-6);if(k)k[1]=v;else{A.push([t,v,"io"]);A.sort((p,q)=>p[0]-q[0])}}', [step['act'], step['t'], n, v])
            before = pg.evaluate('([a,t,f])=>score(a,t,f)', [step['act'], step['t'], step['frame']])
            r = pg.evaluate('([a,t,f,p,s,n])=>fit(a,t,f,p,s,n)', [step['act'], step['t'], step['frame'], step['params'], step['step'], step.get('rounds', 14)])
            print(step['t'], 'frame', step['frame'], 'score', before['iou'], 'raw', before.get('raw'), '→', round(r['iou'], 4), r['vals'], flush=True); res[str(step['t'])] = dict(before=before, **r)
        res['_final'] = [pg.evaluate('([a,t,f])=>score(a,t,f)', [s_['act'], s_['t'], s_['frame']]) for s_ in plan]
        res['_action'] = pg.evaluate("a=>rig.def.actions[a]", plan[0]['act']); b.close()
finally: srv.terminate(); os.remove(os.path.join(pkg, '_fit.html')); shutil.rmtree(os.path.join(pkg, '_m'))
json.dump(res, open(sys.argv[3], 'w'), indent=0)
