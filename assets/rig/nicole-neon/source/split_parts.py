"""18 네온 니콜(nicole-neon) 조각 오리기 (2026-10-17)
입력: sheets/partsA.png (조각 묶음 시트 1차, DHL 제작), sheets/sheet0.png (원화)
출력: cut/<이름>.png (마젠타 키잉, 자루 토막은 아직 안 지움) + cut/_index.json
실행: cd source && python3 -I split_parts.py
불합격(재요청): fistF_REJ, thigh_REJ, shin_REJ — 리그에 쓰지 않음.
"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))

def key(fn):
    a = np.asarray(Image.open(fn).convert('RGB')).astype(float); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    bgc = np.median(a[:8, :8].reshape(-1, 3), 0); s = np.minimum(r, b) - g
    alpha = np.clip((175 - s) / (175 - 95), 0, 1); A = alpha[..., None]
    col = np.clip(np.where(A > .02, (a - (1 - A) * bgc) / np.maximum(A, 1e-3), 0), 0, 255)
    return np.dstack([col, alpha * 255]).astype(np.uint8), alpha

def pieces(fn, minpx=400, dil=6):
    rgba, alpha = key(fn)
    lab, n = nd.label(nd.binary_dilation(alpha > .5, iterations=dil)); out = []
    for i, sl in enumerate(nd.find_objects(lab)):
        m = lab[sl] == i + 1
        if m.sum() < minpx: continue
        p = rgba[sl].copy(); p[..., 3] = (p[..., 3] * m).astype(np.uint8)
        out.append(dict(x=sl[1].start, y=sl[0].start, w=sl[1].stop - sl[1].start, h=sl[0].stop - sl[0].start, img=p))
    return out

ROWS = [  # 시트 위→아래, 각 줄 왼쪽→오른쪽
    ['head', 'torso', 'collar', 'pauldron', 'pauldronF', 'coat', 'tails', 'pouchA', 'pouchB'],
    ['face_effort', 'face_shout', 'face_happy', 'face_sad', 'face_angry', 'face_grimace', 'face_focus', 'face_relaxed', 'blink_half', 'blink_closed'],
    ['armU', 'armL', 'armLF', 'armF', 'foreF'],
    ['fistF_REJ', 'handL', 'handR', 'waveSleeve', 'waveFore', 'waveHandW'],
    ['thigh_REJ', 'shin_REJ', 'boot', 'bootB'],
    ['weapon'],
]

if __name__ == '__main__':
    ps = pieces(os.path.join(HERE, 'sheets', 'partsA.png'))
    ps.sort(key=lambda p: p['y'] + p['h'] / 2)
    rows = []; 
    for p in ps:
        cy = p['y'] + p['h'] / 2
        if rows and abs(cy - rows[-1][0]) < 160: rows[-1][1].append(p)
        else: rows.append([cy, [p]])
    assert [len(r[1]) for r in rows] == [len(r) for r in ROWS], [len(r[1]) for r in rows]
    idx = {}
    for (cy, row), names in zip(rows, ROWS):
        row.sort(key=lambda p: p['x'])
        for p, nm in zip(row, names):
            Image.fromarray(p['img'], 'RGBA').save(os.path.join(HERE, 'cut', nm + '.png'))
            idx[nm] = dict(x=p['x'], y=p['y'], w=p['w'], h=p['h'])
    json.dump(idx, open(os.path.join(HERE, 'cut', '_index.json'), 'w'), indent=1)
    # 원화(시트 0) 키잉 → 정지 그림 후보
    rgba, al = key(os.path.join(HERE, 'sheets', 'sheet0.png')); im = Image.fromarray(rgba, 'RGBA')
    im.save(os.path.join(HERE, 'cut', 'sheet0_keyed.png'))
    print(len(idx), 'pieces')
