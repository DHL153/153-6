"""17 네온 루시아 새 원화(프롬프트 0 · 0-3b) 검수 — python3 -I check_art17.py 새원화.png [출력.png]
기준: 7 러스트 루시아 원화(char_0007 — 라벨 lucia-rust/source/work) · 도끼 맞춤 fit17(러스트 쥔 점 G (434.5,294) · 자루 축 −105.8° · 도끼 상자 y 50~372)
보는 것: ①불투명 범위·잘림·투명 배경 ②두 발바닥(러스트 448)·평평 ③몸 겹침 IoU(y ≥ 320, 러스트 몸·다리·먼 팔 — 방패·도끼 뺌)
④머리: 옛 17 원화 머리(모자·얼굴)와 SIFT 배율 ⑤도끼: 옛 원화 도끼 날을 SIFT 로 찾아 배율(fit .811)·러스트 쥔 점과 거리 ⑥방패: 아래 끝·y 300 오른쪽 끝(러스트 226)·옛 원화 방패 SIFT 배율
출력: review/check_art17.png (새 원화 + 파랑 러스트 몸 외곽선 · 머리 나란히 · 먼 주먹 3배 · 두 발 3배)
"""
import sys, os, math, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); RIG = os.path.abspath(os.path.join(SRC, '..', '..')); ART = os.path.join(RIG, '..', 'art', 'characters')
new = np.array(Image.open(sys.argv[1]).convert('RGBA')); assert new.shape[:2] == (512, 512)
out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SRC, 'review', 'check_art17.png')
a7 = np.array(Image.open(os.path.join(ART, 'char_0007.png')).convert('RGBA'))
a17 = np.array(Image.open(os.path.join(SRC, 'refs', 'ref_design_char0017.png')).convert('RGBA'))
RS = os.path.join(RIG, 'lucia-rust', 'source'); L7 = np.load(os.path.join(RS, 'work', 'labels.npy')); NM = json.load(open(os.path.join(RS, 'work', 'label_names.json')))
J7 = json.load(open(os.path.join(RS, 'joints7.json')))
lab = lambda *ns: np.logical_or.reduce([L7 == NM.index(n) + 1 for n in ns])
YY, XX = np.mgrid[0:512, 0:512]
op = new[..., 3] > 128; rep = []
ys, xs = np.nonzero(op); rep.append(f'불투명 범위 x {xs.min()}~{xs.max()} · y {ys.min()}~{ys.max()}')
edge = op[0].any() or op[-1].any() or op[:, 0].any() or op[:, -1].any(); rep.append('가장자리 잘림: ' + ('있음 ✗' if edge else '없음 ✓'))
corner = int(new[:8, :8, 3].max()) + int(new[-8:, -8:, 3].max()); rep.append('투명 배경: ' + ('✓' if corner == 0 else f'✗ (모서리 알파 {corner})'))
semi = int(((new[..., 3] > 0) & (new[..., 3] < 255)).sum()); rep.append(f'반투명 픽셀 {semi}')
# ② 발 — 러스트 발목 x(가까운 205 · 먼 338) 둘레
FEET = {}
for nm, x0, x1 in (('가까운', 170, 275), ('먼', 290, 400)):
    m = op & (XX >= x0) & (XX < x1) & (YY > 400) & (YY < 470); yb = int(np.nonzero(m.any(1))[0].max()); w6 = [int(m[y].sum()) for y in range(yb - 5, yb + 1)]
    FEET[nm] = yb; rep.append(f'{nm} 발바닥 y {yb} (러스트 448) · 맨 아래 6줄 폭 {w6} → ' + ('평평 ✓' if min(w6[:3]) >= 20 else '좁음 ✗'))
# ③ 몸 겹침
b7 = (a7[..., 3] > 128) & lab('body', 'hips', 'legN', 'legF', 'foreF', 'handF', 'pauldron')
low = YY >= 320; iou = (op & b7 & low).sum() / max(1, ((op | b7) & low).sum()); rep.append(f'몸 겹침 IoU(y ≥ 320, 방패 칸 빼고 셈은 아님) {iou:.3f}')
# ④ 머리 SIFT
_g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY)
sf = cv2.SIFT_create(4000)
def sift_find(src, smask, dmask, tag):
    k1, d1 = sf.detectAndCompute(_g(src), (smask * 255).astype(np.uint8)); k2, d2 = sf.detectAndCompute(_g(new), (dmask * 255).astype(np.uint8))
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < 0.75 * b.distance]
    if len(mm) < 6: raise ValueError(f'{tag}: 맞는 점 {len(mm)}개')
    M, inl = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in mm]), np.float32([k2[a.trainIdx].pt for a in mm]), ransacReprojThreshold=4.0)
    return M, int(inl.sum())
