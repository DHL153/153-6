# 둘시네 내려찍기 프레임 표 (12 네온: 러스트 tools/frame_table.py 복사 — RID=dulcinea-rust 로 러스트도) — 실제 rig.def 동작을 1/60(또는 STEP)씩 돌려 팔마다 늘임·펴짐·손목·윗팔 각·얼굴 겹침을 잼
#   python3 tools/frame_table.py [vx=0] [t0=0] [t1=1] [step=1/60]   → 판정 어긋난 프레임은 끝에 ✗ 표시
#   판정: 늘임 0.98~1.02 · 빈틈 ≤0.5 · 손목 ±47° · 펴짐 ≤0.92(잡은 동안) · 가까운 윗팔 35~160°, 먼 윗팔 0~175° · 팔꿈치·주먹 얼굴 밖
import sys, time, socket, subprocess, os, json, math
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ID = os.environ.get('RID', 'dulcinea-neon'); VX = float(sys.argv[1]) if len(sys.argv) > 1 else 0; T0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0
T1 = float(sys.argv[3]) if len(sys.argv) > 3 else 1; STEP = eval(sys.argv[4]) if len(sys.argv) > 4 else 1 / 60
FACEBOX = '[[-55,-345],[140,-345],[140,-140],[-55,-140]]' if ID == 'dulcinea-rust' else '[[-46,-400],[154,-400],[154,-140],[-46,-140]]'   # 얼굴 상자(대기 골반 기준 리그 px)
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d=MR_RIG_DEFS['{ID}'];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src}})));
const IM=Object.fromEntries(ims);const inv=m=>{{const q=m[0]*m[3]-m[1]*m[2];return [m[3]/q,-m[1]/q,-m[2]/q,m[0]/q,(m[2]*m[5]-m[3]*m[4])/q,(m[1]*m[4]-m[0]*m[5])/q]}};
const ap=(m,x,y)=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]];
let FACE=null;{{const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<60;i++)an.update(1/120,{{vx:0}});
 const H=rig.by.hip.m,iH=inv(rig.by.head.m);FACE={FACEBOX}.map(p=>ap(iH,H[4]+p[0],H[5]+p[1]))}}
window.run=(vx,T0,T1,step)=>{{const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<240;i++)an.update(1/120,{{vx}});an.attack('smash');
 const out=[];let t=0;const P=(b,x,y)=>{{const m=rig.by[b].wm||rig.by[b].m;return [m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]}};
 const pt=b=>{{if(!rig.by[b])return null;const pn=rig.swap[b]||rig.by[b].part,p=d.parts[pn];if(!p)return null;const q=p.grip||p.fist||p.pivot,k=p.scale||1;return P(b,(q[0]-p.pivot[0])*k,(q[1]-p.pivot[1])*k)}};
 const el=b=>{{if(!rig.by[b])return null;const pn=rig.swap[b]||rig.by[b].part,p=d.parts[pn];if(!p||!p.elbow)return null;const k=p.scale||1;return P(b,(p.elbow[0]-p.pivot[0])*k,(p.elbow[1]-p.pivot[1])*k)}};
 while(an.act){{const tt=an.act.t;if(tt>=T0-1e-9&&tt<=T1+1e-9){{const Hd=rig.by.head.m,H=rig.by.hip.m;
   out.push({{t:tt,stN:an.stN||0,stF:an.stF||0,wrN:an.wrN||0,wrF:an.wrF||0,gN:an.gapN||0,gF:an.gapF||0,reach:an.reachV===undefined?null:an.reachV,
    SN:(m=>[m[4],m[5]])(rig.by.armF.wm||rig.by.armF.m),SF:(m=>[m[4],m[5]])(rig.by.armU.wm||rig.by.armU.m),eN:el('foreFf'),eF:el('armLf'),fN:pt('foreF'),fF:pt('armL'),
    pN:rig.swap.foreF||rig.by.foreF.part,pF:rig.swap.armL||rig.by.armL.part,face:FACE.map(p=>ap(Hd,p[0],p[1])),hip:[H[4],H[5]],aF:rig.alpha.armLf}})}}
  an.update(step,{{vx}});t+=step;if(t>3)break}}
 return out}};window.ready=1}})()</script>'''
open(os.path.join(root, '_ft.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_ft.html'); pg.wait_for_function('window.ready', timeout=30000)
        R = pg.evaluate('([v,a,b_,s])=>run(v,a,b_,s)', [VX, T0, T1, STEP]); b.close()
        if errs: print('errors', errs[:5])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_ft.html'))
LN, LF = (202.3, 188.8) if ID == 'dulcinea-rust' else (186.5, 183.8)   # 팔 길이(리그): 먼 팔 어깨→팔꿈치→쥔 점 · 가까운 팔 어깨→팔꿈치→주먹 (build 출력)
def inside(poly, q, m=0):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    return q is not None and min(xs) - m <= q[0] <= max(xs) + m and min(ys) - m <= q[1] <= max(ys) + m
ang = lambda a, b_: math.degrees(math.atan2(b_[1] - a[1], b_[0] - a[0]))
H = lambda r, q: '%4d,%4d' % (q[0] - r['hip'][0], q[1] - r['hip'][1]) if q else '   -    '
bad = 0
print('    t   | 먼팔 늘임 펴짐 손목 윗팔각 | 가까운 늘임 펴짐 손목 윗팔각 | 먼 주먹      가까운 주먹 | 조각')
for r in R:
    f = []; grip = r['aF'] is not None and r['aF'] > .5   # 가까운 손이 자루를 잡은 동안(팔뚝 armLf 보임)
    wN, wF = math.degrees(r['wrN']), math.degrees(r['wrF'])
    rN = math.dist(r['SN'], r['fN']) / LN; rF = math.dist(r['SF'], r['fF']) / LF
    aN = ang(r['SN'], r['eN']) if r['eN'] else 0; aF = ang(r['SF'], r['eF']) if r['eF'] else 0
    if not (.98 <= r['stN'] <= 1.02): f.append('늘임N')
    if grip and not (.98 <= r['stF'] <= 1.02): f.append('늘임F')
    if r['gN'] > .5 or (grip and r['gF'] > .5): f.append('빈틈')
    if abs(wN) > 47: f.append('손목N')
    if grip and abs(wF) > 47: f.append('손목F')
    if rN > .92: f.append('펴짐N')
    if grip and rF > .92: f.append('펴짐F')
    if grip and not 35 <= aF <= 160: f.append('윗팔F')
    if not 0 <= aN <= 175: f.append('윗팔N')
    if inside(r['face'], r['eN'], 8) or (grip and inside(r['face'], r['eF'], 8)): f.append('팔꿈치얼굴')
    bad += bool(f)
    print(f"{r['t']:.4f} | {r['stN']:.2f} {rN:.2f} {wN:4.0f} {aN:5.0f} | {r['stF']:.2f} {rF:.2f} {wF:4.0f} {aF:5.0f} {'잡' if grip else '  '} | {H(r, r['fN'])} {H(r, r['fF'])} | {r['pN']:6} {r['pF']:6} {'✗ ' + ' '.join(f) if f else ''}" + (f" | eN {H(r, r['eN'])} SN {H(r, r['SN'])}" if os.environ.get('EN') else ''))
print('frames', len(R), 'bad', bad)
