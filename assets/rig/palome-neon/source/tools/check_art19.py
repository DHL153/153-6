"""19 네온 팔로메 새 원화(프롬프트 0) 검수 — python3 -I check_art19.py 새원화.png [출력.png]
기준: 첨부 2 = char_0009(9 러스트 자세·크기), 첨부 3 = refs/ref_sword_fit19.png 의 칼 자리(날밑 (374,239) · 칼끝 (124,66) · 폼멜 (469,327), 원화 512 px)
보는 것: ①발바닥·머리 위·몸 키(9 = 160 → 501, 341) ②몸 실루엣 겹침 IoU(y ≥ 250, 칼 띠 빼고 — 22 기준 .75) ③칼끝·폼멜이 그림 안인지(가장자리 잘림)
④칼 자리: 칼 띠(가이드 날 축 ±30px) 안 불투명 픽셀이 날 축 어디까지 가는지(칼끝까지 거리) ⑤투명 배경(모서리 알파 0) ⑥원화 19 와 얼굴 나란히(디자인 눈으로)
출력 그림: 새 원화 위에 가이드 칼 외곽선(빨강) + 9 몸 외곽선(파랑) / 19 원화 · 새 원화 머리 확대 / 숫자
"""
import sys, os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); RIG = os.path.abspath(os.path.join(HERE, '..', '..', '..')); ART = os.path.join(RIG, '..', 'art', 'characters')
new = np.array(Image.open(sys.argv[1]).convert('RGBA').resize((512, 512), Image.LANCZOS) if Image.open(sys.argv[1]).size != (512, 512) else Image.open(sys.argv[1]).convert('RGBA'))
out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, '..', 'review', 'check_art19.png'); os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
a9 = np.array(Image.open(os.path.join(ART, 'char_0009.png')).convert('RGBA')); a19 = np.array(Image.open(os.path.join(HERE, '..', 'refs', 'ref_design_char0019.png')).convert('RGBA'))   # 옛 19 원화(디자인 기준 — 게임 char_0019 는 10-20 19:0x 새 원화로 바뀜)
L9 = np.load(os.path.join(RIG, 'palome-rust', 'source', 'work', 'labels.npy'))
GD, TP, PM = np.array([374.0, 239.0]), np.array([124.0, 66.0]), np.array([469.0, 327.0])   # 가이드 칼 점
u = (TP - GD) / np.linalg.norm(TP - GD); nrm = np.array([-u[1], u[0]])
YY, XX = np.mgrid[0:512, 0:512]; Dg = np.stack([XX - GD[0], YY - GD[1]], -1); tg, sg = Dg @ u, Dg @ nrm
band = (tg > 20) & (tg < 700) & (np.abs(sg) < 30)   # 칼날 띠(날밑 위, 그림 끝까지 — 칼이 길게 오면 그 끝까지 잼)
op = new[..., 3] > 128
rep = []; HEAD = None   # (19 원화 머리 가운데 (240,200) 가 새 원화에서 놓인 자리, 배율) — 머리 확대 자리
ys, xs = np.nonzero(op); rep.append(f'불투명 범위 x {xs.min()}~{xs.max()} · y {ys.min()}~{ys.max()}')
edge = op[0].any() or op[-1].any() or op[:, 0].any() or op[:, -1].any(); rep.append('가장자리 잘림: ' + ('있음 ✗' if edge else '없음 ✓'))
corner = int(new[:8, :8, 3].max()) + int(new[-8:, -8:, 3].max()); rep.append('투명 배경: ' + ('✓' if corner == 0 else f'✗ (모서리 알파 {corner})'))
body = op & ~band & ~((tg > -10) & (tg < 40) & (np.abs(sg) < 55))
by = np.nonzero(body.any(1))[0]; top, sole = int(by.min()), int(by.max())
rep.append(f'발바닥 {sole} (9 = 501)')
# 머리 크기·자리 = 19 원화 머리(머리카락·안경·수염)와 SIFT 닮음 → 배율(목표 ×0.914 = 9 몸 크기) · 머리 가운데 자리
_g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY)
_hm = np.zeros((512, 512), np.uint8); _hm[120:300, 150:335] = 255; _hm &= ((a19[..., 3] > 128) * 255).astype(np.uint8)
_sf = cv2.SIFT_create(3000); _k1, _d1 = _sf.detectAndCompute(_g(a19), _hm); _k2, _d2 = _sf.detectAndCompute(_g(new), (op * 255).astype(np.uint8))
try:
    _m = [a for a, b in cv2.BFMatcher().knnMatch(_d1, _d2, k=2) if a.distance < 0.75 * b.distance]
    _M, _in = cv2.estimateAffinePartial2D(np.float32([_k1[a.queryIdx].pt for a in _m]), np.float32([_k2[a.trainIdx].pt for a in _m]), ransacReprojThreshold=4.0)
    _sc = float(np.hypot(_M[0, 0], _M[1, 0])); _c = _M[:, :2] @ np.array([230.0, 205.0]) + _M[:, 2]
    if int(_in.sum()) < 20: raise ValueError(f'맞는 점 {int(_in.sum())}개뿐')   # 19 머리를 못 찾음(다른 얼굴·그림체)
    HEAD = (_c, _sc)
    rep.append(f'머리(19 원화와 SIFT {int(_in.sum())}점): 배율 ×{_sc:.3f}(목표 .914) · 회전 {math.degrees(math.atan2(_M[1, 0], _M[0, 0])):+.1f}° · 안경 가운데 ({_c[0]:.0f},{_c[1]:.0f})')
