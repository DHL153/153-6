"""5 바실 — 공격 키 시각 그림 한 줄: python3 -I keyshots5.py 출력.png [t,t,...]"""
import sys, os, subprocess, json
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); R = json.load(open(os.path.join(H, '..', '..', 'rig.json'))); dur = R['actions']['smash']['dur']
ts = [float(x) for x in (sys.argv[2].split(',') if len(sys.argv) > 2 else '0,0.1,0.2,0.28,0.38,0.45,0.6,0.8'.split(','))]
ims = []
for t in ts:
    p = f'/tmp/_ks_{t}.png'; subprocess.run(['python3', os.path.join(H, 'shot.py'), f'mode=idle&atk=smash&apre={round(t * dur * 60)}&k=0.45&pre=60&oy=120', p], check=True, capture_output=True); ims.append(Image.open(p).convert('RGB'))
W = Image.new('RGB', (sum(i.width for i in ims), ims[0].height), (255, 255, 255)); x = 0
for i in ims: W.paste(i, (x, 0)); x += i.width
W.save(sys.argv[1]); print('saved', sys.argv[1], ts)
