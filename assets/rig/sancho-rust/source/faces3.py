"""3 러스트 산초 표정: 조각 시트 머리 그림(face_*)에서 눈·눈썹·입만 원화 얼굴 자리로 옮겨 붙임 (build_sancho.py 가 exec). 11 faces11.py 방식.
- face_* 끼리는 머리카락으로 맞춤(ECC 아핀) → face_neutral 기준
- face_neutral → 원화: geom.json faceNeutral (tools/face_fit.py — 원화 얼굴 피부 영역에서 그림 차이 최소, sx 0.926 sy 0.944)
- 붙이는 곳 = 원화 얼굴 피부(가장 큰 덩어리, 구멍 메움 = 눈·입 포함, 앞머리·귀 밖) — 앞머리는 원화 그대로 남음. 1.2px 흐림. 시트 피부색은 원화 피부색으로 옮김
- 깜빡임 그림은 시트에 없음 → v1 은 깜빡임 없음(BLINK None)
입력 전역: RA, PC, W, o_head, GEO
출력: work/face_<n>.png (머리 그림과 같은 칸), FACE_N, FACES, BLINK"""
FACE_N = ['happy', 'angry', 'focus', 'shout', 'effort']
def _fload(n):   # 자홍 배경 번짐(턱 외곽선 보라색) 지움 — sheet_copy 와 같은 방법
    a = np.array(Image.open(os.path.join(PC, f'face_{n}.png')).convert('RGBA')).astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None)
    a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
def _gray_pad(a):
    bg = np.full((260, 220), 255, np.float32); gray = a[..., :3].astype(np.float32).mean(2) * a[..., 3] / 255 + 255 * (1 - a[..., 3] / 255)
    bg[20:20 + gray.shape[0], 20:20 + gray.shape[1]] = gray; return bg
_ref = _gray_pad(_fload('neutral')); _hm = np.zeros_like(_ref, np.uint8); _hm[20:125, :] = 1   # 머리카락 띠(조각 0~105줄)로 맞춤
_N2O = np.array(GEO['faceNeutral']['M'], np.float64)
def _skin(a):
    h = cv2.cvtColor(a[..., :3], cv2.COLOR_RGB2HSV); return (h[..., 0] >= 5) & (h[..., 0] <= 25) & (h[..., 1] > 80) & (h[..., 2] > 140) & (a[..., 3] > 200)
_fs = np.zeros((512, 512), bool); _fs[262:332, 268:356] = _skin(RA)[262:332, 268:356]
_lb, _n = ndimage.label(_fs); _sz = ndimage.sum(_fs, _lb, range(1, _n + 1)); _face = ndimage.binary_fill_holes(_lb == (int(np.argmax(_sz)) + 1))
_fm = np.clip(   # 바깥 경계는 안쪽으로만 흐림(앞머리 선 그대로)
cv2.GaussianBlur(cv2.erode(_face.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
_osk = _skin(RA) & _face; _omean = RA[..., :3][_osk].mean(0)
FACE_INFO = {}
for n in FACE_N:
    a = _fload(n); W2 = np.eye(2, 3, dtype=np.float32)
    try: _, W2 = cv2.findTransformECC(_ref, _gray_pad(a), W2, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), _hm, 5)
    except cv2.error: print('  face ECC fail', n)
    P = np.vstack([W2, [0, 0, 1]]); Pi = np.linalg.inv(P)
    T_in = np.array([[1, 0, 20], [0, 1, 20], [0, 0, 1.0]]); T_out = np.array([[1, 0, -20], [0, 1, -20], [0, 0, 1.0]])
    M = np.vstack([_N2O, [0, 0, 1]]) @ T_out @ Pi @ T_in                  # 조각 → 원화
    wf = cv2.warpAffine(a, M[:2], (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    sk = _skin(wf) & _face
    if sk.sum() > 50:
        d = _omean - wf[..., :3][sk].mean(0); s3 = _skin(wf); wf = wf.copy(); wf[..., :3][s3] = np.clip(wf[..., :3][s3].astype(np.float32) + d, 0, 255).astype(np.uint8)
    al = _fm * (wf[..., 3] / 255.0)
    out = RA.astype(np.float32).copy(); out[..., :3] = out[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]
    out = out.astype(np.uint8)
    hb = np.array(Image.open(os.path.join(W, 'headArt.png')))
    x0, y0 = int(o_head[0]), int(o_head[1]); hh, ww = hb.shape[:2]
    fc = out[y0:y0 + hh, x0:x0 + ww].copy(); fc[..., 3] = hb[..., 3]
    hrgb = hb[..., :3]; fc[..., :3] = np.where((_face[y0:y0 + hh, x0:x0 + ww] == 0)[..., None], hrgb, fc[..., :3])   # 얼굴 밖은 머리 그림 그대로(칼 뒤 메운 머리카락 포함)
    Image.fromarray(fc).save(os.path.join(W, f'face_{n}.png')); FACE_INFO[n] = [round(float(W2[0, 0]), 3), round(float(W2[0, 2]), 1), round(float(W2[1, 2]), 1)]
print('  faces (ECC to neutral)', FACE_INFO)
FACES = {n: f'face_{n}' for n in FACE_N}; FACES['grimace'] = 'face_effort'; FACES['surprised'] = 'face_shout'
BLINK = None
