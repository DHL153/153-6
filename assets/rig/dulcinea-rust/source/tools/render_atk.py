# 둘시네 공격 확인 그림: python3 tools/render_atk.py out.png "t1,t2,..." ["f1,f2,..."] [overlay|side]
#  t = 동작 시각(초, 타격 정지 시간 빼고 동작 시계), f = 시트 4번 칸 번호(1~8, 0 = 없음) — 같은 시각 리그 위에 시트 칸을 겹침(땅·발 가운데 맞춤, 편집기와 같은 값)
#  환경: SC(배율, 기본 .5) · STEP(1/120)
import sys, time, socket, subprocess, base64, io, os, json
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..'); root = os.environ.get('ROOT') or os.path.abspath(os.path.join(SRC, '..', '..'))
out = sys.argv[1]; TS = [float(v) for v in sys.argv[2].split(',')]; FS = [int(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 and sys.argv[3] else [0] * len(TS)
mode = sys.argv[4] if len(sys.argv) > 4 else 'overlay'; SC = float(os.environ.get('SC', '.5'))
# 시트 칸 맞춤 값(편집기 DUL2_M 공격 8칸과 같음): [폭, 땅 y, 발 x 목록, 리그 배율]
CAL = [[601, 582, [42.0, 470.0], 1.6], [458, 817, [51.0, 447.0], 1.6], [537, 720, [122.0, 526.0], 1.6], [571, 738, [62.0, 517.0], 1.6], [638, 590, [28.0, 471.0], 1.6], [606, 468, [10.0, 583.0], 1.6], [588, 445, [10.0, 572.0], 1.6], [568, 546, [64.0, 476.0], 1.6]]
ACT = open(os.environ['ACT']).read() if os.environ.get('ACT') else '{}'
ID = 'dulcinea-rust'; CW, CH, GX, GY = 900, 1000, 430, 930
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const def=JSON.parse(JSON.stringify(MR_RIG_DEFS['{ID}']));Object.assign(def.actions.smash,{ACT});def.hidden=(def.hidden||[]).concat({json.dumps(os.environ.get('HIDE','').split(',') if os.environ.get('HIDE') else [])});const ims=await Promise.all(Object.entries(def.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src+'?x={time.time()}'}})));
const IM=Object.fromEntries(ims);
window.at=(T,sc)=>{{const rig=new CharacterRig(def,IM),an=new RunAnimator(rig,{{runSpeed:620}});const HB={json.dumps(os.environ.get('HIDE','').split(',') if os.environ.get('HIDE') else [])};for(let i=0;i<60;i++)an.update(1/120,{{vx:0}});an.attack('smash');let n=0;
 while(an.act&&an.act.t<T-1e-6&&n<4000){{an.update(1/240,{{vx:0}});n++}}
 for(const n of HB)rig.alpha[n]=0;const c=document.createElement('canvas');c.width={CW};c.height={CH};const g=c.getContext('2d');rig.draw(g,{GX},{GY},sc,1);window.LEGS=an.legPose||rig.legPose;
 const ft=an.ft;return [c.toDataURL(),(ft.near.x+ft.far.x)/2, an.act?an.act.t:-1, an.stN||0, an.stF||0, an.wrN||0, an.wrF||0]}};
window.ready=1}})()</script>'''
open(os.path.join(root, '_atk.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
dec = lambda d: Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).convert('RGBA')
res = []
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{port}/_atk.html'); pg.wait_for_function('window.ready', timeout=30000)
        for t in TS: res.append(pg.evaluate('([t,s])=>at(t,s)', [t, SC]))
        b.close()
        if errs: print('errors', errs[:5])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_atk.html'))
tiles = []
for t, f, r in zip(TS, FS, res):
    im = dec(r[0]); fx = r[1]
    bg = Image.new('RGBA', im.size, (244, 239, 226, 255)); d = ImageDraw.Draw(bg); d.line([(0, GY), (CW, GY)], fill=(150, 150, 150), width=2)
    if f:
        W_, gy, feet, k = CAL[f - 1]; fr = Image.open(os.path.join(SRC, 'atk_frames', f'a{f}.png')).convert('RGBA'); s = k * SC
        fr = fr.resize((int(fr.width * s), int(fr.height * s)), Image.LANCZOS); ffx = (feet[0] + feet[-1]) / 2
        ox = GX + fx * SC - ffx * s; oy = GY - gy * s
        if mode == 'side':
            sb = Image.new('RGBA', im.size, (244, 239, 226, 255)); sb.alpha_composite(fr, (int(ox), int(oy))); ImageDraw.Draw(sb).line([(0, GY), (CW, GY)], fill=(150, 150, 150), width=2)
        else:
            a = np.array(fr); a[..., 3] = (a[..., 3] * .42).astype(np.uint8); bg.alpha_composite(Image.fromarray(a), (int(ox), int(oy)))
    bg.alpha_composite(im) if mode != 'over2' else None
    d = ImageDraw.Draw(bg); d.text((10, 10), f't={t:.3f} (act {r[2]:.3f}) sheet {f}  stN {r[3]:.2f} stF {r[4]:.2f} wrN {np.degrees(r[5]):.0f} wrF {np.degrees(r[6]):.0f}', fill=(0, 0, 0))
    tiles.append(bg.convert('RGB'))
    if f and mode == 'side': tiles.append(sb.convert('RGB'))
cols = min(4, len(tiles)); rows = (len(tiles) + cols - 1) // cols; tw, th = tiles[0].size
c = Image.new('RGB', (tw * cols, th * rows), 'white')
for i, tl in enumerate(tiles): c.paste(tl, ((i % cols) * tw, (i // cols) * th))
c.save(out); print('ok', [(round(r[2], 3), round(r[3], 2), round(r[4], 2), round(float(np.degrees(r[5]))), round(float(np.degrees(r[6])))) for r in res])
