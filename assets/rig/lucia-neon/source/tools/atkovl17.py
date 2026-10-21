# 17 네온 루시아 공격 중 다리 ↔ 쥔 손·도끼 겹침 px (7 러스트 legoverlap7 와 같은 셈, 실수 57) — 달리다/서서 공격 .333~.867 1/60
#   python3 -I tools/atkovl17.py OUTDIR [run|stand] ['{"smash":{...}}']  → 시각별 겹침 px · 합 · 최대
import sys, os, json, subprocess
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.abspath(sys.argv[1]); os.makedirs(D, exist_ok=True)
MODE = sys.argv[2] if len(sys.argv) > 2 else 'run'; OV = sys.argv[3] if len(sys.argv) > 3 else '{}'
T = ','.join(f'{i / 60:.4f}' for i in range(20, 53))
LEGS = os.environ.get('LEGS', 'legFar,legNear').split(',')
for tag, lst in (('L', LEGS), ('H', ['foreFf', 'weapon', 'weaponA', 'foreF', 'fistF'])):
    open(f'{D}/defx_{tag}.json', 'w').write(json.dumps({'draw': lst, 'drawA': lst}))
    env = dict(os.environ, TS=T, SC='1', DEFX=f'{D}/defx_{tag}.json', RAW=D, TAG=tag + MODE)
    r_ = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'atkrun17.py'), f'{D}/_g{tag}.png', MODE, OV], env=env, capture_output=True, text=True, check=True)
    if tag == 'L':
        import re
        rr = [(float(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))) for m in re.finditer(r't ([\d.]+) .*?부츠\s+([+-]?\d+)\s+([+-]?\d+)° · 굽힘\s+(\d+)\s+(\d+)', r_.stdout)]
        fr = [x[2] for x in rr]; fb = [x[4] for x in rr]
        print(f'  먼 다리 정강이↔부츠 {min(fr)}~{max(fr)}° (대기 원화 −6) · 먼 무릎 굽힘 {min(fb)}~{max(fb)}° (대기 47)')
tot, mx = 0, (0, 0)
for t in T.split(','):
    f = lambda tag: np.array(Image.open(f'{D}/{tag}{MODE}_{float(t):.3f}.png'))[..., 3] > 40
    try: o = int((f('L') & f('H')).sum())
    except FileNotFoundError: continue
    tot += o; mx = max(mx, (o, float(t)))
    if o: print(f'  {float(t):.3f} 겹침 {o}')
print(MODE, '합', tot, '최대', mx)
