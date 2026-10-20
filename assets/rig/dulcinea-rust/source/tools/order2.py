# 2 러스트 둘시네(10-20 18:32 DHL '같이 진행' — 12 v1.4 앞뒤 규칙을 2 에도): 그리는 순서 바꾸기 시험 (12 order12.py 복사) — 지금 rig.def.js 와 '바꾼 순서(DEFX json)'를 대기·달리기·공격(서서·달리다) 1/60 마다 그려 견줌
#   (10-20 12:18 DHL ①달리기·대기 = 먼 주먹·망치가 다리 뒤 ②공격 = 손·망치가 머리 뒤 ③공격 = 손·망치가 다리 뒤)
#   python3 -I tools/order2.py VARIANT.json [OUTDIR]
#     VARIANT.json = {"draw":[...], "drawA":[...], ..., "order":[[t,"drawA"],...]}   ("order" 는 actions.smash.order 로 들어감)
#   표: 장면 · t · 바뀐 px(지금 vs 바꾼 순서) · 겹침 px(주먹∩다리·골반·상체·머리 / 망치∩… / 팔뚝∩다리·골반 / 상체∩다리·골반) · 주먹 넓이
#   OUTDIR 이 있으면 SAVE="stand:0,run:.2,atk0:.2" 장면의 지금|바꾼 그림을 나란히 PNG 로
import sys, time, socket, subprocess, os, json, base64, io
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ID = 'dulcinea-rust'
VAR = json.load(open(sys.argv[1])); OUT = sys.argv[2] if len(sys.argv) > 2 else None
SAVE = [(s.split(':')[0], float(s.split(':')[1])) for s in os.environ.get('SAVE', '').split(',') if ':' in s]
G = {'FIST': ['fistF', 'gFart', 'gFart2', 'gFh'], 'FORE': ['foreF', 'afFart', 'afFart2', 'auFart'], 'WEAP': ['weapon', 'weaponA'],
     'LEGS': ['bootFFoot', 'bootFShin', 'bootNFoot', 'bootNShin', 'rboot', 'rshin', 'rthighF', 'rthighN', 'rknee', 'thighF', 'thighN'],
     'HIPS': ['hips', 'belt', 'flapN', 'flapC'], 'TORSO': ['torso'], 'HEAD': ['head'], 'PONY': ['pony']}
