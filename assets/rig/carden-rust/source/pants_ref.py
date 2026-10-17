"""원화(ref1024)에서 바지(벨트 아래 ~ 무릎 아래 바짓단)를 오려 '반바지 치마'(skirt 뼈) 그림으로 (DHL 2026-10-17 23:51 '표시한 곳까지 다리가 없고 그 아래 다리가 걷게')
시트 조각(엉덩이 띠 + 허벅지 2)은 원화의 둥근 바지 모양과 달라서(23:58 비교) 원화를 그대로 씀. 위는 몸통 밑으로 들어감(770), 아래는 바짓단(≈932) 부드럽게.
손(왼쪽 위)·부츠는 뺌. 결과: parts_work/pants.png + pants.json {pivot: 허리(skirt 뼈) 자리}"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(HERE, 'measure', 'joints_ref.json')))
R = np.asarray(Image.open(os.path.join(HERE, 'ref1024.png')).convert('RGBA')).astype(float)
x0, y0, x1, y1 = 260, 770, 680, 950
a = R[y0:y1, x0:x1].copy(); H, W = a.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]; X, Y = xx + x0, yy + y0
k = np.ones((H, W))
k[(X < 305) & (Y < 828)] = 0                                    # 가까운 손
# 바짓단: 원화의 바짓단 검은 선 바로 아래(그 밑 갈색·검은 띠는 부츠 목 — 00:15 세로줄 색 분석: 따뜻한 갈색 시작점·알파 끝)에서 자르고
# 마지막 3px 을 원화 선 색으로 칠해 마감 (자른 면이 평평하게 보이던 것 수정)
HX = [260, 290, 320, 350, 380, 410, 440, 470, 500, 530, 560, 590, 620, 650, 680]
HY = [917, 919, 915, 916, 915, 918, 918, 918, 917, 919, 921, 922, 921, 916, 914]
cut = np.interp(np.arange(W) + x0, HX, HY)[None, :]
k *= np.clip(cut - Y + .5, 0, 1)
line = (Y > cut - 3.5) & (R[y0:y1, x0:x1, 3] > 128); t_ = np.clip(Y - (cut - 3.5), 0, 1)
a[..., :3][line] = a[..., :3][line] * (1 - t_[line, None]) + np.array([26, 21, 21]) * t_[line, None]
a[..., 3] *= k
m = a[..., 3] > 30; lb, n = nd.label(m); sz = nd.sum(m, lb, range(1, n + 1)); a[..., 3] *= (lb == 1 + int(np.argmax(sz)))
ys, xs = np.nonzero(a[..., 3] > 4); ox, oy = int(xs.min()), int(ys.min()); a = a[oy:ys.max() + 1, ox:xs.max() + 1]
Image.fromarray(a.astype(np.uint8), 'RGBA').save(os.path.join(HERE, 'parts_work', 'pants.png'))
waist = np.array(J['waist'], float) * 2
piv = [round(waist[0] - x0 - ox, 1), round(waist[1] - y0 - oy, 1)]
json.dump({'pivot': piv, 'size': [a.shape[1], a.shape[0]], 'from': 'ref1024'}, open(os.path.join(HERE, 'pants.json'), 'w')); print('pants', a.shape[1], a.shape[0], 'pivot', piv)
# 부츠·정강이도 원화에서 (시트 부츠는 원화보다 작고 각졌음 — 23:58 비교). 부츠 = 먼 발(앞코가 오른쪽 = 달리는 쪽), 두 발 같은 그림
bx0, by0, bx1, by1 = 543, 924, 658, 992
b = R[by0:by1, bx0:bx1].copy(); hh, ww = b.shape[:2]; yy, xx = np.mgrid[0:hh, 0:ww]
b[..., 3] *= np.clip((yy - 2) / 4, 0, 1)                       # 위 테(바짓단과 이어지는 곳) 부드럽게
Image.fromarray(b.astype(np.uint8), 'RGBA').save(os.path.join(HERE, 'parts_work', 'bootR.png'))
s = R[930:948, 560:612].copy(); s = np.concatenate([s] * 4, 0)        # 부츠 목(어두운 가죽) 줄을 이어 붙여 정강이 — 위 절반은 부드럽게 사라짐(무릎은 바지 속)
hh_, ww_ = s.shape[:2]; yy_, xx_ = np.mgrid[0:hh_, 0:ww_]; s[..., 3] *= np.clip((yy_ - 2) / 10, 0, 1)
hw_ = 26 * np.sqrt(np.clip((yy_ + 4) / 34, 0, 1))                  # 위 끝은 둥글게 좁힘: 다리가 기울어도 네모 모서리가 바짓단 옆으로 안 삐져나옴 (00:10 legs8i)
s[..., 3] *= np.clip((hw_ - np.abs(xx_ + .5 - ww_ / 2)) / 3, 0, 1)
Image.fromarray(s.astype(np.uint8), 'RGBA').save(os.path.join(HERE, 'parts_work', 'shinR.png'))
json.dump({'pivot': [round(waist[0] - x0 - ox, 1), round(waist[1] - y0 - oy, 1)], 'size': [a.shape[1], a.shape[0]], 'from': 'ref1024',
           'boot': {'ankle': [585 - bx0, 955 - by0], 'sole': [[-37, 28], [-30, 33], [45, 33], [65, 22]]}, 'shin': {'a': [26, 0], 'b': [26, 72]}},
          open(os.path.join(HERE, 'pants.json'), 'w'))
