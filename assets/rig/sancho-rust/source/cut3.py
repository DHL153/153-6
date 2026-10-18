# 3 러스트 산초 조각 시트 1(05:45 받음, 자홍 배경) 자르기 — 키잉은 6 카르덴 cut_sheet.key, 조각 = 덩어리(줄 → 왼쪽부터)
#  배율(SIFT, 시트 → 원화): 전체 자세·머리·표정·칼 = 1.00(원화 크기 그대로, 칼은 원화 칼을 −21.4° 세운 것), 몸 조각은 0.7~1.0 → 조각마다 따로 맞춤
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'carden-rust', 'source'))
from cut_sheet import key, blobs
HERE = os.path.dirname(os.path.abspath(__file__))
#  줄 1: 전체 자세 · 머리 · 표정 2 · 칼 / 줄 2: 표정 3 / 줄 3: 표정 1 · 상체 · 앞자락 · 어깨갑 / (팔 4) / 다리 8 / 주먹 4
NAMES = {'pose': 0, 'head': 1, 'face_neutral': 2, 'face_happy': 3, 'sword': 4, 'face_angry': 5, 'face_focus': 6, 'face_shout': 7,
         'face_effort': 8, 'torso': 9, 'upperA': 10, 'upperB': 11, 'foreA': 12, 'foreB': 13, 'skirt': 14, 'pauldronF': 15,   # 팔: 소매 윗팔 2(A·B) · 붕대 팔뚝 2 — 가까운/먼은 조립 때 원화와 비교해 정함
         'thighN': 16, 'kneeN': 17, 'shinN': 18, 'bootN': 19, 'thighF': 20, 'kneeF': 21, 'shinF': 22, 'bootF': 23,
         'gNv': 24, 'gNh': 25, 'gFv': 26, 'gFh': 27}
if __name__ == '__main__':
    rgba, alpha = key(np.asarray(Image.open(os.path.join(HERE, 'sheets', 'sheet1.png')).convert('RGB')))
    bs = [b for b in blobs(alpha) if (b['x1'] - b['x0']) * (b['y1'] - b['y0']) > 300]
    #  순서 = 시트 자리(아래 표의 왼쪽 위 점)에 가장 가까운 덩어리 — 줄 묶기가 작은 조각 줄(팔 y 650)과 상체 줄(y 590~680)을 섞었음
    AT = [(114, 31), (610, 51), (870, 51), (1130, 51), (1415, 80), (610, 301), (870, 301), (1131, 301), (612, 551), (871, 593),
          (101, 651), (241, 651), (382, 650), (522, 651), (1052, 621), (1232, 617), (103, 801), (261, 801), (421, 800), (581, 802),
          (743, 801), (900, 800), (1061, 801), (1221, 801), (351, 941), (630, 941), (912, 941), (1190, 942)]
    bs = [min(bs, key=lambda b: abs(b['x0'] - x) + abs(b['y0'] - y)) for x, y in AT]
    print('pieces', len(bs))
    assert len(bs) == len(NAMES), len(bs)
    os.makedirs(os.path.join(HERE, 'pieces'), exist_ok=True); idx = {}
    for nm, i in NAMES.items():
        b = bs[i]; p = rgba[b['y0']:b['y1'], b['x0']:b['x1']].copy(); p[..., 3] = (p[..., 3] * b['mask'][b['y0']:b['y1'], b['x0']:b['x1']]).astype(np.uint8)
        Image.fromarray(p, 'RGBA').save(os.path.join(HERE, 'pieces', nm + '.png')); idx[nm] = [int(b['x0']), int(b['y0']), int(b['x1'] - b['x0']), int(b['y1'] - b['y0'])]
    json.dump(idx, open(os.path.join(HERE, 'pieces', 'index.json'), 'w'), ensure_ascii=False, indent=0)
    print(idx)
