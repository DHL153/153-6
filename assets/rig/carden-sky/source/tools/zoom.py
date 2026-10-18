#!/usr/bin/env python3
"""관절 확대 장면표: 장면·시각마다 목·어깨(가까운/먼)·팔꿈치·손목·손-자루·허리를 3배로 잘라 한 줄에.
python3 zoom.py PKG out.png scene:t,scene:t,..."""
import os, sys, json, subprocess, socket, time, base64, io
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
pkg = os.path.abspath(sys.argv[1]); out = sys.argv[2]; items = [x.split(':') for x in sys.argv[3].split(',')]
here = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(here, 'render.html')).read().replace('window.ready=1', '''
window.zoomAt=(scene,T)=>{const c=document.createElement('canvas');c.width=1300;c.height=1150;const g=c.getContext('2d');const an=new RunAnimator(rig);let v=0;const dt=1/120,f=SC[scene];
 for(let i=0;i*dt<=T+1e-9;i++){const t=i*dt,s=f(t);const tgt=an.busy?0:s.vx;v+=(tgt-v)*(1-Math.exp(-(an.busy?16:tgt?4.2:6.5)*dt));if(s.atk)an.attack('thrust');if(s.wave)an.wave();an.update(dt,{vx:v})}
 g.fillStyle='#f6eed2';g.fillRect(0,0,1300,1150);rig.draw(g,650,1100,1,1);rig.compute();const P=n=>{const p=rig.point(n);return [650+p[0],1100+p[1]]};
 const al=n=>(rig.alpha[n]??1)>.5;const pts={neck:P('head'),shN:P('armU'),shF:P('armF')};
 if(al('armL'))pts.elN=P('armL');if(al('foreF'))pts.elF=P('foreF');if(al('fistF'))pts.wrF=P('fistF');if(al('handL'))pts.gripL=P('handL');if(al('handR'))pts.gripR=[650+rig.partPoint('handR',...rig.def.parts.handR.pivot)[0],1100+rig.partPoint('handR',...rig.def.parts.handR.pivot)[1]];
 if(al('wFore'))pts.wave=P('wFore');pts.waist=P('torso');return {img:c.toDataURL(),pts}};window.ready=1''')
open(os.path.join(pkg, '_zoom.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=pkg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.5)
rows = []
try:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path='/opt/pw-browsers/chromium'); pg = b.new_page()
        pg.goto(f'http://127.0.0.1:{port}/_zoom.html'); pg.wait_for_function('window.ready', timeout=30000)
        for sc, t in items: rows.append((sc, t, pg.evaluate('([s,t])=>zoomAt(s,t)', [sc, float(t)])))
        b.close()
finally: srv.terminate(); os.remove(os.path.join(pkg, '_zoom.html'))
K = 2; R = 55; cell = R * 2 * K
keys = ['neck', 'shN', 'shF', 'elN', 'elF', 'wrF', 'gripL', 'gripR', 'wave', 'waist']
W = 260 + cell * len(keys); H = max(cell, 260) + 16
o = Image.new('RGB', (W, H * len(rows)), (255, 255, 255)); d = ImageDraw.Draw(o)
for i, (sc, t, r) in enumerate(rows):
    im = Image.open(io.BytesIO(base64.b64decode(r['img'].split(',')[1]))).convert('RGB'); y = i * H
    full = im.crop((250, 300, 1150, 1120)); full.thumbnail((250, 250)); o.paste(full, (4, y + 14)); d.text((4, y + 2), f'{sc} t={t}', fill=(0, 0, 0))
    for j, k in enumerate(keys):
        if k not in r['pts']: continue
        x0, y0 = r['pts'][k]; c = im.crop((int(x0 - R), int(y0 - R), int(x0 + R), int(y0 + R))).resize((cell, cell), Image.LANCZOS)
        o.paste(c, (260 + j * cell, y + 14)); d.text((262 + j * cell, y + 2), k, fill=(200, 0, 0))
o.save(out); print(out)
