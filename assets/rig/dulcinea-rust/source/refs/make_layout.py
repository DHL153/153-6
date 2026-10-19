# 2 러스트 둘시네 — 조각 시트 배치도(첨부 B) 만들기: python3 -I make_layout.py
# 3072×3072, 6×6 칸(512), 자홍 배경. 1번 칸 = 원화 그대로(크기 기준), 나머지 = 회색 모양(원화 크기 1배 기준 대략) + 번호·이름
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'ref512_received.png')
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
f_num = ImageFont.truetype(FONT, 46); f_lab = ImageFont.truetype(FONT, 30)
C = 512; W = C * 6
img = Image.new('RGBA', (W, W), (255, 0, 255, 255)); d = ImageDraw.Draw(img)
G = (150, 150, 158, 255); K = (40, 40, 44, 255)

def cell(n):  # 1부터, 왼→오, 위→아래
    i = n - 1; return (i % 6) * C, (i // 6) * C

def rr(n, w, h, dx=0, dy=0, r=18):   # 둥근 사각형 (가운데 기준)
    x, y = cell(n); cx, cy = x + C // 2 + dx, y + C // 2 + dy
    d.rounded_rectangle((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), r, fill=G, outline=K, width=4)

def poly(n, pts):
    x, y = cell(n); d.polygon([(x + C // 2 + a, y + C // 2 + b) for a, b in pts], fill=G, outline=K, width=4)

def ell(n, w, h, dx=0, dy=0):
    x, y = cell(n); cx, cy = x + C // 2 + dx, y + C // 2 + dy
    d.ellipse((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), fill=G, outline=K, width=4)

LAB = {}
# 1줄: 크기 기준 · 머리 · 포니테일 · 리본 꼬리 2 · 망치
art = Image.open(SRC).convert('RGBA'); img.alpha_composite(art, cell(1)); LAB[1] = '전체 자세(원화 그대로)'
ell(2, 150, 150); LAB[2] = '머리(무표정·포니테일 없이)'
ell(3, 250, 250, dy=-10); LAB[3] = '포니테일 전체'
rr(4, 40, 120); LAB[4] = '리본 꼬리 긴 것'
rr(5, 40, 80); LAB[5] = '리본 꼬리 짧은 것'
rr(6, 190, 110, dy=-140); rr(6, 34, 290, dy=60, r=10); LAB[6] = '망치 단독(자루 세로)'
# 2줄: 몸통
rr(7, 130, 85); LAB[7] = '상체(팔 없이)'
rr(8, 60, 45); LAB[8] = '가까운 어깨 쇠 보호대'
rr(9, 125, 60); LAB[9] = '골반(허리띠+반바지)'
poly(10, [(-14, -35), (14, -35), (6, 35), (-8, 25)]); LAB[10] = '가운데 앞 천자락'
poly(11, [(-20, -30), (20, -30), (10, 30), (-16, 22)]); LAB[11] = '가까운 엉덩이 천자락'
rr(12, 30, 60, r=14); LAB[12] = '먼 윗팔(곧게)'
# 3줄: 팔·손
rr(13, 30, 60, r=14); LAB[13] = '가까운 윗팔(곧게)'
rr(14, 30, 55, r=14); LAB[14] = '가까운 팔뚝+붕대(곧게)'
rr(15, 45, 50); LAB[15] = '가까운 주먹(원화 방향)'
rr(16, 50, 45); LAB[16] = '가까운 주먹(옆, 엄지 위)'
rr(17, 30, 55, r=14); LAB[17] = '먼 팔뚝+붕대(곧게)'
rr(18, 16, 110, r=6); rr(18, 46, 50); LAB[18] = '먼 손(자루 쥔 주먹)'
# 4줄: 다리
rr(19, 40, 75, r=14); LAB[19] = '가까운 허벅지(곧게)'
rr(20, 40, 75, r=14); LAB[20] = '먼 허벅지(곧게)'
poly(21, [(-40, -65), (30, -65), (30, 30), (70, 40), (70, 65), (-40, 65)]); LAB[21] = '가까운 부츠(옆·앞코 오른쪽)'
poly(22, [(-40, -65), (30, -65), (30, 30), (70, 40), (70, 65), (-40, 65)]); LAB[22] = '먼 부츠(옆·앞코 오른쪽)'
rr(23, 70, 45); LAB[23] = '가까운 무릎 쇠 덮개'
rr(24, 70, 45); LAB[24] = '먼 무릎 쇠 덮개'
# 5줄: 표정 6
for k, nm in enumerate(['기본', '웃음', '화남', '집중', '외침', '힘줌']):
    ell(25 + k, 150, 150); LAB[25 + k] = f'표정 {nm}'
# 6줄: 깜빡임 2
ell(31, 150, 150); LAB[31] = '눈 반쯤 감음'
ell(32, 150, 150); LAB[32] = '눈 다 감음'

for n in range(1, 37):
    x, y = cell(n)
    d.rectangle((x + 2, y + 2, x + C - 3, y + C - 3), outline=(255, 160, 255, 255), width=2)
    if n in LAB:
        d.text((x + 14, y + 6), str(n), font=f_num, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(60, 0, 60, 255))
        if n == 1: d.text((x + 70, y + 16), LAB[n], font=f_lab, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(60, 0, 60, 255))
        else: d.text((x + C // 2, y + C - 14), LAB[n], font=f_lab, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(60, 0, 60, 255), anchor='md')
out = os.path.join(HERE, 'ref_B_parts_layout_32.png'); img.convert('RGB').save(out); print(out)
