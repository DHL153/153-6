"""배율을 고정하거나 좁은 범위로 두고 회전·위치만 찾는 템플릿 매칭 (색 + 외곽선). python3 -I fixmatch.py jobs.json → fix_result.json"""
import json, sys, os, numpy as np, cv2
from PIL import Image
ref = np.asarray(Image.open('ref1024.png').convert('RGBA')).astype(np.float32)
def prem(a): b = a.copy(); b[..., :3] *= b[..., 3:4] / 255; return b
R0 = prem(ref)
def xform(img, s, deg):
    h, w = img.shape[:2]; c = (w / 2, h / 2); M = cv2.getRotationMatrix2D(c, deg, s)
    cs, sn = abs(M[0, 0]), abs(M[0, 1]); nw = int(h * sn + w * cs) + 4; nh = int(h * cs + w * sn) + 4
    M[0, 2] += nw / 2 - c[0]; M[1, 2] += nh / 2 - c[1]
    return cv2.warpAffine(img, M, (nw, nh), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0)), M
def go(j):
    img = prem(np.asarray(Image.open(j['file']).convert('RGBA')).astype(np.float32)); x0, y0, x1, y1 = j['roi']; R = R0[y0:y1, x0:x1]
    best = None
    for s in np.arange(*j['s']):
        for d in np.arange(*j['r']):
            T, M = xform(img, s, d); m = (T[..., 3] > 200).astype(np.float32); m = cv2.erode(m, np.ones((3, 3), np.uint8))
            if T.shape[0] >= R.shape[0] or T.shape[1] >= R.shape[1] or m.sum() < 50: continue
            res = cv2.matchTemplate(R[..., :3], T[..., :3], cv2.TM_SQDIFF, mask=np.dstack([m] * 3)) / m.sum()
            mn, _, loc, _ = cv2.minMaxLoc(res)
            if best is None or mn < best[0]: best = (mn, s, d, loc, M)
    mn, s, d, loc, M = best; M = M.copy(); M[0, 2] += loc[0] + x0; M[1, 2] += loc[1] + y0
    return dict(file=j['file'], score=float(mn), s=float(s), deg=float(d), M=M.tolist())
if __name__ == '__main__':
    jobs = json.load(open(sys.argv[1])); out = json.load(open('fix_result.json')) if os.path.exists('fix_result.json') else {}
    for n, j in jobs.items(): out[n] = go(j); print(n, round(out[n]['score']), round(out[n]['s'], 3), out[n]['deg'])
    json.dump(out, open('fix_result.json', 'w'), indent=1)
