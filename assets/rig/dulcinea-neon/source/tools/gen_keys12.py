# 12 네온 둘시네: 러스트 v6.4 한 손 내려찍기 키 → 네온 몸 키 (10-20 08:43 기록)
#   왜: 네온 먼 팔(어깨→팔꿈치→쥔 점)은 186.5 리그로 러스트 202.3 의 0.92배, 먼 어깨 자리도 다름(대기 골반 기준 네온 (54,−114) · 러스트 (76,−108))
#       → 러스트 쥔 점 키를 그대로 쓰면 휘두름~버팀(.32~.73)에 손이 자루에 안 닿음(빈틈), 들어 올림 펴짐 .93~.96
#   방법(팔 모양을 러스트와 같게): 키 시각마다 엔진에서 잼 — 러스트 먼 어깨 S_r·쥔 점 G_r·상체 각 θ_r, 네온 먼 어깨 S_n·상체 각 θ_n
#       v = R(−θ_r)(G_r − S_r) (상체 기준 어깨→쥔 점) → G_n = S_n + R(θ_n)·v·k (k = 네온 팔 / 러스트 팔) → gx·gy = 골반 행렬 역으로
#       자루 각(sa)은 러스트 그대로(같은 휘두름), 대기 자리(첫·끝 키)는 네온 원화 그대로. 펴짐·손목·팔꿈치 모양이 러스트와 같아짐.
#   python3 -I tools/gen_keys12.py → attack/keys12.json (smash12.py 가 읽음) + 표
import sys, time, socket, subprocess, os, json, math
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); root = os.path.abspath(os.path.join(SRC, '..', '..'))
LR, LN = 202.3, 186.5; K = LN / LR
sys.path.insert(0, SRC)
src = open(os.path.join(SRC, 'attack', 'smash12.py')).read()
# 키 시각 = smash12.py POSE 의 시각(대기 첫·끝 빼고)
LIFT, WIND, SW1, SW2, HIT, HOLD, RET1, RET, END = .18, .27, .32, .36, .40, .58, .68, .82, 1.0
TS = [LIFT, WIND, SW1, SW2, HIT, HOLD, RET1, RET]
html = f'''<!doctype html><meta charset=utf-8><script src="rig.js?x={time.time()}"></script>
<script src="dulcinea-rust/rig.def.js?x={time.time()}"></script><script src="dulcinea-neon/rig.def.js?x={time.time()}"></script><script>
const load=async id=>{{const d=MR_RIG_DEFS[id];const ims=await Promise.all(Object.entries(d.parts).map(([k,p])=>new Promise((r,j)=>{{const im=new Image();im.onload=()=>r([k,im]);im.onerror=()=>j(p.src);im.src=id+'/'+p.src}})));return [d,Object.fromEntries(ims)]}};
window.meas=async(id,T)=>{{const [d,IM]=await load(id);const rig=new CharacterRig(d,IM),an=new RunAnimator(rig,{{runSpeed:620}});for(let i=0;i<240;i++)an.update(1/120,{{vx:0}});an.attack('smash');let n=0;
 while(an.act&&an.act.t<T-1e-6&&n<8000){{an.update(1/480,{{vx:0}});n++}}
 const S=rig.by.armF.m, Tm=rig.by.torso.m, H=rig.by.hip.m;
 return {{t:an.act?an.act.t:-1,S:[S[4],S[5]],G:an.swordG,a:an.swordA,th:Math.atan2(Tm[1],Tm[0]),H:H}}}};window.ready=1</script>'''
open(os.path.join(root, '_gk.html'), 'w').write(html)
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(.6)
rot = lambda v, a: [v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)]
def inv_apply(m, p):
    q = m[0] * m[3] - m[1] * m[2]; x, y = p[0] - m[4], p[1] - m[5]
    return [(m[3] * x - m[2] * y) / q, (-m[1] * x + m[0] * y) / q]
out = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium'); pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/_gk.html'); pg.wait_for_function('window.ready', timeout=30000)
        print('  t     러스트 S→G(상체 기준)      네온 S        새 gx,gy (러스트 gx,gy)')
        for T in TS:
            r = pg.evaluate('([i,t])=>meas(i,t)', ['dulcinea-rust', T]); n = pg.evaluate('([i,t])=>meas(i,t)', ['dulcinea-neon', T])
            v = rot([r['G'][0] - r['S'][0], r['G'][1] - r['S'][1]], -r['th']); w = rot([v[0] * K, v[1] * K], n['th'])
            Gn = [n['S'][0] + w[0], n['S'][1] + w[1]]; g = inv_apply(n['H'], Gn); gr = inv_apply(r['H'], r['G'])
            out[str(T)] = [round(g[0], 1), round(g[1], 1)]
            print(f"  {T:.2f}  ({v[0]:6.1f},{v[1]:6.1f})  ({n['S'][0]:6.1f},{n['S'][1]:6.1f})  ({g[0]:6.1f},{g[1]:6.1f})  ({gr[0]:6.1f},{gr[1]:6.1f})")
        b.close()
        if errs: print('errors', errs[:3])
finally:
    srv.terminate(); os.remove(os.path.join(root, '_gk.html'))
json.dump({'K': round(K, 4), 'G': out, 'note': 'gen_keys12.py — 러스트 v6.4 쥔 점 키를 네온 먼 어깨·팔 길이로 옮김(상체 기준 어깨→쥔 점 × K)'}, open(os.path.join(SRC, 'attack', 'keys12.json'), 'w'), ensure_ascii=False, indent=1)
print('→ attack/keys12.json  K', round(K, 4))
