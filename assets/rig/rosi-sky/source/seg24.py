# 24 스카이 로시: 새 원화(1254)를 부품별로 나누기 — 7 루시아 seg7.py 와 같은 방식(대략 다각형 씨앗 + 원화 외곽선 따라 watershed) (10-21 08:40)
#  부품: gun(총·총 끝 호스 고리) · foreN/foreF(팔뚝 맨살+장갑 — 총과 한 몸) · armN/armF(어깨판+윗팔+팔꿈치 감은 띠 — 어깨에서 돎) · hose · head · pack · body · legs
#  출력: work/labels24.npy · work/labels24.png      실행: python3 -I seg24.py
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw
from skimage.segmentation import watershed
H = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(H, 'work')
A = np.array(Image.open(os.path.join(H, 'sheets/art_v1_0958.png')).convert('RGBA')); OP = A[..., 3] > 40; S = A.shape[0]
NAMES = ['gun', 'foreN', 'foreF', 'armN', 'armF', 'hose', 'head', 'pack', 'body', 'legs']; LID = {n: i + 1 for i, n in enumerate(NAMES)}   # hose = 탄띠
K = 1254 / 512.0
P5 = lambda pts: [(x * K, y * K) for x, y in pts]   # 512 좌표 → 1254
# 팔 = 손으로 따라 그린 다각형(512, 원화 외곽선 ±2px) — 씨앗은 안으로 줄이고 결과는 다각형 +4px 안으로만(옆 부품을 먹지 않게)
ARM = {'armN': [(150,252),(170,243),(192,241),(201,249),(201,266),(199,290),(197,306),(190,311),(170,315),(150,316),(142,306),(140,292),(142,276),(147,262)],
       'foreN': [(150,292),(160,286),(176,286),(188,294),(194,306),(206,311),(218,321),(219,340),(206,349),(190,347),(178,331),(166,317),(155,309)],   # 소매 입구에서 보이는 맨살부터
       'armF': [(276,250),(292,247),(302,255),(312,267),(326,275),(329,292),(321,306),(301,307),(290,297),(282,283),(276,266)],
       'foreF': [(293,281),(306,279),(322,283),(337,288),(352,297),(362,310),(363,331),(346,335),(334,319),(322,305),(300,302),(292,294)]}   # 소매 입구에서 보이는 맨살부터
SEED = {
 'gun':  [P5([(140,345),(175,338),(206,330),(208,304),(290,304),(300,318),(330,330),(360,330),(410,342),(450,354),(452,406),(430,410),(370,398),(320,392),(260,388),(205,378),(165,388),(136,382),(128,360)])],
 'head': [P5([(156,150),(178,98),(232,84),(290,92),(316,130),(318,176),(304,212),(284,230),(252,234),(216,234),(192,222),(162,212),(152,186)])],
 'pack': [P5([(38,178),(56,152),(100,138),(106,128),(164,128),(168,150),(166,240),(150,246),(146,262),(148,308),(62,310),(42,290),(38,232)])],
 'body': [P5([(212,244),(262,240),(278,250),(280,292),(262,297),(214,297),(208,280)]), P5([(150,246),(162,244),(150,262)])],   # 아래 끝 y 297 — 그 아래 남색 총 덮개(x 205~290, y 300~325)는 총(10-21 12:45)
 'legs': [P5([(160,412),(190,412),(192,452),(160,456)]), P5([(272,412),(300,412),(310,446),(272,448)])],
}
HOSE = P5([(62,230),(58,242),(55,254),(53,266),(53,278),(55,290),(58,302),(63,313),(69,323),(77,332),(86,340),(96,347),(107,352),(119,356),(132,358),(145,359),(151,360)])   # 탄띠 가운데 선(512) — 총 왼쪽 끝까지 = 탄띠
def poly(pts):
    m = Image.new('L', (S, S), 0); ImageDraw.Draw(m).polygon([tuple(map(float, p)) for p in pts], fill=255); return np.array(m) > 0
seeds = np.zeros((S, S), np.int32)
for n, ps in SEED.items():
    for p in ps: seeds[poly(p) & OP] = LID[n]
hm = Image.new('L', (S, S), 0); ImageDraw.Draw(hm).line(HOSE, fill=255, width=60); seeds[(np.array(hm) > 0) & OP] = LID['hose']
def erode(m, r): return cv2.erode(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
def dilate(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
ARMM = {n: poly(P5(p)) for n, p in ARM.items()}; anyArm = np.logical_or.reduce(list(ARMM.values()))
seeds[dilate(anyArm, 14) & ~np.logical_or.reduce([erode(m, 8) for m in ARMM.values()])] = 0   # 팔 둘레는 비움(경계는 외곽선이 정함)
for n, m in ARMM.items():
    sd = erode(m, 8)
    if n.startswith('arm'): sd &= ~dilate(ARMM['fore' + n[3:]], 3)   # 소매 씨앗은 팔뚝(맨살) 다각형과 겹치지 않게 — 소매 안에 맨살이 남아 '어두운 얼룩'이 되던 것(10-21 12:40)
    seeds[sd & OP] = LID[n]
lum = A[..., :3].astype(np.float32).mean(-1)
elev = cv2.GaussianBlur(255 - lum, (5, 5), 1.2)
lab = watershed(elev, markers=seeds, mask=OP)
for n, m in ARMM.items():   # 팔 라벨은 다각형 +10px 안으로만 — 밖으로 샌 것: 팔뚝(총 묶음)에서 샌 것 = 총(손잡이 등), 소매에서 샌 것 = 몸 (10-21 12:30 DHL 12:19 '무기가 짤려있어요' — 팔뚝 둘레 손잡이가 몸으로 가서 총에서 빠졌음)
    out_ = (lab == LID[n]) & ~dilate(m, 10); lab[out_] = LID['gun'] if n.startswith('fore') else LID['body']
np.save(os.path.join(W, 'labels24.npy'), lab.astype(np.uint8)); json.dump(NAMES, open(os.path.join(W, 'labels24.json'), 'w'))
COL = np.array([(0,0,0),(230,60,60),(255,170,40),(255,120,200),(60,180,90),(40,140,255),(160,90,220),(240,220,60),(120,200,220),(150,150,150),(110,70,40)], np.uint8)
v = (A[..., :3] * .45 + COL[lab] * .55).astype(np.uint8); v[~OP] = 236
b = cv2.morphologyEx(lab.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; v[b & OP] = 0
Image.fromarray(v).resize((940, 940), Image.LANCZOS).save(os.path.join(W, 'labels24.png'))
print({n: int((lab == LID[n]).sum()) for n in NAMES})
