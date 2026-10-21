# 27 스카이 루시아 지우기 가이드: 격자에서 읽은 다각형 ∩ 불투명 → 빨강
# N = 방패 + 가까운 주먹 · F = 먼 팔(어깨갑~주먹) + 도끼
import numpy as np, cv2, sys, json
from PIL import Image, ImageDraw, ImageFont
ref=np.array(Image.open('ref512.png').convert('RGBA')); A=ref[...,3]>8
SHIELD=[(0,40),(140,40),(140,140),(168,166),(186,191),(199,203),(212,206),(232,212),(240,216),(240,287),
        (231,292),(227,310),(225,321),(234,322),(236,358),(212,364),(200,372),(193,380),(186,400),(179,418),(177,440),(170,512),(0,512)]
FAR=[(337,250),(344,240),(396,246),(412,262),(470,262),(470,365),(420,365),(402,352),(372,352),(350,342),(340,312),(334,286)]
AXE=[(362,30),(372,30),(512,30),(512,262),(470,262),(470,365),(430,365),(410,262),(395,232),(352,205),(342,165),(362,128),(371,104)]
def mask(polys):
    m=Image.new('L',(512,512),0); d=ImageDraw.Draw(m)
    for p in polys: d.polygon(p,fill=255)
    return (np.array(m)>0)&A
FN='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; f=ImageFont.truetype(FN,30,index=1); fb=ImageFont.truetype(FN,40,index=1); BH=112
def white(a):
    al=a[...,3:4]/255.0; return Image.fromarray((a[...,:3]*al+255*(1-al)).astype(np.uint8)).resize((1024,1024),Image.LANCZOS)
def banded(img,l1,l2,c1):
    W=Image.new('RGB',(1024,1024+BH),(255,255,255)); W.paste(img,(0,BH)); d=ImageDraw.Draw(W)
    d.text((20,14),l1,fill=c1,font=f); d.text((20,56),l2,fill=(30,30,30),font=f); d.line([(0,BH-2),(1024,BH-2)],fill=(200,200,200),width=2); return W
def red_guide(m0,l1,l2,name):
    m=cv2.dilate(m0.astype(np.uint8),np.ones((3,3),np.uint8))>0
    m2=np.array(Image.fromarray((m*255).astype(np.uint8)).resize((1024,1024),Image.BILINEAR))>127
    im=np.array(white(ref)).astype(float); im[m2]=im[m2]*.45+np.array([235,40,40])*.55
    e=m2&~(cv2.erode(m2.astype(np.uint8),np.ones((3,3),np.uint8))>0); im[e]=(200,0,0)
    banded(Image.fromarray(im.astype(np.uint8)),l1,l2,(200,0,0)).save('refs/'+name); print(name,int(m0.sum()))
N=mask([SHIELD]); F=mask([FAR,AXE]); np.save('work/maskN27.npy',N); np.save('work/maskF27.npy',F)
red_guide(N,'빨간 곳(방패 전체 + 방패를 쥔 가까운 주먹)만 지우고 그 뒤 몸을 그려 주세요','가까운 팔·손은 그리지 않음 · 나머지는 첨부 1과 픽셀 그대로','ref_N27_shield_remove.png')
red_guide(F,'빨간 곳(먼 팔 전체 + 도끼 전체)만 지우고 그 뒤를 그려 주세요','먼 팔은 새로 그리지 않음 · 나머지는 첨부 1과 픽셀 그대로','ref_F27_far_arm_axe_remove.png')
M=json.load(open('measure27.json')); img=white(ref); d=ImageDraw.Draw(img); P=lambda p:(2*p[0],2*p[1])
fa=M['far']; lines=[('13',fa['SH'],fa['EL'],(230,30,30),(-62,-10)),('14',fa['EL'],fa['WR'],(230,30,30),(10,10))]
for n,a,b,c,off in lines:
    d.line([P(a),P(b)],fill=c,width=7)
    for q in (a,b): x,y=P(q); d.ellipse([x-9,y-9,x+9,y+9],outline=(0,0,0),width=3)
    x,y=P(((a[0]+b[0])/2,(a[1]+b[1])/2)); d.text((x+off[0],y+off[1]),n,fill=c,font=fb)
for n,sd,off in (('15·17','near',(-150,-30)),('16·18','far',(24,-60))):
    g=M['legs'][sd]; d.line([P(g['hip']),P(g['knee'])],fill=(150,60,200),width=7); d.line([P(g['knee']),P(g['ankle'])],fill=(150,60,200),width=7)
    for q in (g['hip'],g['knee'],g['ankle']): x,y=P(q); d.ellipse([x-9,y-9,x+9,y+9],outline=(0,0,0),width=3)
    x,y=P(g['knee']); d.text((x+off[0],y+off[1]),n,fill=(150,60,200),font=fb)
banded(img,'빨강 = 먼 윗팔(13)·먼 팔뚝(14) · 보라 = 허벅지·정강이(15~18)','조각 길이 = 선 길이 + 양 끝 둥근 마디, 굵기 = 그림 속 팔·다리 그대로',(30,30,30)).save('refs/ref_L27_limb_guide.png')
print({n:round(float(np.hypot(a[0]-b[0],a[1]-b[1])),1) for n,a,b,c,o in lines})
