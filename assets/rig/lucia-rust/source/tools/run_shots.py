# 22 스카이 둘시네 달리기 1/60 장면(공격 없이) — python3 -I tools/run_shots.py OUT.png [프레임수=36] [SC=.5] [RID]  (10-20 기록)
import sys, time, socket, subprocess, base64, io, os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 36; SC = float(sys.argv[3]) if len(sys.argv) > 3 else .5; ID = sys.argv[4] if len(sys.argv) > 4 else 'lucia-rust'
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d=MR_RIG_DEFS['{ID}'];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src}})));const IM=Object.fromEntries(ims);
window.run=(N,sc)=>{{const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<240;i++)an.update(1/120,{{vx:620}});const o=[];
 for(let i=0;i<N;i++){{an.update(1/60,{{vx:620}});const c=document.createElement('canvas');c.width=Math.round(1040*sc/.9);c.height=Math.round(1120*sc/.9);const g=c.getContext('2d');rig.draw(g,c.width/2,c.height-20,sc,1);o.push(c.toDataURL())}}return o}};window.ready=1}})()</script>'''
open(os.path.join(root, '_run.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); pg.goto(f'http://127.0.0.1:{port}/_run.html'); pg.wait_for_function('window.ready', timeout=30000)
        R = pg.evaluate('([n,s])=>run(n,s)', [N, SC]); b.close()
finally:
    srv.terminate(); os.remove(os.path.join(root, '_run.html'))
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14); cols = int(os.environ.get('COLS', 9)); TW, TH = int(os.environ.get('TW', 260)), int(os.environ.get('TH', 280)); W = Image.new('RGB', (TW * cols, TH * ((N + cols - 1) // cols)), 'white')
for i, u in enumerate(R):
    im = Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    t = bg.convert('RGB').resize((TW, TH)); ImageDraw.Draw(t).text((4, 4), f'{i}/60', fill='red', font=f); W.paste(t, ((i % cols) * TW, (i // cols) * TH))
W.save(out); print(out, W.size)
