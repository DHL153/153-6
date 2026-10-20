# 22 스카이 둘시네: 먼 어깨를 몸(상체·머리) 뒤에 숨기고 쥔 점을 팔이 닿는 곳으로 — 키 다시 뽑기 (10-20 DHL 10:37 '0.35초 팔 길이가 이상, 원래 리소스 유지하면서')
#   원인: 러스트 v6.4 키를 옮기며 먼 어깨를 몸 밖으로 22~80 밀어냄(러스트는 큰 머리숱이 가렸음) → 네온은 짧은 머리라 윗팔 관(남색 소매 끝)이 목 옆 허공에 떠 보이고,
#         망치가 멀어 팔이 거의 다 펴짐(.35초 .96). 조각 그림(원화 팔뚝·주먹·윗팔)·길이는 그대로 두고 자세만 바꿈.
#   방법(키 시각마다 엔진에서 잼): 몸 실루엣(상체·골반·어깨 보호대·머리)을 그려 거리 변환 → 어깨 후보(상체 기준 좌표 격자) 중 깊이 ≥ DEP 인 곳 →
#         쥔 점 G' = S + (G − S)·min(1, RT·L / |G − S|) (러스트 방향 그대로, 팔 펴짐 ≤ RT) → 팔꿈치(두 관절, 같은 쪽)가 얼굴 상자 밖 → 점수 = |G' − G| + .3|S − S0| 가장 작은 것
#   python3 -I tools/shoulder12.py → attack/keys12b.json(시각별 shL[상체 기준 어깨]·G[골반 기준 쥔 점]) — smash12.py 가 읽음
import sys, time, socket, subprocess, os, json, math, base64, io
import numpy as np, cv2
from PIL import Image
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); root = os.path.abspath(os.path.join(SRC, '..', '..'))
ID = 'dulcinea-sky'; L1, L2 = 74.7, 111.8; LN = L1 + L2
DEP = float(os.environ.get('DEP', 22)); RT = float(os.environ.get('RT', .86)); SH0 = np.array([54.0, -114.0])
WK = float(os.environ.get('WK', 0)); WMAX = float(os.environ.get('WMAX', 40))
TS = [float(v) for v in os.environ.get('TS', '.18,.27,.32,.34,.36,.40,.58,.68,.82').split(',')]
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script><script src="{ID}/rig.def.js?x={time.time()}"></script><script>
(async()=>{{const d=MR_RIG_DEFS['{ID}'];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src='{ID}/'+p.src+'?x={time.time()}'}})));
const IM=Object.fromEntries(ims);const clr=im=>{{const c=document.createElement('canvas');c.width=im.width;c.height=im.height;return c}};const IM3={{}};
for(const k in IM)IM3[k]=['torso','hips','pauldron','head'].includes(k)||k.startsWith('face')||k.startsWith('blink')?IM[k]:clr(IM[k]);
const inv=m=>{{const q=m[0]*m[3]-m[1]*m[2];return [m[3]/q,-m[1]/q,-m[2]/q,m[0]/q,(m[2]*m[5]-m[3]*m[4])/q,(m[1]*m[4]-m[0]*m[5])/q]}};const ap=(m,x,y)=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]];
let FACEL;{{const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<60;i++)an.update(1/120,{{vx:0}});const H=rig.by.hip.m,iH=inv(rig.by.head.m);FACEL=[[-46,-400],[154,-400],[154,-140],[-46,-140]].map(p=>ap(iH,H[4]+p[0],H[5]+p[1]))}}
window.at=(T)=>{{const R=[new CharacterRig(d,IM),new CharacterRig(d,IM3)],A=R.map(r=>new RunAnimator(r,{{runSpeed:620}}));for(let i=0;i<240;i++)A.forEach(a=>a.update(1/120,{{vx:0}}));A.forEach(a=>a.attack('smash'));let n=0;
 while(A[0].act&&A[0].act.t<T-1e-6&&n<8000){{A.forEach(a=>a.update(1/480,{{vx:0}}));n++}}
 const c=document.createElement('canvas');c.width=1000;c.height=1000;const g=c.getContext('2d');R[1].draw(g,500,900,1,1);const rig=R[0];
 const Sm=rig.by.armF.wm||rig.by.armF.m;const P=(b,x,y)=>{{const m=rig.by[b].wm||rig.by[b].m;return [m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]}};const fn=rig.swap.foreFf||rig.by.foreFf.part,fp=d.parts[fn];const E=P('foreFf',(fp.elbow[0]-fp.pivot[0])*(fp.scale||1),(fp.elbow[1]-fp.pivot[1])*(fp.scale||1));
 const pn=rig.swap.foreF||rig.by.foreF.part,pp=d.parts[pn];
 return {{t:A[0].act.t,img:c.toDataURL(),H:rig.by.hip.m,T:rig.by.torso.m,S:[Sm[4],Sm[5]],G:A[0].swordG,E,sa:A[0].swordA,wr:A[0].wrN,fd:pp.foreDir||null,sd:pp.shaftDir||null,pn,face:FACEL.map(p=>ap(rig.by.head.m,p[0],p[1]))}}}};window.ready=1}})()</script>'''
open(os.path.join(root, '_sh.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); pg.goto(f'http://127.0.0.1:{port}/_sh.html'); pg.wait_for_function('window.ready', timeout=30000)
        M = [pg.evaluate('t=>at(t)', t) for t in TS]; b.close()
finally:
    srv.terminate(); os.remove(os.path.join(root, '_sh.html'))
if os.environ.get('DUMP'): json.dump([{k: v for k, v in r.items() if k != 'img'} for r in M], open(os.environ['DUMP'], 'w'))
ap = lambda m, p: np.array([m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]])
def inv(m):
    q = m[0] * m[3] - m[1] * m[2]; return [m[3] / q, -m[1] / q, -m[2] / q, m[0] / q, (m[2] * m[5] - m[3] * m[4]) / q, (m[1] * m[4] - m[0] * m[5]) / q]
def ik_elbow(S, G, side):   # 두 관절: 팔꿈치 = S 에서 L1, G 에서 L2 — side 로 고름
    v = G - S; dd = float(np.linalg.norm(v)); dd = min(dd, L1 + L2 - 1e-3); a = (L1 * L1 - L2 * L2 + dd * dd) / (2 * dd); h = math.sqrt(max(0, L1 * L1 - a * a))
    u = v / np.linalg.norm(v); n = np.array([-u[1], u[0]]); return S + u * a + n * h * side
if os.environ.get('MAP') or os.environ.get('DRY'):   # 상체 기준 좌표에서 몸 깊이 지도(# ≥20 · + ≥12 · . ≥1) — 어깨가 지나갈 길 보기
    for t, r in zip(TS, M):
        im = np.array(Image.open(io.BytesIO(base64.b64decode(r['img'].split(',')[1]))).convert('RGBA')); dist = cv2.distanceTransform((im[..., 3] > 128).astype(np.uint8), cv2.DIST_L2, 5)
        print('t', t, 'x -40..150 (6씩), y -240..-60 (6씩)')
        for y in range(-240, -59, 6):
            row = ''
            for x in range(-40, 151, 6):
                Sw = ap(r['T'], (x, y)); d_ = dist[int(round(900 + Sw[1])), int(round(500 + Sw[0]))]; row += '#' if d_ >= 20 else '+' if d_ >= 12 else '.' if d_ >= 1 else ' '
            print(f'{y:5d} {row}')
    sys.exit()
out = {}; xs = np.arange(-40, float(os.environ.get('XMAX', 140)), 2.0); ys = np.arange(float(os.environ.get('YMIN', -230)), -40, 2.0)
for t, r in zip(TS, M):
    im = np.array(Image.open(io.BytesIO(base64.b64decode(r['img'].split(',')[1]))).convert('RGBA'))
    dist = cv2.distanceTransform((im[..., 3] > 128).astype(np.uint8), cv2.DIST_L2, 5)
    H, T = r['H'], r['T']; iH = inv(H); S0w = np.array(r['S']); G0w = np.array(r['G']); Gcur = G0w.copy()
    _k1 = json.load(open(os.path.join(SRC, 'attack', 'keys12.json')))['G']   # 기준 = 러스트에서 옮긴 쥔 점(gen_keys12) — 여러 번 돌려도 그 자리에서 잼
    if str(t) in _k1 or f'{t:.2f}' in _k1: G0w = ap(H, _k1.get(str(t), _k1.get(f'{t:.2f}')))
    # 지금 팔꿈치 쪽(엔진과 같은 쪽) — 지금 S·G 로 두 해 중 엔진 팔꿈치에 가까운 쪽 대신: side=+1/−1 중 지금 쓰는 해를 지금 자세 E 로 고름(엔진 E 를 안 받았으니 지금 S·G 로 두 해를 그려 얼굴 쪽이 아닌 것)
    face = np.array(r['face']); fx0, fy0 = face.min(0) - 8; fx1, fy1 = face.max(0) + 8
    best = None
    E0w = np.array(r['E']); side_ = min((1, -1), key=lambda sd: float(np.linalg.norm(ik_elbow(S0w, Gcur, sd) - E0w)))
    def wrist(Ew, Gw):   # 손목 꺾임(도): 팔뚝(쥔 점→팔꿈치) 과 주먹 그림이 바라는 팔뚝 방향(foreDir 를 자루 각만큼 돌림) 사이
        if not r['fd']: return 0.0
        a_pref = math.atan2(r['fd'][1], r['fd'][0]) + r['sa'] - math.atan2(r['sd'][1], r['sd'][0]); a = math.atan2(Ew[1] - Gw[1], Ew[0] - Gw[0])
        return math.degrees((a - a_pref + math.pi) % (2 * math.pi) - math.pi)
    print(f"  t {t:.2f} 조각 {r['pn']} 엔진 손목 {math.degrees(r['wr'] or 0):.0f} · 계산 {wrist(E0w, Gcur):.0f} · 쪽 {side_}")
    GR = float(os.environ.get('GR', 0))   # 쥔 점도 격자로 찾음(±GR, 4px) — 0 이면 어깨→쥔 점 선 위에서만 줄임
    dgx, dgy = np.meshgrid(np.arange(-GR, GR + .1, 4.0), np.arange(-GR, GR + .1, 4.0)); DG = np.stack([dgx.ravel(), dgy.ravel()], 1)
    a_pref = (math.atan2(r['fd'][1], r['fd'][0]) + r['sa'] - math.atan2(r['sd'][1], r['sd'][0])) if r['fd'] else None
    SNAT = np.array([54.0, -114.0])
    for x in xs:
        for y in ys:
            Sw = ap(T, (x, y)); cx, cy = int(round(500 + Sw[0])), int(round(900 + Sw[1]))
            if not (0 <= cx < 1000 and 0 <= cy < 1000) or dist[cy, cx] < DEP: continue
            v = G0w - Sw; dv = float(np.linalg.norm(v)); Gl_ = Sw + v * min(1.0, RT * LN / dv)
            GG = Gl_[None] + DG; V = GG - Sw[None]; dd = np.linalg.norm(V, axis=1)
            ok = (dd <= RT * LN + .5) & (dd >= .55 * LN)
            if not ok.any(): continue
            GG, V, dd = GG[ok], V[ok], dd[ok]
            aa = (L1 * L1 - L2 * L2 + dd * dd) / (2 * dd); hh = np.sqrt(np.maximum(0, L1 * L1 - aa * aa)); U = V / dd[:, None]; N = np.stack([-U[:, 1], U[:, 0]], 1)
            EE = Sw[None] + U * aa[:, None] + N * (hh * side_)[:, None]
            if a_pref is not None:
                A_ = np.arctan2(EE[:, 1] - GG[:, 1], EE[:, 0] - GG[:, 0]); WR = np.degrees((A_ - a_pref + np.pi) % (2 * np.pi) - np.pi)
            else: WR = np.zeros(len(GG))
            inE = (EE[:, 0] >= fx0) & (EE[:, 0] <= fx1) & (EE[:, 1] >= fy0) & (EE[:, 1] <= fy1)
            fo = np.zeros(len(GG), bool)
            for k_ in np.linspace(0, 1, 9):
                Q = EE + (GG - EE) * k_; fo |= (Q[:, 0] >= fx0 + 18) & (Q[:, 0] <= fx1 - 18) & (Q[:, 1] >= fy0 + 18) & (Q[:, 1] <= fy1 - 18)
            inF = inE | (fo if not os.environ.get('NOFO') else False)
            SC = np.linalg.norm(GG - G0w[None], axis=1) + .2 * float(np.linalg.norm(np.array([x, y]) - SNAT)) + 400 * inF + WK * np.maximum(0, np.abs(WR) - WMAX)
            i = int(np.argmin(SC))
            if best is None or SC[i] < best[0]: best = (float(SC[i]), x, y, Sw, GG[i], EE[i], bool(inF[i]), float(dist[cy, cx]), float(WR[i]))
    sc, x, y, Sw, Gw, Ew, inface, dp, wr_ = best
    gl = ap(iH, Gw); sl0 = ap(inv(T), S0w)
    out[f'{t:.2f}'] = {'shL': [round(x, 1), round(y, 1)], 'G': [round(float(gl[0]), 1), round(float(gl[1]), 1)]}
    print(f"t {t:.2f}  어깨(상체) {sl0.round(1)} → ({x:.0f},{y:.0f}) 깊이 {dp:.0f} · 쥔 점 이동 {np.linalg.norm(Gw - G0w):5.1f} · 펴짐 {np.linalg.norm(Gw - Sw) / LN:.2f} · 손목 {wr_:.0f} · 팔꿈치 얼굴 {inface} · G(골반) {out[f'{t:.2f}']['G']}")
_KB = os.path.join(SRC, 'attack', 'keys12b.json')
if not os.environ.get('FRESH') and os.path.exists(_KB): out = dict(json.load(open(_KB))['keys'], **out)
json.dump({'note': 'tools/shoulder12.py — 먼 어깨 = 몸 실루엣 안(깊이 ≥ %g), 쥔 점 = 러스트 방향 그대로 펴짐 ≤ %g' % (DEP, RT), 'keys': out}, open(os.path.join(SRC, 'attack', 'keys12b.json'), 'w'), ensure_ascii=False, indent=1)
print('→ attack/keys12b.json')
