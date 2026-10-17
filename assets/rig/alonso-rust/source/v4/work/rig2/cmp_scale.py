# 리그 조각 시트 2 크기 검수: a01(대기 키 포즈) 2배 옆에 새 조각을 부츠 길이 기준으로 맞춰 다리처럼 쌓아 비교
from PIL import Image,ImageDraw
import numpy as np
P='pieces/rig2/';A='pieces/all/'
def L(p):return Image.open(p).convert('RGBA')
a01=L(A+'a01.png');Z=2
a01=a01.resize((a01.width*Z,a01.height*Z),Image.LANCZOS)
boot=L(P+'r08.png')
def solid_w(im):
    al=np.asarray(im)[...,3]>128;xs=np.where(al.any(0))[0];return xs[-1]-xs[0]
s=(47.5*Z)/solid_w(boot)   # 키 포즈 부츠 길이 47.5(1x)
print('scale new->2x',s, 'new->1x',s/Z)
def sc(im,k=s):return im.resize((max(1,int(im.width*k)),max(1,int(im.height*k))),Image.LANCZOS)
W=a01.width+900;H=max(a01.height,800)+40
cv=Image.new('RGBA',(W,H),(250,240,190,255));cv.alpha_composite(a01,(10,10))
d=ImageDraw.Draw(cv)
x=a01.width+40
# 쌓기: 엉덩이(r07) / 허벅지 r01 / 무릎 r05 / 정강이 r03 / 부츠 r08
hip=sc(L(P+'r07.png'));th=sc(L(P+'r01.png'));kn=sc(L(P+'r05.png'));sh=sc(L(P+'r03.png'));bt=sc(boot)
y=40;cv.alpha_composite(hip,(x,y));
cx=x+hip.width//4
ty=y+hip.height-th.width//2
cv.alpha_composite(th,(cx-th.width//2,ty))
ky=ty+th.height-th.width//2
cv.alpha_composite(sh,(cx-sh.width//2,ky-sh.width//2))
cv.alpha_composite(kn,(cx-kn.width//2,ky-kn.height//2))
by=ky-sh.width//2+sh.height-int(bt.height*.55)
cv.alpha_composite(bt,(cx-bt.width//3,by))
d.text((x,10),'new stacked (boot-length scale)',fill=(0,0,0,255))
# 개별 조각 나열
xx=x+260;yy=40
for f in ['r09','r10','r11','r12','r13','r14','r15','r16','r06','r02','r04']:
    im=sc(L(P+f+'.png'))
    if xx+im.width>W-10:xx=x+260;yy+=150
    cv.alpha_composite(im,(xx,yy));d.text((xx,yy-12),f,fill=(0,0,0,255));xx+=im.width+12
# 기존 상체 a07, 윗팔 a13 같은 배율(ALL 조각 시트 배율 = 부츠 a30 기준)
a30=L(A+'a30.png');s2=(47.5*Z)/solid_w(a30);print('ALL pieces->2x',s2)
xx=x+260;yy+=200
for f in ['a07','a13','a14','a30','a25','a28','a06']:
    im=sc(L(A+f+'.png'),s2);cv.alpha_composite(im,(xx,yy));d.text((xx,yy-12),'old '+f,fill=(120,0,0,255));xx+=im.width+12
cv.convert('RGB').save('work/rig2/cmp_scale.png')
