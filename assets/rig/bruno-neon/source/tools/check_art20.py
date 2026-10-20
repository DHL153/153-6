"""20 네온 브루노 새 원화(프롬프트 0) 검수 — python3 -I check_art20.py 새원화.png [출력.png]   (2026-10-21 01:01, check_art19 구조)
기준: 첨부 2 = char_0010(10 러스트 자세·크기), 첨부 3 = refs/ref_mace_fit20.png(fit20.py — 철퇴 공 가운데 = 러스트 도끼 머리 가운데, 가시 끝 반지름 48)
보는 것: ①불투명 범위·가장자리 잘림·투명 배경 ②두 발바닥(러스트 498)·바닥 평평(맨 아래 6줄 폭 — 가시 끝이면 좁음)
③몸 겹침 IoU(y ≥ 320, 러스트 몸 라벨 = 상체·골반·다리·팔·주먹 — 포니테일·머리숱·도끼 뺌; 네온은 포니테일이 없어 머리 아래를 뺌)
④머리: 네온 원화(char_0020 옛 그림) 머리와 SIFT → 배율(목표 ≈ .83 = 러스트 머리 134 / 네온 162)·안경 자리
⑤철퇴 공: 네온 원화 가까운 공을 SIFT 로 찾아 가운데·배율(목표 .75)·fit 가운데와 거리 ⑥자루: 러스트 주먹 → 찾은 공 가운데 선 위 불투명 비율
출력 그림: 새 원화 + 파랑 러스트 몸 외곽선 + 빨강 fit 철퇴(공 원·자루 선) / 머리 나란히 / 두 주먹 3배 / 두 발 3배 / 숫자
"""
import sys, os, math, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); RIG = os.path.abspath(os.path.join(SRC, '..', '..')); ART = os.path.join(RIG, '..', 'art', 'characters')
_im = Image.open(sys.argv[1]).convert('RGBA'); new = np.array(_im if _im.size == (512, 512) else _im.resize((512, 512), Image.LANCZOS))
out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SRC, 'review', 'check_art20.png'); os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
a10 = np.array(Image.open(os.path.join(ART, 'char_0010.png')).convert('RGBA'))
a20 = np.array(Image.open(os.path.join(SRC, 'refs', 'ref_design_char0020.png')).convert('RGBA'))      # 옛 20 원화(디자인 기준)
BR = os.path.join(RIG, 'bruno-rust', 'source'); L10 = np.load(os.path.join(BR, 'work', 'labels.npy')); NM = json.load(open(os.path.join(BR, 'work', 'label_names.json')))
M10 = json.load(open(os.path.join(BR, 'measure10.json')))
lab = lambda *ns: np.logical_or.reduce([L10 == NM.index(n) + 1 for n in ns])
YY, XX = np.mgrid[0:512, 0:512]
FIT = {'near': np.array(M10['near']['head']), 'far': np.array(M10['far']['head'])}; FIST = {'near': np.array(M10['near']['fist'], float), 'far': np.array(M10['far']['fist'], float)}; BALL_R = 48.0
op = new[..., 3] > 128; rep = []
ys, xs = np.nonzero(op); rep.append(f'불투명 범위 x {xs.min()}~{xs.max()} · y {ys.min()}~{ys.max()}')
edge = op[0].any() or op[-1].any() or op[:, 0].any() or op[:, -1].any(); rep.append('가장자리 잘림: ' + ('있음 ✗' if edge else '없음 ✓'))
corner = int(new[:8, :8, 3].max()) + int(new[-8:, -8:, 3].max()); rep.append('투명 배경: ' + ('✓' if corner == 0 else f'✗ (모서리 알파 {corner})'))
# ② 발 — 몸 가운데(x 252) 기준 왼쪽 = 가까운 발, 오른쪽 = 먼 발
feet = {}
for nm, xm in (('가까운', XX < 252), ('먼', XX >= 252)):
    m = op & xm & (YY > 420); yb = int(np.nonzero(m.any(1))[0].max()); w6 = [int(m[y].sum()) for y in range(yb - 5, yb + 1)]
    feet[nm] = (yb, w6); rep.append(f'{nm} 발바닥 y {yb} (러스트 498) · 맨 아래 6줄 폭 {w6} → ' + ('평평 ✓' if min(w6[:3]) >= 25 else '좁음(뾰족?) ✗'))
