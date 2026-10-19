# 12 네온 둘시네 새 원화(프롬프트 0 결과) 1차 검수 — 숫자로 볼 수 있는 합격선 + 러스트 둘시네와 겹친 그림 (10-20 07:35 원화 오기 전 준비)
#   python3 -I tools/check_art12.py 새원화.png [이름]  → 표 + review/art_<이름>.png(왼쪽: 새 원화 + 러스트 실루엣 빨강 + 러스트 관절 / 오른쪽: 러스트 다각형(polys.json) 겹침)
#   사람(Claude)이 그림으로 볼 것: 손가락 4 + 엄지(두 주먹) · 망치 머리 뒤(옆머리가 쇠 머리 모서리 덮음) · 얼굴 안 가림 · 디자인(첨부 1)
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
RS = os.path.join(REPO, 'assets', 'rig', 'dulcinea-rust', 'source')
fn = sys.argv[1]; tag = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(os.path.basename(fn))[0]
N = np.array(Image.open(fn).convert('RGBA')); R = np.array(Image.open(os.path.join(RS, 'ref512.png')).convert('RGBA'))
ok = lambda c: '✓' if c else '✗'
rows = []
rows.append(('크기 512×512', N.shape[:2] == (512, 512), f'{N.shape[1]}×{N.shape[0]}'))
if N.shape[:2] != (512, 512): N = np.array(Image.fromarray(N).resize((512, 512), Image.LANCZOS))
An, Ar = N[..., 3] > 40, R[..., 3] > 40
corner = N[:6, :6, 3].max() + N[-6:, -6:, 3].max(); rows.append(('투명 배경(모서리 알파 0)', corner == 0, f'모서리 알파 {corner}'))
edge = int(An[0].sum() + An[-1].sum() + An[:, 0].sum() + An[:, -1].sum()); rows.append(('잘린 곳 없음(가장자리 1px 불투명 0)', edge == 0, f'{edge}px'))
sole = lambda A: int(np.nonzero(A.any(1))[0].max())
rows.append(('발바닥 높이 = 러스트(485 ±4)', abs(sole(An) - sole(Ar)) <= 4, f'{sole(An)} (러스트 {sole(Ar)})'))
# 머리 위: 망치·포니테일이 없는 가로 띠(러스트 정수리 오른쪽 x 280~320, 포니테일 매듭 x<270 빼고)에서 가장 위 — 러스트 104
# (10-20 07:55 고침) 러스트는 큰 머리숱·포니테일이라 '머리카락 위'로는 몸 크기를 못 견줌 → 러스트 몸 = 머리 위 120(머리숱 빼고, fit12 와 같은 값) ~ 발바닥 485 = 365,
#   새 원화 = 망치 없는 왼쪽(x<300) 가장 위 ~ 발바닥 (짧은 머리 네온은 머리카락 위 = 머리 위)
hn = int(np.nonzero(An[:, :300].any(1))[0].min()); kH = (sole(An) - hn) / 365
rows.append(('몸 크기(머리 위~발바닥) = 러스트 365 ±4%', abs(kH - 1) <= .04, f'{sole(An) - hn} (×{kH:.3f})'))
# 망치: 오른쪽 위(x ≥ 330, y ≤ 300 — 러스트 원화에선 망치만 있는 곳)의 가장 위·가장 오른쪽
def hz(A):
    m = A.copy(); m[:, :330] = False; m[300:, :] = False; ys, xs = np.nonzero(m)
    return (int(ys.min()), int(xs.max()), int(m.sum())) if len(ys) else (None, None, 0)
tn, rn, pn = hz(An); tr, rr, pr = hz(Ar)
if tn is None: rows.append(('망치 쇠 머리 자리 = 러스트', False, '오른쪽 위에 그림 없음'))
else:
    rows.append(('쇠 머리 위 끝 = 러스트 ±15', abs(tn - tr) <= 15, f'y {tn} (러스트 {tr})'))
    rows.append(('쇠 머리 오른쪽 끝 = 러스트 ±15', abs(rn - rr) <= 15 and rn < 511, f'x {rn} (러스트 {rr})'))
    rows.append(('쇠 머리 넓이 = 러스트 ±25%', abs(pn / pr - 1) <= .25, f'{pn}px (러스트 {pr}, ×{pn / pr:.2f})'))
# 실루엣 겹침(러스트 포니테일 자리 x<170 빼고)
cut = np.zeros_like(An); cut[250:, :] = True   # (10-20 07:55 고침) 머리·망치 빼고 목 아래 몸만(러스트 머리숱이 합집합을 키움)
iou = float((An & Ar & cut).sum() / max(1, ((An | Ar) & cut).sum())); rows.append(('몸 실루엣 겹침(y≥250) ≥ 0.75', iou >= .75, f'IoU {iou:.2f}'))
print(f'== {tag}')
for n, c, v in rows: print(f'  {ok(c)} {n:34s} {v}')
# 그림
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
def panel(polys):
    bg = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); bg.alpha_composite(Image.fromarray(N)); im = bg.resize((1024, 1024), Image.LANCZOS); d = ImageDraw.Draw(im)
    import cv2
    cs, _ = cv2.findContours(Ar.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for c in cs: d.line([tuple(p[0] * 2) for p in c] + [tuple(c[0][0] * 2)], fill=(230, 30, 30, 255), width=2)
    if polys:
        P = {k: v for k, v in json.load(open(os.path.join(RS, 'polys.json'))).items() if not k.startswith('_')}
        cols = [(0, 140, 255), (0, 170, 80), (200, 120, 0), (160, 0, 200), (0, 160, 160), (120, 120, 0)]
        for i, (k, pts) in enumerate(P.items()):
            q = [(x * 2, y * 2) for x, y in pts]; d.line(q + [q[0]], fill=cols[i % 6] + (255,), width=2); d.text(q[0], k, fill=cols[i % 6] + (255,), font=f)
    else:
        J = dict(O=(207, 485), HIP=(232, 316), NECK=(244, 250), SH_N=(170, 248), EL_N=(146, 280), WR_N=(133, 299), SH_F=(270, 262), EL_F=(255, 300), WR_F=(288, 304), G=(314.3, 311))
        for k, (x, y) in J.items(): d.ellipse([x * 2 - 6, y * 2 - 6, x * 2 + 6, y * 2 + 6], fill=(0, 120, 255, 255)); d.text((x * 2 + 8, y * 2 - 8), k, fill=(0, 60, 200, 255), font=f)
        G = np.array([314.3, 311.0]); HU = np.array([.574, -.819]); HU /= np.linalg.norm(HU)
        d.line([tuple((G - HU * 58) * 2), tuple((G + HU * 230) * 2)], fill=(0, 120, 255, 255), width=3)
    return im
os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
W = Image.new('RGB', (2048, 1024), 'white'); W.paste(panel(False).convert('RGB'), (0, 0)); W.paste(panel(True).convert('RGB'), (1024, 0))
W.save(os.path.join(HERE, 'review', f'art_{tag}.png')); print('  →', os.path.join('review', f'art_{tag}.png'))
