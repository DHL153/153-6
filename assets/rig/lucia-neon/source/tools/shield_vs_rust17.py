"""17 네온 루시아 — DHL 09:25 손으로 고친 그림 위에 러스트 루시아 방패 외곽선(빨강)·가까운 주먹(파랑)·발바닥 줄(초록)을 겹쳐 봄
  러스트 = char_0007 라벨(lucia-rust/source/work/labels.npy: shield · handN), 같은 512 캔버스(발바닥 448 · 첫 그림 445)
  출력: ../review/shield_vs_rust17.png · 숫자(방패 아래 끝·발바닥 차이)
실행: python3 -I shield_vs_rust17.py
"""
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); REPO = os.path.abspath(os.path.join(SRC, '..', '..', '..', '..'))
RS = os.path.join(REPO, 'assets', 'rig', 'lucia-rust', 'source')
LAB = np.load(os.path.join(RS, 'work', 'labels.npy')); NAMES = json.load(open(os.path.join(RS, 'work', 'label_names.json')))
MAN = Image.open(os.path.join(SRC, 'refs', 'ref_dhl_0925_manual.png')).convert('RGBA')
A = np.asarray(MAN)[..., 3] > 60
K = 2; W = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); W.alpha_composite(MAN); W = W.convert('RGB').resize((512 * K, 512 * K), Image.LANCZOS)
d = ImageDraw.Draw(W)
for name, col in (('shield', (230, 0, 0)), ('handN', (0, 90, 255))):
    m = (LAB == NAMES.index(name) + 1).astype(np.uint8)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cs:
        pts = [(int(p[0][0] * K), int(p[0][1] * K)) for p in c]
        if len(pts) > 2: d.line(pts + [pts[0]], fill=col, width=4)
ys = np.nonzero(A[:, :250])[0]
print('DHL 방패 쪽(x<250) 아래 끝', ys.max(), '· 러스트 방패 아래 끝', np.nonzero(LAB == NAMES.index('shield') + 1)[0].max(), '· 발바닥 첫 그림 445 / 러스트 448')
for y, col in ((445, (0, 160, 0)),):
    d.line([(0, y * K), (512 * K, y * K)], fill=col, width=3)
f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 34)
d.text((20, 16), '빨강 = 러스트 방패 자리 · 파랑 = 러스트 가까운 주먹 · 초록 = 발바닥', fill=(20, 20, 20), font=f)
W.save(os.path.join(SRC, 'review', 'shield_vs_rust17.png')); print('저장 review/shield_vs_rust17.png')
