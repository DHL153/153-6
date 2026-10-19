# 둘시네 두 손 자세 풀이 — 엔진(rig.js) 그대로 돌려서 고름: python3 tools/pose_search.py spec.json [out.json]
#  spec = {"T":0.2, "consts":{트랙: 값 ...}, "gx":[a,b,step], "gy":[a,b,step], "sa":[...], "sF":[...], "sides":[[N,F],...], "pref":[gx,gy], "top":8}
#  판정(하나라도 어기면 탈락): 늘임 0.98~1.02 · 빈틈 0 · 손목 들어가는 각 ±47° · 펴짐(어깨~손 / 팔 길이) 0.45~0.88(팔꿈치가 보이게 굽음)
#   · 가까운 윗팔은 어깨에서 아래로(35~160°, 어깨갑 밑에서 나옴) · 먼 윗팔도 어깨보다 아래(0~175°) · 두 팔꿈치·두 주먹이 얼굴 상자 밖 · 먼 팔뚝이 얼굴을 안 지남
#  엔진 'N' = 둘시네 먼 팔(armF·foreF·foreFf), 'F' = 가까운 팔(armU·armL·armLf)
import sys, time, socket, subprocess, os, json, math
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ID = 'dulcinea-rust'; spec = json.load(open(sys.argv[1]))
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const base=MR_RIG_DEFS['{ID}'];const ims=await Promise.all(Object.entries(base.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src}})));
const IM=Object.fromEntries(ims);
const inv=m=>{{const d=m[0]*m[3]-m[1]*m[2];return [m[3]/d,-m[1]/d,-m[2]/d,m[0]/d,(m[2]*m[5]-m[3]*m[4])/d,(m[1]*m[4]-m[0]*m[5])/d]}};
const ap=(m,x,y)=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]];
// 쉬는 자세 얼굴 상자(골반 기준 x −55..140, y −345..−140) → 머리 좌표
let FACE=null;{{const rig=new CharacterRig(JSON.parse(JSON.stringify(base)),IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<60;i++)an.update(1/120,{{vx:0}});
 const H=rig.by.hip.m,Hd=rig.by.head.m,iH=inv(Hd);FACE=[[-55,-345],[140,-345],[140,-140],[-55,-140]].map(p=>{{const w=[H[4]+p[0],H[5]+p[1]];return ap(iH,w[0],w[1])}})}}
