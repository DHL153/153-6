"""10 러스트 브루노 — '번갈아 내려찍기'(DHL 10-20 21:49 '양손 무기를 한 번씩 번갈아') 키 풀이 + 1/60 검사 + 키 자세 그림(조각 오기 전 연구) — 2026-10-20 22:02
  엔진에 옮길 때의 구조(그대로 쓸 수 있게 같은 식으로 풂):
   · 먼 도끼(화면 오른쪽, 왼손) = swordGrip 칼(키 gx·gy·sa) + 먼 팔 길이 고정 두 관절 IK(armIK) — 9·19 팔로메와 같은 길
   · 가까운 도끼(화면 왼쪽, 오른손) = freeArm(키 fuA·flA — 윗팔·팔뚝 각을 더함, 길이 그대로) + 팔뚝 뼈에 붙은 도끼(손목 고정: 도끼 각 = 팔뚝 각 + 대기 때 차이)
  키는 '세상 각(도)·원화 px' 로 적고, 엔진 값(fuA·flA = 세상 각 − 대기 각 − 몸 기울기)으로 바꿔 표에 같이 적음
  검사(1/60): 팔 펴짐 d/(윗팔+팔뚝) ≤ .90(실수 33) · 먼 손목 꺾임 ≤ 35°(대기 대비) · 도끼 꼭대기 ≥ 게임 칸 위 끝 + 10(실수 36) · 도끼 머리 땅 위 · 팔뚝·주먹이 얼굴 위를 지나는 프레임 수(실수 30·32) · 먼 어깨 깊이(실수 41)
입력: ../measure10.json · 원화(measure10 과 같은 것)   출력: ../review/plan_alt10.png(키 자세 그림) · ../review/plan_alt10.json(1/60 표)
실행: python3 -I plan_alt10.py
"""
import json, math, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(os.path.join(HERE, '..')); REPO = os.path.abspath(os.path.join(SRC, '..', '..', '..', '..'))
M = json.load(open(os.path.join(SRC, 'measure10.json')))
RA = np.array(Image.open(os.path.join(REPO, 'assets', 'art', 'characters', M['art'])).convert('RGBA'))
V = lambda p: np.array(p, float); X2 = lambda a, b: float(a[0] * b[1] - a[1] * b[0]); ang = lambda v: math.degrees(math.atan2(v[1], v[0])); U = lambda d: np.array([math.cos(math.radians(d)), math.sin(math.radians(d))])
H = V(M['hip']); N, F = M['near'], M['far']
SHN, ELN, FN, HDN = V(N['SH']), V(N['EL']), V(N['fist']), V(N['head']); SHF, ELF, FF, HDF = V(F['SH']), V(F['EL']), V(F['fist']), V(F['head'])
L1N, L2N = np.linalg.norm(ELN - SHN), np.linalg.norm(FN - ELN); L1F, L2F = np.linalg.norm(ELF - SHF), np.linalg.norm(FF - ELF)
u0N, f0N, a0N = ang(ELN - SHN), ang(FN - ELN), ang(HDN - FN); dN = a0N - f0N          # 가까운 팔: 윗팔·팔뚝·도끼 세상 각(대기), 도끼 − 팔뚝
f0F, a0F = ang(FF - ELF), ang(HDF - FF); wF0 = a0F - f0F                                # 먼 팔: 팔뚝·도끼(대기), 손목 차이
sideF = np.sign(X2(FF - SHF, ELF - SHF))                                          # 먼 팔꿈치 쪽(대기와 같게)
GROUND = M['sole_y']; TOPLIM = M['gameTop_est']['y'] + 10
FACE_C, FACE_R = V([262, 262]), (30, 36)                                                # 얼굴(눈·코) 타원 — 몸과 같이 움직임
# ---- 키 (시각 s, 몸: lean 라디안 + 골반 이동 px / 가까운 팔: 윗팔·팔뚝 세상 각 / 먼 팔: 주먹 자리 + 도끼 세상 각) ----
#  ① 0~.10 예비(몸 살짝 뒤로, 가까운 도끼를 머리 뒤로 더 젖힘)  ② .10~.28 가까운 도끼 내려찍기(머리 위를 넘어 앞 아래, 날이 앞장섬) — 1타 .28
#  ③ .28~.40 가까운 도끼 버팀 → 다시 들기(풍차처럼: 한쪽이 내려오면 다른 쪽이 올라감), 먼 도끼 젖힘   ④ .40~.54 먼 도끼 내려찍기 — 2타 .54   ⑤ .54~1.0 둘 다 대기 자세로
# 몸(시각, 기울기 rad, 골반 x, 골반 y) — 엔진 칼 동작엔 골반 x 트랙이 없어 x = 0(골반은 hipY 로 내려감만)
KB = [(0.00, 0.00, 0, 0), (0.10, -0.06, 0, 3), (0.20, 0.04, 0, 4), (0.28, 0.14, 0, 8), (0.36, 0.08, 0, 6), (0.42, -0.02, 0, 4), (0.48, 0.08, 0, 8),
      (0.54, 0.18, 0, 12), (0.64, 0.12, 0, 10), (0.84, 0.02, 0, 2), (1.00, 0.00, 0, 0)]
