# 7 루시아: build_lucia7.py 를 돌린 뒤 원화 오린 조각(ART)을 대기 그리는 순서로 겹쳐 원화와 비교 → review/v1_idle_artcomp.png(원화 | 겹침 | 차이) + review/v1_pieces.png
import os; _bp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build_lucia7.py'); g = {'__file__': _bp, '__name__': 'idlecomp'}
try: exec(compile(open(_bp).read(), _bp, 'exec'), g)
except SystemExit: pass
globals().update(g); os.chdir(os.path.dirname(_bp))
ORD = ['torso', 'upF', 'foreF', 'axe', 'fistF', 'thighF', 'bootF', 'thighN', 'bootN', 'hips', 'head', 'pauldron', 'shield', 'fistN']   # 리그 대기 순서(v1)
can = Image.new('RGBA', (512, 512), (255, 255, 255, 255))
for n in ORD: can.alpha_composite(Image.fromarray(ART[n]))
ref = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); ref.alpha_composite(Image.fromarray(RA))
d = np.abs(np.array(can).astype(int)[..., :3] - np.array(ref).astype(int)[..., :3]).sum(-1)
print('idle 차이 px(>40)', int((d > 40).sum()), 'max', int(d.max()))
ys, xs = np.nonzero(d > 40); print('diff bbox', (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None)
B = Image.new('RGB', (1536, 512), 'white'); B.paste(ref.convert('RGB'), (0, 0)); B.paste(can.convert('RGB'), (512, 0))
dm = Image.fromarray(np.clip(d * 2, 0, 255).astype(np.uint8)); B.paste(dm.convert('RGB'), (1024, 0)); B.save('review/v1_idle_artcomp.png')
# pieces board
S = Image.new('RGB', (1536, 1024), (90, 100, 120)); x = y = 0; rowh = 0
for n in ORD:
    a = Image.open(f'work/{n}Art.png'); a2 = a.resize((a.width * 2, a.height * 2), Image.NEAREST)
    if x + a2.width > 1536: x = 0; y += rowh + 10; rowh = 0
    S.paste(a2, (x, y), a2); ImageDraw.Draw(S).text((x + 2, y + 2), n, fill=(255, 255, 0)); x += a2.width + 10; rowh = max(rowh, a2.height)
S.save('review/v1_pieces.png')
