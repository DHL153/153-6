#!/usr/bin/env python3
"""서 있는 자세 리그 vs 원화: 머리 위·코트 밑단·발 위치 차이(px, 1024 기준). python3 idlediff.py render.png"""
import sys, numpy as np
from PIL import Image
R = np.asarray(Image.open('ref1024.png'))[..., 3] > 128; G = np.asarray(Image.open(sys.argv[1]))[..., 3] > 128
def m(A):
    top = np.nonzero(A[:, 300:660].any(1))[0].min()
    # 코트 밑단: x 420~600 열에서 위에서부터 첫 '빈 줄' (다리 사이) 직전 → 열마다 불투명 아래 끝 중 900 미만
    hem = []
    for x in range(430, 600, 10):
        col = np.nonzero(A[600:1000, x])[0] + 600; runs = np.split(col, np.nonzero(np.diff(col) > 1)[0] + 1); hem.append(runs[0][-1])
    feet = A[960:1020]; ys, xs = np.nonzero(feet)
    return dict(top=int(top), hem=float(np.median(hem)), feetX=[int(xs.min()), int(xs.max())])
print('ref', m(R)); print('rig', m(G))
