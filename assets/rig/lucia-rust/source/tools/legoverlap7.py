# 7 루시아 먼 다리(legFar) ↔ 쥔 손·도끼(foreFf·weapon·weaponA·foreF) 겹침 px — 공격 .333~.867 1/60 마다 (10-21 v1.5, DHL 00:10 '다리가 손·도끼에 걸리지 않게')
#   python3 -I tools/legoverlap7.py OUTDIR TAG '{smash 덮어쓰기 JSON, 예: {"farDx":[[0,0,"io"],[0.32,0,"io"],[0.4,10],[0.58,10,"io"],[0.88,0]]}}' [VX]
#   다리만·손무기만 따로 그려(DEFX draw·drawA) 알파 > 40 겹침을 셈 — 빌드 안 함, 지금 rig.def.js 위에 ACT 만 덮어씀
import sys, os, json, subprocess
import numpy as np
from PIL import Image
S = os.path.abspath(sys.argv[1]); os.makedirs(S, exist_ok=True); tag = sys.argv[2]; act = sys.argv[3]; vx = sys.argv[4] if len(sys.argv) > 4 else '0'
T = ','.join(f'{i/60:.4f}' for i in range(20, 53))   # .333 ~ .867
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
open(f'{S}/act_{tag}.json', 'w').write(act)
for m, lst in (('L', ['legFar']), ('H', ['foreFf', 'weapon', 'weaponA', 'foreF'])):
    open(f'{S}/defx_{m}.json', 'w').write(json.dumps({'draw': lst, 'drawA': lst}))
    env = dict(os.environ, ACT=f'{S}/act_{tag}.json', DEFX=f'{S}/defx_{m}.json', VX=vx)
    subprocess.run([sys.executable, '-I', f'{R}/lucia-rust/source/tools/rig_shots.py', f'{S}/{tag}{m}', T], cwd=R, env=env, stdout=subprocess.DEVNULL, check=True)
tot = 0; mx = (0, 0)
for t in T.split(','):
    a = np.array(Image.open(f'{S}/{tag}L_{float(t):.3f}.png'))[..., 3] > 40; b = np.array(Image.open(f'{S}/{tag}H_{float(t):.3f}.png'))[..., 3] > 40
    o = int((a & b).sum()); tot += o; mx = max(mx, (o, float(t)))
    if o: print(f'  {float(t):.3f} 겹침 {o}')
print(tag, 'vx', vx, '합', tot, '최대', mx)
