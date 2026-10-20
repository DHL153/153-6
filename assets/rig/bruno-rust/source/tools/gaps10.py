"""10 러스트 브루노 — 조각 사이 틈(배경이 비치는 실금) 세기: 같은 장면을 자홍·초록 배경으로 두 번 찍어 다른 픽셀 = 투명,
   그중 실루엣을 닫은(9×9) 안쪽 = 틈. 대기(숨쉬기 한 주기)·달리기·서서 공격·달리다 공격.
실행: python3 gaps10.py [출력 접두어]   → 장면별 틈 px 표 + 접두어_gaps.png(틈 빨강, 가장 많은 장면 4장)
"""
import sys, subprocess, os
import numpy as np, cv2
from PIL import Image
SP = sys.argv[1] if len(sys.argv) > 1 else '/tmp/gaps10'
H = os.path.dirname(os.path.abspath(__file__))
SETS = {'대기': 'mode=idle&n=12&step=10', '달리기': 'mode=run&n=12&step=3', '서서공격': 'mode=idle&atk=smash&n=20&step=3', '달리다공격': 'mode=run&atk=smash&pre=120&n=20&step=3'}
res = {}; worst = []
for nm, q in SETS.items():
    ims = []
    for bg in ('ff00ff', '00ff00'):
        out = f'{SP}_{nm}_{bg}.png'; subprocess.run(['python3', os.path.join(H, 'shot.py'), q + f'&k=0.5&bgc={bg}', out], check=True, capture_output=True); ims.append(np.array(Image.open(out).convert('RGB')).astype(int))
    tr = np.abs(ims[0] - ims[1]).max(-1) > 60; op = ~tr
    n = tr.shape[1] // 512; row = []
    for i in range(n):
        o = op[:, i * 512:(i + 1) * 512]; t = tr[:, i * 512:(i + 1) * 512]
        cl = cv2.morphologyEx(o.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0
        g = t & cl; row.append(int(g.sum())); worst.append((int(g.sum()), nm, i, g, ims[0][:, i * 512:(i + 1) * 512]))
    res[nm] = row; print(nm, '틈 px', row)
worst.sort(key=lambda x: -x[0]); tiles = []
for s, nm, i, g, im in worst[:4]:
    v = im.copy(); v[g] = (255, 0, 0); tiles.append(Image.fromarray(v.astype(np.uint8)).crop((40, 60, 460, 500)))
W = Image.new('RGB', (420 * len(tiles), 440), (255, 255, 255))
for k, t in enumerate(tiles): W.paste(t, (k * 420, 0))
W.save(f'{SP}_gaps.png'); print('가장 많은 장면', [(s, nm, i) for s, nm, i, _, _ in worst[:4]])
