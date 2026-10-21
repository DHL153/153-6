"""20 네온 브루노 — 게임 정지 그림(char_0020.png: 카드·필살기 컷신 얼굴·마이룸·리그 받기 전 그림)을 리그 v1.9 처럼 치마로
DHL 10-21 '모두 치마로 변경합니다' — 리그 대기가 늘 치마(골반 뼈 = hipsRun)라 정지 그림도 같게(실수 51③).
만드는 법: 원화(ref512, 0번 합격 원화 — 리그 빌드 입력은 그대로) 위에 치마 조각(../parts/hipsRun.png, 원화 자리 = 골반 뼈 − 피벗)을 얹고,
대기에서 치마보다 앞에 그리는 부품(상체·어깨갑·팔·주먹·철퇴·머리 라벨)은 원화 픽셀을 다시 위에. 치마 밖은 원화 픽셀 그대로.
실행: cd source && python3 -I tools/art_skirt20.py [출력=../../../art/characters/char_0020.png] → review/art_skirt20.png(원화 | 새 그림)
"""
import os, sys, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # source/
R = os.path.dirname(HERE)                                              # assets/rig/bruno-neon
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(R, '..', '..', 'art', 'characters', 'char_0020.png')
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'))
L = np.load(os.path.join(HERE, 'work', 'labels.npy')); NAMES = json.load(open(os.path.join(HERE, 'work', 'label_names.json')))
lab = lambda n: L == NAMES.index(n) + 1
rig = json.load(open(os.path.join(R, 'rig.json')))
bones = {b['name']: b for b in rig['bones']}
sk = bones['skirt']; assert sk.get('part') == 'hipsRun', '골반 뼈 조각이 hipsRun 이 아님 — 리그 v1.9 이후만'
# 뼈 자리(리그 px) → 원화 px: 원화 = refOrigin/2 + 뼈 누적 pos/2
def world(n):
    b = bones[n]; p = np.array(b['pos'], float)
    return p + (world(b['parent']) if b['parent'] else 0)
O = np.array(rig['refOrigin'], float) / 2
hip = O + world('skirt') / 2
pv = np.array(rig['parts']['hipsRun']['pivot'], float)
ox, oy = [int(round(v)) for v in hip - pv]
S = np.array(Image.open(os.path.join(R, 'parts', 'hipsRun.png')).convert('RGBA'))
lay = np.zeros_like(RA); lay[oy:oy + S.shape[0], ox:ox + S.shape[1]] = S
# 맞춤 확인: 치마 조각 위쪽(허리띠·쌈지)은 원화 픽셀 그대로라 같은 자리여야 함
m = (lay[..., 3] >= 250) & (RA[..., 3] >= 250); same = (np.abs(lay[..., :3].astype(int) - RA[..., :3].astype(int)).sum(-1) == 0) & m
print('치마 조각 자리', (ox, oy), '· 원화와 같은 px', int(same.sum()), '/ 겹침', int(m.sum()))
assert same.sum() > 1000, '치마 조각 자리가 원화와 안 맞음'
FRONT = ['torso', 'pauldN', 'upperN', 'foreN', 'fistN', 'maceN', 'fistF', 'maceF', 'head']   # 대기 그리는 순서에서 치마(skirt)보다 뒤에 그리는 = 앞에 보이는 부품
fm = np.zeros(L.shape, bool)
for n in FRONT: fm |= lab(n)
A = np.array(Image.alpha_composite(Image.fromarray(RA), Image.fromarray(lay)))
A[fm] = RA[fm]   # 앞 부품은 원화 픽셀 그대로(덮어쓰기 — 겹쳐 그리면 알파 253 이 올라감)
out = Image.fromarray(A)
chg = np.abs(A.astype(int) - RA.astype(int)).sum(-1) > 0
ys, xs = np.nonzero(chg)
print('바뀐 px', int(chg.sum()), '범위 x', int(xs.min()), '~', int(xs.max()), 'y', int(ys.min()), '~', int(ys.max()), '· 앞 부품 위 바뀜', int((chg & fm).sum()))
out.save(OUT); print('저장', os.path.relpath(OUT, os.getcwd()))
# 검수 그림: 원화 | 새 그림
bg = (236, 232, 224, 255)
def on(im):
    c = Image.new('RGBA', im.size, bg); c.alpha_composite(im); return c.convert('RGB')
cells = [on(Image.fromarray(RA)), on(out)]
rv = os.path.join(HERE, 'review'); os.makedirs(rv, exist_ok=True)
sheet = Image.new('RGB', (512 * len(cells) + 10 * (len(cells) - 1), 512), 'white')
for i, c in enumerate(cells): sheet.paste(c, (i * 522, 0))
sheet.save(os.path.join(rv, 'art_skirt20.png'))
