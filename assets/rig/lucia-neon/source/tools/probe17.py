# 17 네온 루시아(7 러스트 probe7 복사): 엔진에서 뼈 값 재기 — python3 -I tools/probe7.py "JS 식(rig, an 사용)" [vx=620] [프레임=12]
import sys, time, socket, subprocess, os, json
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(HERE, '..', '..', '..')); ID = os.environ.get('RID', 'lucia-neon')
EXPR = sys.argv[1]; VX = float(sys.argv[2]) if len(sys.argv) > 2 else 620; N = int(sys.argv[3]) if len(sys.argv) > 3 else 12
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d=MR_RIG_DEFS['{ID}'];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src}})));const IM=Object.fromEntries(ims);
const wA=m=>Math.atan2(m[1],m[0]);window.go=(vx,n)=>{{const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<240;i++)an.update(1/120,{{vx}});const o=[];
 for(let i=0;i<n;i++){{an.update(1/60,{{vx}});rig.compute();o.push({EXPR})}}return o}};window.ready=1}})()</script>'''
open(os.path.join(root, '_probe.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{port}/_probe.html'); pg.wait_for_function('window.ready', timeout=30000)
        for r in pg.evaluate('([v,n])=>go(v,n)', [VX, N]): print(r)
        if errs: print('errors', errs[:3])
        b.close()
finally:
    srv.terminate(); os.remove(os.path.join(root, '_probe.html'))
