# 둘시네 리그 확인 그림: python3 tools/render.py idle|run|both out.png [vx hz]
#  idle: 1.5초 숨쉬기 뒤 대기 자세를 원화와 겹침(원화 · 리그 · 차이) / run: 1초 달린 뒤 0.9초(두 걸음) 12장 / both
#  환경: BIG=1 (0.9배) · SC=1.6 CROP=x0,y0,x1,y1 (부분 확대, 예: 골반 SC=1.6 CROP=250,170,570,450)
import sys, time, socket, subprocess, base64, io, os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageDraw
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..'); root = os.path.abspath(os.path.join(SRC, '..', '..'))
mode, out = sys.argv[1], sys.argv[2]; vx = float(sys.argv[3]) if len(sys.argv) > 3 else 300; hz = float(sys.argv[4]) if len(sys.argv) > 4 else 2.22
ID = 'dulcinea-rust'
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const def=JSON.parse(JSON.stringify(MR_RIG_DEFS['{ID}']));const ims=await Promise.all(Object.entries(def.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=j;im.src='{ID}/'+p.src+'?x={time.time()}'}})));
const IM=Object.fromEntries(ims);
window.idle=(T)=>{{const rig=new CharacterRig(def,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<T*120;i++)an.update(1/120,{{vx:0}});
 const c=document.createElement('canvas');c.width=512;c.height=512;const g=c.getContext('2d');rig.draw(g,def.refOrigin[0]/2,def.refOrigin[1]/2,.5,1);return c.toDataURL()}};
window.run=(vx,hz)=>{{const rig=new CharacterRig(def,IM),an=new RunAnimator(rig,{{runSpeed:620}});const out=[];const c=document.createElement('canvas');c.width=700;c.height=900;const g=c.getContext('2d');
 for(let i=0;i<=120*1.9;i++){{an.update(1/120,{{vx,stepHz:hz}});if(i>=120&&(i-120)%9==0&&out.length<12){{g.clearRect(0,0,700,900);g.fillStyle='#f4efe2';g.fillRect(0,0,700,900);g.fillStyle='#bbb';g.fillRect(0,860,700,2);
  const x=((-an.odo)%120+120)%120;for(let k=-1;k<7;k++)g.fillRect(k*120+x,860,6,14);rig.draw(g,330,860,window.SC||.45,1);out.push(c.toDataURL())}}}}return out}};
window.ready=1}})()</script>'''
open(os.path.join(root, '_drender.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
dec = lambda d: Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).convert('RGBA')
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None); pg.on('response', lambda r: errs.append('404 ' + r.url) if r.status == 404 else None)
        pg.goto(f'http://127.0.0.1:{port}/_drender.html'); pg.wait_for_function('window.ready', timeout=30000)
        I = dec(pg.evaluate('t=>idle(t)', float(os.environ.get('IDLE_T','1.5')))) if mode in ('idle', 'both') else None
        BIG = os.environ.get('BIG')
        if BIG: pg.evaluate('window.SC=.9')
        if os.environ.get('SC'): pg.evaluate(f"window.SC={float(os.environ['SC'])}")
        R = pg.evaluate('([v,h])=>run(v,h)', [vx, hz]) if mode in ('run', 'both') else None
        b.close()
        if errs: print('errors', errs[:5])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_drender.html'))
if I is not None:
    ref = Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA')
    bg = lambda im: Image.alpha_composite(Image.new('RGBA', im.size, (255, 255, 255, 255)), im).convert('RGB')
    a, r = np.array(bg(I)).astype(int), np.array(bg(ref)).astype(int); d = np.abs(a - r).max(2)
    print('idle vs 원화: mean diff', round(float(np.abs(a - r).mean()), 2), 'px >40:', int((d > 40).sum()))
    dm = np.full((512, 512, 3), 255, np.uint8); dm[d > 40] = (255, 0, 0); dm[(d > 12) & (d <= 40)] = (255, 170, 170)
    c = Image.new('RGB', (1536, 512), 'white'); c.paste(bg(ref), (0, 0)); c.paste(bg(I), (512, 0)); c.paste(Image.fromarray(dm), (1024, 0))
    c.save(out if mode == 'idle' else out.replace('.png', '_idle.png'))
if R:
    CROP = tuple(int(v) for v in os.environ['CROP'].split(',')) if os.environ.get('CROP') else ((150, 380, 650, 880) if BIG else (130, 430, 630, 880))
    ims = [dec(d).convert('RGB').crop(CROP) for d in R]; tw, th = ims[0].size
    c = Image.new('RGB', (tw * 4, th * 3), 'white')
    for i, im in enumerate(ims): c.paste(im, ((i % 4) * tw, (i // 4) * th))
    c.save(out if mode == 'run' else out.replace('.png', '_run.png'))
print('ok')
