"""16 네온 카르덴 표정 패치 (2026-10-18) — 6 러스트 faces.py 복사. 네온은 머리 그림 = 무표정 얼굴 조각 통째(head_face) → MH = face_neutral 변환, 얼굴 칸 FB 는 얼굴 조각 px
6 카르덴 표정 패치 (2026-10-17) — 고글 그대로, 눈썹·코·입만 바뀜(깜빡임 없음, DHL 20:52)
표정 시트 6장(face_*: 머리+옆머리+수염 통째)은 같은 자세 → ECC 로 무표정(face_neutral)에 맞춘 뒤
'무표정과 다른 곳'만(눈썹·입·코) 오려 머리 그림 좌표로 옮김. 수염 위에 그려야 하므로(입이 수염 속) 게임에선 headFront 자리에서 그림.
결과: parts_work/face_*.png, faces_out.json {parts:{이름:{x0,y0}}, faces:{표정:조각}, clip}, review/faces_check.png
실행: python3 -I faces.py   (그 다음 build_carden.py)"""
import json, os
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'parts_work')
S = json.load(open(os.path.join(HERE, 'sift_result.json')))
A = lambda v: np.array(v, np.float64)
H3 = lambda m: np.vstack([A(m), [0, 0, 1]])
load = lambda n: np.asarray(Image.open(os.path.join(HERE, 'cut', n + '.png')).convert('RGBA')).astype(np.float32)
MH = H3(S['face_neutral']['M']); MN = H3(S['face_neutral']['M'])   # 네온: 머리 그림 = 무표정 얼굴 조각
PAD = (80, 60)                                           # 머리 그림 좌표 밖(수염 아래·옆머리 옆)까지 담는 여백
_HW, _HH = Image.open(os.path.join(HERE, 'cut', 'face_neutral.png')).size; CW, CH = _HW + 2 * PAD[0], _HH + 2 * PAD[1]
def to_head(img, M):                                     # 조각(M: 조각→ref1024) → 머리 그림 좌표(+여백) 캔버스
    T = np.linalg.inv(MH) @ M; T = np.array([[1, 0, PAD[0]], [0, 1, PAD[1]], [0, 0, 1]]) @ T
    return cv2.warpAffine(img, T[:2], (CW, CH), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
N = load('face_neutral'); g = lambda a: cv2.cvtColor(np.clip(a[..., :3] * (a[..., 3:] / 255), 0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
NAMES = ['happy', 'angry', 'focus', 'sad', 'shout']
res = {'parts': {}, 'faces': {}, 'clip': [[0, 0], [1, 0], [0, 1]], 'facesFree': True, 'ecc': {}}
NW = to_head(N, MN); tiles = []
F = json.load(open(os.path.join(HERE, 'fix_result.json')))
def over(dst, src): a = src[..., 3:] / 255.; out = dst.copy(); out[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a); out[..., 3] = np.maximum(dst[..., 3], src[..., 3]); return out
BASE = NW                                                 # 네온: 옆머리·수염이 머리 그림 안에 있음
REF = BASE if os.environ.get('VS', 'nw') == 'base' else NW   # 기본: 무표정 시트와 다른 곳만(작은 패치). base 는 패치가 얼굴 전체로 커져 칸 경계에 이음매가 보임(22:40 확인)
yy, xx = np.mgrid[0:CH, 0:CW]; hx, hy = xx - PAD[0], yy - PAD[1]   # 머리 그림 좌표
FB = (80, 48, 184, 188)                                  # 얼굴 칸(얼굴 조각 px): 눈썹 y≈55 ~ 벌린 입 아래 y≈180, 땋은 끝(y>188)은 뺌 (review/g_faces)
BOX = np.clip(np.minimum.reduce([(hx - FB[0]) / 8, (FB[2] - hx) / 8, (hy - FB[1]) / 8, (FB[3] - hy) / 8]), 0, 1)
for nm in NAMES:
    X = load('face_' + nm); W = np.eye(2, 3, dtype=np.float32)
    try: _, W = cv2.findTransformECC(g(N), g(X), W, cv2.MOTION_EUCLIDEAN, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 5)
    except cv2.error: pass
    res['ecc'][nm] = np.round(W, 3).tolist()
    XW = to_head(X, MN @ np.linalg.inv(H3(W)))          # X → N 좌표(ECC 역) → ref1024 → 머리 좌표
    d = np.abs(XW[..., :3] - REF[..., :3]).max(-1) * (np.minimum(XW[..., 3], REF[..., 3]) > 128) + (np.abs(XW[..., 3] - REF[..., 3]) > 128) * 255
    m = d > 42; m = nd.binary_opening(m, iterations=1); lb, n = nd.label(m); sz = nd.sum(m, lb, range(1, n + 1))
    m = np.isin(lb, np.nonzero(sz >= 25)[0] + 1); m = nd.binary_closing(m, iterations=4); m = nd.binary_fill_holes(m); m = nd.binary_dilation(m, iterations=5)
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.2); a = np.clip(a * 1.6, 0, 1) * BOX   # 얼굴 칸 밖(옆머리·수염 끝·귀)은 패치에 안 넣음: 그 조각은 따로 출렁여서 겹치면 두 겹으로 보임
    P = XW.copy(); P[..., 3] = P[..., 3] * a
    ys, xs = np.nonzero(P[..., 3] > 4); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    Image.fromarray(np.clip(P[y0:y1, x0:x1], 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'face_' + nm + '.png'))
    res['parts']['face_' + nm] = {'x0': int(x0) - PAD[0], 'y0': int(y0) - PAD[1]}; res['faces'][nm] = 'face_' + nm
    t = np.clip(XW, 0, 255).astype(np.uint8).copy(); t[..., :3][m] = (t[..., :3][m] * .5 + np.array([255, 40, 40]) * .5).astype(np.uint8); tiles.append(t)
res['faces']['effort'] = 'face_angry'                    # 찌르기 트랙 이름(8 니콜) → 6 표정
json.dump(res, open(os.path.join(HERE, 'faces_out.json'), 'w'), indent=1)
o = np.concatenate(tiles, 1); bg = np.full(o.shape, 235, np.uint8); al = o[..., 3:] / 255.
Image.fromarray((o[..., :3] * al + bg[..., :3] * (1 - al)).astype(np.uint8)).save(os.path.join(HERE, 'review', 'faces_check.png'))
print(json.dumps({k: res[k] for k in ['parts', 'ecc']}))