# 가까운 팔(윗팔·팔뚝 세상 각) — 펴짐 ≤ .9 이려면 두 마디 사이 각 ≥ 57°
# v1.2(10-21 00:17, DHL 00:15 '팔이 떨어져 있어요' — 0.22초): 가까운 윗팔(34.5px)은 원화에서 거의 재킷 짧은 소매 속이고, 보이는 건 소매 입구 → 팔꿈치뿐.
#   v1 은 윗팔을 대기 방향에서 +76°(머리 위, .19)~−66°(아래, .28~.42) 돌려서, 팔꿈치가 소매 입구를 벗어나 팔뚝이 소매·몸과 떨어져 보였음(윗팔 관은 상체·머리 뒤라 안 보임).
#   → 윗팔은 소매 입구 방향(대기 158°) ±25° 안에서만(UCONE), 내려찍기는 팔꿈치 둘레 팔뚝 회전 + 몸 기울기로
UCONE = 25
KN = [(0.00, u0N, f0N), (0.10, 176, -126), (0.19, 180, -64), (0.28, 160, 18), (0.34, 160, 20), (0.40, 176, -64), (0.50, 172, -82), (0.62, 165, -96), (0.80, 160, -100), (1.00, u0N, f0N)]
# v1 키(비교용): (0.19, -126, -62) (0.28, 92, 15) (0.34, 96, 17) (0.42, 105, -10) (0.50, 135, -70) (0.62, 152, -94)
# 먼 팔(주먹 자리 원화 px · 도끼 세상 각) — 'a' = 그 둘레 ±28px 에서 펴짐 ≤ .86 · 손목 꺾임 최소인 자리로 찾음(rekey19 와 같은 생각)
KF = [(0.00, FF, a0F), (0.10, (345, 287), -64), (0.28, (334, 262), -88), (0.40, (322, 254), -112, 'a'), (0.47, (366, 268), -45, 'a'), (0.54, (384, 352), 14, 'a'),
      (0.64, (380, 352), 15, 'a'), (0.84, (362, 300), -42, 'a'), (1.00, FF, a0F)]
HIT = [0.28, 0.54]
def ease(x): return x * x * (3 - 2 * x)
def lerpk(K, t):
    for i in range(len(K) - 1):
        if K[i][0] <= t <= K[i + 1][0]:
            w = ease((t - K[i][0]) / (K[i + 1][0] - K[i][0])); return K[i], K[i + 1], w
    return K[-1], K[-1], 0.0
def wrap(d): return (d + 180) % 360 - 180
def body(t):
    a, b, w = lerpk(KB, t); return a[1] + (b[1] - a[1]) * w, np.array([a[2] + (b[2] - a[2]) * w, a[3] + (b[3] - a[3]) * w])
