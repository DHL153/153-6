"""14 네온 로시 새 원화(프롬프트 0) 검수 — python3 -I check_art14.py 새원화.png [출력.png]   (2026-10-21 07:30, check_art20 구조)
기준: 첨부 2 = char_0004(4 러스트 로시 자세·크기, 리그 jointMap = 512 원화 좌표)
보는 것: ①불투명 범위·가장자리·투명 ②두 발바닥(러스트와 같은 높이)·바닥 평평 ③실루엣 겹침 IoU(전체 · 총 띠 · 몸 띠)
④총: 총구 오른쪽 끝·위 손잡이 위 끝·총 띠 위아래(러스트와 차이 px) ⑤두 손목 자리(러스트 wristN·wristF)에 장갑이 있는지(어두운 픽셀 비율)
⑥머리: 옛 14 원화 머리와 SIFT → 배율·눈 자리
출력: 새 원화 + 파랑 러스트 외곽선 · 빨강 러스트 관절점 / 머리 나란히 / 두 손 ×3 / 두 발 ×3 / 숫자
"""
import sys, os, math, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); RIG = os.path.abspath(os.path.join(SRC, '..', '..'))
_im = Image.open(sys.argv[1]).convert('RGBA'); new = np.array(_im if _im.size == (512, 512) else _im.resize((512, 512), Image.LANCZOS))
out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SRC, 'review', 'check_art14.png')
a4 = np.array(Image.open(os.path.join(SRC, 'refs', 'ref_pose_char0004.png')).convert('RGBA'))
a14 = np.array(Image.open(os.path.join(SRC, 'refs', 'ref_design_char0014.png')).convert('RGBA'))
J = json.load(open(os.path.join(RIG, 'rosi-rust', 'rig.json')))['jointMap']
YY, XX = np.mgrid[0:512, 0:512]; op = new[..., 3] > 128; o4 = a4[..., 3] > 128; rep = []
ys, xs = np.nonzero(op); rep.append(f'불투명 범위 x {xs.min()}~{xs.max()} · y {ys.min()}~{ys.max()} (러스트 x 32~500 · y 88~447)')
edge = op[0].any() or op[-1].any() or op[:, 0].any() or op[:, -1].any(); rep.append('가장자리 잘림: ' + ('있음 ✗' if edge else '없음 ✓'))
corner = int(new[:8, :8, 3].max()) + int(new[-8:, -8:, 3].max()); rep.append('투명 배경: ' + ('✓' if corner == 0 else f'✗ (모서리 알파 {corner})'))
HX = J['hip'][0]
for nm, xm in (('가까운(왼쪽)', XX < HX), ('먼(오른쪽)', XX >= HX)):
    res = []
    for a in (o4, op):
        m = a & xm & (YY > 380) & (XX > 150) & (XX < 330); yb = int(np.nonzero(m.any(1))[0].max()); res.append((yb, [int(m[y].sum()) for y in range(yb - 5, yb + 1)]))
    rep.append(f'{nm} 발바닥 y {res[1][0]} (러스트 {res[0][0]}, 차 {res[1][0] - res[0][0]:+d}) · 맨 아래 6줄 폭 {res[1][1]} (러스트 {res[0][1]})' + (' ✓' if abs(res[1][0] - res[0][0]) <= 6 and min(res[1][1][:3]) >= 12 else ' ✗ 확인'))
iou = lambda m: (op & o4 & m).sum() / max(1, ((op | o4) & m).sum())
GB = (YY >= 270) & (YY <= 370) & (XX >= 200); BB = (XX >= 170) & (XX <= 330) & (YY >= 200) & (YY < 270)
rep.append(f'실루엣 IoU 전체 {iou(np.ones_like(op)):.3f} · 총 띠(y 270~370, x ≥ 200) {iou(GB):.3f} · 몸 띠(가슴) {iou(BB):.3f}')
def gun_ext(a):
    band = a & (YY >= 250) & (YY <= 380) & (XX >= 380); xr = int(np.nonzero(band.any(0))[0].max())
    col = a[:, 380:500].any(1); yr = np.nonzero(col & (np.arange(512) > 200) & (np.arange(512) < 400))[0]
    return xr, int(yr.min()), int(yr.max())
g4, gN = gun_ext(o4), gun_ext(op)
rep.append(f'총(x 380~500 기둥): 총구 오른쪽 끝 x {gN[0]} (러스트 {g4[0]}) · 위 끝 y {gN[1]} ({g4[1]}) · 아래 끝 y {gN[2]} ({g4[2]})' + (' ✓' if abs(gN[0] - g4[0]) <= 12 and abs(gN[1] - g4[1]) <= 12 and abs(gN[2] - g4[2]) <= 12 else ' ✗ 확인'))
for nm, k in (('가까운 손목', 'wristN'), ('먼 손목', 'wristF')):
    x, y = J[k]; m = (np.hypot(XX - x, YY - y) < 10) & op; rgb = new[..., :3].astype(int).sum(2)
    dark = float(((rgb < 160) & m).sum() / max(1, m.sum())); rep.append(f'{nm} ({x},{y}) 반지름 10 안 불투명 {m.sum()} · 어두운(장갑) 비율 {dark:.2f}')