PAIRS = [('FIST', 'LEGS'), ('FIST', 'HIPS'), ('FIST', 'TORSO'), ('FIST', 'HEAD'), ('WEAP', 'LEGS'), ('WEAP', 'HIPS'), ('WEAP', 'TORSO'), ('WEAP', 'HEAD'),
         ('FORE', 'LEGS'), ('FORE', 'HIPS'), ('FORE', 'TORSO'), ('FORE', 'HEAD'), ('FORE', 'WEAP'), ('WEAP', 'PONY'), ('FIST', 'PONY'), ('TORSO', 'LEGS'), ('FIST', 'FIST')]
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d0=MR_RIG_DEFS['{ID}'];const V={json.dumps(VAR)};const d1=JSON.parse(JSON.stringify(d0));for(const k in V){{if(k==='order')d1.actions.smash.order=V[k];else d1[k]=V[k]}}
const ims=await Promise.all(Object.entries(d0.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src+'?x={time.time()}'}})));
const IM=Object.fromEntries(ims);const G={json.dumps(G)};const PAIRS={json.dumps(PAIRS)};const clr=im=>{{const c=document.createElement('canvas');c.width=im.width;c.height=im.height;return c}};
const names=Object.keys(G);const sets=names.map(n=>{{const o={{}};for(const k in IM)o[k]=(G[n].includes(k)||(n==='HEAD'&&(k.startsWith('face')||k.startsWith('blink'))))?IM[k]:clr(IM[k]);return o}});
const W=900,H=900,X0=430,Y0=850,SC=.8;const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d',{{willReadFrequently:true}});
window.run=(mode,save)=>{{const vx=(mode==='run'||mode==='atk1')?620:0;const atk=mode.startsWith('atk');
 const mk=(d,ims)=>{{const r=new CharacterRig(d,ims),a=new RunAnimator(r,{{runSpeed:620}});for(let i=0;i<240;i++)a.update(1/120,{{vx}});if(atk)a.attack('smash');return [r,a]}};
 const all=[mk(d0,IM),mk(d1,IM),...sets.map(s=>mk(d0,s))];const out=[];const shots={{}};
 for(let f=0;f<(atk?400:60);f++){{const a0=all[0][1];if(atk&&!a0.act)break;const t=atk?a0.act.t:f/60;
  g.clearRect(0,0,W,H);all[0][0].draw(g,X0,Y0,SC,1);const A=g.getImageData(0,0,W,H).data;const cA=save.some(s=>Math.abs(s-t)<.009)?c.toDataURL():null;
  g.clearRect(0,0,W,H);all[1][0].draw(g,X0,Y0,SC,1);const B=g.getImageData(0,0,W,H).data;if(cA)shots[t.toFixed(3)]=[cA,c.toDataURL()];
  let dif=0;for(let j=0;j<A.length;j+=4){{if(Math.abs(A[j]-B[j])+Math.abs(A[j+1]-B[j+1])+Math.abs(A[j+2]-B[j+2])+Math.abs(A[j+3]-B[j+3])>40)dif++}}
  const M={{}};names.forEach((n,i)=>{{g.clearRect(0,0,W,H);all[2+i][0].draw(g,X0,Y0,SC,1);const D=g.getImageData(0,0,W,H).data;const m=new Uint8Array(W*H);for(let j=0;j<m.length;j++)m[j]=D[j*4+3]>60?1:0;M[n]=m}});
  const ov=PAIRS.map(([a,b])=>{{let s=0;const x=M[a],y=M[b];for(let j=0;j<x.length;j++)s+=x[j]&y[j];return s}});
  out.push({{t,dif,ov,ord:(a0.act&&a0.act.orderKey)||''}});all.forEach(([r,a])=>a.update(1/60,{{vx}}))}}
 return [out,shots]}};window.ready=1}})()</script>'''
open(os.path.join(root, '_ord.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
RES = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_ord.html'); pg.wait_for_function('window.ready', timeout=30000)
        for mode in ('stand', 'run', 'atk0', 'atk1'):
            RES[mode] = pg.evaluate('([m,s])=>run(m,s)', [mode, [t for m, t in SAVE if m == mode]])
        b.close()
        if errs: print('errors', errs[:3])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_ord.html'))
hdr = ' '.join(f'{a[:2]}{b[:2]}' for a, b in PAIRS)
for mode, (rows, shots) in RES.items():
    tot = sum(r['dif'] for r in rows); mx = max((r['dif'] for r in rows), default=0)
    print(f'== {mode}: 바뀐 px 합 {tot} · 한 장 최대 {mx}   [{hdr}]')
    last = None
    for r in rows:
        if last is not None and abs(r['t'] - last) < 1e-6: continue
        last = r['t']
        if os.environ.get('ALL') or r['dif'] or any(r['ov'][:10]):
            print(f"{r['t']:.3f} {r['ord']:7} 바뀜 {r['dif']:5d} | " + ' '.join(f'{v:5d}' for v in r['ov']))
    if OUT:
        from PIL import Image
        os.makedirs(OUT, exist_ok=True)
        for t, (a, b_) in shots.items():
            ims = [Image.open(io.BytesIO(base64.b64decode(x.split(',')[1]))).convert('RGBA') for x in (a, b_)]
            bb = ims[0].getbbox() or (0, 0, 900, 900); bb2 = ims[1].getbbox() or bb
            box = (max(0, min(bb[0], bb2[0]) - 10), max(0, min(bb[1], bb2[1]) - 10), min(900, max(bb[2], bb2[2]) + 10), min(900, max(bb[3], bb2[3]) + 10))
            w, h = box[2] - box[0], box[3] - box[1]; sh = Image.new('RGBA', (w * 2 + 10, h), (40, 56, 96, 255))
            for i, im in enumerate(ims): sh.alpha_composite(im.crop(box), (i * (w + 10), 0))
            sh.convert('RGB').save(os.path.join(OUT, f'{mode}_{t}.png'))