# ③ 몸 겹침
b10 = (a10[..., 3] > 128) & lab('torso', 'hips', 'legN', 'legF', 'upperN', 'foreN', 'fistN', 'upperF', 'foreF', 'fistF')
low = YY >= 320; iou = (op & b10 & low).sum() / max(1, ((op | b10) & low).sum()); rep.append(f'몸 겹침 IoU(y ≥ 320) {iou:.3f} (19 합격 .875 · 기준 .75)')
# ④ 머리 SIFT — 옛 원화 머리(먼 철퇴 자루 띠 뺌)
_g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY)
sf = cv2.SIFT_create(4000)
def band_mask(p, q, w):
    p, q = np.array(p, float), np.array(q, float); d = q - p; L = np.linalg.norm(d); u = d / L; n = np.array([-u[1], u[0]])
    s = (XX - p[0]) * u[0] + (YY - p[1]) * u[1]; t = (XX - p[0]) * n[0] + (YY - p[1]) * n[1]; return (s > -w) & (s < L + w) & (np.abs(t) < w)
hm = np.zeros((512, 512), bool); hm[85:305, 170:405] = True; hm &= (a20[..., 3] > 128) & ~band_mask((180, 40), (500, 250), 20) & ~(np.hypot(XX - 235, YY - 75) < 70)
HEAD = None
def sift_find(src, smask, dmask, tag):
    k1, d1 = sf.detectAndCompute(_g(src), (smask * 255).astype(np.uint8)); k2, d2 = sf.detectAndCompute(_g(new), (dmask * 255).astype(np.uint8))
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < 0.75 * b.distance]
    if len(mm) < 6: raise ValueError(f'{tag}: 맞는 점 {len(mm)}개')
    M, inl = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in mm]), np.float32([k2[a.trainIdx].pt for a in mm]), ransacReprojThreshold=4.0)
    return M, int(inl.sum())
try:
    M, n_in = sift_find(a20, hm, op & (YY < 360), '머리'); sc = float(np.hypot(M[0, 0], M[1, 0])); gl = M[:, :2] @ np.array([345.0, 235.0]) + M[:, 2]
    HEAD = (M, sc); rep.append(f'머리(옛 20 원화와 SIFT {n_in}점): 배율 ×{sc:.3f} (목표 ≈ .83) · 회전 {math.degrees(math.atan2(M[1, 0], M[0, 0])):+.1f}° · 안경 가운데 ({gl[0]:.0f},{gl[1]:.0f})' + (' ✓' if n_in >= 20 and abs(sc - .83) < .08 else ' ✗ 확인'))
except Exception as e:
    rep.append(f'머리: 옛 20 원화 머리와 못 맞춤({e}) ✗ — 눈으로')
# ⑤ 철퇴 공 SIFT — 옛 원화 가까운 공(가려진 곳 없음)
ball_src = (a20[..., 3] > 128) & (np.hypot(XX - 90, YY - 390) <= 64) & (XX < 150)
BALL = {}
for side, reg in (('near', (XX < 230) & (YY < 220)), ('far', (XX > 320) & (YY < 260))):
    try:
        M, n_in = sift_find(a20, ball_src, op & reg, side); sc = float(np.hypot(M[0, 0], M[1, 0])); c = M[:, :2] @ np.array([90.0, 390.0]) + M[:, 2]
        BALL[side] = (c, sc); dd = float(np.linalg.norm(c - FIT[side]))
        rep.append(f'{"가까운" if side == "near" else "먼"} 철퇴 공(SIFT {n_in}점): 가운데 ({c[0]:.0f},{c[1]:.0f}) · fit ({FIT[side][0]:.0f},{FIT[side][1]:.0f}) 와 {dd:.0f}px · 배율 ×{sc:.3f} (fit .75 → 반지름 {64 * sc:.0f} / 48)' + (' ✓' if dd < 20 and abs(sc - .75) < .1 else ' ✗ 확인'))
    except Exception as e:
        rep.append(f'{side} 철퇴 공 못 찾음({e}) ✗ — 눈으로')
# ⑥ 자루: 러스트 주먹 → 찾은 공 가운데, 공 가장자리 ~ 주먹 사이 선 위 불투명 비율 + 주먹 → 공 거리(러스트 도끼 184 · 174)
for side in ('near', 'far'):
    if side not in BALL: continue
    c, sc = BALL[side]; f = FIST[side]; L = np.linalg.norm(c - f); u = (c - f) / L
    pts = [f + u * s for s in np.linspace(20, L - 64 * sc, 40)]; cov = np.mean([op[int(round(p[1])), int(round(p[0]))] for p in pts])
    ang = math.degrees(math.atan2(u[0], -u[1])); ang0 = math.degrees(math.atan2(*(FIT[side] - f)[[0]], -(FIT[side] - f)[1])) if False else math.degrees(math.atan2((FIT[side] - f)[0], -(FIT[side] - f)[1]))
    rep.append(f'{"가까운" if side == "near" else "먼"} 자루: 러스트 주먹 → 공 {L:.0f}px (러스트 도끼 {np.linalg.norm(FIT[side] - f):.0f}) · 각 {ang:+.1f}° (fit {ang0:+.1f}°, 세로 기준) · 선 위 불투명 {cov:.2f}' + (' ✓' if cov > .9 else ' ✗ 주먹 자리 다름?'))
