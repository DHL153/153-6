# 17 네온 루시아 공격 1/60 장면 — 편집 툴과 같은 진행(simStep: 달리기 620 → 공격 중 목표 속도 0, 걸음 박자 2000/900)으로 달리다/서서 공격
#   python3 -I tools/atkrun17.py OUT.png [run|stand] ['{"smash":{...}}' 동작 덮어쓰기] → 칸마다 공격 시각 · 다리 그림(서 있는 원화 다리 비율 standW) 표시
#   env: TS="0.05,0.1,..."(공격 시각) · SC(배율 .7) · COLS · CROP="x0,y0,x1,y1"(캔버스 비율, 기본 다리·몸 아래쪽)
#   (DHL 10-21 15:40 '공격 0.33 에 다리를 틀지 말고 이전 다리 모양으로 공격을 끝내고 이동 전에 다리를 틀면')
import sys, time, socket, subprocess, base64, io, os, json
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
out = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else 'run'; OV = sys.argv[3] if len(sys.argv) > 3 else '{}'
TS = [float(v) for v in os.environ.get('TS', ','.join(f'{x / 60:.4f}' for x in range(0, 61, 3))).split(',')]
SC = float(os.environ.get('SC', .7)); ID = os.environ.get('RID', 'lucia-neon')
DEFX = open(os.environ['DEFX']).read() if os.environ.get('DEFX') else '{}'   # rig.def 덮어쓰기(예: draw·drawA 를 다리만/손·도끼만 — 겹침 재기, tools/atkovl17.py)
RAW = os.environ.get('RAW')   # 장면마다 투명 PNG 저장 폴더
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d=JSON.parse(JSON.stringify(MR_RIG_DEFS['{ID}']));const ov={OV};for(const n in ov)Object.assign(d.actions[n],ov[n]);Object.assign(d,{DEFX});
 const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src}})));const IM=Object.fromEntries(ims);
 window.run=(TS,sc,mode)=>{{const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});let vx=0;const dt=1/60;
  const step=(m)=>{{const target=m==='run'&&!an.busy?620:0;vx+=(target-vx)*(1-Math.exp(-6*dt));an.update(dt,{{vx,facing:1,stepHz:m==='run'?2000/900:0}})}};
  for(let i=0;i<180;i++)step(mode);an.attack(d.ui&&d.ui.attack||'smash',d.ui&&d.ui.attackOpts);const o=[];let t=0,k=0;
  for(let i=0;i<600&&k<TS.length;i++){{const at=an.act?an.act.t:null;if(at==null&&i>0)break;   // 타격 멈춤(hitStop) 동안 공격 시각이 안 가므로 프레임 수가 아니라 시각으로
   if(k<TS.length&&at!=null&&at>=TS[k]-1e-6){{const c=document.createElement('canvas');c.width=Math.round(1200*sc);c.height=Math.round(1150*sc);const g=c.getContext('2d');rig.draw(g,c.width/2,c.height-30,sc,1);
     const P=rig.legPose;const rel=s_=>{{const q=P[s_];return Math.round(((Math.atan2(q.ankle[1]-q.knee[1],q.ankle[0]-q.knee[0])-Math.PI/2-q.foot)*180/Math.PI+540)%360-180)}};const bend=s_=>{{const q=P[s_],a1=Math.atan2(q.knee[1]-q.hip[1],q.knee[0]-q.hip[0]),a2=Math.atan2(q.ankle[1]-q.knee[1],q.ankle[0]-q.knee[0]);return Math.round(Math.abs(((a2-a1)*180/Math.PI+540)%360-180))}};o.push({{img:c.toDataURL(),t:at,sw:[P.near.standW??-1,P.far.standW??-1],A:an.A,rel:[rel('near'),rel('far')],bend:[bend('near'),bend('far')]}});k++}}
   step(mode)}}return o}};window.ready=1}})()</script>'''
fn = os.path.join(root, f'_ar{os.getpid()}.html'); open(fn, 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); pg.on('console', lambda m: print('JS', m.text) if m.type == 'error' else None)
        pg.goto(f'http://127.0.0.1:{port}/{os.path.basename(fn)}'); pg.wait_for_function('window.ready', timeout=30000)
        R = pg.evaluate('([t,s,m])=>run(t,s,m)', [TS, SC, MODE]); b.close()
finally:
    srv.terminate(); os.remove(fn)
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15); cols = int(os.environ.get('COLS', 7))
cx0, cy0, cx1, cy1 = [float(v) for v in os.environ.get('CROP', '0.12,0.3,0.8,1').split(',')]
tiles = []
for r in R:
    im = Image.open(io.BytesIO(base64.b64decode(r['img'].split(',')[1]))).convert('RGBA'); W, H = im.size
    if RAW: os.makedirs(RAW, exist_ok=True); im.save(os.path.join(RAW, f"{os.environ.get('TAG', 'f')}_{r['t']:.3f}.png"))
    bg = Image.new('RGBA', im.size, (34, 48, 84, 255)); bg.alpha_composite(im); t = bg.crop((int(W * cx0), int(H * cy0), int(W * cx1), int(H * cy1))).convert('RGB')
    ImageDraw.Draw(t).text((4, 4), f"{r['t']:.3f} 선다리 {r['sw'][0]:.0f}/{r['sw'][1]:.0f} A {r['A']:.2f}", fill=(255, 220, 90), font=f); tiles.append(t)
    print(f"  t {r['t']:.3f} standW near {r['sw'][0]:.2f} far {r['sw'][1]:.2f} A {r['A']:.3f} · 정강이↔부츠 {int(r['rel'][0]):+4d} {int(r['rel'][1]):+4d}° · 굽힘 {int(r['bend'][0]):4d} {int(r['bend'][1]):4d}°")
tw, th = tiles[0].size; G = Image.new('RGB', (tw * cols, th * ((len(tiles) + cols - 1) // cols)), 'white')
for i, t in enumerate(tiles): G.paste(t, ((i % cols) * tw, (i // cols) * th))
G.save(out); print(out, G.size)
