"""팔다리 조각의 관절 끝점(둥근 끝의 중심) — 긴 축(PCA) 양 끝에서 그 끝 폭의 절반만큼 안쪽."""
import numpy as np
from PIL import Image
def ends(fn, inset=0.5):
    A = np.asarray(Image.open(fn))[..., 3] > 128; ys, xs = np.nonzero(A); P = np.c_[xs, ys].astype(float); c = P.mean(0)
    w, v = np.linalg.eigh(np.cov((P - c).T)); u = v[:, -1]; n = v[:, 0]
    t = (P - c) @ u; s = (P - c) @ n; out = []
    for sgn in (-1, 1):
        tt = t * sgn; tmax = tt.max(); band = tt > tmax - 25; wid = s[band].max() - s[band].min()
        sel = tt > tmax - 6; mid = (s[band].max() + s[band].min()) / 2
        e = c + u * sgn * (tmax - wid * inset) + n * mid; out.append((e, wid))
    return out, u
if __name__ == '__main__':
    import sys
    for f in sys.argv[1:]:
        (a, wa), (b, wb), u = *ends(f)[0], ends(f)[1]
        print(f, 'end1', a.round(1), 'w', round(wa), 'end2', b.round(1), 'w', round(wb), 'len', round(float(np.linalg.norm(a - b)), 1))
