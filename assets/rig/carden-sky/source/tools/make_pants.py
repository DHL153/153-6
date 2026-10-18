#!/usr/bin/env python3
"""바지 윗부분(엉덩이 + 두 허벅지, 서 있는 자세)을 한 장으로 — '반바지 치마'(skirt 뼈) 그림 (DHL 2026-10-17 23:51)
표시한 곳(벨트 아래 ~ 무릎)까지는 몸, 그 아래만 다리가 걷게: 허벅지는 이 그림 안에 고정, 리그 다리는 무릎 위에서 시작.
python3 make_pants.py PKG   (PKG = pantsSkirt 끄고 빌드한 리그) → ../parts_work/pants.png + ../pants.json {pivot: skirt 뼈 자리(그림 px)}"""
import os, sys, time, socket, subprocess, json, base64, io
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
pkg = os.path.abspath(sys.argv[1]); here = os.path.dirname(os.path.abspath(__file__)); src = os.path.dirname(here)
html = '''<!doctype html><meta charset=utf-8><script src="rig.js"></script><script>(async()=>{const d=await (await fetch("rig.json")).json();
for(const n of ["shinN","shinF","boot"]){const c=document.createElement("canvas");c.width=c.height=2;d.parts[n].src=c.toDataURL()}
d.draw=["legFar","legNear","hips"];
const images={};await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((res,rej)=>{const im=new Image();im.onload=()=>res(images[k]=im);im.onerror=rej;im.src=p.src})));const rig=new CharacterRig(d,images);window.rig=rig;const an=new RunAnimator(rig);for(let i=0;i<120;i++)an.update(1/120,{vx:0});
const c=document.createElement("canvas");c.width=1400;c.height=1200;const g=c.getContext("2d");rig.draw(g,700,1100,1,1);rig.compute();
window.out={img:c.toDataURL(),skirt:rig.point("skirt")};window.ready=1})()</script>'''
open(os.path.join(pkg, '_pants.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=pkg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.5)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{port}/_pants.html'); pg.wait_for_function('window.ready', timeout=30000)
        R = pg.evaluate('window.out'); b.close()
        if errs: print('ERR', errs)
finally: srv.terminate(); os.remove(os.path.join(pkg, '_pants.html'))
im = Image.open(io.BytesIO(base64.b64decode(R['img'].split(',')[1]))).convert('RGBA'); a = np.asarray(im)
ys, xs = np.nonzero(a[..., 3] > 4); x0, y0 = int(xs.min()) - 2, int(ys.min()) - 2; x1, y1 = int(xs.max()) + 3, int(ys.max()) + 3
im.crop((x0, y0, x1, y1)).save(os.path.join(src, 'parts_work', 'pants.png'))
sk = R['skirt']; piv = [round(700 + sk[0] - x0, 1), round(1100 + sk[1] - y0, 1)]
json.dump({'pivot': piv, 'size': [x1 - x0, y1 - y0], 'skirtWorld': sk}, open(os.path.join(src, 'pants.json'), 'w'))
print('pants', x1 - x0, y1 - y0, 'pivot', piv, 'bottom above ground', round(-(sk[1] + (y1 - y0) - piv[1]), 1))