except Exception as e:
    rep.append(f'머리: 19 원화 머리와 못 맞춤({e}) ✗ — 얼굴이 19 와 다른지 눈으로')
b9 = (a9[..., 3] > 128) & (L9 != 2) & (L9 != 3)
low = YY >= 250; iou = ((body & b9 & low).sum()) / max(1, ((body | b9) & low).sum()); rep.append(f'몸 겹침 IoU(y ≥ 250) {iou:.3f} (22 기준 .75)')
sw = op & band; ts = tg[sw]
if len(ts):
    far = float(ts.max()); rep.append(f'칼날 띠 안 가장 먼 점: 날밑에서 {far:.0f}px (가이드 칼끝 {np.linalg.norm(TP - GD):.0f}) → {"✓" if abs(far - np.linalg.norm(TP - GD)) < 25 else "✗ 확인"}')
    # 띠 안에서 날 가운데 선(가로 위치 평균)이 축에서 얼마나 벗어났나 — 칼 각 차이
    near_t = (sw & (tg > 120) & (tg < far - 20)); 
    if near_t.any():
        off = np.polyfit(tg[near_t], sg[near_t], 1); rep.append(f'칼 각 차이 ≈ {math.degrees(math.atan(off[0])):+.1f}° (가이드 축 기준, + = 칼끝이 시계 방향)')
pmz = op & (np.hypot(XX - PM[0], YY - PM[1]) < 22); rep.append('폼멜 자리(가이드 ±22px)에 그림: ' + ('있음 ✓' if pmz.sum() > 200 else f'적음({int(pmz.sum())}px) ✗ 확인'))
# 그림
def comp(a, bgc=(235, 238, 245)):
    bg = np.zeros((512, 512, 3)); bg[...] = bgc; al = a[..., 3:4] / 255.0; return (a[..., :3] * al + bg * (1 - al)).astype(np.uint8)
v = comp(new).copy()
e9 = cv2.dilate(b9.astype(np.uint8), np.ones((3, 3), np.uint8)) - b9.astype(np.uint8); v[e9 > 0] = (40, 90, 255)
gl = np.zeros((512, 512), np.uint8)
L = np.linalg.norm(TP - GD); poly = [GD + 12 * nrm, GD + (L - 30) * u + 20 * nrm, TP, GD + (L - 30) * u - 20 * nrm, GD - 12 * nrm]
cv2.polylines(v, [np.int32(poly)], True, (230, 30, 30), 1); cv2.circle(v, tuple(int(c) for c in PM), 14, (230, 30, 30), 1); cv2.line(v, tuple(int(c) for c in GD), tuple(int(c) for c in PM), (230, 30, 30), 1)
big = Image.fromarray(v).resize((1024, 1024), Image.LANCZOS)
HS = 268   # 머리 확대 칸
h19 = Image.fromarray(comp(a19)).crop((150, 110, 330, 290)).resize((HS, HS), Image.LANCZOS)
if HEAD is not None:   # SIFT 로 찾은 자리 — 19 머리 상자(150~330 × 110~290, 가운데 (240,200))를 같은 배율로 옮김
    (cx, cy), sc = HEAD; cx, cy = cx + (240 - 230) * sc, cy + (200 - 205) * sc; hh = 90 * sc
    box = (int(round(cx - hh)), int(round(cy - hh)), int(round(cx + hh)), int(round(cy + hh)))
else:                  # 못 찾으면 그림 맨 위에서 아래로
    box = (150, max(0, top - 20), 330, max(0, top - 20) + 180)
hN = Image.fromarray(comp(new)).crop(box).resize((HS, HS), Image.LANCZOS)
W = Image.new('RGB', (1024 + 576, 1024 + 40), (24, 26, 34)); W.paste(big, (0, 40)); W.paste(h19, (1034, 70)); W.paste(hN, (1034 + HS + 12, 70))
d = ImageDraw.Draw(W); FN = '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'; f = ImageFont.truetype(FN, 20); fs = ImageFont.truetype(FN, 18)
d.text((8, 8), '새 원화 · 빨강 = 가이드 칼 자리 · 파랑 = 9 몸 외곽선', fill=(255, 230, 120), font=f); d.text((1034, 44), '19 원화 머리', fill=(255, 255, 255), font=f); d.text((1034 + HS + 12, 44), '새 원화 머리(같은 자리·배율)', fill=(255, 255, 255), font=f)
def wrap(t, w=548):   # 글자 폭으로 줄 나눔
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
W.save(out_path)
print('\n'.join(rep)); print('그림', os.path.abspath(out_path))
