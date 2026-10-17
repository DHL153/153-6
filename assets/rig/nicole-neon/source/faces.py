"""표정 10칸(+깜빡임 2)을 기준 머리(cut/head.png)에 맞추고 얼굴(피부 영역)만 오려 패치로. python3 -I faces.py
결과: parts_work/face_*.png, blink_*.png + faces.json (rig.json 의 faces / blinkFaces / parts 조각)"""
import json, os, cv2, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
def prem(a): b = a.copy(); b[..., :3] *= b[..., 3:4] / 255; return b
base = np.asarray(Image.open(os.path.join(HERE, 'cut/head.png')).convert('RGBA')).astype(np.float32); bh, bw = base.shape[:2]; B = prem(base)
r, g, b, al = base[..., 0], base[..., 1], base[..., 2], base[..., 3]
skin = (al > 200) & (r > 170) & (g > 110) & (b < 175) & (r - b > 45)
skin = cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(skin); big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); skin = (lab == big).astype(np.uint8)
cnts, _ = cv2.findContours(skin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); face = np.zeros_like(skin); cv2.drawContours(face, cnts, -1, 1, -1)
face = cv2.erode(face, np.ones((5, 5), np.uint8))
cv2.ellipse(face, (276, 178), (19, 37), 0, 0, 360, 1, -1)   # 먼 눈·눈썹(머리카락 가장자리에 붙어 있음)도 패치 범위에
face = (face & (base[..., 3] > 128)).astype(np.uint8)
feather = cv2.GaussianBlur(face.astype(np.float32), (0, 0), 1.6)
Image.fromarray((face * 255).astype(np.uint8)).save(os.path.join(HERE, 'parts_work/face_mask.png'))
names = {'face_effort': 'effort', 'face_shout': 'shout', 'face_happy': 'happy', 'face_sad': 'sad', 'face_angry': 'angry', 'face_grimace': 'grimace',
         'face_focus': 'focus', 'face_relaxed': 'relaxed', 'blink_half': None, 'blink_closed': None}
gb = cv2.cvtColor(B[..., :3].clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
hairM = ((base[..., 3] > 128) & (face == 0)).astype(np.uint8)   # 정렬은 머리카락(바뀌지 않는 부분)으로
out = {'parts': {}, 'faces': {}, 'report': {}}
for fn, key in names.items():
    cell = np.asarray(Image.open(os.path.join(HERE, 'cut', fn + '.png')).convert('RGBA')).astype(np.float32); C = prem(cell)
    best = None
    for s in np.arange(.85, 1.35, .01):
        M = cv2.getRotationMatrix2D((0, 0), 0, s); w = cv2.warpAffine(C, M, (bw + 300, bh + 300))
        a1 = (w[..., 3] > 128); a0 = base[..., 3] > 128
        if a1.sum() < 100: continue
        cy1, cx1 = np.argwhere(a1).mean(0); cy0, cx0 = np.argwhere(a0).mean(0); M2 = M.copy(); M2[0, 2] += cx0 - cx1; M2[1, 2] += cy0 - cy1
        a2 = cv2.warpAffine(C, M2, (bw, bh))[..., 3] > 128; iou = (a2 & a0).sum() / (a2 | a0).sum()
        if best is None or iou > best[0]: best = (iou, M2, s)
    iou, M, s = best
    gc = cv2.cvtColor(C[..., :3].clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    Minv = cv2.invertAffineTransform(M).astype(np.float32)
    cr, cg, cb_, ca = cell[..., 0], cell[..., 1], cell[..., 2], cell[..., 3]
    cskin = (ca > 200) & (cr > 170) & (cg > 110) & (cb_ < 175) & (cr - cb_ > 45)
    cmask = ((ca > 128) & ~cv2.dilate(cskin.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)).astype(np.uint8)
    try: cc, Minv = cv2.findTransformECC(gb, gc, Minv, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 400, 1e-6), cmask, 5)
    except Exception as e: cc = 0; print('ecc fail', fn, e)
    al_ = cv2.warpAffine(cell, Minv, (bw, bh), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    gw = cv2.cvtColor(prem(al_)[..., :3].clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    hairErr = float(np.abs(gw - gb)[hairM > 0].mean())
    patch = al_.copy(); patch[..., 3] = al_[..., 3] * feather
    ys, xs = np.nonzero(patch[..., 3] > 2); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    crop = patch[y0:y1, x0:x1].clip(0, 255).astype(np.uint8); Image.fromarray(crop, 'RGBA').save(os.path.join(HERE, 'parts_work', fn + '.png'))
    # 패치 pivot = 머리 pivot 과 같은 점이 되도록: head pivot 은 build 에서 neckImg → 여기선 머리 그림 좌표 원점 기준 오프셋만 기록
    out['parts'][fn] = {'x0': int(x0), 'y0': int(y0)}; out['report'][fn] = {'iou': round(float(iou), 3), 'ecc': round(float(cc), 3), 'hairErr': round(hairErr, 1)}
    if key: out['faces'][key] = fn
    comp = Image.fromarray(base.astype(np.uint8), 'RGBA'); comp.alpha_composite(Image.fromarray(crop, 'RGBA'), (int(x0), int(y0))); comp.save(os.path.join(HERE, 'parts_work', 'check_' + fn + '.png'))
json.dump(out, open(os.path.join(HERE, 'faces_raw.json'), 'w'), indent=1); print(json.dumps(out['report'], indent=0))
