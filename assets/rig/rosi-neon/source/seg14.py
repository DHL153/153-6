# 14 네온 로시: 새 원화(1254)를 부품별로 나누기 — 7 루시아 seg7.py 와 같은 방식(대략 다각형 씨앗 + 원화 외곽선 따라 watershed) (10-21 08:40)
#  부품: gun(총·총 끝 호스 고리) · foreN/foreF(팔뚝 맨살+장갑 — 총과 한 몸) · armN/armF(어깨판+윗팔+팔꿈치 감은 띠 — 어깨에서 돎) · hose · head · pack · body · legs
#  출력: work/labels14.npy · work/labels14.png      실행: python3 -I seg14.py
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw
from skimage.segmentation import watershed
H = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(H, 'work')
A = np.array(Image.open(os.path.join(H, 'sheets/art_v1_0730.png')).convert('RGBA')); OP = A[..., 3] > 40; S = A.shape[0]
NAMES = ['gun', 'foreN', 'foreF', 'armN', 'armF', 'hose', 'head', 'pack', 'body', 'legs']; LID = {n: i + 1 for i, n in enumerate(NAMES)}
SEED = {
 'gun':  [[(470,775),(560,772),(640,800),(800,815),(950,842),(1100,872),(1178,892),(1178,975),(1130,996),(950,972),(800,942),(650,912),(560,912),(470,900),(410,878),(405,850),(455,835)]],
 'foreN': [[(388,712),(422,708),(466,748),(476,798),(440,816),(404,798),(394,760)]],
 'foreF': [[(808,708),(838,708),(896,732),(900,778),(852,786),(828,758)]],
 'armN': [[(424,588),(498,584),(506,628),(452,648),(404,662),(376,690),(372,668),(392,648),(430,632)]],
 'armF': [[(710,612),(738,614),(744,658),(770,670),(808,682),(806,698),(770,698),(728,694),(714,660)]],
 'head': [[(500,262),(640,232),(780,262),(836,350),(826,470),(758,556),(650,580),(566,572),(476,520),(448,420),(466,322)]],
 'pack': [[(142,322),(300,304),(420,312),(424,400),(416,556),(410,700),(300,712),(152,700),(132,500)]],
 'body': [[(562,590),(648,590),(698,642),(698,700),(640,712),(562,712),(548,642)]],
 'legs': [[(452,962),(488,962),(480,1078),(424,1088),(414,1050)], [(682,962),(728,962),(776,1056),(702,1072),(672,1040)], [(484,918),(548,918),(544,944),(492,948)]],
}
HOSE = [(195,568),(172,600),(155,640),(148,684),(152,725),(168,762),(196,792),(232,808),(272,816),(312,822),(345,826)]
def poly(pts):
    m = Image.new('L', (S, S), 0); ImageDraw.Draw(m).polygon([tuple(map(float, p)) for p in pts], fill=255); return np.array(m) > 0
seeds = np.zeros((S, S), np.int32)
for n, ps in SEED.items():
    for p in ps: seeds[poly(p) & OP] = LID[n]
hm = Image.new('L', (S, S), 0); ImageDraw.Draw(hm).line(HOSE, fill=255, width=26); seeds[(np.array(hm) > 0) & OP] = LID['hose']
lum = A[..., :3].astype(np.float32).mean(-1)
elev = cv2.GaussianBlur(255 - lum, (5, 5), 1.2)
lab = watershed(elev, markers=seeds, mask=OP)
np.save(os.path.join(W, 'labels14.npy'), lab.astype(np.uint8)); json.dump(NAMES, open(os.path.join(W, 'labels14.json'), 'w'))
COL = np.array([(0,0,0),(230,60,60),(255,170,40),(255,120,200),(60,180,90),(40,140,255),(160,90,220),(240,220,60),(120,200,220),(150,150,150),(110,70,40)], np.uint8)
v = (A[..., :3] * .45 + COL[lab] * .55).astype(np.uint8); v[~OP] = 236
b = cv2.morphologyEx(lab.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; v[b & OP] = 0
Image.fromarray(v).resize((940, 940), Image.LANCZOS).save(os.path.join(W, 'labels14.png'))
print({n: int((lab == LID[n]).sum()) for n in NAMES})
