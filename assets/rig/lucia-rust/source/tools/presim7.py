# 7 루시아 한 손 도끼 내려찍기 미리 재기 — 12 네온 둘시네 v1.4 공격(엔진 1/60 표, tools/sample_ref.py)을 루시아 몸·팔·도끼로 옮겨
#   팔 펴짐·늘임, 손목 꺾임, 도끼 꼭대기(전투 칸 위 끝 = 몸 키 ×1.817 PC · ×1.75 폰 — 2·12·22 게임 잼으로 맞춤), 타격 때 날 아래 끝(땅), 도끼∩볏·머리·방패
#   옮기는 법 MODE: A = 팔 길이 배율(12 와 같은 팔 모양·펴짐) · B = 몸 키 배율(몸에 대한 손 자리 같음, 팔은 더 굽음)
#   쥔 손: 원화 손(시트 18) 팔뚝 방향 = 자루 각 −100.3° · 자루 따라 쥔 손(시트 19, 2 러스트 gFh 모양) = −146.6° — 12 nPiece 구간대로
#   대기 자리 섞기 w(t): 0 → .18 에 12 자세로, .82 → .97 에 루시아 대기로(자루 각·쥔 점)
#   python3 -I tools/presim7.py [A|B] [기준 id] → 표 + review/presim7_<MODE>.png
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
MODE = sys.argv[1] if len(sys.argv) > 1 else 'A'; REF = sys.argv[2] if len(sys.argv) > 2 else 'dulcinea-neon'
J = json.load(open(os.path.join(SRC, 'joints7.json'))); RS = json.load(open(os.path.join(SRC, 'work', 'ref_samples.json')))[REF]
O = np.array(J['O'], float); rig = lambda a: (np.array(a, float) - O) * 2
HIP, S0, E0, W0, G0 = (rig(J[k]) for k in ('HIP', 'SH_F', 'EL_F', 'WR_F', 'G'))
L1, L2 = float(np.linalg.norm(E0 - S0)), float(np.linalg.norm(W0 - E0))
SA0 = math.radians(J['AXE']['shaft_deg']); BODY = (J['feet'] - J['helmet_top']) * 2
ARM12 = 74.8 + 112.0; ARML = L1 + float(np.linalg.norm(G0 - E0))
K = ARML / ARM12 if MODE == 'A' else BODY / RS['bodyH']; KB = BODY / RS['bodyH']
R = lambda a: np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
F = RS['frames']; f0 = F[0]
def P(f, k): return np.array(f[k], float)
th0, hip0, S12_0, G12_0, sa12_0 = f0['th'], P(f0, 'hip'), P(f0, 'S'), P(f0, 'G'), f0['sa']
v0 = R(-th0) @ (G12_0 - S12_0) * K; dG = (G0 - S0) - v0
sm = lambda u: u * u * (3 - 2 * u)
def w(t):
    if t <= 0: return 1.0
    if t < .18: return 1 - sm(t / .18)
    if t <= .82: return 0.0
    if t < .97: return sm((t - .82) / .15)
    return 1.0
NP = [[0, 'art'], [.36, 'gFh'], [.68, 'art']]
FD = {'art': math.radians(-100.3), 'gFh': math.radians(-146.6)}
WG = float(np.linalg.norm(W0 - G0))
# 도끼(+먼 주먹) 실루엣 점: seg7 라벨에서
lab = np.load(os.path.join(SRC, 'work', 'labels.npy')); NM = json.load(open(os.path.join(SRC, 'work', 'label_names.json')))
ys, xs = np.nonzero((lab == NM.index('axe') + 1)); AX = (np.stack([xs, ys], 1).astype(float) - O) * 2
idx = np.linspace(0, len(AX) - 1, min(len(AX), 4000)).astype(int); AXs = AX[idx]
hy, hx = np.nonzero(lab == NM.index('head') + 1); HEAD = (np.stack([hx, hy], 1).astype(float) - O) * 2
sy_, sx_ = np.nonzero(lab == NM.index('shield') + 1); SHD = (np.stack([sx_, sy_], 1).astype(float) - O) * 2
def ang(v): return math.atan2(v[1], v[0])
def cr(a, b): return float(a[0] * b[1] - a[1] * b[0])
def adiff(a, b): return (a - b + math.pi) % (2 * math.pi) - math.pi
side0 = np.sign(cr(W0 - S0, E0 - S0))
BEND0 = math.degrees(adiff(ang(E0 - W0), ang(W0 - G0)))   # 원화 대기 손목 꺾임(원화 그대로 = 0 으로 봄)
BENDH0 = -32.0   # gFh 0 = 2 러스트 게임 버팀 꺾임(MODE A dulcinea-rust .40–.58 = -31~-33°) — 시트 19 는 2 러스트 gFh 모양으로 그림
EASE = {'io': lambda u: u * u * (3 - 2 * u), 'lin': lambda u: u, 'i': lambda u: u * u, 'o': lambda u: 1 - (1 - u) ** 2}
def frames_K(path):
    KS = json.load(open(path))['keys']; out = []
    for i in range(0, 61):
        t = i / 60
        for k0, k1 in zip(KS, KS[1:]):
            if k0[0] <= t <= k1[0]:
                e = EASE[k0[7] if len(k0) > 7 else 'io']; u = e((t - k0[0]) / max(1e-6, k1[0] - k0[0])); v = [k0[j] + (k1[j] - k0[j]) * u for j in range(1, 7)]; break
        else: v = KS[-1][1:7]
        gx, gy, sad, lean, hx, hy = v; th = math.radians(lean); hipL = HIP + np.array([hx, hy])
        out.append(dict(t=t, th=th, hipL=hipL, S=hipL + R(th) @ (S0 - HIP), G=hipL + np.array([gx, gy]), sa=math.radians(sad)))
    return out
