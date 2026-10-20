"""10 러스트 브루노 — 프롬프트 2·3 '부품만 지운 원화' 검수 (SIFT 배율·이동 · 지운 곳 밖 색 차이 · 지운 곳에 남은 흔적)
입력: ../ref512.png · ../sheets/nonear_*.png(가까운 팔·도끼 지움) · ../sheets/nofar_*.png(먼 팔·도끼 지움) · ../work/labels.npy
출력: ../review/check_remove10.png(원화 · 받은 그림 · 바뀐 곳 빨강, 어두운 배경) + 숫자
실행: python3 -I check_remove10.py nonear.png nofar.png
"""
import json, os, sys
import numpy as np, cv2
from PIL import Image
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RA = np.array(Image.open(os.path.join(S, 'ref512.png')).convert('RGBA'))
lab = np.load(os.path.join(S, 'work', 'labels.npy')); NAMES = json.load(open(os.path.join(S, 'work', 'label_names.json')))
L = lambda *ns: np.logical_or.reduce([lab == NAMES.index(n) + 1 for n in ns])
def sift(a, b):
    s = cv2.SIFT_create(); g = lambda x: cv2.cvtColor(x[..., :3], cv2.COLOR_RGB2GRAY)
    k1, d1 = s.detectAndCompute(g(a), None); k2, d2 = s.detectAndCompute(g(b), None)
    m = [p for p, q in cv2.BFMatcher().knnMatch(d1, d2, k=2) if p.distance < .7 * q.distance]
    P = np.float32([k1[x.queryIdx].pt for x in m]); Q = np.float32([k2[x.trainIdx].pt for x in m])
    A, inl = cv2.estimateAffinePartial2D(P, Q, ransacReprojThreshold=2)
    return len(m), int(inl.sum()), float(np.hypot(A[0, 0], A[0, 1])), A[:, 2]
def onbg(im):
    b = Image.new('RGBA', (512, 512), (52, 52, 62, 255)); b.alpha_composite(Image.fromarray(im)); return np.array(b.convert('RGB'))
rows = []
for path, rem in ((sys.argv[1], L('upperN', 'foreN', 'fistN', 'axeN')), (sys.argv[2], L('upperF', 'foreF', 'fistF', 'axeF'))):
    B = np.array(Image.open(path).convert('RGBA'))
    n, ni, sc, t = sift(RA, B)
    remD = cv2.dilate(rem.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    pa = RA[..., :3].astype(float) * RA[..., 3:4] / 255; pb = B[..., :3].astype(float) * B[..., 3:4] / 255
    d = np.abs(pa - pb).max(-1); da = np.abs(RA[..., 3].astype(int) - B[..., 3].astype(int))
    ch = (d > 24) | (da > 40)
    out = ch & ~remD
    print(os.path.basename(path), f'SIFT {n}/{ni} 배율 {sc:.4f} 이동 ({t[0]:.2f},{t[1]:.2f})',
          f'· 지운 곳(+4px) 밖 평균 차 {d[~remD].mean():.3f} · 밖 바뀐 px {int(out.sum())} · 지운 곳 안 바뀐 px {int((ch & remD).sum())}/{int(rem.sum())}',
          f'· 지운 곳 안 여전히 불투명 px {int((rem & (B[..., 3] > 128)).sum())}')
    ys, xs = np.nonzero(out)
    if len(ys): print('   밖 바뀐 곳 상자 x', xs.min(), xs.max(), 'y', ys.min(), ys.max())
    v = onbg(B).copy(); r = onbg(RA).copy(); r[ch] = (r[ch] * .3 + np.array([255, 40, 40]) * .7).astype(np.uint8)
    rows.append(np.hstack([onbg(RA), np.full((512, 8, 3), 255, np.uint8), v, np.full((512, 8, 3), 255, np.uint8), r]))
Image.fromarray(np.vstack([rows[0], np.full((8, rows[0].shape[1], 3), 255, np.uint8), rows[1]])).save(os.path.join(S, 'review', 'check_remove10.png'))