hm = (a17[..., 3] > 128) & (XX > 205) & (XX < 345) & (YY > 180) & (YY < 310)
try:
    M, n = sift_find(a17, hm, op & (XX > 180) & (XX < 380) & (YY > 150) & (YY < 330), '머리'); sc = float(np.hypot(M[0, 0], M[1, 0]))
    rep.append(f'머리(옛 17 원화와 SIFT {n}점): 배율 ×{sc:.3f} · 회전 {math.degrees(math.atan2(M[1, 0], M[0, 0])):+.1f}°')
except Exception as e: rep.append(f'머리: 못 맞춤({e})')
# ⑤ 도끼 날 SIFT
am = (a17[..., 3] > 128) & (XX >= 200) & (YY < 182)
try:
    M, n = sift_find(a17, am, op & (XX > 280) & (YY < 260), '도끼'); sc = float(np.hypot(M[0, 0], M[1, 0])); rot = math.degrees(math.atan2(M[1, 0], M[0, 0]))
    g = M[:, :2] @ np.array([92.0, 232.0]) + M[:, 2]
    rep.append(f'도끼 날(SIFT {n}점): 배율 ×{sc:.3f} (fit .811) · 회전 {rot:+.1f}° (fit {-(-31.7 + 105.8):+.1f}°) · 옛 쥔 점 → ({g[0]:.0f},{g[1]:.0f}) (러스트 G {J7["G"]})')
except Exception as e: rep.append(f'도끼: 못 맞춤({e})')
ya = np.nonzero(op[:, 280:].any(1))[0].min(); rep.append(f'도끼 위 끝 y {ya} (러스트 57 · fit 50)')
# ⑥ 방패
smk = (a17[..., 3] > 128) & (XX >= 352) & (YY >= 195) & ~((XX < 365) & (YY > 430))
try:
    M, n = sift_find(a17, smk, op & (XX < 260), '방패'); sc = float(np.hypot(M[0, 0], M[1, 0])); rot = math.degrees(math.atan2(M[1, 0], M[0, 0]))
    rep.append(f'방패(SIFT {n}점): 배율 ×{sc:.3f} · 회전 {rot:+.1f}°(+ = 시계)')
except Exception as e: rep.append(f'방패: 못 맞춤({e})')
sb = int(np.nonzero(op[:, :200].any(1))[0].max()); rep.append(f'방패 쪽(x < 200) 아래 끝 y {sb} (발바닥 + {sb - FEET["가까운"]} · 러스트 459 = 발 + 11)')
for nm, txt in [(k, f'{k} {v}') for k, v in FEET.items()]: pass
print('\n'.join(rep))
# 그림
def comp(a, bgc=(235, 238, 245)):
    bg = np.zeros((512, 512, 3)); bg[...] = bgc; al = a[..., 3:4] / 255.0; return (a[..., :3] * al + bg * (1 - al)).astype(np.uint8)
v = comp(new).copy(); e7 = cv2.dilate(b7.astype(np.uint8), np.ones((3, 3), np.uint8)) - b7.astype(np.uint8); v[e7 > 0] = (40, 90, 255)
es = cv2.dilate(lab('shield').astype(np.uint8), np.ones((3, 3), np.uint8)) - lab('shield').astype(np.uint8); v[es > 0] = (230, 40, 40)
cv2.circle(v, tuple(int(round(x)) for x in J7['G']), 4, (230, 40, 40), -1)
big = Image.fromarray(v).resize((1024, 1024), Image.LANCZOS)
c3 = lambda a, box, k: Image.fromarray(comp(a)).crop(box).resize(((box[2] - box[0]) * k, (box[3] - box[1]) * k), Image.LANCZOS)
heads = [c3(a17, (195, 170, 355, 320), 2), c3(new, (195, 150, 355, 300), 2)]
fist = c3(new, (395, 240, 475, 340), 3); feet = c3(new, (150, 390, 410, 470), 2)
W = 1024 + 20 + 640; out = Image.new('RGB', (W, 1024 + 60), (255, 255, 255)); out.paste(big, (0, 60))
f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 22)
d = ImageDraw.Draw(out); d.text((10, 8), '새 원화 + 파랑 = 러스트 몸·다리 · 빨강 = 러스트 방패 · 빨간 점 = 러스트 도끼 쥔 점', fill=(20, 20, 20), font=f)
x0 = 1044; d.text((x0, 30), '머리: 옛 17 · 새', fill=(20, 20, 20), font=f); out.paste(heads[0], (x0, 60)); out.paste(heads[1], (x0 + 320, 60))
d.text((x0, 370), '먼 주먹 3배', fill=(20, 20, 20), font=f); out.paste(fist, (x0, 400))
d.text((x0, 710), '두 발 2배', fill=(20, 20, 20), font=f); out.paste(feet.resize((520, 160)), (x0, 740))
for i, line in enumerate(rep[-6:]): d.text((x0, 910 + i * 26), line[:60], fill=(60, 60, 60), font=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 16))
out.save(out_path); print('저장', out_path)