if MODE == 'K':
    _kf = sys.argv[3] if len(sys.argv) > 3 else os.path.join(SRC, 'attack', 'keys7.json')
    if 'fist' in json.load(open(_kf)): NP = json.load(open(_kf))['fist']
    FR = frames_K(sys.argv[3] if len(sys.argv) > 3 else os.path.join(SRC, 'attack', 'keys7.json'))
else:
    FR = []
    for f in F:
        t = f['t']; th = f['th'] - th0; ww = w(t)
        hipL = HIP + (P(f, 'hip') - hip0) * KB
        dS = R(-f['th']) @ (P(f, 'S') - P(f, 'hip')) - R(-th0) @ (S12_0 - hip0)
        S = hipL + R(th) @ ((S0 - HIP) + dS * KB)
        v = R(-f['th']) @ (P(f, 'G') - P(f, 'S')) * K
        FR.append(dict(t=t, th=th, hipL=hipL, S=S, G=S + R(th) @ (v + dG * ww), sa=f['sa'] + (SA0 - sa12_0) * ww))
rows = []
for fr in FR:
    t, th, hipL, S, G, sa = fr['t'], fr['th'], fr['hipL'], fr['S'], fr['G'], fr['sa']
    fist = [n for tt, n in NP if t >= tt - 1e-9][-1]
    fd = sa + FD[fist] if fist == 'gFh' else sa + FD['art']
    Wp = G + np.array([math.cos(fd), math.sin(fd)]) * WG
    d = float(np.linalg.norm(Wp - S)); reach = d / (L1 + L2)
    if d >= L1 + L2: E = S + (Wp - S) / d * L1; stretch = d / (L1 + L2)
    else:
        a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(0, L1 * L1 - a * a)); m = S + (Wp - S) * a / d; n = np.array([-(Wp - S)[1], (Wp - S)[0]]) / d
        E1, E2 = m + n * h, m - n * h; E = E1 if np.sign(cr(Wp - S, E1 - S)) == side0 else E2; stretch = 1.0
    bend = math.degrees(adiff(ang(E - Wp), fd)) - (BEND0 if fist == 'art' else BENDH0)
    AXt = (AXs - G0) @ R(sa - SA0).T + G
    top = -AXt[:, 1].min(); low = AXt[:, 1].max(); front = AXt[:, 0].max()
    HD = HEAD + (hipL - HIP); ov_head = 0
    rows.append(dict(t=t, S=S, E=E, W=Wp, G=G, sa=sa, fist=fist, reach=reach, stretch=stretch, bend=bend, top=top / BODY, low=low, front=front / BODY, hip=hipL, th=th))
print(f'{REF} → 루시아 MODE {MODE}: 팔 L1 {L1:.0f} · L2 {L2:.0f} · 손목→쥔 점 {WG:.0f} (리그 px) · 배율 K {K:.3f} (팔 {ARML / ARM12:.2f} · 몸 {KB:.3f}) · 몸 키 {BODY:.0f}')
print(f'  t     손    펴짐  늘임  손목°(art: 원화 대기 {BEND0:+.0f}° = 0 · gFh: 2 러스트 버팀 {BENDH0:+.0f}° = 0)  도끼꼭대기(몸키×)  날아래(땅=0, +면 땅속)  앞끝(골반 기준 몸키×)')
for i_, r in enumerate(rows):
    flag = ('✗' if r['stretch'] > 1.001 or r['reach'] > .92 or abs(r['bend']) > (35 if r['fist'] == 'art' else 25) or r['top'] > 1.70 or r['low'] > 20 else '')
    if i_ % 3 == 0 or flag:
        print(f"  {r['t']:.3f} {r['fist']:4s} {r['reach']:.2f}  {r['stretch']:.2f}  {r['bend']:+5.0f}   {r['top']:.2f}   {r['low']:+6.0f}  {r['front']:.2f} {flag}")
