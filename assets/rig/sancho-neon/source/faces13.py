"""13 네온 산초 표정·깜빡임: 조각 시트 머리 그림(face_*, blink_*)에서 눈·눈썹만 원화 얼굴 자리로 옮겨 붙임 (build_neon.py 가 exec).
- 시트 표정 9장은 눈·눈썹 둘레(조각 x91~161, y103~144)만 다르고 나머지는 같은 그림(차이 평균 0.1~0.35) → 붙이는 곳 = 표정마다 neutral 과 다른 곳 전부의 합 + 5px(피부·눈 둘레에서 끝남)
- 시트 머리 → 원화: geom.json head (reg13 SIFT 0.997배·2.3°, 시트 head = face_neutral 같은 그림). 두 눈 다 바뀜(가까운·먼 눈), 입은 마스크가 가려 모든 표정이 마스크 그대로
- 깜빡임 = 시트 9(반쯤)·10(감음) 같은 방법
입력 전역: RA, PC, W, o_head, GEO, desp
출력: work/face_<n>.png (머리 그림과 같은 칸), FACE_N, BLINK_N, FACES, BLINK"""
FACE_N = ['happy', 'angry', 'focus', 'shout', 'effort']; BLINK_N = ['half', 'closed']
_SRC = {**{n: f'face_{n}' for n in FACE_N}, 'half': 'blink_half', 'closed': 'blink_closed'}
_fl = lambda nm: desp(np.array(Image.open(os.path.join(PC, nm + '.png')).convert('RGBA')))[0]
_neu = _fl('face_neutral').astype(np.int16); _U = np.zeros(_neu.shape[:2], bool)
for n in FACE_N + BLINK_N: _U |= np.abs(_fl(_SRC[n]).astype(np.int16) - _neu).max(2) > 40
_reg = cv2.dilate(_U.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))   # +5px
_N2O = np.array(GEO['head']['M'], np.float32)
_face = cv2.warpAffine(_reg, _N2O, (512, 512), flags=cv2.INTER_NEAREST) > 0
_face &= (RA[..., 3] > 200)
_fm = np.clip(cv2.GaussianBlur(cv2.erode(_face.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
_ys, _xs = np.nonzero(_face); print('  face region px', int(_face.sum()), 'art bbox', (int(_xs.min()), int(_ys.min()), int(_xs.max()), int(_ys.max())))
hb = np.array(Image.open(os.path.join(W, 'headArt.png'))); x0, y0 = int(o_head[0]), int(o_head[1]); hh, ww = hb.shape[:2]
for n in FACE_N + BLINK_N:
    wf = cv2.warpAffine(_fl(_SRC[n]), _N2O, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    al = _fm * (wf[..., 3] / 255.0)
    out = RA.astype(np.float32).copy(); out[..., :3] = out[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]; out = out.astype(np.uint8)
    fc = out[y0:y0 + hh, x0:x0 + ww].copy(); fc[..., 3] = hb[..., 3]
    fc[..., :3] = np.where((_face[y0:y0 + hh, x0:x0 + ww] == 0)[..., None], hb[..., :3], fc[..., :3])   # 얼굴 밖은 머리 그림 그대로
    Image.fromarray(fc).save(os.path.join(W, f'face_{n}.png'))
FACES = {n: f'face_{n}' for n in FACE_N}; FACES['grimace'] = 'face_effort'; FACES['surprised'] = 'face_shout'
BLINK = {'half': 'face_half', 'closed': 'face_closed'}
