"""26 스카이아크 카르덴 — 16 네온 pants_ref.py 복사, 자리·색은 스카이 원화에서 다시 잼 (10-18 22:27): 바짓단 = 남색 끝(열마다) + 4px 검은 선, 먼 무릎 덧댐 쪽은 검은 선 위치, 부츠 = 먼 발(앞코 오른쪽), 바지 통 색 = 남색
16 네온 카르덴 — 6 러스트 pants_ref.py 복사, 자리·색은 네온 원화(review/g_pants·g_hemN·g_hemF 격자)에서 다시 잼 (10-18 12:45)
원화(ref1024)에서 바지(벨트 아래 ~ 무릎 아래 바짓단)를 오려 '반바지 치마'(skirt 뼈) 그림으로 (DHL 2026-10-17 23:51 '표시한 곳까지 다리가 없고 그 아래 다리가 걷게')
시트 조각(엉덩이 띠 + 허벅지 2)은 원화의 둥근 바지 모양과 달라서(23:58 비교) 원화를 그대로 씀. 위는 몸통 밑으로 들어감(770), 아래는 바짓단(≈932) 부드럽게.
손(왼쪽 위)·부츠는 뺌. 결과: parts_work/pants.png + pants.json {pivot: 허리(skirt 뼈) 자리}"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(HERE, 'measure', 'joints_ref.json')))
R = np.asarray(Image.open(os.path.join(HERE, 'ref1024.png')).convert('RGBA')).astype(float)
x0, y0, x1, y1 = 250, 768, 736, 950
a = R[y0:y1, x0:x1].copy(); H, W = a.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]; X, Y = xx + x0, yy + y0
k = np.ones((H, W))
# 가까운 손: 네온은 장갑과 바지 사이가 투명(g_glovepants) → 가장 큰 덩어리만 남기면 빠짐
# 바짓단: 원화의 바짓단 검은 선 바로 아래(그 밑 갈색·검은 띠는 부츠 목 — 00:15 세로줄 색 분석: 따뜻한 갈색 시작점·알파 끝)에서 자르고
# 마지막 3px 을 원화 선 색으로 칠해 마감 (자른 면이 평평하게 보이던 것 수정)
HX = [250, 280, 295, 310, 325, 340, 355, 370, 385, 400, 415, 430, 445, 520, 535, 550, 565, 580, 595, 610, 625, 640, 650, 665, 680, 695, 710, 736]
HY = [866, 881, 892, 892, 901, 906, 908, 909, 907, 902, 892, 871, 862, 853, 862, 893, 900, 905, 902, 901, 903, 899, 906, 904, 899, 892, 874, 860]
cut = np.interp(np.arange(W) + x0, HX, HY)[None, :]
k *= np.clip(cut - Y + .5, 0, 1)
line = (Y > cut - 3.5) & (R[y0:y1, x0:x1, 3] > 128); t_ = np.clip(Y - (cut - 3.5), 0, 1)
a[..., :3][line] = a[..., :3][line] * (1 - t_[line, None]) + np.array([16, 15, 20]) * t_[line, None]
a[..., 3] *= k
# (스카이 확인 10-18 22:27: 가까운 장갑과 바지·주머니 사이는 투명 틈 — 장갑은 가장 큰 덩어리 남기기로 빠짐. 장갑 지우기·메우기 안 함)
m = a[..., 3] > 30; lb, n = nd.label(m); sz = nd.sum(m, lb, range(1, n + 1)); a[..., 3] *= (lb == 1 + int(np.argmax(sz)))
ys, xs = np.nonzero(a[..., 3] > 4); ox, oy = int(xs.min()), int(ys.min()); a = a[oy:ys.max() + 1, ox:xs.max() + 1]
Image.fromarray(a.astype(np.uint8), 'RGBA').save(os.path.join(HERE, 'parts_work', 'pants.png'))
waist = np.array(J['waist'], float) * 2
piv = [round(waist[0] - x0 - ox, 1), round(waist[1] - y0 - oy, 1)]
json.dump({'pivot': piv, 'size': [a.shape[1], a.shape[0]], 'from': 'ref1024'}, open(os.path.join(HERE, 'pants.json'), 'w')); print('pants', a.shape[1], a.shape[0], 'pivot', piv)
# 부츠·정강이도 원화에서 (시트 부츠는 원화보다 작고 각졌음 — 23:58 비교). 부츠 = 먼 발(앞코가 오른쪽 = 달리는 쪽), 두 발 같은 그림
bx0, by0, bx1, by1 = 552, 900, 760, 1004
b = R[by0:by1, bx0:bx1].copy(); hh, ww = b.shape[:2]; yy, xx = np.mgrid[0:hh, 0:ww]
b[..., 3] *= np.clip((yy - 2) / 4, 0, 1)                       # 위 테(바짓단과 이어지는 곳) 부드럽게
if True:   # 위 12줄은 부츠 목 폭(그림 x 8~78)만 남기고 흐리게 — 원화에서 함께 잘려 온 바짓단 끝·가죽 띠가 네모 상자로 보였음(10-18 01:19, 바지 통 정강이가 그 자리를 이음)
    top_ = np.clip((yy - 4) / 8, 0, 1); side_ = np.clip(np.minimum(xx - 30, 112 - xx) / 4, 0, 1); keep_ = np.where(yy < 20, np.minimum(top_, side_), 1.0); b[..., 3] *= keep_
Image.fromarray(b.astype(np.uint8), 'RGBA').save(os.path.join(HERE, 'parts_work', 'bootR.png'))
s = R[912:926, 596:640].copy(); s = np.concatenate([s] * 4, 0)        # 부츠 목(어두운 가죽) 줄을 이어 붙여 정강이 — 위 절반은 부드럽게 사라짐(무릎은 바지 속)
hh_, ww_ = s.shape[:2]; yy_, xx_ = np.mgrid[0:hh_, 0:ww_]; s[..., 3] *= np.clip((yy_ - 2) / 10, 0, 1)
hw_ = 26 * np.sqrt(np.clip((yy_ + 4) / 34, 0, 1))                  # 위 끝은 둥글게 좁힘: 다리가 기울어도 네모 모서리가 바짓단 옆으로 안 삐져나옴 (00:10 legs8i)
s[..., 3] *= np.clip((hw_ - np.abs(xx_ + .5 - ww_ / 2)) / 3, 0, 1)
Image.fromarray(s.astype(np.uint8), 'RGBA').save(os.path.join(HERE, 'parts_work', 'shinR.png'))
json.dump({'pivot': [round(waist[0] - x0 - ox, 1), round(waist[1] - y0 - oy, 1)], 'size': [a.shape[1], a.shape[0]], 'from': 'ref1024',
           'boot': {'ankle': [620 - bx0, 950 - by0], 'sole': [[-52, 28], [-44, 36], [96, 45], [124, 36]]}, 'shin': {'a': [22, 0], 'b': [22, 56]}},
          open(os.path.join(HERE, 'pants.json'), 'w'))
# 바지 정강이 통(shinP, DHL 10-18 01:19 '다리가 하체와 붙게, 분리돼서 유령처럼 되지 않게'): 정강이를 가는 가죽 띠 대신 바지 천 통으로
# — 바짓단 밑에서 부츠까지 바지가 이어져 보임(런지로 발이 멀리 나가도 떨어져 보이지 않음). 색 = 원화 바지(중간 62,54,51 · 그림자 · 테두리)
TW, TH = 105, 110
tub = np.zeros((TH, TW, 4), np.float32); xs_ = (np.arange(TW) + .5) / TW
base = np.array([53, 57, 70], np.float32); dark = np.array([40, 43, 58], np.float32); hi = np.array([66, 71, 86], np.float32); ol = np.array([16, 15, 20], np.float32)   # 스카이 바지 남색(원화 중앙값 53,57,70)
edge = np.clip(1 - np.minimum(xs_, 1 - xs_) / .2, 0, 1) ** 1.5; hl = np.exp(-((xs_ - .36) / .1) ** 2) * .8
col = base[None] * (1 - edge[:, None]) + dark[None] * edge[:, None]; col = col * (1 - hl[:, None]) + hi[None] * hl[:, None]
rng = np.random.default_rng(6); nz = rng.normal(0, 2.2, (TH, TW, 1)).astype(np.float32)
tub[..., :3] = col[None] + nz
xo = np.arange(TW); olm = (xo < 4) | (xo >= TW - 4); tub[:, olm, :3] = ol
yy2 = np.arange(TH)[:, None]; hw2 = (TW / 2 + 3) * np.sqrt(np.clip((yy2 + 6) / 30, 0, 1))   # +3: 양옆 테두리까지 다 보이게
tub[..., 3] = 255 * np.clip((yy2 - 2) / 10, 0, 1) * np.clip((TH - 1 - yy2) / 6, 0, 1) * np.clip((hw2 - np.abs(xo[None] + .5 - TW / 2)) / 3, 0, 1)   # 아래 끝도 흐리게(부츠 속에서 끝남)
Image.fromarray(np.clip(tub, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(HERE, 'parts_work', 'shinP.png'))
PJ_ = json.load(open(os.path.join(HERE, 'pants.json'))); PJ_['shinP'] = {'a': [TW / 2, 0], 'b': [TW / 2, TH - 4]}; json.dump(PJ_, open(os.path.join(HERE, 'pants.json'), 'w'))
print('shinP', TW, TH)
