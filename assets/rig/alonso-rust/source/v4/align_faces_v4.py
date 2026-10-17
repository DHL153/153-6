"""표정 머리 12장을 기준 머리(work/head3q.png)에 ECC(닮음)로 정렬 → 얼굴 부분만 오려 work/face_<name>.png (기준 머리와 같은 크기·좌표).
머리카락·머리띠·외곽선은 기준 머리 것을 쓰고, 눈·눈썹·입만 바뀜 (니콜과 같은 원칙). 실행: cd v4 && python3 -I align_faces_v4.py"""
import cv2, numpy as np, json
from PIL import Image
names = ['neutral', 'happy', 'effort', 'shout', 'angry', 'focus', 'sad', 'grimace', 'relaxed', 'surprised', 'blink_half', 'blink_closed']
B = np.asarray(Image.open('work/head3q.png').convert('RGBA')).astype(np.float32); H, W = B.shape[:2]
def gray(a): A = a[..., 3:4] / 255; return (a[..., :3] * A + 200 * (1 - A)).mean(-1).astype(np.float32)
gB = gray(B)
yy, xx = np.mgrid[0:H, 0:W]
ell = ((xx - 222) / 98) ** 2 + ((yy - 208) / 66) ** 2
mask = np.clip((1.0 - ell) / 0.12, 0, 1)            # 얼굴 타원, 가장자리 부드럽게
mask *= (B[..., 3] > 200)                            # 기준 머리 안쪽만
res = {}
for i, n in enumerate(names):
    E = np.asarray(Image.open(f'work/expr{i + 1:02d}.png').convert('RGBA')).astype(np.float32)
    s = W / E.shape[1]; M = np.array([[s, 0, 0], [0, s, 0]], np.float32)
    M[1, 2] = (H - E.shape[0] * s)                   # 아래(목) 맞춤으로 시작
    gE = gray(E)
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6)
    try:
        cc, M = cv2.findTransformECC(gB, cv2.warpAffine(gE, M, (W, H), borderValue=200).astype(np.float32) * 0 + gB * 0 + gE.mean(), M, cv2.MOTION_AFFINE, crit) if False else (0, M)
    except Exception: pass
    # 역방향: 기준 → 표정 좌표가 아니라 표정 → 기준 변환을 직접 최적화
    warp = np.eye(2, 3, dtype=np.float32)
    E0 = cv2.warpAffine(gE, M, (W, H), borderValue=200)
    try: cc, warp = cv2.findTransformECC(gB, E0.astype(np.float32), warp, cv2.MOTION_AFFINE, crit, None, 5)
    except cv2.error as e: cc = -1
    Mf = np.vstack([M, [0, 0, 1]]); Wf = np.vstack([warp, [0, 0, 1]]); Mt = (np.linalg.inv(Wf) @ Mf)[:2]   # warp 는 기준→E0 이므로 역을 곱함
    Ew = cv2.warpAffine(E, Mt, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    diff = float(np.abs(gray(Ew) - gB)[(B[..., 3] > 200) & (mask < .05)].mean())   # 얼굴 밖(머리카락) 차이 = 정렬 품질
    out = Ew.copy(); out[..., 3] = Ew[..., 3] * mask
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA').save(f'work/face_{n}.png')
    res[n] = {'cc': round(float(cc), 3), 'hairDiff': round(diff, 1)}
    print(n, res[n])
json.dump(res, open('work/faces.json', 'w'), indent=1)
