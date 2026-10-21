"""30 스카이 브루노 — 번갈아 내려찍기 키(10 러스트 브루노 v1.2 를 스카이 팔·도끼로 다시 풂, plan_alt30 구조) + 1/60 검사 + 키 자세 그림
  30 에서 더: 먼 팔이 짧음(윗팔 20.6 + 팔뚝~주먹 56.6 = 77 — 10 은 102) → 10 의 먼 쥔 점(어깨 기준)을 팔 길이 비로 줄여 옮긴 뒤 ±28 에서 다시 찾음
  구조(10 과 같음, rig.js 안 바꿈): 먼 도끼 = swordGrip 칼(gx·gy·sa) + 먼 팔 길이 고정 IK · 가까운 도끼 = freeArm(fuA·flA) + 팔뚝 뼈에 붙은 도끼(손목 고정)
  10 과 다른 곳:
   · 가까운 윗팔이 맨살로 길게 보임(51.4 — 10 은 34.5, 재킷 소매 속) → 윗팔을 상체 앞·어깨갑(pauldron 조각) 밑에 그림. 10 v1.2 의 '소매 입구 ±25°'(UCONE) 대신
     '팔꿈치·팔뚝이 얼굴 밖 · 펴짐 ≤ .9' 로 윗팔 각을 풂(어깨는 어깨갑 밑 원 안이라 어느 각에서도 붙어 보임)
   · 가까운 키 = 10 의 같은 시각 도끼 세상 각 + 주먹 자리(어깨 기준)를 그대로 따라가게 윗팔 각만 찾음(팔뚝 각 = 도끼 각 − 손목 차이, 손목 고정)
   · 먼 키 = 10 의 쥔 점(어깨 기준)·도끼 각을 옮기고 둘레 ±28 에서 펴짐 ≤ .86 · 손목 최소로 다시 찾음(41번 — 옮긴 키는 이 몸으로 다시 잼)
  검사(1/60): 펴짐 ≤ .90 · 먼 손목 ≤ 35° · 도끼 꼭대기 ≥ 게임 칸 위 끝 추정 + 10 · 도끼 땅 위 · 팔뚝·주먹·팔꿈치가 얼굴 위 프레임 · 가까운 윗팔 각 범위
입력: ../measure30.json · ../ref512.png · ../work/labels.npy · ../../../bruno-rust/source/review/plan_alt10.json   출력: ../review/plan_alt30.png · ../review/plan_alt30.json
실행: python3 -I plan_alt30.py
"""
import json, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(os.path.join(HERE, '..'))
M = json.load(open(os.path.join(SRC, 'measure30.json'))); R10 = json.load(open(os.path.join(SRC, '..', '..', 'bruno-rust', 'source', 'review', 'plan_alt10.json')))
M10 = json.load(open(os.path.join(SRC, '..', '..', 'bruno-rust', 'source', 'measure10.json')))
RA = np.array(Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'))
LAB = np.load(os.path.join(SRC, 'work', 'labels.npy')); NM = json.load(open(os.path.join(SRC, 'work', 'label_names.json'))); lab = lambda *ns: np.logical_or.reduce([LAB == NM.index(n) + 1 for n in ns])
V = lambda p: np.array(p, float); X2 = lambda a, b: float(a[0] * b[1] - a[1] * b[0]); ang = lambda v: math.degrees(math.atan2(v[1], v[0])); U = lambda d: np.array([math.cos(math.radians(d)), math.sin(math.radians(d))])
def wrap(d): return (d + 180) % 360 - 180
H = V(M['hip']); N, F = M['near'], M['far']
SHN, ELN, FN, BN = V(N['SH']), V(N['EL']), V(N['fist']), V(N['head']); SHF, ELF, FF, BF = V(F['SH']), V(F['EL']), V(F['fist']), V(F['head'])
L1N, L2N = np.linalg.norm(ELN - SHN), np.linalg.norm(FN - ELN); L1F, L2F = np.linalg.norm(ELF - SHF), np.linalg.norm(FF - ELF)
u0N, f0N, a0N = ang(ELN - SHN), ang(FN - ELN), ang(BN - FN); dN = a0N - f0N
f0F, a0F = ang(FF - ELF), ang(BF - FF); wF0 = a0F - f0F
sideF = np.sign(X2(FF - SHF, ELF - SHF))
GROUND = M['sole_y']; TOPLIM = M['gameTop_est']['y'] + 10
FACE_C, FACE_R = V([286, 285]), (30, 34)
# ---- 10 키 ----
KB = [tuple(k) for k in R10['keys']['body']]
S10 = R10['summary']; L1r, L2r = S10['arm']['near']; dNr = S10['restAngles']['near_axe_minus_fore']
SHr_N, SHr_F = V(M10['near']['SH']), V(M10['far']['SH'])
def near_from10(t, ur, fr):   # 10 의 (윗팔·팔뚝 세상 각) → 도끼 각 + 주먹 자리(어깨 기준) → 네온 윗팔 각 찾기
    A = fr + dNr; f = A - dN; tgt = L1r * U(ur) + L2r * U(fr); best = None
    for u10 in range(900, 2701, 5):
        u = u10 / 10; Fr = L1N * U(u) + L2N * U(f); reach = np.linalg.norm(Fr) / (L1N + L2N)
        if reach > .9: continue
        sc = np.linalg.norm(Fr - tgt) + 0.05 * abs(wrap(u - u0N))
        if best is None or sc < best[0]: best = (sc, u, reach, float(np.linalg.norm(Fr - tgt)))
    return (t, best[1], f), best
# 타격·버팀(.28·.34): 10 의 주먹 자리(어깨 기준)를 따르면 긴 윗팔이 왼쪽 아래로 뻗고 팔뚝이 되접혀 '팔꿈치를 뒤로 찌르는' 모양(키 그림 ③ 첫 판)
#   → 윗팔을 몸 앞 아래(어깨갑 밑에서 앞으로)로 내리고 팔뚝은 도끼 각 그대로 — 휘두름이 위 → 왼쪽 → 아래 → 앞으로 이어짐. 펴짐 ≤ .9 안에서 가장 앞(작은 각)
HIT_U = {0.28: None, 0.34: None}
def hit_u(f, lo=40, hi=130):
    for u in range(lo, hi + 1):
        Fr = L1N * U(u) + L2N * U(f)
        if np.linalg.norm(Fr) / (L1N + L2N) <= .88: return float(u)
KN = [(0.0, u0N, f0N)]
for k in R10['keys']['near'][1:-1]:
    key, b = near_from10(*k)
    if k[0] in HIT_U: u_ = hit_u(key[2]); key = (key[0], u_, key[2]); print(f'near key {k[0]:.2f}: 타격 — 윗팔 {u_:.0f}°(몸 앞 아래) · 팔뚝 {key[2]:.1f}'); KN.append(key); continue
    KN.append(key); print(f'near key {k[0]:.2f}: 10 (윗팔 {k[1]:.0f}, 팔뚝 {k[2]:.0f}) → 네온 윗팔 {b[1]:.1f} · 팔뚝 {key[2]:.1f} · 펴짐 {b[2]:.2f} · 주먹 자리 차 {b[3]:.1f}px')
KN.append((1.0, u0N, f0N))
ARMK_F = (L1F + L2F) / sum(S10['arm']['far'])   # 먼 팔 길이 비(30 ÷ 10)
KF = [(0.0, FF, a0F)] + [(k[0], tuple(SHF + (V(k[1]) - SHr_F) * ARMK_F), k[2], 'a') for k in R10['keys']['far'][1:-1]] + [(1.0, FF, a0F)]
print('먼 팔 길이 비', round(ARMK_F, 3))
HIT = list(S10['hits'])
def ease(x): return x * x * (3 - 2 * x)
def lerpk(K, t):
    for i in range(len(K) - 1):
        if K[i][0] <= t <= K[i + 1][0]:
            w = ease((t - K[i][0]) / (K[i + 1][0] - K[i][0])); return K[i], K[i + 1], w
    return K[-1], K[-1], 0.0
def body(t):
    a, b, w = lerpk(KB, t); return a[1] + (b[1] - a[1]) * w, np.array([a[2] + (b[2] - a[2]) * w, a[3] + (b[3] - a[3]) * w])
def xf(p, th, off):
    c, s = math.cos(th), math.sin(th); q = V(p) - H; return H + off + np.array([c * q[0] - s * q[1], s * q[0] + c * q[1]])
def near(t, th, off):
    a, b, w = lerpk(KN, t); u = a[1] + wrap(b[1] - a[1]) * w; f = a[2] + wrap(b[2] - a[2]) * w
    S = xf(SHN, th, off); E = S + L1N * U(u); Fi = E + L2N * U(f); A = f + dN
    return dict(S=S, E=E, F=Fi, A=A, u=u, f=f, fuA=wrap(u - u0N - math.degrees(th)), flA=wrap((f - u) - (f0N - u0N)), reach=np.linalg.norm(Fi - S) / (L1N + L2N))
def far(t, th, off):
    a, b, w = lerpk(KF, t); G = V(a[1]) + (V(b[1]) - V(a[1])) * w; A = a[2] + wrap(b[2] - a[2]) * w
    S = xf(SHF, th, off); d = np.linalg.norm(G - S); dd = min(d, L1F + L2F - 1e-6); ca = (L1F ** 2 + dd ** 2 - L2F ** 2) / (2 * L1F * dd)
    base = math.atan2(*(G - S)[::-1]); off_a = math.acos(max(-1, min(1, ca)))
    E1 = S + L1F * np.array([math.cos(base + off_a), math.sin(base + off_a)]); E2 = S + L1F * np.array([math.cos(base - off_a), math.sin(base - off_a)])
    E = E1 if np.sign(X2(G - S, E1 - S)) == sideF else E2
    f = ang(G - E); return dict(S=S, E=E, F=G, A=A, wrist=wrap((A - f) - wF0), reach=d / (L1F + L2F), over=d > L1F + L2F)
YY, XX = np.mgrid[0:512, 0:512].astype(float); AL = RA[..., 3] > 20
mN, mF = lab('axeN') & AL, lab('axeF') & AL
def mace_px(m, Fi, A0):
    ys, xs = np.nonzero(m); P = np.stack([xs, ys], 1).astype(float) - Fi; c, s = math.cos(math.radians(-A0)), math.sin(math.radians(-A0))
    return np.stack([c * P[:, 0] - s * P[:, 1], s * P[:, 0] + c * P[:, 1]], 1)
PN, PF = mace_px(mN, FN, a0N), mace_px(mF, FF, a0F)
def place(P, Fi, A):
    c, s = math.cos(math.radians(A)), math.sin(math.radians(A)); return np.stack([c * P[:, 0] - s * P[:, 1], s * P[:, 0] + c * P[:, 1]], 1) + Fi
def solve_far_keys():
    for i, k in enumerate(KF):
        if len(k) < 4: continue
        th, off = body(k[0]); best = None
        for dx in range(-28, 29, 2):
            for dy in range(-28, 29, 2):
                G = V(k[1]) + [dx, dy]; S = xf(SHF, th, off); d = np.linalg.norm(G - S)
                if d > .86 * (L1F + L2F): continue
                KF[i] = (k[0], tuple(G), k[2]); w = far(k[0], th, off)['wrist']; sc = w * w + 0.03 * (dx * dx + dy * dy)
                if place(PF, G, k[2])[:, 1].max() > GROUND - 14: continue
                if best is None or sc < best[0]: best = (sc, tuple(map(float, G)), w)
        KF[i] = (k[0], best[1], k[2]); print('far key', k[0], 'grip', np.round(best[1], 1), '(10 옮김', np.round(V(k[1]), 1), ') wrist', round(best[2], 1))
solve_far_keys()
def seg_face(p, q, th, off, n=12):
    C = xf(FACE_C, th, off)
    for k in range(n + 1):
        z = p + (q - p) * k / n
        if ((z[0] - C[0]) / FACE_R[0]) ** 2 + ((z[1] - C[1]) / FACE_R[1]) ** 2 <= 1: return True
    return False
rows = []; worst = dict(reachN=0, reachF=0, wrist=0, top=1e9, low=-1e9, faceN=0, faceF=0, handleN=0, upperMin=1e9, upperMax=-1e9, elbowFace=0)
for i in range(61):
    t = i / 60; th, off = body(t); n = near(t, th, off); f = far(t, th, off)
    QN = place(PN, n['F'], n['A']); QF = place(PF, f['F'], f['A'])
    top = float(min(QN[:, 1].min(), QF[:, 1].min())); low = float(max(QN[:, 1].max(), QF[:, 1].max()))
    fN = seg_face(n['E'], n['F'], th, off); fF = seg_face(f['E'], f['F'], th, off); hN = seg_face(n['F'], n['F'] + 150 * U(n['A']), th, off)
    eF = seg_face(n['S'], n['E'], th, off)
    r = dict(t=round(t, 3), lean=round(th, 3), reachN=round(n['reach'], 3), reachF=round(f['reach'], 3), wristF=round(f['wrist'], 1), fuA=round(math.radians(n['fuA']), 3), flA=round(math.radians(n['flA']), 3),
             upperN=round(n['u'], 1), maceN=round(n['A'], 1), maceF=round(f['A'], 1), top=round(top, 1), low=round(low, 1), faceN=bool(fN), faceF=bool(fF), handleN=bool(hN), upperFace=bool(eF), overF=bool(f['over']))
    rows.append(r); worst['reachN'] = max(worst['reachN'], r['reachN']); worst['reachF'] = max(worst['reachF'], r['reachF']); worst['wrist'] = max(worst['wrist'], abs(r['wristF']))
    worst['top'] = min(worst['top'], top); worst['low'] = max(worst['low'], low); worst['faceN'] += fN; worst['faceF'] += fF; worst['handleN'] += hN; worst['elbowFace'] += eF
    uu = n['u'] if n['u'] > 0 else n['u'] + 360; worst['upperMin'] = min(worst['upperMin'], uu); worst['upperMax'] = max(worst['upperMax'], uu)
bad = [r['t'] for r in rows if r['reachN'] > .9 or r['reachF'] > .9 or abs(r['wristF']) > 35 or r['top'] < TOPLIM or r['low'] > GROUND - 4 or r['overF'] or r['faceN'] or r['upperFace']]
summ = dict(arm={'near': [round(L1N, 1), round(L2N, 1)], 'far': [round(L1F, 1), round(L2F, 1)]}, restAngles={'near_upper': round(u0N, 1), 'near_fore': round(f0N, 1), 'near_axe_minus_fore': round(dN, 1), 'far_axe': round(a0F, 1), 'far_wrist_rest': round(wF0, 1)},
            limits={'top': TOPLIM, 'ground': GROUND}, worst={k: (round(v, 3) if isinstance(v, float) else v) for k, v in worst.items()}, badFrames=bad, hits=HIT)
TK = sorted(set([k[0] for k in KB] + [k[0] for k in KN] + [k[0] for k in KF]))
# 엔진은 fuA·flA 키 값을 그대로 보간 → 값을 감지 말고(wrap) 키 사이 윗팔·팔뚝 각 변화를 따라 이어 붙임(unwrap).
#   감은 값으로 넣으면 .19 → .28 에 엔진이 팔뚝을 반대로 150° 돌려 .25 에 도끼가 땅으로 향함(첫 v1 렌더)
KNu = [list(KN[0])]
for k in KN[1:]: KNu.append([k[0], KNu[-1][1] + wrap(k[1] - KNu[-1][1]), KNu[-1][2] + wrap(k[2] - KNu[-1][2])])
def near_unwrapped(t):
    a, b, w = lerpk(KNu, t); return a[1] + (b[1] - a[1]) * w, a[2] + (b[2] - a[2]) * w
ENG = []
for t in TK:
    th, off = body(t); f = far(t, th, off); u, fo = near_unwrapped(t)
    fuA = u - u0N - math.degrees(th); flA = (fo - u) - (f0N - u0N)
    ENG.append([round(t, 3), round(float(f['F'][0] - H[0]), 2), round(float(f['F'][1] - H[1]), 2), round(float(f['A']), 2), round(th, 4), round(float(off[1]), 2), round(math.radians(fuA), 4), round(math.radians(flA), 4)])
print('engine fuA·flA(이어 붙임):', [(e[0], e[6], e[7]) for e in ENG])
json.dump(dict(summary=summ, rows=rows, engine=ENG, keys=dict(body=KB, near=[list(map(float, k)) for k in KN], far=[(k[0], list(map(float, k[1])), k[2]) for k in KF])), open(os.path.join(SRC, 'review', 'plan_alt30.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps(summ, ensure_ascii=False, indent=1))
# ---- 키 자세 그림(조각 오리기 전 모양 — 팔은 막대, 도끼는 원화) ----
def warp(img, Mx, W, Hh): return cv2.warpAffine(img, Mx, (W, Hh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
def aff(Fi0, A0, Fi, A, ox, oy):
    c, s = math.cos(math.radians(A - A0)), math.sin(math.radians(A - A0)); Rm = np.array([[c, -s], [s, c]]); t = Fi - Rm @ Fi0
    return np.hstack([Rm, (t + [ox, oy])[:, None]])
OX, OY, CW, CH = 120, 150, 512 + 260, 512 + 150
mcN = np.zeros_like(RA); mcN[mN] = RA[mN]; mcF = np.zeros_like(RA); mcF[mF] = RA[mF]
ghost = RA.copy(); ghost[(cv2.dilate((mN | mF).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) | lab('upperN', 'foreN', 'fistN', 'upperF', 'foreF', 'fistF')] = 0
up_ = ghost.copy(); up_[YY >= 386] = 0; lo_ = ghost.copy(); lo_[YY < 386] = 0
fnt = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 22); fs = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 17)
def over(dst, src):
    a = src[..., 3:4] / 255.0; dst[..., :3] = (src[..., :3] * a + dst[..., :3] * (1 - a)).astype(np.uint8); dst[..., 3] = np.maximum(dst[..., 3], src[..., 3])
def limb(d, p, q, w, col):
    d.line([tuple(p), tuple(q)], fill=(25, 20, 20), width=w + 5); d.line([tuple(p), tuple(q)], fill=col, width=w)
    for z in (p, q): d.ellipse([z[0] - w / 2, z[1] - w / 2, z[0] + w / 2, z[1] + w / 2], fill=col)
def frame(t, label):
    th, off = body(t); n = near(t, th, off); f = far(t, th, off); o = np.array([OX, OY])
    C = np.zeros((CH, CW, 4), np.uint8); C[..., :3] = 255; C[..., 3] = 255
    img = Image.fromarray(C); d = ImageDraw.Draw(img)
    limb(d, f['S'] + o, f['E'] + o, 22, (226, 128, 60)); limb(d, f['E'] + o, f['F'] + o, 22, (236, 222, 196))
    C = np.array(img)
    c, s = math.cos(th), math.sin(th); Rm = np.array([[c, -s], [s, c]]); Mb = np.hstack([Rm, (H + off - Rm @ H + o)[:, None]])
    over(C, warp(up_, Mb, CW, CH)); over(C, warp(lo_, np.array([[1, 0, OX + off[0] * .3], [0, 1, OY]], float), CW, CH))
    over(C, warp(mcF, aff(FF, a0F, f['F'], f['A'], OX, OY), CW, CH))
    img = Image.fromarray(C); d = ImageDraw.Draw(img); d.ellipse([f['F'][0] + OX - 15, f['F'][1] + OY - 15, f['F'][0] + OX + 15, f['F'][1] + OY + 15], fill=(40, 36, 38), outline=(10, 10, 10), width=4)
    C = np.array(img); over(C, warp(mcN, aff(FN, a0N, n['F'], n['A'], OX, OY), CW, CH))
    img = Image.fromarray(C); d = ImageDraw.Draw(img)
    limb(d, n['S'] + o, n['E'] + o, 26, (226, 128, 60)); limb(d, n['E'] + o, n['F'] + o, 26, (236, 222, 196))
    d.ellipse([n['F'][0] + OX - 16, n['F'][1] + OY - 16, n['F'][0] + OX + 16, n['F'][1] + OY + 16], fill=(40, 36, 38), outline=(10, 10, 10), width=4)
    d.line([(0, TOPLIM - 10 + OY), (CW, TOPLIM - 10 + OY)], fill=(230, 60, 60), width=2); d.line([(0, GROUND + OY), (CW, GROUND + OY)], fill=(150, 150, 150), width=2)
    r = rows[min(60, round(t * 60))]
    d.text((10, 8), label, fill=(20, 20, 20), font=fnt)
    d.text((10, 38), f"t {t:.2f}  펴짐 가까운 {n['reach']:.2f} · 먼 {f['reach']:.2f}  먼 손목 {f['wrist']:+.0f}°  가까운 윗팔 {n['u']:.0f}°", fill=(60, 60, 60), font=fs)
    d.text((10, 60), f"fuA {math.radians(n['fuA']):+.2f} · flA {math.radians(n['flA']):+.2f}  꼭대기 y {r['top']:.0f}(한계 {TOPLIM:.0f}) · 아래 {r['low']:.0f}", fill=(60, 60, 60), font=fs)
    return img
SHOTS = [(0.00, '대기(원화)'), (0.10, '① 예비 — 가까운 도끼 젖힘'), (0.19, '② 머리 위를 넘음'), (0.28, '③ 1타 — 가까운(오른손) 도끼'), (0.40, '④ 먼 도끼 젖힘 · 가까운 도끼 다시 듦'),
         (0.47, '⑤ 먼 도끼 휘두름'), (0.54, '⑥ 2타 — 먼(왼손) 도끼'), (0.72, '⑦ 돌아옴'), (1.00, '대기')]
tiles = [frame(t, l) for t, l in SHOTS]; s = 0.6; tw, thh = int(CW * s), int(CH * s)
sheet = Image.new('RGB', (tw * 3 + 20, thh * 3 + 20), (255, 255, 255))
for k, im in enumerate(tiles): sheet.paste(im.convert('RGB').resize((tw, thh), Image.LANCZOS), ((k % 3) * (tw + 10), (k // 3) * (thh + 10)))
sheet.save(os.path.join(SRC, 'review', 'plan_alt30.png')); print('saved review/plan_alt30.png', sheet.size)
