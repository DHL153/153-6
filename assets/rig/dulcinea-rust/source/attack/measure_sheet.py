"""4번 시트 내려찍기 8칸(atk_frames/a1~a8) 측정: 원화 조각(머리·망치·몸통·골반)을 칸마다 SIFT 로 찾아 배율·각도·자리 → attack/sheet_meas.json
좌표 = 칸 그림 px. 원화→칸 변환 M 의 배율 = 칸 그림 크기 / 원화 크기."""
import json, os, sys, numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(SRC, 'tools'))
from place import sift_M
img = lambda p: np.array(Image.open(p).convert('RGBA'))
RA = img(os.path.join(SRC, 'ref512.png')); L = np.load(os.path.join(SRC, 'work', 'labels.npy'))
PB = ['armL', 'pauldron', 'armU', 'fistF', 'hammer', 'head', 'torso', 'foreF', 'belt', 'flapC', 'flapN', 'hips', 'thighN', 'bootN', 'thighF', 'bootF', 'pony']
def piece(names):
    m = np.isin(L, [PB.index(n) for n in names]); a = RA.copy(); a[..., 3] = np.where(m, RA[..., 3], 0); return a
P = {'head': piece(['head']), 'hammer': piece(['hammer']), 'torso': piece(['torso']), 'belt': piece(['belt']), 'bootN': piece(['bootN']), 'bootF': piece(['bootF']), 'pony': piece(['pony'])}
out = {}
for i in range(1, 9):
    F = img(os.path.join(SRC, 'atk_frames', f'a{i}.png')); r = {'size': [F.shape[1], F.shape[0]]}
    ys = np.nonzero((F[..., 3] > 128).any(1))[0]; r['ground'] = int(ys.max())
    for n, a in P.items():
        try: M, inl, good = sift_M(a, F)
        except Exception as e: M, inl, good = None, 0, 0
        if M is None or inl < 6: r[n] = None; continue
        s = float(np.hypot(M[0, 0], M[1, 0])); rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
        r[n] = dict(s=round(s, 3), rot=round(rot, 1), M=np.round(M, 4).tolist(), inl=inl)
    out[f'a{i}'] = r; print(i, r['size'], 'ground', r['ground'], {n: (v['s'], v['rot'], v['inl']) if v else None for n, v in r.items() if n in P})
json.dump(out, open(os.path.join(HERE, 'sheet_meas.json'), 'w'), indent=1)
