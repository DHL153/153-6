"""19 네온 팔로메 — 시트 요청 가이드 그림 3장(새 원화 합격 뒤 seg19.py 를 돌린 다음) — 2026-10-20 18:40 준비
  W19 = 프롬프트 2 첨부 2: 가까운 팔(윗팔 소매·토시·주먹)만 빨갛게 — '그 부품만 지운 원화'(29 v2.0 ref_W 와 같은 꼴)
  X19 = 프롬프트 3 첨부 2: 칼 전체 + 먼 주먹·먼 토시만 빨갛게 — 칼을 들면 드러나는 먼 어깨·어깨갑·수염 오른쪽·몸(29 는 시트 3 으로 받았던 곳)
  B19 = 프롬프트 1 첨부 2: 팔 길이 선(빨강 = 윗팔 · 초록 = 팔뚝, 숫자 = 시트 칸 번호) — 29 시트 1 의 먼 윗팔이 원화 팔의 0.6배로 와서 다시 받은 것(ref_B) 처음부터 막음
입력: 원화(기본 source/ref512.png) · work/labels.npy + work/label_names.json(seg19) · joints19.json
실행: python3 -I guides19.py [원화.png] [라벨.npy] [이름.json] [출력폴더]   (기본 출력 = source/refs/)
"""
import json, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(os.path.join(HERE, '..'))
arg = lambda i, d: sys.argv[i] if len(sys.argv) > i else d
ART = arg(1, os.path.join(SRC, 'ref512.png')); LAB = arg(2, os.path.join(SRC, 'work', 'labels.npy')); NMS = arg(3, os.path.join(SRC, 'work', 'label_names.json')); OUT = arg(4, os.path.join(SRC, 'refs'))
for p in (ART, LAB, NMS):
    if not os.path.exists(p): sys.exit(f'없음: {p} — 새 원화를 넣고 seg19.py 를 먼저 돌리세요')
os.makedirs(OUT, exist_ok=True)
RA = np.array(Image.open(ART).convert('RGBA').resize((512, 512), Image.LANCZOS)); lab = np.load(LAB); NAMES = json.load(open(NMS)); LID = {n: i + 1 for i, n in enumerate(NAMES)}
J = json.load(open(os.path.join(SRC, 'joints19.json')))
FN = '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'; f = ImageFont.truetype(FN, 30)
BH = 112   # 글씨 띠(그림 위) — 그림 칸은 1024 그대로라 원화 2배 자리와 1:1
def white(a):   # 흰 배경 1024
    al = a[..., 3:4] / 255.0; return Image.fromarray((a[..., :3] * al + 255 * (1 - al)).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
def banded(img, l1, l2, c1):   # 위에 글씨 띠를 붙임(칼끝이 그림 위 끝까지 와서 글씨가 칼을 덮었음)
    W = Image.new('RGB', (1024, 1024 + BH), (255, 255, 255)); W.paste(img, (0, BH)); d = ImageDraw.Draw(W)
    d.text((20, 14), l1, fill=c1, font=f); d.text((20, 56), l2, fill=(30, 30, 30), font=f); d.line([(0, BH - 2), (1024, BH - 2)], fill=(200, 200, 200), width=2); return W
def red_guide(mask, l1, l2, name):
    m = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0   # 외곽선까지 덮음
    m2 = np.array(Image.fromarray((m * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR)) > 127
    im = np.array(white(RA)).astype(float); im[m2] = im[m2] * .45 + np.array([235, 40, 40]) * .55
    edge = m2 & ~(cv2.erode(m2.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0); im[edge] = (200, 0, 0)
    banded(Image.fromarray(im.astype(np.uint8)), l1, l2, (200, 0, 0)).save(os.path.join(OUT, name)); print('저장', name, '빨간 px@512', int(mask.sum()))
has = lambda *ns: np.logical_or.reduce([lab == LID[n] for n in ns if n in LID])
red_guide(has('upperN', 'foreN'), '빨간 곳(가까운 팔: 윗팔 소매·토시·주먹)만 지우고 그 뒤를 그려 주세요',
          '나머지(어깨갑·배 판·허리띠·칼·얼굴·수염)는 1번과 픽셀 그대로', 'ref_W19_near_arm_remove.png')
red_guide(has('sword', 'handF', 'foreF', 'upperF'), '빨간 곳(칼 전체·먼 주먹·먼 토시)만 지우고 그 뒤를 그려 주세요',
          '나머지는 1번과 픽셀 그대로 · 칼이 있던 몸 밖은 투명', 'ref_X19_sword_farhand_remove.png')
# B19: 시트 칸 15·17·18 팔 길이 선(가까운 팔뚝·주먹은 원화 조각을 쓰므로 선 없음)
img = white(RA); d = ImageDraw.Draw(img); P = lambda p: (2 * p[0], 2 * p[1])
na, fa = J['nearArm'], J['farArm']
for a, b, c in [(na['SH'], na['EL'], (230, 30, 30)), (fa['SH'], fa['EL'], (230, 30, 30)), (fa['EL'], fa['WR'], (20, 160, 40))]:
    d.line([P(a), P(b)], fill=c, width=6)
for p in [na['SH'], na['EL'], fa['SH'], fa['EL'], fa['WR']]:
    x, y = P(p); d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(0, 0, 0), width=3)
fb = ImageFont.truetype(FN, 44)
for txt, p, off in [('15', na['SH'], (-70, -60)), ('17', fa['SH'], (-70, -10)), ('18', fa['WR'], (30, -20))]:
    x, y = P(p); d.text((x + off[0], y + off[1]), txt, fill=(230, 30, 30), font=fb)
banded(img, '빨강 = 윗팔(어깨→팔꿈치) · 초록 = 먼 팔뚝(팔꿈치→손목) · 숫자 = 칸 번호',
       '조각 길이 = 선 길이 + 양 끝 둥근 마디, 굵기 = 그림 속 팔 그대로', (30, 30, 30)).save(os.path.join(OUT, 'ref_B19_arm_guide.png'))
print('저장 ref_B19_arm_guide.png',
      '가까운 윗팔', round(float(np.hypot(*np.subtract(na['SH'], na['EL']))), 1), '먼 윗팔', round(float(np.hypot(*np.subtract(fa['SH'], fa['EL']))), 1),
      '먼 팔뚝', round(float(np.hypot(*np.subtract(fa['EL'], fa['WR']))), 1), '(원화 px)')
