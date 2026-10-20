# 7 루시아 조각 시트 19칸(자루 따라 쥔 먼 손) 기준 그림: ① 손 디자인 = 7 새 원화 먼 손 · ② 쥐는 모양·팔뚝 방향 = 2 러스트 둘시네 시트 손(gFh)
#   python3 -I tools/make_gfh_guide7.py → refs/ref_gFh_guide7.png
import os, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..'); RIG = os.path.join(SRC, '..', '..')
FB = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 24); FS = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 17)
W, H = 1000, 520; out = Image.new('RGB', (W, H), (255, 255, 255)); d = ImageDraw.Draw(out)
# ① 7 새 원화 먼 손(도끼 자루를 세로로 쥠)
art = Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'); bg = Image.new('RGBA', art.size, (255, 255, 255, 255)); bg.alpha_composite(art)
c = bg.crop((372, 248, 472, 348)).convert('RGB').resize((330, 330), Image.LANCZOS); out.paste(c, (60, 110))
d.text((20, 14), '① 손 디자인 = 7 루시아 먼 손', font=FB, fill=(20, 20, 20))
d.text((20, 48), '맨손 + 손목 갈색 띠 (이 그림은 자루를 세로로 쥔 모양 — 디자인만)', font=FS, fill=(90, 90, 90))
# ② 2 러스트 둘시네 시트 '자루 따라 쥔 손'(gFh): 자루 가로, 팔뚝 왼쪽 위 약 30°
g = Image.open(os.path.join(RIG, 'dulcinea-rust', 'parts', 'gFh.png')).convert('RGBA'); k = 2.3
g = g.resize((int(g.width * k), int(g.height * k)), Image.LANCZOS); ox, oy = 600, 130; out.paste(g, (ox, oy), g)
gx, gy = ox + 86 * k, oy + 68 * k
d.line([(ox - 40, gy), (ox + g.width + 60, gy)], fill=(20, 110, 255), width=4)
fx, fy = -0.8346, -0.5508; L = 210; d.line([(gx, gy), (gx + fx * L, gy + fy * L)], fill=(220, 0, 0), width=7)
d.text((gx + fx * L - 70, gy + fy * L - 32), '팔뚝 방향(자루와 약 30°)', font=FS, fill=(220, 0, 0))
d.text((ox + 90, oy + g.height + 14), '자루 → 도끼 날 쪽 (오른쪽)', font=FS, fill=(20, 110, 255))
d.text((520, 14), '② 쥐는 모양·팔뚝 방향 = 이 그림', font=FB, fill=(20, 20, 20))
d.text((520, 48), '(러스트 둘시네 시트 손 — 디자인은 ①)', font=FS, fill=(90, 90, 90))
d.line([(500, 10), (500, H - 10)], fill=(200, 200, 200), width=2)
out.save(os.path.join(SRC, 'refs', 'ref_gFh_guide7.png')); print('ok', math.degrees(math.atan2(-fy, -fx)))