window.evalSet=(T,consts,cands)=>{{const out=[];const d=JSON.parse(JSON.stringify(base));const A=d.actions.smash;
 for(const [k,v] of Object.entries(consts))A[k]=v;
 for(const c of cands){{A.gx=[[0,c[0]]];A.gy=[[0,c[1]]];A.sa=[[0,c[2]]];A.sF=[[0,c[3]]];A.ikSideK={{N:[[0,c[4]]],F:[[0,c[5]]]}};
  const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<30;i++)an.update(1/120,{{vx:0}});an.attack('smash');
  let n=0;while(an.act&&an.act.t<T-1e-6&&n<400){{an.update(1/60,{{vx:0}});n++}}
  const P=(b,x,y)=>{{const m=rig.by[b].wm||rig.by[b].m;return [m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]}};
  const pt=b=>{{const pn=rig.swap[b]||rig.by[b].part,p=d.parts[pn];if(!p)return null;const q=p.grip||p.fist||p.pivot,k=p.scale||1;return P(b,(q[0]-p.pivot[0])*k,(q[1]-p.pivot[1])*k)}};
  const el=b=>{{const pn=rig.swap[b]||rig.by[b].part,p=d.parts[pn];if(!p||!p.elbow)return null;const k=p.scale||1;return P(b,(p.elbow[0]-p.pivot[0])*k,(p.elbow[1]-p.pivot[1])*k)}};
  const Hd=rig.by.head.m,face=FACE.map(p=>ap(Hd,p[0],p[1])),H=rig.by.hip.m;
  out.push({{c,stN:an.stN||0,stF:an.stF||0,wrN:an.wrN||0,wrF:an.wrF||0,gN:an.gapN||0,gF:an.gapF||0,SN:[rig.by.armF.wm[4],rig.by.armF.wm[5]],SF:[rig.by.armU.wm[4],rig.by.armU.wm[5]],
   eN:el('foreFf'),eF:el('armLf'),fN:pt('foreF'),fF:pt('armL'),face,hip:[H[4],H[5]],tip:rig.partPoint('weapon',...d.parts.weapon.tip)}})}}
 return out}};window.ready=1}})()</script>'''
open(os.path.join(root, '_ps.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
fr = lambda a: [a[0] + i * a[2] for i in range(int(round((a[1] - a[0]) / a[2])) + 1)]
cands = [[x, y, sa, sf, sd[0], sd[1]] for x in fr(spec['gx']) for y in fr(spec['gy']) for sa in spec['sa'] for sf in spec['sF'] for sd in spec.get('sides', [[1, 1], [1, -1], [-1, 1], [-1, -1]])]
R = []
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_ps.html'); pg.wait_for_function('window.ready', timeout=30000)
        for i in range(0, len(cands), 400): R += pg.evaluate('([T,c,cs])=>evalSet(T,c,cs)', [spec.get('T', .2), spec.get('consts', {}), cands[i:i + 400]])
        b.close()
        if errs: print('errors', errs[:5])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_ps.html'))
LN, LF = 202.3, 188.8
def inside(poly, q, m=0):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]   # 머리 기울기가 작아 축 정렬 상자로 충분(가장자리 m 만큼 넓힘)
    return min(xs) - m <= q[0] <= max(xs) + m and min(ys) - m <= q[1] <= max(ys) + m
def seg_hits(poly, a, b_, m=0):
    return any(inside(poly, (a[0] + (b_[0] - a[0]) * t / 20, a[1] + (b_[1] - a[1]) * t / 20), m) for t in range(21))
ang = lambda a, b_: math.degrees(math.atan2(b_[1] - a[1], b_[0] - a[0]))
good = []
for r in R:
    f = []
    if r['gN'] > .5 or r['gF'] > .5: f.append('gap')
    if not (.98 <= r['stN'] <= 1.02 and .98 <= r['stF'] <= 1.02): f.append('st')
    wN, wF = math.degrees(r['wrN']), math.degrees(r['wrF'])
    if abs(wN) > spec.get('wrN', spec.get('wr', 47)) or abs(wF) > spec.get('wrF', spec.get('wr', 47)): f.append('wr')   # wrN = 엔진 N(둘시네 먼 손) · wrF = 가까운 손
    rN = math.dist(r['SN'], r['fN']) / LN; rF = math.dist(r['SF'], r['fF']) / LF
    if not (spec.get('rmin', .45) <= rN <= spec.get('rmax', .88) and spec.get('rmin', .45) <= rF <= spec.get('rmax', .88)): f.append('r')
    aF = ang(r['SF'], r['eF']); aN = ang(r['SN'], r['eN'])
    if not 35 <= aF <= 160: f.append('nearUp')
    if not 0 <= aN <= 175: f.append('farUp')
    fc = r['face']
    if inside(fc, r['eN'], 8) or inside(fc, r['eF'], 8): f.append('elbowFace')
    if inside(fc, r['fN'], 18) or inside(fc, r['fF'], 18): f.append('fistFace')
    if seg_hits(fc, r['eN'], r['fN'], 6): f.append('foreFace')
    if spec.get('headFace') is not None:   # 망치 쇠 머리(무기 그림 y 15~270 = 쥔 점에서 180~435, 폭 −184~206)가 얼굴 상자에 겹침
        _g = r['fN']; _t = r['tip']; _L = math.dist(_g, _t) or 1; _u = ((_t[0] - _g[0]) / _L, (_t[1] - _g[1]) / _L); _v = (-_u[1], _u[0])
        if any(inside(fc, (_g[0] + _u[0] * tt + _v[0] * ss, _g[1] + _u[1] * tt + _v[1] * ss), spec['headFace']) for tt in range(180, 436, 25) for ss in range(-180, 207, 40)): f.append('headFace')
    if spec.get('shaftFace') and seg_hits(fc, r['fF'], r['tip'], spec['shaftFace']): f.append('shaftFace')   # 자루(가까운 주먹→쇠 머리)가 얼굴 상자를 지남 — 망치 맨 앞 레이어일 때
    f = [x for x in f if x not in spec.get('allow', [])]
    r.update(rN=rN, rF=rF, aN=aN, aF=aF, wN=wN, wF=wF, flags=f)
    if True:
        r.setdefault('rN', rN)
    if not f:
        pr = spec.get('pref', r['c'][:2])
        r['score'] = abs(rN - .7) * 60 + abs(rF - .7) * 60 + (abs(wN) + abs(wF)) * .4 + math.hypot(r['c'][0] - pr[0], r['c'][1] - pr[1]) * .25 + abs(r['c'][2] - spec.get('saPref', r['c'][2])) * 40
        good.append(r)
good.sort(key=lambda r: r['score'])
if spec.get('dump'):
    Hh = lambda r, q: [round(q[0] - r['hip'][0]), round(q[1] - r['hip'][1])] if q else None
    for r in R: print('  ', r['c'], 'rN %.2f rF %.2f wN %d wF %d aN %d aF %d' % (r['rN'], r['rF'], r['wN'], r['wF'], r['aN'], r['aF']), 'SN', Hh(r, r['SN']), 'SF', Hh(r, r['SF']), 'eN', Hh(r, r['eN']), 'eF', Hh(r, r['eF']), 'gap %.0f %.0f' % (r['gN'], r['gF']), r['flags'])
from collections import Counter
print('cands', len(R), 'good', len(good), 'fails', Counter(x for r in R for x in r['flags']).most_common())
if spec.get('diag'):
    for k_ in spec['diag']:
        sub = [r for r in R if set(r['flags']) <= {k_}]
        print(' only', k_, len(sub), sorted([(round(r['rN'], 2), round(r['rF'], 2), round(r['wN']), round(r['wF']), r['c']) for r in sub], key=lambda t: max(t[0], t[1]))[:6])
H = lambda r, q: [round(q[0] - r['hip'][0]), round(q[1] - r['hip'][1])]
for r in good[:spec.get('top', 8)]:
    print(f"  G {r['c'][0]:4} {r['c'][1]:4} sa {r['c'][2]:5} sF {r['c'][3]} side {r['c'][4]:2},{r['c'][5]:2} | rN {r['rN']:.2f} rF {r['rF']:.2f} wN {r['wN']:4.0f} wF {r['wF']:4.0f} | aN {r['aN']:4.0f} aF {r['aF']:4.0f} | eN {H(r, r['eN'])} eF {H(r, r['eF'])} fN {H(r, r['fN'])} fF {H(r, r['fF'])} tip {H(r, r['tip'])} | {r['score']:.1f}")
if len(sys.argv) > 2: json.dump(good[:5000], open(sys.argv[2], 'w'))