# 그림
def comp(a, bgc=(235, 238, 245)):
    bg = np.zeros((512, 512, 3)); bg[...] = bgc; al = a[..., 3:4] / 255.0; return (a[..., :3] * al + bg * (1 - al)).astype(np.uint8)
v = comp(new).copy()
e10 = cv2.dilate(b10.astype(np.uint8), np.ones((3, 3), np.uint8)) - b10.astype(np.uint8); v[e10 > 0] = (40, 90, 255)
for side in ('near', 'far'):
    cv2.circle(v, tuple(int(round(x)) for x in FIT[side]), int(BALL_R), (230, 30, 30), 1); cv2.line(v, tuple(int(x) for x in FIST[side]), tuple(int(round(x)) for x in FIT[side]), (230, 30, 30), 1)
    cv2.circle(v, tuple(int(x) for x in FIST[side]), 4, (230, 30, 30), -1)
big = Image.fromarray(v).resize((1024, 1024), Image.LANCZOS)
HS = 268
h20 = Image.fromarray(comp(a20)).crop((180, 90, 410, 320)).resize((HS, HS), Image.LANCZOS)
if HEAD is not None:
    Mh, sc = HEAD; cc = Mh[:, :2] @ np.array([295.0, 205.0]) + Mh[:, 2]; hh = 115 * sc; box = tuple(int(round(x)) for x in (cc[0] - hh, cc[1] - hh, cc[0] + hh, cc[1] + hh))
else:
    box = (170, 140, 360, 330)
hN = Image.fromarray(comp(new)).crop(box).resize((HS, HS), Image.LANCZOS)
Z = 3; zs = lambda b: Image.fromarray(comp(new)).crop(b).resize(((b[2] - b[0]) * Z, (b[3] - b[1]) * Z), Image.LANCZOS)
fN = zs((116, 214, 186, 290)); fF = zs((320, 258, 390, 334))                                    # 두 주먹 둘레(러스트 주먹 자리)
ftN = zs((150, 440, 250, 500)); ftF = zs((262, 440, 362, 500))                                  # 두 발
W = Image.new('RGB', (1024 + 600, 1024 + 40 + 330), (24, 26, 34)); W.paste(big, (0, 40))
W.paste(h20, (1034, 70)); W.paste(hN, (1034 + HS + 12, 70))
W.paste(fN, (10, 1074)); W.paste(fF, (10 + fN.width + 14, 1074)); W.paste(ftN, (10 + 2 * fN.width + 40, 1094)); W.paste(ftF, (10 + 2 * fN.width + 40 + ftN.width + 14, 1094))
d = ImageDraw.Draw(W); FN = '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'; f = ImageFont.truetype(FN, 20); fs = ImageFont.truetype(FN, 18)
d.text((8, 8), '새 원화 · 빨강 = fit 철퇴(공 원·주먹→공 선·러스트 주먹 점) · 파랑 = 러스트 몸 외곽선', fill=(255, 230, 120), font=f)
d.text((1034, 44), '옛 20 원화 머리', fill=(255, 255, 255), font=f); d.text((1034 + HS + 12, 44), '새 원화 머리(같은 자리·배율)', fill=(255, 255, 255), font=f)
d.text((10, 1046), '두 주먹 ×3 (러스트 주먹 자리)', fill=(255, 255, 255), font=f); d.text((10 + 2 * fN.width + 40, 1066), '두 발 ×3', fill=(255, 255, 255), font=f)
def wrap(t, w=570):
    out, cur = [], ''
    for ch in t:
        if d.textlength(cur + ch, font=fs) > w: out.append(cur); cur = '   ' + ch
        else: cur += ch
    return out + [cur]
yy = 70 + HS + 24
for line in rep:
    for seg in wrap(line):
        col = (255, 120, 110) if '✗' in line else (150, 230, 160) if '✓' in line else (220, 220, 220)
        d.text((1034, yy), seg.replace('✗', '×'), fill=col, font=fs); yy += 26
W.save(out_path); print('\n'.join(rep)); print('그림', os.path.abspath(out_path))
