"""17 네온 루시아 — 방패 후보(DHL 09:25 손으로 고친 그림 '아직 마음에 쏙 들지는 않아요')
  바탕 = 0번 첫 그림(08:13: 몸·가까운 어깨갑·주먹·다리가 다 그려져 있음)에서 옛 방패(x ≤ 206)를 지움
  방패 = 첫 그림의 방패(같은 그림체)를 TILT° 시계 방향으로 기울여, 오른쪽 가장자리가 가까운 주먹 바로 왼쪽(ANCHOR)을 지나게 · 아래 끝 = BOTTOM
  주먹 = 첫 그림 가까운 주먹을 방패 위에 다시(가장자리를 감아 쥔 모양 — 러스트 루시아와 같은 쥠)
  출력: ../review/shield_cand17.png (러스트 · DHL 09:25 · 후보들, 같은 배율) · 숫자(기울기·아래 끝·방패 ∩ 몸)
실행: python3 -I shield_cand17.py
"""
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); REPO = os.path.abspath(os.path.join(SRC, '..', '..', '..', '..'))
L = lambda n: np.array(Image.open(os.path.join(SRC, 'refs', n)).convert('RGBA')).astype(np.float32)
NEW0, MAN, RUST = L('ref_dhl_0813_new0.png'), L('ref_dhl_0925_manual.png'), L('ref_pose_char0007.png')
YY, XX = np.mgrid[0:512, 0:512]
sh_mask = (NEW0[..., 3] > 0) & (XX <= 206) & (YY >= 125) & (YY <= 458)
SH = NEW0.copy(); SH[~sh_mask] = 0
fist = (NEW0[..., 3] > 0) & (XX >= 203) & (XX <= 238) & (YY >= 298) & (YY <= 358)      # 가까운 주먹(첫 그림, 방패 오른쪽 가장자리를 감아 쥔 손가락)
FI = NEW0.copy(); FI[~fist] = 0
base = NEW0.copy(); base[sh_mask] = 0
ys, xs = np.nonzero(sh_mask); R_ANCH = np.array([205.0, 335.0])          # 첫 그림 방패 오른쪽 가장자리(주먹 높이)
def over(dst, src):
    a = src[..., 3:4] / 255.0; o = dst.copy(); o[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a); o[..., 3:4] = np.maximum(dst[..., 3:4], src[..., 3:4]); return o
def cand(tilt, anchor, bottom, show_fist=True):
    M = cv2.getRotationMatrix2D((float(R_ANCH[0]), float(R_ANCH[1])), -tilt, 1.0); M[:, 2] += np.array(anchor) - R_ANCH
    w = cv2.warpAffine(SH, M, (512, 512), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    yb = np.nonzero(w[..., 3] > 60)[0].max(); M[1, 2] += bottom - yb
    w = cv2.warpAffine(SH, M, (512, 512), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    img = over(base, w)
    if show_fist: img = over(img, FI)
    a = w[..., 3] > 60; body = base[..., 3] > 60
    return img, int((a & body).sum()), int(np.nonzero(a)[0].max()), int(np.nonzero(a)[0].min())
f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 26)
C = [('러스트 7 (자세 기준)', RUST, None), ('DHL 09:25 손으로 고침', MAN, None)]
for name, tilt, anc, bot in [('A · 15° 주먹 보임', 15, (207, 335), 459), ('B · 10° 주먹 보임', 10, (207, 335), 459), ('C · 15° 주먹 숨김', 15, (226, 320), 459)]:
    img, inter, yb, yt = cand(tilt, anc, bot, show_fist=('보임' in name))
    C.append((name, img, (inter, yb, yt))); print(name, '방패∩몸 px', inter, '· 방패 위·아래', yt, yb)
body_feet = 445
cells = []
for name, img, info in C:
    W = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); W.alpha_composite(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)))
    d = ImageDraw.Draw(W); d.line([(0, body_feet), (512, body_feet)], fill=(255, 80, 80, 255), width=1)
    W = W.convert('RGB').crop((0, 20, 512, 512)).resize((640, 615), Image.LANCZOS)
    cell = Image.new('RGB', (640, 615 + 44), (255, 255, 255)); cell.paste(W, (0, 44)); ImageDraw.Draw(cell).text((10, 6), name, fill=(150, 0, 0), font=f)
    cells.append(cell)
out = Image.new('RGB', (640 * 3 + 20, (659) * 2 + 10), (235, 235, 235))
for i, c in enumerate(cells): out.paste(c, ((i % 3) * 650, (i // 3) * 669))
out.save(os.path.join(SRC, 'review', 'shield_cand17.png')); print('저장 review/shield_cand17.png (빨간 줄 = 첫 그림 발바닥 445)')
# DHL 그림 숫자
m = (MAN[..., 3] > 60); print('DHL 그림 불투명 아래 끝', np.nonzero(m)[0].max(), '· 첫 그림', np.nonzero(NEW0[..., 3] > 60)[0].max())
