# 2 러스트 둘시네 내려찍기 — 기준 그림(첨부 D): python3 -I make_attack_keys.py
# 위: ① 대기 = 원화(손 고친 그림), ⑥ 타격 = 전투 그림 자세. 아래: 8 시계(망치 방향 = 두 손 → 쇠 머리)
import os, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.join(HERE, '..')
F = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
f_t = ImageFont.truetype(F, 34); f_h = ImageFont.truetype(FB, 28); f_s = ImageFont.truetype(F, 24)
W, H = 1760, 1380
img = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(img)
d.text((30, 20), '러스트 둘시네 내려찍기 — 기준 그림 (망치 방향 = 시계 바늘, 두 손 → 쇠 머리가 가리키는 시각)', font=f_t, fill='black')

def paste(path, x, y, s=0.86):
    im = Image.open(path).convert('RGBA'); im = im.resize((int(512 * s), int(512 * s)), Image.LANCZOS)
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); img.paste(bg.convert('RGB'), (x, y))

paste(os.path.join(RIG, 'ref512.png'), 40, 80)
paste(os.path.join(RIG, '..', '..', '..', 'art', 'battle_characters', 'battle_char_0002_Idle.png'), 620, 80)
RED, ORG = (190, 0, 0), (215, 90, 0)
d.text((40, 535), '① 대기 = 원화 (망치 1시)', font=f_h, fill=RED)
for i, t in enumerate(['먼 손(화면 오른쪽·왼손) = 자루 끝 쪽', '가까운 손(화면 왼쪽·오른손) = 주먹, 몸 옆', '쇠 어깨 보호대 = 가까운 어깨 하나']):
    d.text((40, 575 + i * 32), t, font=f_s, fill=(40, 40, 40))
d.text((620, 535), '⑥ 타격 = 전투 그림 자세 (망치 4시, 쇠 머리가 앞 땅에)', font=f_h, fill=RED)
for i, t in enumerate(['주의: 전투 그림은 가까운 손이 자루 끝 쪽이에요', '→ 원화처럼 먼 손 = 자루 끝 쪽, 가까운 손 = 그 위(쇠 머리 쪽)', '   으로 그려 주세요 (대기에서 그대로 이어지게)']):
    d.text((620, 575 + i * 32), t, font=f_s, fill=ORG)
d.text((1210, 120), '시간(1초 = 1.0)', font=f_h, fill=(40, 40, 40))
for i, t in enumerate(['0.00 대기', '0.08 가까운 손이 자루를 잡음', '0.30 머리 위 뒤로 들어 올려 멈칫', '0.30~0.40 한 번에 내려침', '0.40 타격 — 0.15 멈춤', '0.55~0.72 버팀', '0.72~0.95 어깨로 들어 올림', '0.85 가까운 손 놓음']):
    d.text((1210, 160 + i * 34), t, font=f_s, fill=(40, 40, 40))

KEYS = [('① 대기', '1시', 1, ''), ('② 잡기', '12시', 12, ''), ('③ 예비', '11시', 11, '머리 위 뒤'), ('④ 휘두름 시작', '12시 반', 12.5, ''),
        ('⑤ 휘두름', '2시', 2, '가장 빠름'), ('⑥ 타격', '4시', 4, '전투 그림'), ('⑦ 버팀', '4시', 4, '더 가라앉음'), ('⑧ 들어 올림', '2시 → 1시', 1.5, '가까운 손 놓음')]
R = 82; y0 = 820
for k, (nm, tx, hr, sub) in enumerate(KEYS):
    cx = 110 + k * 212; cy = y0 + 110
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(150, 150, 150), width=3)
    for m in range(12):
        a = math.radians(m * 30); d.line((cx + (R - 10) * math.sin(a), cy - (R - 10) * math.cos(a), cx + R * math.sin(a), cy - R * math.cos(a)), fill=(150, 150, 150), width=2)
    a = math.radians(hr * 30); ex, ey = cx + (R - 14) * math.sin(a), cy - (R - 14) * math.cos(a)
    d.line((cx, cy, ex, ey), fill=(30, 80, 210), width=7)
    # 쇠 머리 = 끝에서 바늘과 직각인 막대
    px, py = math.cos(a), math.sin(a)
    d.line((ex - px * 22, ey - py * 22, ex + px * 22, ey + py * 22), fill=(90, 90, 100), width=14)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(20, 20, 20))
    d.text((cx - R, cy + R + 14), nm, font=f_h, fill=RED)
    d.text((cx - R, cy + R + 52), '망치 ' + tx, font=f_s, fill=(40, 40, 40))
    if sub: d.text((cx - R, cy + R + 84), sub, font=f_s, fill=(110, 110, 110))
notes = ['② 가까운 손이 올라와 먼 손 위(쇠 머리 쪽)를 잡음 · ③ 몸을 뒤로 젖히고 무릎을 굽혀 힘을 모음, 쇠 머리는 머리·포니테일 위 뒤',
         '④ 앞발을 크게 내딛기 시작 · ⑥ 넓은 런지, 쇠 머리 아래가 앞 땅에 닿음 · ⑦ 몸이 조금 더 가라앉고 포니테일·천자락이 앞으로 넘어옴',
         '파란 선 = 자루(두 손 → 쇠 머리), 회색 막대 = 쇠 머리, 검은 점 = 두 손. 오른쪽이 앞(캐릭터가 보는 쪽). 망치는 늘 몸 앞·위 반원(11시~4시)만 지나요.']
for i, t in enumerate(notes):
    d.text((30, H - 130 + i * 38), t, font=f_s, fill=(40, 40, 40))
out = os.path.join(HERE, 'ref_D_attack_keys.png'); img.save(out); print(out)
