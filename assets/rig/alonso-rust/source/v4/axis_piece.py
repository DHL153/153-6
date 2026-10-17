"""팔 조각을 '관절 → 끝'이 아래로 곧게 서도록 돌리고, 길이 방향만 늘이거나 줄여 키 포즈 팔의 굵기:길이 비율에 맞춤.
(시트마다 팔 비율이 달라서, 길이만 맞추면 너무 가늘거나 굵어짐 — 2026-10-17 알론소 먼 팔)
python3 -I axis_piece.py IN.png Ex Ey Fx Fy RATIO OUT.png  → 출력 그림의 관절점·끝점(JSON) 출력. RATIO = 중간(50%) 굵기 / 길이 목표"""
import sys, json, math, numpy as np
from PIL import Image
fn, Ex, Ey, Fx, Fy, R, out = sys.argv[1], *map(float, sys.argv[2:7]), sys.argv[7]
im = Image.open(fn).convert('RGBA'); W, H = im.size; E = np.array([Ex, Ey]); F = np.array([Fx, Fy]); L = np.linalg.norm(F - E)
ang = math.degrees(math.atan2(F[1] - E[1], F[0] - E[0])) - 90
big = Image.new('RGBA', (W * 3, H * 3)); big.paste(im, (W, H)); c = (E[0] + W, E[1] + H)
r = big.rotate(ang, center=c, resample=Image.BICUBIC); a = np.asarray(r)[..., 3] > 128
xs = np.nonzero(a[int(c[1] + L * .5)])[0]; w = xs.max() - xs.min(); k = (w / L) / R          # 길이 방향 배율
bb = r.getbbox(); r = r.crop(bb); cx, cy = c[0] - bb[0], c[1] - bb[1]
r = r.resize((r.width, max(1, round(r.height * k))), Image.LANCZOS)
E2 = [round(cx, 1), round(cy * k, 1)]; F2 = [round(cx, 1), round((cy + L) * k, 1)]
r.save(out); print(json.dumps({'joint': E2, 'end': F2, 'lenK': round(k, 3), 'size': r.size}))
