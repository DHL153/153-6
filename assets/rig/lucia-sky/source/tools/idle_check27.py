# 17 네온 루시아(7 러스트 idle_check7 복사): 엔진 대기(서 있기, 숨쉬기 몇 위상)를 원화 크기(배율 .5)로 그려 원화와 겹침 — python3 -I tools/idle_check7.py → 표 + review/idle_check.png(원화 | 리그 | 차이)
import sys, time, socket, subprocess, base64, io, os, json
import numpy as np
from playwright.sync_api import sync_playwright
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); root = os.path.abspath(os.path.join(SRC, '..', '..')); ID = 'lucia-sky'
rig = json.load(open(os.path.join(SRC, '..', 'rig.json'))); OX, OY = rig['refOrigin'][0] / 2, rig['refOrigin'][1] / 2
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d=MR_RIG_DEFS['{ID}'];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src}})));const IM=Object.fromEntries(ims);
window.go=(ts)=>{{const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});let T=0;const o=[];for(const t of ts){{while(T<t){{an.update(1/120,{{vx:0}});T+=1/120}}
 const c=document.createElement('canvas');c.width=512;c.height=512;rig.draw(c.getContext('2d'),{OX},{OY},.5,1);o.push(c.toDataURL())}}return o}};window.ready=1}})()</script>'''
open(os.path.join(root, '_idle.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); pg.goto(f'http://127.0.0.1:{port}/_idle.html'); pg.wait_for_function('window.ready', timeout=30000)
        R = pg.evaluate('(ts)=>go(ts)', [1.0, 1.7, 2.4, 3.1]); b.close()
finally:
    srv.terminate(); os.remove(os.path.join(root, '_idle.html'))
A = np.array(Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA')); Aa = A[..., 3] > 128
rows = []
for i, d in enumerate(R):
    im = np.array(Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).convert('RGBA')); m = im[..., 3] > 128
    iou = (m & Aa).sum() / (m | Aa).sum(); both = m & Aa; cd = np.abs(im[..., :3].astype(int) - A[..., :3].astype(int)).sum(-1)[both].mean() / 3
    rows.append((iou, cd)); print(f'  위상 {i}: 실루엣 겹침 {iou:.3f} · 색 차이 평균 {cd:.1f}/255')
    if i == 0: R0 = im
W = Image.new('RGB', (1536, 512), 'white')
bg = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); bg.alpha_composite(Image.fromarray(A)); W.paste(bg.convert('RGB'), (0, 0))
bg = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); bg.alpha_composite(Image.fromarray(R0)); W.paste(bg.convert('RGB'), (512, 0))
df = np.zeros((512, 512, 3), np.uint8); m0 = R0[..., 3] > 128; df[Aa & ~m0] = (220, 40, 40); df[m0 & ~Aa] = (40, 90, 230); df[m0 & Aa] = (200, 200, 200); W.paste(Image.fromarray(df), (1024, 0))
os.makedirs(os.path.join(SRC, 'review'), exist_ok=True); W.save(os.path.join(SRC, 'review', 'idle_check.png'))
