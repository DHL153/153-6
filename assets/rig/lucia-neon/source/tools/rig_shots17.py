# 리그 공격 장면을 투명 PNG 로 (12 네온 — 러스트 kit5/rig_shots.py 복사, RID 로 다른 리그): python3 kit5/rig_shots.py OUTPREFIX "t1,t2,.." [SC]  → OUTPREFIX_<t>.png (캔버스 900×1000, 땅 y=930, 발 가운데 x 기록)
import sys, time, socket, subprocess, base64, io, os, json
from playwright.sync_api import sync_playwright
from PIL import Image
SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); root = os.path.abspath(os.path.join(SRC, '..', '..'))   # (12 네온: 러스트 kit5/rig_shots.py 복사, ID = dulcinea-sky)
pre = sys.argv[1]; TS = [float(v) for v in sys.argv[2].split(',')]; SC = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
ACT = open(os.environ['ACT']).read() if os.environ.get('ACT') else '{}'
DEFX = open(os.environ['DEFX']).read() if os.environ.get('DEFX') else '{}'
VX = float(os.environ.get('VX', 0))   # 달리며 치기 확인: VX=620
ID = os.environ.get('RID', 'lucia-neon'); CW, CH, GX, GY = 1400, 1400, 600, 1300
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const def=JSON.parse(JSON.stringify(MR_RIG_DEFS['{ID}']));Object.assign(def.actions.smash,{ACT});Object.assign(def,{DEFX});const ims=await Promise.all(Object.entries(def.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src+'?x={time.time()}'}})));
const IM=Object.fromEntries(ims);
window.at=(T,sc)=>{{const rig=new CharacterRig(def,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<240;i++)an.update(1/120,{{vx:{VX}}});an.attack('smash');let n=0;
 while(an.act&&an.act.t<T-1e-6&&n<4000){{an.update(1/240,{{vx:{VX}}});n++}}
 const c=document.createElement('canvas');c.width={CW};c.height={CH};const g=c.getContext('2d');rig.draw(g,{GX},{GY},sc,1);const ft=an.ft;return [c.toDataURL(),(ft.near.x+ft.far.x)/2,an.act?an.act.t:-1]}};
window.ready=1}})()</script>'''
open(os.path.join(root, '_shot.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
meta = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_shot.html'); pg.wait_for_function('window.ready', timeout=30000)
        for t in TS:
            d, fx, ta = pg.evaluate('([t,s])=>at(t,s)', [t, SC]); im = Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).convert('RGBA')
            fn = f'{pre}_{t:.3f}.png'; im.save(fn); meta[f'{t:.3f}'] = {'file': fn, 'feetX': GX + fx * SC, 'groundY': GY, 'actT': ta, 'sc': SC}
        b.close()
        if errs: print('errors', errs[:5])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_shot.html'))
json.dump(meta, open(pre + '_meta.json', 'w'), indent=1); print(meta)