def xf(p, th, off):   # 윗몸 점 → 기울기(골반 둘레) + 골반 이동
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
def solve_far_keys():   # 'a' 키: 둘레 격자에서 펴짐 ≤ .86 · |손목| 최소(+ 목표 자리와 거리)
    for i, k in enumerate(KF):
        if len(k) < 4: continue
        th, off = body(k[0]); best = None
        for dx in range(-28, 29, 2):
            for dy in range(-28, 29, 2):
                G = V(k[1]) + [dx, dy]; S = xf(SHF, th, off); d = np.linalg.norm(G - S)
                if d > .86 * (L1F + L2F): continue
                KF[i] = (k[0], tuple(G), k[2]); w = far(k[0], th, off)['wrist']; sc = w * w + 0.03 * (dx * dx + dy * dy)
                if place(PF, G, k[2])[:, 1].max() > GROUND - 14: continue   # 도끼 날이 땅 위 14px 이상
                if best is None or sc < best[0]: best = (sc, tuple(map(float, G)), w)
        KF[i] = (k[0], best[1], k[2]); print('far key', k[0], 'grip', np.round(best[1], 1), 'wrist', round(best[2], 1))
# ---- 도끼 오림(원화) — 손잡이 띠 ±11 + 머리 상자, 축 좌표(u 축 따라 머리 쪽 +, v 오른쪽 +) ----
YY, XX = np.mgrid[0:512, 0:512].astype(float); AL = RA[..., 3] > 20
def axe_mask(Fi, Hd):
    ax = (Hd - Fi) / np.linalg.norm(Hd - Fi); nv = np.array([-ax[1], ax[0]]); hu = np.linalg.norm(Hd - Fi)
    u = (XX - Fi[0]) * ax[0] + (YY - Fi[1]) * ax[1]; v = (XX - Fi[0]) * nv[0] + (YY - Fi[1]) * nv[1]
    return AL & (((u > -32) & (u < hu) & (np.abs(v) < 11)) | ((u > hu - 62) & (u < hu + 82) & (v > -72) & (v < 104)))