_g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY)
sf = cv2.SIFT_create(4000)
def sift(src, sm, dm):
    k1, d1 = sf.detectAndCompute(_g(src), (sm * 255).astype(np.uint8)); k2, d2 = sf.detectAndCompute(_g(new), (dm * 255).astype(np.uint8))
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < .75 * b.distance]
    M, inl = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in mm]), np.float32([k2[a.trainIdx].pt for a in mm]), ransacReprojThreshold=4.0); return M, int(inl.sum()), len(mm)
HEADBOX14 = (120, 330, 120, 300)   # 옛 14 원화 머리(머리카락·얼굴) y 120~300 · x 330~... 아래에서 정함
hm = (a14[..., 3] > 128) & (YY >= 100) & (YY <= 300) & (XX >= 210) & (XX <= 400) & ~((YY < 260) & (XX < 300) & (YY < XX * 0 + 400) & ((YY - 30) < (XX - 0) * .55))
HEAD = None
try:
    M, n, nm_ = sift(a14, hm, op & (YY < 330) & (XX > 160) & (XX < 380)); sc = float(np.hypot(M[0, 0], M[1, 0])); HEAD = M
    rep.append(f'머리(옛 14 원화와 SIFT {n}/{nm_}점): 배율 ×{sc:.3f} · 회전 {math.degrees(math.atan2(M[1, 0], M[0, 0])):+.1f}°')
except Exception as e: rep.append(f'머리: 옛 14 원화와 못 맞춤({e}) — 눈으로')
def comp(a, bgc=(235, 238, 245)):
    bg = np.zeros((512, 512, 3)); bg[...] = bgc; al = a[..., 3:4] / 255.0; return (a[..., :3] * al + bg * (1 - al)).astype(np.uint8)
v = comp(new).copy(); e4 = cv2.dilate(o4.astype(np.uint8), np.ones((3, 3), np.uint8)) - o4.astype(np.uint8); v[e4 > 0] = (40, 90, 255)
for k, p in J.items(): cv2.circle(v, tuple(int(x) for x in p), 3, (230, 30, 30), -1)
big = Image.fromarray(v).resize((1024, 1024), Image.LANCZOS)
HS = 268; Z = 3
hR = Image.fromarray(comp(a4)).crop((180, 110, 340, 270)).resize((HS, HS), Image.LANCZOS); hN = Image.fromarray(comp(new)).crop((180, 110, 340, 270)).resize((HS, HS), Image.LANCZOS)
zs = lambda a, b: Image.fromarray(comp(a)).crop(b).resize(((b[2] - b[0]) * Z, (b[3] - b[1]) * Z), Image.LANCZOS)
hands = [zs(new, (130, 260, 200, 330)), zs(new, (310, 255, 380, 325))]; feet = [zs(new, (160, 400, 260, 460)), zs(new, (240, 390, 340, 450))]
W = Image.new('RGB', (1024 + 600, 1024 + 40 + 330), (24, 26, 34)); W.paste(big, (0, 40)); W.paste(hR, (1034, 70)); W.paste(hN, (1034 + HS + 12, 70))
x = 10
for t in hands + feet: W.paste(t, (x, 1074)); x += t.width + 14
d = ImageDraw.Draw(W); FN = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; f = ImageFont.truetype(FN, 20, index=1); fs = ImageFont.truetype(FN, 18, index=1)
d.text((8, 8), '새 원화 · 파랑 = 러스트 로시 외곽선 · 빨강 = 러스트 관절점(손목·어깨·팔꿈치·골반)', fill=(255, 230, 120), font=f)
d.text((1034, 44), '러스트 머리(같은 칸)', fill=(255, 255, 255), font=f); d.text((1034 + HS + 12, 44), '새 원화 머리(같은 칸)', fill=(255, 255, 255), font=f)
d.text((10, 1046), '두 손 ×3 · 두 발 ×3', fill=(255, 255, 255), font=f)
def wrap(t, w=570):
    out, cur = [], ''
    for ch in t:
        if d.textlength(cur + ch, font=fs) > w: out.append(cur); cur = '   ' + ch
        else: cur += ch
    return out + [cur]
yy = 70 + HS + 24
for line in rep:
    for seg in wrap(line):
        col = (255, 120, 110) if '✗' in line else (150, 230, 160) if '✓' in line else (220, 220, 220); d.text((1034, yy), seg.replace('✗', '×'), fill=col, font=fs); yy += 26
W.save(out_path); print('\n'.join(rep)); print('그림', os.path.abspath(out_path))
