# 새 다리 조각을 키 포즈 a01 관절 점에 맞춰 놓아 보기 (조각 검수용 · 같은 배율 비교)
import math,numpy as np
from PIL import Image,ImageDraw
P='pieces/rig2/';A='pieces/all/';Z=3
def L(p):return Image.open(p).convert('RGBA')
def body(im):
    al=np.asarray(im)[...,3]>128;ys=np.where(al.any(1))[0];xs=np.where(al.any(0))[0];return xs[0],ys[0],xs[-1],ys[-1]
def seg(cv,im,p0,p1,width,ext0,ext1,sq=None):
    """조각(세로, 위=p0쪽)을 p0→p1 뼈에 놓음. width=목표 폭(1x), ext=관절 끝 덮개 길이 비율(폭 대비)"""
    x0,y0,x1,y1=body(im);im=im.crop((x0,y0,x1+1,y1+1))
    sx=width/im.width
    L_=math.dist(p0,p1)+width*(ext0+ext1)
    sy=L_/im.height
    im=im.resize((max(1,int(im.width*sx*Z)),max(1,int(im.height*sy*Z))),Image.LANCZOS)
    ang=math.degrees(math.atan2(p1[0]-p0[0],p1[1]-p0[1]))
    # 위쪽 끝(ext0) 기준 회전
    pad=Image.new('RGBA',(im.width*3,im.height*3));pad.alpha_composite(im,(im.width,im.height))
    piv=(im.width*1.5,im.height+width*ext0*Z)
    r=pad.rotate(ang,center=piv,resample=Image.BICUBIC)
    cv.alpha_composite(r,(int(p0[0]*Z-piv[0]),int(p0[1]*Z-piv[1])))
    return sx,sy
def put(cv,im,c,w,flip=False):
    x0,y0,x1,y1=body(im);im=im.crop((x0,y0,x1+1,y1+1))
    if flip:im=im.transpose(Image.FLIP_LEFT_RIGHT)
    s=w/im.width;im=im.resize((int(im.width*s*Z),int(im.height*s*Z)),Image.LANCZOS)
    cv.alpha_composite(im,(int(c[0]*Z-im.width/2),int(c[1]*Z-im.height/2)));return s
a01=L(A+'a01.png');a01=a01.resize((a01.width*Z,a01.height*Z),Image.LANCZOS)
W,H=a01.size
def build():
    cv=Image.new('RGBA',(W,H),(0,0,0,0))
    # 먼 다리 (뒤)
    seg(cv,L(P+'r02.png'),(215,262),(225,300),44,.35,.3)
    seg(cv,L(P+'r04.png'),(225,300),(242,345),27,.3,.2)
    put(cv,L(P+'r08.png'),(250,362),50)
    put(cv,L(P+'r06.png'),(229,304),30)
    # 엉덩이
    put(cv,L(P+'r07.png'),(190,268),112)
    # 가까운 다리
    seg(cv,L(P+'r01.png'),(160,262),(160,300),50,.35,.3)
    seg(cv,L(P+'r03.png'),(160,300),(150,347),28,.3,.2)
    put(cv,L(P+'r08.png'),(147,362),46)
    put(cv,L(P+'r05.png'),(168,301),44)
    return cv
leg=build()
bg=(250,240,190,255)
cmpw=Image.new('RGBA',(W*3,H),bg)
cmpw.alpha_composite(a01,(0,0))
cmpw.alpha_composite(leg,(W,0))
ov=a01.copy();o2=leg.copy();o2.putalpha(Image.fromarray((np.asarray(o2)[...,3]*.6).astype(np.uint8)));ov.alpha_composite(o2)
cmpw.alpha_composite(ov,(2*W,0))
cmpw.crop((0,int(230*Z),W*3,int(390*Z))).convert('RGB').save('work/rig2/fit_legs.png')
