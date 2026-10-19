# 시트 조각 → 원화 자리 맞춤 (SIFT 닮음변환 + 마스크 SQDIFF 미세조정): from tools.place import place
import numpy as np, cv2
from PIL import Image
def comp(a, bg=255):
    A = a[..., 3:4].astype(np.float32) / 255; return (a[..., :3] * A + bg * (1 - A)).astype(np.uint8)
def sift_M(piece, ref, up=2, ratio=.75, thr=6):
    g = lambda a: cv2.cvtColor(comp(a), cv2.COLOR_RGB2GRAY)
    R = cv2.resize(g(ref), None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC); P = cv2.resize(g(piece), None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
    s = cv2.SIFT_create(); kr, dr = s.detectAndCompute(R, None); kp, dp = s.detectAndCompute(P, None)
    ms = cv2.BFMatcher().knnMatch(dp, dr, k=2); good = [m for m, n in ms if m.distance < ratio * n.distance]
    src = np.float32([kp[m.queryIdx].pt for m in good]) / up; dst = np.float32([kr[m.trainIdx].pt for m in good]) / up
    M, inl = cv2.estimateAffinePartial2D(src, dst, ransacReprojThreshold=thr / up * 2)
    return M, int(inl.sum()) if inl is not None else 0, len(good)
def refine(piece, ref, M, rng=(3, 3, .03, 2.0), steps=(7, 7, 7, 5)):
    """M 주변에서 이동·배율·각도를 바꿔 가며 (조각 불투명 곳) 원화와 색 차이 최소"""
    s0 = np.hypot(M[0, 0], M[1, 0]); a0 = np.degrees(np.arctan2(M[1, 0], M[0, 0])); best = None
    R = comp(ref).astype(np.float32); RA = ref[..., 3] > 128
    for ds in np.linspace(-rng[2], rng[2], steps[2]):
        for da in np.linspace(-rng[3], rng[3], steps[3]):
            s = s0 * (1 + ds); a = np.radians(a0 + da); c, si = np.cos(a) * s, np.sin(a) * s
            for dx in np.linspace(-rng[0], rng[0], steps[0]):
                for dy in np.linspace(-rng[1], rng[1], steps[1]):
                    Mt = np.float32([[c, -si, M[0, 2] + dx], [si, c, M[1, 2] + dy]])
                    w = cv2.warpAffine(piece, Mt, (ref.shape[1], ref.shape[0]), flags=cv2.INTER_LINEAR)
                    m = (w[..., 3] > 200) & RA
                    if m.sum() < 50: continue
                    e = np.abs(w[..., :3].astype(np.float32) - R)[m].mean()
                    if best is None or e < best[0]: best = (e, Mt)
    return best
