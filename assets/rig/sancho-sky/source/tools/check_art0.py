"""0번 새 원화 검수(받자마자): python3 -I check_art0.py 새원화.png [기준=3 러스트 산초 원화]
출력: 실루엣 겹침 IoU · 발바닥 y · 머리~발 높이 · 칼 쪽(왼쪽 위) 불투명 범위 · 반투명 점 수 · 비교 그림(나란히 + 겹침 + 손 4배 + 얼굴 4배) → ../work/art0_check.png
합격선(프롬프트 0): 자세·칼 11시·손 순서 = 3 · 손가락 4 + 엄지 · 디자인 = 지금 23 · 칼이 머리카락·목도리 앞 · 크기·발바닥 = 3 · 투명 배경"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..', '..', '..', '..')
new = Image.open(sys.argv[1]).convert('RGBA'); ref = Image.open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'assets', 'art', 'characters', 'char_0003.png')).convert('RGBA')
old = Image.open(os.path.join(HERE, '..', 'orig_char_0023_onehand.png')).convert('RGBA')
assert new.size == (512, 512), new.size
A, B = np.array(new)[..., 3], np.array(ref)[..., 3]
def info(a):
    m = a > 128; ys, xs = np.nonzero(m); return dict(bbox=(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), sole=int(ys.max()), px=int(m.sum()))
iou = ((A > 128) & (B > 128)).sum() / max(1, ((A > 128) | (B > 128)).sum())
semi = int(((A > 0) & (A < 255)).sum()); print('새', info(A), '기준(3)', info(B), 'IoU', round(float(iou), 3), '반투명 점', semi)
# 그림: 새 · 기준 · 겹침(새 = 빨강, 기준 = 파랑) · 옛 23
def onw(im): bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); return bg.convert('RGB')
ov = np.full((512, 512, 3), 255, np.uint8); ov[B > 128] = (140, 160, 255); ov[A > 128] = (255, 120, 120); ov[(A > 128) & (B > 128)] = (170, 90, 170)
W = Image.new('RGB', (512 * 4 + 30, 512 + 30), 'white'); d = ImageDraw.Draw(W)
for i, (t, im) in enumerate([('새 원화', onw(new)), ('기준 3 러스트 산초', onw(ref)), ('겹침 빨강=새 파랑=3', Image.fromarray(ov)), ('지금 23(디자인)', onw(old))]):
    W.paste(im, (i * 522, 30)); d.text((i * 522 + 6, 8), t, fill='black')
W.save(os.path.join(HERE, '..', 'work', 'art0_check.png'))
# 손·얼굴 4배(위치는 3 러스트 원화 기준 — 같은 자세면 같은 자리)
crops = {'hands': (200, 280, 300, 380), 'face': (270, 230, 400, 340)}
for k, bx in crops.items():
    c = onw(new).crop(bx); c = c.resize((c.width * 4, c.height * 4), Image.NEAREST); c.save(os.path.join(HERE, '..', 'work', f'art0_{k}.png'))
print('그림:', os.path.normpath(os.path.join(HERE, '..', 'work')), 'art0_check.png · art0_hands.png · art0_face.png')
