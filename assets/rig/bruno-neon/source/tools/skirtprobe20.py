"""20 네온 브루노 — 달릴 때 다리가 치마 밖으로 나오는 px(1/60 한 주기): 다리만·치마만 따로 그려, 치마 단(열마다 치마 아래 끝)보다 위에 있는데 치마 밖인 다리 px
   (치마 조각 = hipsRun 뼈, 없으면 skirt 뼈 — v1.9 부터 늘 치마)
   (치마 옆은 끝 열의 단 높이로 늘인 선 위) + 허벅지 각(엉덩이→무릎, 세로 기준 도, + = 앞). 실행: python3 tools/skirtprobe20.py [n=40] [출력 그림]
"""
import sys, threading, functools, http.server, socketserver, base64, io
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Q, directory='/home/claude/153-6')); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
DBG = 0
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40; OUT = sys.argv[2] if len(sys.argv) > 2 else None
JS = """([n, mode])=>{const an=window.__an,rig=window.__rig,out=[];const c=document.createElement('canvas');c.width=c.height=1024;const g=c.getContext('2d');
const all=rig.def.draw.slice();const SK=all.includes('hipsRun')?'hipsRun':'skirt';
const shot=(keep)=>{g.clearRect(0,0,1024,1024);const sv={};for(const b of all){sv[b]=rig.alpha[b];if(!keep.includes(b))rig.alpha[b]=0}const LL=rig.def.legs;if(!keep.includes('legFar'))rig.def.legs=null;rig.draw(g,rig.def.refOrigin[0],rig.def.refOrigin[1],1,1);rig.def.legs=LL;for(const b of all)rig.alpha[b]=sv[b];return c.toDataURL('image/png')};   // 다리는 alpha 를 안 따름 → 치마만 그릴 땐 legs 를 잠깐 비움
const VX=mode==='satk'?0:620;for(let i=0;i<120;i++)an.update(1/60,{vx:VX,facing:1});
if(mode==='ratk'||mode==='satk')an.attack('smash');
for(let i=0;i<n;i++){const lp=rig.legPose,th={};for(const s of ['near','far']){const q=lp[s];th[s]=+(Math.atan2(q.knee[0]-q.hip[0],q.knee[1]-q.hip[1])*180/Math.PI).toFixed(1)}
 const sk=rig.alpha[SK]??1;out.push({t:+(i/60).toFixed(3),th,sk,legs:shot(['legFar','legNear']),skirt:shot([SK]),full:i%5==0?shot(all):null});an.update(1/60,{vx:mode==='run'?VX:0,facing:1})}
return out}"""
def arr(d): return np.array(Image.open(io.BytesIO(base64.b64decode(d.split(',')[1]))).convert('RGBA'))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.goto(f'http://127.0.0.1:{port}/assets/rig/bruno-neon/source/tools/view.html?pre=0')
    pg.wait_for_function("document.title==='done'||document.title.startsWith('ERR')", timeout=20000)
    for mode in ('run', 'ratk', 'satk'):
        rows = pg.evaluate(JS, [N if mode == 'run' else 60, mode]); worst = []; ths = []
        for r in rows:
            L = arr(r['legs'])[..., 3] > 64; S = arr(r['skirt'])[..., 3] > 64
            if not S.any() or r["sk"] < .5: worst.append(0); ths.append(r["th"]); continue
            ys, xs = np.nonzero(S); x0, x1 = xs.min(), xs.max(); yb = np.full(1024, -1)
            for x in range(x0, x1 + 1):
                c = np.nonzero(S[:, x])[0]
                if len(c): yb[x] = c.max()
            hem = int(np.median(yb[x0:x1 + 1][yb[x0:x1 + 1] > 0])); ybf = yb.copy(); ybf[:x0] = yb[x0]; ybf[x1 + 1:] = yb[x1]; ybf[ybf < 0] = hem   # 치마 밖 열은 가까운 치마 끝 열의 아래 끝(단 선을 옆으로 늘임)
            yy_ = np.arange(1024)[:, None]; xx_ = np.arange(1024)[None, :]
            out_ = L & ~S & (yy_ < ybf[None, :] - 2) & (yy_ > ys.min())   # 치마 단 선(옆은 끝 열 단 높이로 늘임)보다 위인데 치마 밖 = 치마 옆으로 튀어나온 다리
            worst.append(int(out_.sum())); ths.append(r['th'])
        thn = [t['near'] for t in ths]; thf = [t['far'] for t in ths]
        print(f'{mode}: 치마 밖 다리 px 최대 {max(worst)} · 평균 {np.mean(worst):.0f} · 0 인 프레임 {sum(1 for w in worst if w == 0)}/{len(worst)} · 허벅지 각 가까운 {min(thn)}~{max(thn)} · 먼 {min(thf)}~{max(thf)}')
        if OUT and mode == 'run':
            fr = [arr(r['full']) for r in rows if r['full']]; W = Image.new('RGBA', (len(fr) * 300, 330), (52, 67, 122, 255))
            for i, f in enumerate(fr): im = Image.fromarray(f).crop((330, 640, 630, 970)); W.alpha_composite(im, (i * 300, 0))
            W.convert('RGB').save(OUT)
    b.close()
srv.shutdown()
