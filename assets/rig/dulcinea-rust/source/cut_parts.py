# 2 러스트 둘시네 조각 시트 1(10:01 받음, 3072, 자홍, 6×6 칸) 자르기: python3 -I cut_parts.py
#  키잉·덩어리 = 6 카르덴 cut_sheet.key·blobs, 이름 = 조각 가운데가 든 칸 번호(배치도 ref_B 번호)
#  팔 4·허벅지 2(12·13·14·17·19·20)는 배치도 회색 도형을 칠한 것 → 'bad_' 붙여 따로 둠(쓰지 않음, 실수 28)
#  자홍 배경 조각 외곽선이 보라색으로 남는 것 정리(산초 교훈 6): min(R,B) − G 만큼 R·B 를 뺌
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'carden-rust', 'source'))
from cut_sheet import key, blobs
CELL = {1: 'pose', 2: 'head', 3: 'pony', 4: 'ribbonL', 5: 'ribbonS', 6: 'hammer', 7: 'torso', 8: 'pauldron', 9: 'hips',
        10: 'flapC', 11: 'flapN', 12: 'bad_upperF', 13: 'bad_upperN', 14: 'bad_foreN', 15: 'fistN', 16: 'fistNside', 17: 'bad_foreF',
        18: 'gripF', 19: 'bad_thighN', 20: 'bad_thighF', 21: 'bootN', 22: 'bootF', 23: 'kneeN', 24: 'kneeF',
        25: 'face_neutral', 26: 'face_happy', 27: 'face_angry', 28: 'face_focus', 29: 'face_shout', 30: 'face_effort',
        31: 'blink_half', 32: 'blink_closed'}

def unpurple(p):
    a = p.astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    s = np.clip(np.minimum(r, b) - g, 0, None); edge = a[..., 3] < 250
    k = np.where(edge, s, (s * .5).astype(int))
    a[..., 0] = np.clip(r - k, 0, 255); a[..., 2] = np.clip(b - k, 0, 255)
    return a.astype(np.uint8)

if __name__ == '__main__':
    src = np.asarray(Image.open(os.path.join(HERE, 'sheets', 'parts_v1.png')).convert('RGB'))
    rgba, alpha = key(src); H, W = alpha.shape; C = W / 6
    bs = [b for b in blobs(alpha, minpx=120) if b['px'] > 120]
    got = {}
    for b in bs:
        n = int(b['cy'] // C) * 6 + int(b['cx'] // C) + 1
        if n not in CELL: print('칸 밖 덩어리', n, b['px']); continue
        if n in got and got[n]['px'] >= b['px']: continue
        got[n] = b
    miss = [n for n in CELL if n not in got]; print('빠진 칸', miss)
    os.makedirs(os.path.join(HERE, 'cut'), exist_ok=True); idx = {}
    for n, b in sorted(got.items()):
        nm = CELL[n]; p = rgba[b['y0']:b['y1'], b['x0']:b['x1']].copy()
        p[..., 3] = (p[..., 3] * b['mask'][b['y0']:b['y1'], b['x0']:b['x1']]).astype(np.uint8)
        p = unpurple(p)
        Image.fromarray(p, 'RGBA').save(os.path.join(HERE, 'cut', nm + '.png'))
        idx[nm] = dict(cell=n, box=[int(b['x0']), int(b['y0']), int(b['x1'] - b['x0']), int(b['y1'] - b['y0'])], px=int(b['px']))
    json.dump(idx, open(os.path.join(HERE, 'cut', '_index.json'), 'w'), ensure_ascii=False, indent=0)
    print(len(idx), '조각')
    for k, v in idx.items(): print(f"{v['cell']:2d} {k:14s} {v['box']}")