for T in (0, .18, .27, .32, .36, .4, .58, .68, .82, .97):
    r = min(rows, key=lambda q: abs(q['t'] - T)); g = r['G'] - r['hip']
    print(f"  키 {T:.2f}: gx {g[0]:+.0f} gy {g[1]:+.0f} sa {math.degrees(r['sa']):+.0f}° lean {math.degrees(r['th']):+.1f}° hip {r['hip'][0] - HIP[0]:+.0f},{r['hip'][1] - HIP[1]:+.0f} 날아래 {r['low']:+.0f} 앞끝 ×{r['front']:.2f}")
mx = max(rows, key=lambda r: r['top']); print(f"  도끼 꼭대기 최대 ×{mx['top']:.2f} @ {mx['t']:.2f} (PC 칸 ×1.817 · 폰 ×1.75) · 펴짐 최대 {max(r['reach'] for r in rows):.2f} · 손목 최대 {max(abs(r['bend']) for r in rows):.0f}°")
# 그림: 키 장면
art = Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'); A = np.array(art)
body = A.copy(); rm = np.isin(lab, [NM.index(n) + 1 for n in ('axe', 'handF', 'foreF')]); body[rm, 3] = 0
axeim = A.copy(); keep = np.isin(lab, [NM.index(n) + 1 for n in ('axe', 'handF')]); axeim[~keep, 3] = 0
BI, AI = Image.fromarray(body), Image.fromarray(axeim)
TS = [0, .1, .18, .27, .32, .36, .4, .5, .58, .68, .82, .97]
cell = 330; CW = 420; sc = .5; im = Image.new('RGB', (CW * 6, cell * 2 + 60), (40, 56, 96)); d = ImageDraw.Draw(im)
try: FT = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 13)
except Exception: FT = None
for i, T in enumerate(TS):
    r = min(rows, key=lambda q: abs(q['t'] - T)); ox, oy = 0, 0
    tile = Image.new('RGBA', (CW, cell), (40, 56, 96, 255))
    def to_t(p): return (p[0] * sc / 2 + cell / 2 - 60, p[1] * sc / 2 + cell - 60)
    dh = (r['hip'] - HIP) * sc / 2
    b2 = BI.resize((int(512 * sc), int(512 * sc)), Image.LANCZOS); bx = int(cell / 2 - 60 - O[0] * sc + dh[0]); by = int(cell - 60 - O[1] * sc + dh[1])
    ang_deg = -math.degrees(r['sa'] - SA0)
    a2 = AI.resize((int(512 * sc), int(512 * sc)), Image.LANCZOS)
    gx0, gy0 = J['G'][0] * sc, J['G'][1] * sc
    a2 = a2.rotate(ang_deg, center=(gx0, gy0), resample=Image.BICUBIC)
    Gt = to_t(r['G']); ax_, ay_ = int(Gt[0] - gx0), int(Gt[1] - gy0)
    dr = ImageDraw.Draw(tile)
    for k_, col in ((1.817, (255, 200, 0)), (1.75, (255, 90, 60))):
        y = cell - 60 - k_ * BODY * sc / 2; dr.line([(0, y), (CW, y)], fill=col, width=1)
    dr.line([(0, cell - 60), (CW, cell - 60)], fill=(160, 140, 100), width=2)
    S_, E_, W_ = to_t(r['S']), to_t(r['E']), to_t(r['W'])
    dr.line([S_, E_], fill=(150, 90, 40), width=int(26 * sc)); dr.line([E_, W_], fill=(240, 170, 120), width=int(20 * sc))
    tile.alpha_composite(b2, (bx, by)); tile.alpha_composite(a2, (ax_, ay_))
    dr = ImageDraw.Draw(tile); dr.text((4, 4), f"{r['t']:.2f} {r['fist']} 펴짐{r['reach']:.2f} 손목{r['bend']:+.0f}° 꼭대기×{r['top']:.2f}", fill=(255, 255, 255), font=FT)
    im.paste(tile.convert('RGB'), ((i % 6) * CW, (i // 6) * (cell + 20) + 20))
ImageDraw.Draw(im).text((6, 2), f'presim7 MODE {MODE} ({REF} 키 → 루시아) · 노랑 = 전투 칸 위 끝 PC(×1.817) · 빨강 = 폰(×1.75) · 갈색 = 윗팔 · 살색 = 팔뚝(관절 선, 몸·머리 앞뒤는 아직 아님)', fill=(255, 255, 255), font=FT)
im.save(os.path.join(SRC, 'review', f'presim7_{MODE}.png'))
