# 7 루시아 달리기 다리 재기·그림 (10-20 22:1x, DHL 21:44 '다리가 너무 구부러짐')
#   python3 -I tools/legprobe7.py OUT.png RID ['{"gait":{...},"legs":{...},"draw":[...]}']  → 프레임마다 무릎 굽힘(°)·다리 기울기(°)·펴짐(d/L) 표 + 다리 그림 줄
#   덮어쓰기 JSON: gait·legs 는 키별로 합침(legs.near/far 도), 나머지는 통째로 바꿈 — 빌드 전에 값 고르기용
import sys, time, socket, subprocess, base64, io, os, json, math
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
out = sys.argv[1]; ID = sys.argv[2] if len(sys.argv) > 2 else 'lucia-sky'; OV = sys.argv[3] if len(sys.argv) > 3 else '{}'
N = int(os.environ.get('N', 24)); SC = float(os.environ.get('SC', .6)); VX = float(os.environ.get('VX', 620)); HZ = float(os.environ.get('HZ', 0))
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d=JSON.parse(JSON.stringify(MR_RIG_DEFS['{ID}']));const ov={OV};
 for(const k in ov){{if(k==='gait'||k==='legs'){{d[k]=d[k]||{{}};for(const j in ov[k]){{if((j==='near'||j==='far')&&typeof ov[k][j]==='object')Object.assign(d[k][j],ov[k][j]);else d[k][j]=ov[k][j]}}}}else d[k]=ov[k]}}
 const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src}})));const IM=Object.fromEntries(ims);
 window.run=(N,sc)=>{{const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:{VX}}});const s={{vx:{VX}}};if({HZ}>0)s.stepHz={HZ};for(let i=0;i<240;i++)an.update(1/120,s);const o=[];
  for(let i=0;i<N;i++){{an.update(1/60,s);const c=document.createElement('canvas');c.width=Math.round(1040*sc/.9);c.height=Math.round(1120*sc/.9);const g=c.getContext('2d');rig.draw(g,c.width/2,c.height-20,sc,1);
   const P=rig.legPose;const L=d.legs;const ll=s_=>an._legLen?an._legLen(s_):[L.thigh,L.shin];o.push({{img:c.toDataURL(),P:JSON.parse(JSON.stringify(P)),LL:{{near:ll('near'),far:ll('far')}},st:an.stance}})}}return o}};window.ready=1}})()</script>'''
open(os.path.join(root, f'_lp{os.getpid()}.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); pg.on('console', lambda m: print('JS', m.text) if m.type == 'error' else None)
        pg.goto(f'http://127.0.0.1:{port}/_lp{os.getpid()}.html'); pg.wait_for_function('window.ready', timeout=30000)
        R = pg.evaluate('([n,s])=>run(n,s)', [N, SC]); b.close()
finally:
    srv.terminate(); os.remove(os.path.join(root, f'_lp{os.getpid()}.html'))
ang = lambda a, b: math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
bend = {'near': [], 'far': []}; slant = {'near': [], 'far': []}; ext = {'near': [], 'far': []}
for r in R:
    for sd in ('near', 'far'):
        P = r['P'][sd]; h, k, a = P['hip'], P['knee'], P['ankle']
        bd = abs(((ang(k, a) - ang(h, k)) + 180) % 360 - 180); bend[sd].append(bd); slant[sd].append((ang(h, a) - 90 + 180) % 360 - 180)
        ext[sd].append(math.hypot(a[0] - h[0], a[1] - h[1]) / sum(r['LL'][sd]))
for sd in ('near', 'far'):
    print(f"  {sd:4s} 무릎 굽힘 {min(bend[sd]):4.0f}~{max(bend[sd]):4.0f}° (평균 {sum(bend[sd]) / len(bend[sd]):4.0f}) · 기울기 {min(slant[sd]):+4.0f}~{max(slant[sd]):+4.0f}° · 펴짐 {min(ext[sd]):.2f}~{max(ext[sd]):.2f} · 다리 {[round(v, 1) for v in R[-1]['LL'][sd]]}")
print('  stance', round(R[-1]['st'], 3))
if os.environ.get('SIDE'):   # 무릎이 엉덩이→발목 선의 앞(+, 진행 방향 오른쪽)인지 뒤(−)인지 — 프레임마다 (17 네온 DHL 12:27 '무릎이 갑자기 반대편')
    for j, r in enumerate(R):
        row = []
        for sd in ('near', 'far'):
            P = r['P'][sd]; h, k, a = P['hip'], P['knee'], P['ankle']; cr = (a[0] - h[0]) * (k[1] - h[1]) - (a[1] - h[1]) * (k[0] - h[0])
            d = math.hypot(a[0] - h[0], a[1] - h[1]) or 1; row.append(f"{sd} {'앞' if cr < 0 else '뒤'} {abs(cr) / d:5.1f}px 굽힘 {bend[sd][j]:4.0f} 펴짐 {ext[sd][j]:.2f} 발목dx {a[0] - h[0]:+6.1f}")
        print(f'   {j:2d} ' + ' | '.join(row))
if os.environ.get('DBG'):
    for j, r in enumerate(R):
        P = r['P'][os.environ.get('DBG') if os.environ.get('DBG') in ('near', 'far') else 'near']; h, k, a = P['hip'], P['knee'], P['ankle']; print(f"   {j:2d} 엉덩이 y {h[1]:6.1f} 발목 y {a[1]:6.1f} dx {a[0] - h[0]:+6.1f} 굽힘 {bend['near'][j]:4.0f} 펴짐 {ext['near'][j]:.2f} 발 각 {math.degrees(P.get('foot', 0)):+5.0f}° 듦 {P.get('lift', 0):5.1f} 정강이↔부츠 {(math.degrees(math.atan2(a[1] - k[1], a[0] - k[0])) - math.degrees(P.get('foot', 0)) - 90 + 180) % 360 - 180:+5.0f}°")
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
ims = [Image.open(io.BytesIO(base64.b64decode(r['img'].split(',')[1]))).convert('RGBA') for r in R]
w, h = ims[0].size; y0 = int(h * float(os.environ.get('Y0', .42))); x0, x1 = int(w * float(os.environ.get('X0', .2))), int(w * float(os.environ.get('X1', .8))); step = int(os.environ.get('STEP', 3)); sel = list(range(0, N, step))
W = Image.new('RGB', ((x1 - x0) * len(sel), h - y0), 'white')
for i, j in enumerate(sel):
    bg = Image.new('RGBA', ims[j].size, (255, 255, 255, 255)); bg.alpha_composite(ims[j]); t = bg.crop((x0, y0, x1, h)).convert('RGB')
    ImageDraw.Draw(t).text((4, 4), f'{j}/60 n{bend["near"][j]:.0f} f{bend["far"][j]:.0f}', fill='red', font=f); W.paste(t, (i * (x1 - x0), 0))
W.save(out); print(out, W.size)
