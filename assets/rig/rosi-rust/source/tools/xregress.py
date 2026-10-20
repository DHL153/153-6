#!/usr/bin/env python3
"""Pixel-compare two (engine, rig dir) pairs on the same scenario.
  xregress.py ENGINE_A DIR_A ENGINE_B DIR_B [--game] [--out PREFIX]
--game adds battle-like runs (stepHz 2.22 at the given vx) — only meaningful when both engines are game engines.
Scenario = engine_regress.py scenario + walk/run at several speeds + attack while moving."""
import sys, os, json, io, base64, socket, subprocess, tempfile, shutil, time
import numpy as np
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
PAGE = """<!doctype html><meta charset="utf-8"><canvas id=c width=1000 height=1400></canvas><script>
Math.random=()=>0.5;
const sc=document.createElement('script');sc.src='engine.js';
sc.onload=async()=>{window.rig=await CharacterRig.load('rig.json');window.ready=1};document.head.appendChild(sc);
window.run=(scen)=>{const a=new RunAnimator(rig,{runSpeed:620}),cv=document.getElementById('c'),g=cv.getContext('2d'),out=[],info=[];
 for(const [dur,vx,js,snap,hz] of scen){if(js)eval(js);const n=Math.round(dur*60);for(let i=0;i<n;i++){a.update(1/60,hz?{vx,stepHz:hz,facing:1}:{vx});}
  if(snap){g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,1000,1400);rig.draw(g,520,1330,1,1);out.push(cv.toDataURL());info.push(a.act?a.act.name+':'+a.act.t.toFixed(3):'-')}}
 return [out,info]};
</script>"""
def scenario(d, game=False):
    acts = list((d.get('actions') or {}).keys())
    run = (d.get('ui') or {}).get('runSpeed') or (150 if d.get('carry') else 620)
    s = [[1, 0, None, 1], [0.37, run, None, 1], [0.5, run, None, 1], [0.8, run / 2, None, 1], [1.2, 0, None, 1]]
    for n in (acts or ['thrust', 'wave']):
        if n == 'fire':
            s += [[0.3, 0, 'a.fire(true)', 1], [0.6, 0, None, 1], [0.3, 0, 'a.fire(false)', 1], [1.0, 0, None, 1]]
        else:
            s += [[0.25, 0, f'a.attack({json.dumps(n)})', 1], [0.4, 0, None, 1], [1.5, 0, None, 1]]
    for f in list((d.get('faces') or {}).keys())[:3]:
        s += [[0.5, 0, f'a.setExpression({json.dumps(f)})', 1]]
    s += [[0.5, 0, 'a.setExpression(null)', 0], [0.6, run, None, 1]]
    first = acts[0] if acts else 'thrust'
    if d.get('carry'): s += [[0.2, run, 'a.fire(true)', 1], [0.4, 0, 'a.fire(false)', 1], [1.2, 0, None, 1]]
    else: s += [[0.2, run, f'a.attack({json.dumps(first)})', 1], [1.2, 0, None, 1]]
    for v in (60, 300, 900): s += [[0.25, v, None, 1], [0.25, v, None, 1], [0.5, v, None, 1]]
    s += [[1.0, 0, None, 1]]
    if game:
        for v in (380, 500, 650): s += [[0.3, v, None, 1, 2.22], [0.23, v, None, 1, 2.22], [0.4, v, None, 1, 2.22]]
        s += [[0.2, 500, ('a.fire(true)' if d.get('carry') else f'a.attack({json.dumps(first)},{{speed:1.5}})'), 1, 2.22], [0.3, 0, 'a.fire&&a.fire(false)', 1, 2.22], [1.0, 500, None, 1, 2.22], [1.0, 0, None, 1]]
    return s
def shots(engine, rdir, scen):
    tmp = tempfile.mkdtemp(prefix='xr_')
    for n in os.listdir(rdir):
        if n in ('rig.js', 'engine.js') or n.endswith('.html'): continue
        os.symlink(os.path.join(os.path.abspath(rdir), n), os.path.join(tmp, n))
    shutil.copy(engine, os.path.join(tmp, 'engine.js')); open(os.path.join(tmp, 'x.html'), 'w').write(PAGE)
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.7)
    errs = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=['--headless=new']); pg = b.new_page(); pg.on('pageerror', lambda x: errs.append(str(x)))
            pg.goto(f'http://127.0.0.1:{port}/x.html'); pg.wait_for_function('window.ready', timeout=30000)
            out, info = pg.evaluate(f'run({json.dumps(scen)})'); b.close()
    finally:
        srv.terminate(); shutil.rmtree(tmp, ignore_errors=True)
    dec = lambda u: Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGBA')
    return [dec(x) for x in out], info, errs
def main():
    a = sys.argv[1:]; game = '--game' in a; a = [x for x in a if x != '--game']
    out = None
    if '--out' in a: i = a.index('--out'); out = a[i + 1]; a = a[:i] + a[i + 2:]
    eA, dA, eB, dB = a[:4]
    d = json.load(open(os.path.join(dA, 'rig.json'))); sc = scenario(d, game)
    A, iA, errA = shots(eA, dA, sc); B, iB, errB = shots(eB, dB, sc); nd = 0
    for i, (x, y) in enumerate(zip(A, B)):
        df = np.asarray(ImageChops.difference(x, y)).max(axis=2); n = int((df > 8).sum())
        if n:
            nd += 1; print(f'  snap {i} ({iA[i]} | {iB[i]}): {n} px differ (max {int(df.max())})')
            if out: Image.fromarray(np.hstack([np.asarray(x), np.asarray(y)])).save(f'{out}_{i}.png')
    name = os.path.basename(os.path.abspath(dA))
    print(f'{name}: {len(A)} snapshots, {nd} differ | errors A {errA[:2]} B {errB[:2]}')
    sys.exit(1 if (nd or errA or errB) else 0)
if __name__ == '__main__': main()
