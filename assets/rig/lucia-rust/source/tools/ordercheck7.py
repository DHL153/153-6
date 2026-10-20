# 7 루시아: 대기 그리는 순서 후보별로 원화 조각(ART)을 겹쳐 원화와 차이 px 비교 (10-20 22:0x, 다리를 옷 뒤로 — DHL 21:44)
#   python3 -I tools/ordercheck7.py OUT.png "a,b,c ..." ["..."]
#   주의: 빌드를 idlecomp 로 돌리면 ../parts 를 지우고 멈춤 → 끝에 빌드를 다시 돌려 parts 를 되살림(10-20 22:0x 실수: 이걸 빼먹어 리그 그림이 404)
import os, sys; _bp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build_lucia7.py'); g = {'__file__': _bp, '__name__': 'idlecomp'}
try: exec(compile(open(_bp).read(), _bp, 'exec'), g)
except SystemExit: pass
np, Image, ART, RA = g['np'], g['Image'], g['ART'], g['RA']
out = sys.argv[1]; rows = []
ref = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); ref.alpha_composite(Image.fromarray(RA))
for o in sys.argv[2:]:
    can = Image.new('RGBA', (512, 512), (255, 255, 255, 255))
    for n in o.split(','): can.alpha_composite(Image.fromarray(ART[n.strip()]))
    d = np.abs(np.array(can).astype(int)[..., :3] - np.array(ref).astype(int)[..., :3]).sum(-1)
    print(f'{int((d > 40).sum()):6d} px  {o}'); rows.append((can, d))
B = Image.new('RGB', (1024, 512 * len(rows)), 'white')
for i, (c, d) in enumerate(rows): B.paste(c.convert('RGB'), (0, 512 * i)); B.paste(Image.fromarray(np.clip(d * 2, 0, 255).astype(np.uint8)).convert('RGB'), (512, 512 * i))
B.save(out)
import subprocess, sys as _s; subprocess.run([_s.executable, '-I', _bp], check=True, stdout=subprocess.DEVNULL)   # parts 되살림
