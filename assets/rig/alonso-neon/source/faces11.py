"""11 네온 알론소 표정: 조각 시트의 머리 그림(face_*)에서 눈·눈썹·입만 원화 얼굴 자리로 옮겨 붙임 (build_neon.py 가 exec).
- face_* 끼리는 머리카락으로 맞춤(ECC 아핀) → face_neutral 기준
- face_neutral → 원화: 눈 두 개·입 세 점 아핀 (시트 (58,137)(94,137)(75,163) → 원화 (213,282)(252,279)(227,307))
- 붙이는 곳 = 원화 얼굴 피부 안(앞머리·옆머리 밖) 다각형(코 표시는 남김), 2px 흐림 — 눈 깜빡임(half·closed)은 두 눈 자리만(눈썹 그대로). 시트 피부색은 원화 피부색으로 옮김
입력 전역: RA(원화 RGBA), PC(조각 폴더), W(work), o_head(머리 오린 칸 왼쪽 위), HEAD_SIZE
출력: work/face_<n>.png (머리 그림과 같은 칸)"""
FACE_N = ['effort', 'shout', 'focus', 'happy', 'surprised', 'grimace', 'closed', 'half']
FACE_MASK = [(186, 257), (204, 253), (222, 262), (234, 268), (244, 266), (258, 259), (268, 262), (267, 292), (258, 302), (246, 316), (228, 321), (206, 317), (190, 306), (183, 290)]
def _fload(n):
    return np.array(Image.open(os.path.join(PC, f'face_{n}.png')).convert('RGBA'))
def _gray_pad(a):
    bg = np.full((260, 220), 255, np.float32); gray = a[..., :3].astype(np.float32).mean(2) * a[..., 3] / 255 + 255 * (1 - a[..., 3] / 255)
    bg[20:20 + gray.shape[0], 20:20 + gray.shape[1]] = gray; return bg
_ref = _gray_pad(_fload('neutral')); _hm = np.zeros_like(_ref, np.uint8); _hm[20:130, :] = 1
_N2O = cv2.getAffineTransform(np.float32([[58, 137], [94, 137], [75, 163]]), np.float32([[213, 282], [252, 279], [227, 307]]))
EYE_N = [(193, 272), (200, 266), (212, 267), (224, 271), (230, 276), (229, 288), (222, 296), (208, 297), (197, 293), (191, 284)]   # 눈 깜빡임(half·closed)은 눈만
EYE_F = [(243, 272), (252, 268), (262, 265), (265, 268), (264, 284), (261, 292), (250, 293), (244, 287)]
NOSE = [(240, 290), (253, 290), (253, 302), (240, 302)]   # 원화 코 표시(>)는 남김
def _mask(polys, holes=()):
    m = Image.new('L', (512, 512), 0); d = ImageDraw.Draw(m)
    for P in polys: d.polygon(P, fill=255)
    for P in holes: d.polygon(P, fill=0)
    return cv2.GaussianBlur(np.array(m).astype(np.float32) / 255, (5, 5), 1.2)
_fm = _mask([FACE_MASK], [NOSE]); _em = _mask([EYE_N, EYE_F])
def _skin(a):
    h = cv2.cvtColor(a[..., :3], cv2.COLOR_RGB2HSV); return (h[..., 0] >= 5) & (h[..., 0] <= 25) & (h[..., 1] > 90) & (h[..., 2] > 150) & (a[..., 3] > 200)
_osk = _skin(RA) & (_fm > .9); _omean = RA[..., :3][_osk].mean(0)
FACE_INFO = {}
for n in FACE_N:
    a = _fload(n); W2 = np.eye(2, 3, dtype=np.float32)
    _, W2 = cv2.findTransformECC(_ref, _gray_pad(a), W2, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), _hm, 5)
    # 조각 → (패딩 20) → neutral 패딩 좌표 → neutral 조각 → 원화: 합성 아핀
    P = np.vstack([W2, [0, 0, 1]]); Pi = np.linalg.inv(P)                # neutral_pad = Pi · piece_pad
    T_in = np.array([[1, 0, 20], [0, 1, 20], [0, 0, 1.0]]); T_out = np.array([[1, 0, -20], [0, 1, -20], [0, 0, 1.0]])
    M = np.vstack([_N2O, [0, 0, 1]]) @ T_out @ Pi @ T_in                  # piece → 원화
    wf = cv2.warpAffine(a, M[:2], (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    sk = _skin(wf) & (_fm > .9)
    if sk.sum() > 50:   # 피부색 맞춤: 피부 픽셀만 원화 평균으로 옮김
        d = _omean - wf[..., :3][sk].mean(0); s3 = _skin(wf); wf = wf.copy(); wf[..., :3][s3] = np.clip(wf[..., :3][s3].astype(np.float32) + d, 0, 255).astype(np.uint8)
    al = (_em if n in ('half', 'closed') else _fm) * (wf[..., 3] / 255.0)
    out = RA.astype(np.float32).copy(); out[..., :3] = out[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]
    out = out.astype(np.uint8)
    hb = np.array(Image.open(os.path.join(W, 'headArt.png')))                # 머리 그림 칸 그대로(알파 = 머리 그림 알파)
    x0, y0 = int(o_head[0]), int(o_head[1]); hh, ww = hb.shape[:2]
    fc = out[y0:y0 + hh, x0:x0 + ww].copy(); fc[..., 3] = hb[..., 3]
    Image.fromarray(fc).save(os.path.join(W, f'face_{n}.png')); FACE_INFO[n] = float(np.abs(M[0, 0]))
print('faces', {k: round(v, 3) for k, v in FACE_INFO.items()})