mN, mF = axe_mask(FN, HDN), axe_mask(FF, HDF)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); tt = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + tt * d[0])) ** 2 + (YY - (p[1] + tt * d[1])) ** 2 <= r * r
armN = cap(SHN, ELN, 17) | cap(ELN, FN, 15) | cap(FN, FN, 18); armF = cap(SHF, ELF, 15) | cap(ELF, FF, 14) | cap(FF, FF, 18)
ghost = RA.copy(); ghost[(cv2.dilate((mN | mF).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0) | (armN & AL) | (armF & AL)] = 0   # 도끼 외곽선 2~3px 까지
def axe_px(m, Fi, A0):   # 오린 도끼 픽셀의 축 좌표(꼭대기·땅 검사용)
    ys, xs = np.nonzero(m); P = np.stack([xs, ys], 1).astype(float) - Fi; c, s = math.cos(math.radians(-A0)), math.sin(math.radians(-A0))
    return np.stack([c * P[:, 0] - s * P[:, 1], s * P[:, 0] + c * P[:, 1]], 1)
PN, PF = axe_px(mN, FN, a0N), axe_px(mF, FF, a0F)
def place(P, Fi, A):
    c, s = math.cos(math.radians(A)), math.sin(math.radians(A)); return np.stack([c * P[:, 0] - s * P[:, 1], s * P[:, 0] + c * P[:, 1]], 1) + Fi
solve_far_keys()
def seg_face(p, q, th, off, n=12):   # 선분(팔꿈치→주먹)이 얼굴 타원 안을 지나나
    C = xf(FACE_C, th, off)
    for k in range(n + 1):
        z = p + (q - p) * k / n
        if ((z[0] - C[0]) / FACE_R[0]) ** 2 + ((z[1] - C[1]) / FACE_R[1]) ** 2 <= 1: return True
    return False
# ---- 1/60 표 ----
rows = []; worst = dict(reachN=0, reachF=0, wrist=0, top=1e9, low=-1e9, faceN=0, faceF=0, handleN=0, upperN=0)
for i in range(61):
    t = i / 60; th, off = body(t); n = near(t, th, off); f = far(t, th, off)
    QN = place(PN, n['F'], n['A']); QF = place(PF, f['F'], f['A'])
    top = float(min(QN[:, 1].min(), QF[:, 1].min())); low = float(max(QN[:, 1].max(), QF[:, 1].max()))
    fN = seg_face(n['E'], n['F'], th, off); fF = seg_face(f['E'], f['F'], th, off)
    hN = seg_face(n['F'], n['F'] + 150 * U(n['A']), th, off)   # 가까운 도끼 자루가 얼굴 위
    r = dict(t=round(t, 3), lean=round(th, 3), reachN=round(n['reach'], 3), reachF=round(f['reach'], 3), wristF=round(f['wrist'], 1), fuA=round(math.radians(n['fuA']), 3), flA=round(math.radians(n['flA']), 3),
             upperN=round(wrap(n['u'] - u0N), 1), axeN=round(n['A'], 1), axeF=round(f['A'], 1), top=round(top, 1), low=round(low, 1), faceN=bool(fN), faceF=bool(fF), handleN=bool(hN), overF=bool(f['over']))
    rows.append(r); worst['reachN'] = max(worst['reachN'], r['reachN']); worst['reachF'] = max(worst['reachF'], r['reachF']); worst['wrist'] = max(worst['wrist'], abs(r['wristF']))
    worst['top'] = min(worst['top'], top); worst['low'] = max(worst['low'], low); worst['faceN'] += fN; worst['faceF'] += fF; worst['handleN'] += hN; worst['upperN'] = max(worst['upperN'], abs(r['upperN']))
bad = [r['t'] for r in rows if abs(r['upperN']) > UCONE or r['reachN'] > .9 or r['reachF'] > .9 or abs(r['wristF']) > 35 or r['top'] < TOPLIM or r['low'] > GROUND - 4 or r['overF']]
summ = dict(arm={'near': [round(L1N, 1), round(L2N, 1)], 'far': [round(L1F, 1), round(L2F, 1)]}, restAngles={'near_upper': round(u0N, 1), 'near_fore': round(f0N, 1), 'near_axe_minus_fore': round(dN, 1), 'far_axe': round(a0F, 1), 'far_wrist_rest': round(wF0, 1)},
            limits={'top': TOPLIM, 'ground': GROUND}, worst={k: (round(v, 3) if isinstance(v, float) else v) for k, v in worst.items()}, badFrames=bad, hits=HIT,
            edgeLeads='두 도끼 모두 날이 오른쪽(앞) — 앞 아래로 내려찍는 시계 방향 회전이라 날이 앞장섬(19 v1.3 칼날 반전 교훈 확인)')
TK = sorted(set([k[0] for k in KB] + [k[0] for k in KN] + [k[0] for k in KF]))
ENG = []
for t in TK:   # 엔진 키: [t, gx, gy(골반 기준, 원화 px — 엔진엔 ×2, gy 는 hipY 를 빼서), sa(도), lean(rad), hipY(원화 px), fuA, flA(rad)]
    th, off = body(t); n = near(t, th, off); f = far(t, th, off)
    ENG.append([round(t, 3), round(float(f['F'][0] - H[0]), 2), round(float(f['F'][1] - H[1]), 2), round(float(f['A']), 2), round(th, 4), round(float(off[1]), 2), round(math.radians(n['fuA']), 4), round(math.radians(n['flA']), 4)])
json.dump(dict(summary=summ, rows=rows, engine=ENG, keys=dict(body=KB, near=KN, far=[(k[0], list(map(float, k[1])), k[2]) for k in KF])), open(os.path.join(SRC, 'review', 'plan_alt10.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps(summ, ensure_ascii=False, indent=1))
# ---- 키 자세 그림 ----
def warp(img, Mx, W, Hh): return cv2.warpAffine(img, Mx, (W, Hh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
def aff(Fi0, A0, Fi, A, ox, oy):
    c, s = math.cos(math.radians(A - A0)), math.sin(math.radians(A - A0)); R = np.array([[c, -s], [s, c]]); t = Fi - R @ Fi0
    return np.hstack([R, (t + [ox, oy])[:, None]])
OX, OY, CW, CH = 90, 130, 512 + 230, 512 + 130
axN = np.zeros_like(RA); axN[mN] = RA[mN]; axF = np.zeros_like(RA); axF[mF] = RA[mF]
up = ghost.copy(); up[YY >= 386] = 0; lo = ghost.copy(); lo[YY < 386] = 0
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
    limb(d, f['S'] + o, f['E'] + o, 22, (95, 98, 52)); limb(d, f['E'] + o, f['F'] + o, 20, (226, 206, 168))   # 먼 윗팔·팔뚝 = 몸 뒤
    C = np.array(img)
    c, s = math.cos(th), math.sin(th); R = np.array([[c, -s], [s, c]]); Mb = np.hstack([R, (H + off - R @ H + o)[:, None]])
    over(C, warp(up, Mb, CW, CH)); over(C, warp(lo, np.array([[1, 0, OX + off[0] * .3], [0, 1, OY]], float), CW, CH))
    over(C, warp(axF, aff(FF, a0F, f['F'], f['A'], OX, OY), CW, CH))
    img = Image.fromarray(C); d = ImageDraw.Draw(img); d.ellipse([f['F'][0] + OX - 15, f['F'][1] + OY - 15, f['F'][0] + OX + 15, f['F'][1] + OY + 15], fill=(205, 108, 52), outline=(25, 20, 20), width=4)
    C = np.array(img); over(C, warp(axN, aff(FN, a0N, n['F'], n['A'], OX, OY), CW, CH))
    img = Image.fromarray(C); d = ImageDraw.Draw(img)
    limb(d, n['S'] + o, n['E'] + o, 24, (95, 98, 52)); limb(d, n['E'] + o, n['F'] + o, 22, (226, 206, 168))
    d.ellipse([n['F'][0] + OX - 16, n['F'][1] + OY - 16, n['F'][0] + OX + 16, n['F'][1] + OY + 16], fill=(205, 108, 52), outline=(25, 20, 20), width=4)
    d.line([(0, TOPLIM - 10 + OY), (CW, TOPLIM - 10 + OY)], fill=(230, 60, 60), width=2); d.line([(0, GROUND + OY), (CW, GROUND + OY)], fill=(150, 150, 150), width=2)
    r = rows[min(60, round(t * 60))]
    d.text((10, 8), label, fill=(20, 20, 20), font=fnt)
    d.text((10, 38), f"t {t:.2f}  펴짐 가까운 {n['reach']:.2f} · 먼 {f['reach']:.2f}  먼 손목 {f['wrist']:+.0f}°", fill=(60, 60, 60), font=fs)
    d.text((10, 60), f"fuA {math.radians(n['fuA']):+.2f} · flA {math.radians(n['flA']):+.2f}  꼭대기 y {r['top']:.0f}(한계 {TOPLIM:.0f})", fill=(60, 60, 60), font=fs)
    return img
SHOTS = [(0.00, '대기(원화)'), (0.10, '① 예비 — 가까운 도끼 젖힘'), (0.19, '② 머리 위를 넘음'), (0.28, '③ 1타 — 가까운(오른손) 도끼'), (0.40, '④ 먼 도끼 젖힘 · 가까운 도끼 다시 듦'),
         (0.47, '⑤ 먼 도끼 휘두름'), (0.54, '⑥ 2타 — 먼(왼손) 도끼'), (0.72, '⑦ 돌아옴'), (1.00, '대기')]
tiles = [frame(t, l) for t, l in SHOTS]; s = 0.62; tw, thh = int(CW * s), int(CH * s)
sheet = Image.new('RGB', (tw * 3 + 20, thh * 3 + 20), (255, 255, 255))
for k, im in enumerate(tiles): sheet.paste(im.convert('RGB').resize((tw, thh), Image.LANCZOS), ((k % 3) * (tw + 10), (k // 3) * (thh + 10)))
sheet.save(os.path.join(SRC, 'review', 'plan_alt10.png')); print('saved review/plan_alt10.png', sheet.size)
