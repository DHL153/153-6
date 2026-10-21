"""17 네온 루시아 — 프롬프트 0-3 첨부 2: DHL 09:25 손으로 고친 그림 위에 '옮길 방패 자리'(빨간 외곽선)·가까운 주먹 자리(파란 원)·발바닥(초록)
  방패 외곽 = 09:25 그림에서 방패 윗변 선 아래 · 오른쪽 가장자리 선 왼쪽의 불투명 부분(격자 5배로 읽은 점) → (DX, DY) 만큼 옮김
  옮기는 양 = 러스트 루시아 방패(shield_vs_rust17)와 09:25 사이: 왼쪽 35 · 위 30 → 아래 끝 489 → 459(발바닥 445 + 14)
  가까운 손 = 방패 뒤 손잡이를 쥐어 안 보임(DHL 09:43 '방패를 들었는데 손가락이 보이면 이상해요') — 주먹 자리 원은 뺌
실행: python3 -I guide_shield17b.py
"""
import os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
DX, DY = -35, -30
MAN = Image.open(os.path.join(SRC, 'refs', 'ref_dhl_0925_manual.png')).convert('RGBA'); A = np.asarray(MAN)[..., 3] > 60
YY, XX = np.mgrid[0:512, 0:512]
ytop = 185 + (XX - 150) * 0.475                                    # 방패 윗변(150,185) → (270,242)
RE = np.array([(180, 250), (242, 272), (300, 268), (350, 253), (400, 246), (445, 240), (470, 225), (492, 200)], float)
xr = np.interp(YY, RE[:, 0], RE[:, 1])
sh = A & ((XX < 150) | (YY >= ytop - 3)) & (XX <= xr + 2)
sh = cv2.morphologyEx(sh.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
ys, xs = np.nonzero(sh); print('지금 방패 외곽 상자 x', xs.min(), xs.max(), 'y', ys.min(), ys.max())
M = np.float32([[1, 0, DX], [0, 1, DY]]); tgt = cv2.warpAffine(sh, M, (512, 512), flags=cv2.INTER_NEAREST)
ys, xs = np.nonzero(tgt); print('옮길 자리 상자 x', xs.min(), xs.max(), 'y', ys.min(), ys.max())
FADE = np.asarray(MAN).copy(); FADE[..., 3] = np.where(sh > 0, (FADE[..., 3] * .35).astype(np.uint8), FADE[..., 3])   # 지금 방패는 흐리게(옮길 것)
K = 2; W = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); W.alpha_composite(Image.fromarray(FADE)); W = W.convert('RGB').resize((512 * K, 512 * K), Image.LANCZOS)
d = ImageDraw.Draw(W)
cs, _ = cv2.findContours(tgt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for c in cs:
    pts = [(int(p[0][0] * K), int(p[0][1] * K)) for p in c]
    if len(pts) > 2: d.line(pts + [pts[0]], fill=(230, 0, 0), width=5)
d.line([(0, 445 * K), (512 * K, 445 * K)], fill=(0, 160, 0), width=3)
f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 32)
BH = 100; out = Image.new('RGB', (512 * K, 512 * K + BH), (255, 255, 255)); out.paste(W, (0, BH)); dd = ImageDraw.Draw(out)
dd.text((20, 10), '흐린 방패 = 지금 자리 → 빨간 외곽선 = 옮길 자리 (왼쪽 · 위로 조금)', fill=(190, 0, 0), font=f)
dd.text((20, 52), '가까운 손은 방패 뒤(보이지 않음) · 초록 = 발바닥', fill=(30, 30, 30), font=f)
dd.line([(0, BH - 2), (512 * K, BH - 2)], fill=(200, 200, 200), width=2)
out.save(os.path.join(SRC, 'refs', 'ref_shield_move17b.png')); print('저장 refs/ref_shield_move17b.png')
