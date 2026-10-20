# 22 스카이 둘시네: 12 네온 v1.4 쥔 점·먼 어깨 키 → 22 몸 키 (10-20 15:4x)
#   왜: 22 먼 팔 길이 = 12 와 같게 팔꿈치를 풀어 둠(74.8·112.0 vs 74.7·111.8) → 같은 팔 모양(어깨→쥔 점 벡터, 상체 기준)이면 펴짐·손목 꺾임·팔꿈치 쪽이 12 v1.4 와 같음
#       22 대기 먼 어깨는 상체 기준 (88,−134) — 12 (54,−114) 보다 오른쪽 위(22 상체 실루엣도 골반 기준 그만큼 오른쪽) → 어깨 키 = 12 어깨 + 대기 차이
#   방법(키 시각마다 엔진에서 잼): 12 먼 어깨 S_n·쥔 점 G_n·상체 각 θ_n, 22 먼 어깨 S_s(어깨 키 = 12 + 차이)·상체 각 θ_s·골반 행렬 H_s
#       v = R(−θ_n)(G_n − S_n) → G_s = S_s + R(θ_s)·v → gx·gy = H_s 역으로.  자루 각(sa)은 12 그대로(같은 휘두름).
#   python3 -I tools/keys22.py → attack/keys22b.json (smash22.py 가 읽음) + 표.  22 rig.def.js 가 먼저 있어야 함(어깨 키가 12 + 차이로 들어간 빌드)
import sys, time, socket, subprocess, os, json, math
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); root = os.path.abspath(os.path.join(SRC, '..', '..'))
K12 = json.load(open(os.path.join(root, 'dulcinea-neon', 'source', 'attack', 'keys12b.json')))['keys']
R22 = json.load(open(os.path.join(SRC, '..', 'rig.json'))); SH0 = [b for b in R22['bones'] if b['name'] == 'armF'][0]['pos']
D = (SH0[0] - 54.0, SH0[1] + 114.0)
TS = sorted(float(t) for t in K12)
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script>
<script src="dulcinea-neon/rig.def.js?x={time.time()}"></script><script src="dulcinea-sky/rig.def.js?x={time.time()}"></script><script>
const load=async id=>{{const d=MR_RIG_DEFS[id];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src=id+'/'+p.src}})));return [d,Object.fromEntries(ims)]}};
window.meas=async(id,T)=>{{const [d,IM]=await load(id);const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<240;i++)an.update(1/120,{{vx:0}});an.attack('smash');let n=0;
 while(an.act&&an.act.t<T-1e-6&&n<8000){{an.update(1/480,{{vx:0}});n++}}
 const S=rig.by.armF.wm||rig.by.armF.m, Tm=rig.by.torso.m, H=rig.by.hip.m;
 return {{t:an.act?an.act.t:-1,S:[S[4],S[5]],G:an.swordG,th:Math.atan2(Tm[1],Tm[0]),H:H,T:Tm}}}};window.ready=1</script>'''
open(os.path.join(root, '_k22.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
rot = lambda v, a: [v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)]
ap = lambda m, p: [m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]]
def inv_apply(m, p):
    q = m[0] * m[3] - m[1] * m[2]; x, y = p[0] - m[4], p[1] - m[5]
    return [(m[3] * x - m[2] * y) / q, (-m[1] * x + m[0] * y) / q]
out = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_k22.html'); pg.wait_for_function('window.ready', timeout=30000)
        print(f'  대기 어깨 차이(상체 기준) {D}')
        print('  t     12 S→G(상체 기준)     22 어깨 S(잼 · 키 기대)        새 gx,gy')
        for T in TS:
            n = pg.evaluate('([i,t])=>meas(i,t)', ['dulcinea-neon', T]); s_ = pg.evaluate('([i,t])=>meas(i,t)', ['dulcinea-sky', T])
            v = rot([n['G'][0] - n['S'][0], n['G'][1] - n['S'][1]], -n['th']); w = rot(v, s_['th'])
            shL = [K12[f'{T:.2f}']['shL'][0] + D[0], K12[f'{T:.2f}']['shL'][1] + D[1]]; Sexp = ap(s_['T'], shL)
            Gs = [s_['S'][0] + w[0], s_['S'][1] + w[1]]; g = inv_apply(s_['H'], Gs)
            out[f'{T:.2f}'] = {'shL': [round(shL[0], 1), round(shL[1], 1)], 'G': [round(g[0], 1), round(g[1], 1)]}
            print(f"  {T:.2f}  ({v[0]:6.1f},{v[1]:6.1f})  ({s_['S'][0]:6.1f},{s_['S'][1]:6.1f} · {Sexp[0]:6.1f},{Sexp[1]:6.1f})  ({g[0]:6.1f},{g[1]:6.1f})  θ 12 {n['th']:.3f} · 22 {s_['th']:.3f}")
        b.close()
        if errs: print('errors', errs[:3])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_k22.html'))
json.dump({'note': 'tools/keys22.py — 12 네온 v1.4 keys12b(어깨·쥔 점)를 22 몸으로: 어깨 = 12 + 대기 차이 %s, 쥔 점 = 같은 팔 모양(상체 기준 어깨→쥔 점)' % (D,), 'keys': out},
          open(os.path.join(SRC, 'attack', 'keys22b.json'), 'w'), ensure_ascii=False, indent=1)
print('→ attack/keys22b.json')
