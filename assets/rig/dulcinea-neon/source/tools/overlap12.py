# 12 네온 둘시네: 공격 1/60 마다 부품 무리끼리 겹침 px(그리는 순서를 바꿀 때 '바뀌는 순간 겹치지 않는 시각' 찾기) — 10-20 DHL 11:45 '손·무기를 다리 뒤로'
#   python3 -I tools/overlap12.py [vx=0]   → 표: t · 주먹∩다리 · 주먹∩골반 · 주먹∩상체 · 주먹∩머리 · 망치∩다리 · 망치∩골반 · 망치∩상체 · 망치∩머리 · 팔∩다리
import sys, time, socket, subprocess, os, json
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ID = 'dulcinea-neon'; VX = float(sys.argv[1]) if len(sys.argv) > 1 else 0
G = {'FIST': ['fistF', 'foreF', 'gFart', 'gFart2', 'gFh'], 'ARM': ['afFart', 'afFart2', 'auFart'], 'WEAP': ['weapon', 'weaponA'],
     'LEGS': ['bootFFoot', 'bootFShin', 'bootNFoot', 'bootNShin', 'rboot', 'rshin', 'rthighF', 'rthighN', 'thighF', 'thighN'], 'HIPS': ['hips'], 'TORSO': ['torso'], 'HEAD': ['head']}
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d=MR_RIG_DEFS['{ID}'];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src+'?x={time.time()}'}})));
const IM=Object.fromEntries(ims);const G={json.dumps(G)};const clr=im=>{{const c=document.createElement('canvas');c.width=im.width;c.height=im.height;return c}};
const names=Object.keys(G);const sets=names.map(n=>{{const o={{}};for(const k in IM)o[k]=(G[n].includes(k)||(n==='HEAD'&&(k.startsWith('face')||k.startsWith('blink'))))?IM[k]:clr(IM[k]);return o}});
window.run=(vx)=>{{const R=sets.map(s=>new CharacterRig(d,s)),A=R.map(r=>new RunAnimator(r,{{runSpeed:620}}));for(let i=0;i<240;i++)A.forEach(a=>a.update(1/120,{{vx}}));A.forEach(a=>a.attack('smash'));
 const c=document.createElement('canvas');c.width=900;c.height=900;const g=c.getContext('2d',{{willReadFrequently:true}});const out=[];
 while(A[0].act){{const t=A[0].act.t;const M={{}};names.forEach((n,i)=>{{g.clearRect(0,0,900,900);R[i].draw(g,330,860,.8,1);const D=g.getImageData(0,0,900,900).data;const m=new Uint8Array(900*900);for(let j=0;j<m.length;j++)m[j]=D[j*4+3]>60?1:0;M[n]=m}});
  const ov=(a,b)=>{{let s=0;const x=M[a],y=M[b];for(let j=0;j<x.length;j++)s+=x[j]&y[j];return s}};
  out.push({{t,order:(A[0].act&&A[0].act.orderKey)||'',v:[ov('FIST','LEGS'),ov('FIST','HIPS'),ov('FIST','TORSO'),ov('FIST','HEAD'),ov('WEAP','LEGS'),ov('WEAP','HIPS'),ov('WEAP','TORSO'),ov('WEAP','HEAD'),ov('ARM','LEGS'),ov('ARM','HIPS'),ov('WEAP','ARM'),ov('FIST','ARM'),ov('ARM','TORSO')]}});
  A.forEach(a=>a.update(1/60,{{vx}}))}}return out}};window.ready=1}})()</script>'''
open(os.path.join(root, '_ov.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_ov.html'); pg.wait_for_function('window.ready', timeout=30000)
        R = pg.evaluate('v=>run(v)', VX); b.close()
        if errs: print('errors', errs[:3])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_ov.html'))
print('   t   주먹:다리 골반 상체 머리 | 망치:다리 골반 상체 머리 | 팔:다리 골반 | 망치∩팔 주먹∩팔 팔∩상체')
last = None
for r in R:
    if last is not None and abs(r['t'] - last) < 1e-6: continue
    last = r['t']; v = r['v']; print(f"{r['t']:.3f}  {v[0]:5d} {v[1]:5d} {v[2]:5d} {v[3]:5d} | {v[4]:5d} {v[5]:5d} {v[6]:5d} {v[7]:5d} | {v[8]:5d} {v[9]:5d} | {v[10]:5d} {v[11]:5d} {v[12]:5d}")
