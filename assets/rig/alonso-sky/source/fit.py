# 조각 → 원화(512) 맞춤: 배율·회전·위치를 찾아 겹침 오차가 가장 작은 값 (알파 가린 부분만 비교)
import sys,json,numpy as np
from PIL import Image
from scipy import signal
REF=np.array(Image.open('ref512.png').convert('RGBA')).astype(float)
def score(P,x,y):
    h,w=P.shape[:2]
    if x<0 or y<0 or x+w>512 or y+h>512:return 1e9
    R=REF[y:y+h,x:x+w];m=(P[...,3]>200)&(R[...,3]>200);mp=P[...,3]>200
    if m.sum()<mp.sum()*.7:return 1e9
    return np.abs(R[...,:3][m]-P[...,:3][m]).mean()+ (1-m.sum()/mp.sum())*80
def fit(name,scales,rots,region=None):
    im=Image.open(f'pieces/{name}.png');best=(1e9,)
    for s in scales:
        for r in rots:
            p=im.resize((max(2,int(im.width*s)),max(2,int(im.height*s))),Image.LANCZOS).rotate(r,expand=True,resample=Image.BICUBIC);P=np.array(p).astype(float)
            h,w=P.shape[:2];x0,y0,x1,y1=region or (0,0,512-w,512-h)
            for y in range(y0,min(y1,512-h),4):
                for x in range(x0,min(x1,512-w),4):
                    d=score(P,x,y)
                    if d<best[0]:best=(d,s,r,x,y)
    d,s,r,x,y=best
    # 다듬기
    im2=im.resize((max(2,int(im.width*s)),max(2,int(im.height*s))),Image.LANCZOS).rotate(r,expand=True,resample=Image.BICUBIC);P=np.array(im2).astype(float)
    for yy in range(y-4,y+5):
        for xx in range(x-4,x+5):
            dd=score(P,xx,yy)
            if dd<best[0]:best=(dd,s,r,xx,yy)
    return best
if __name__=='__main__':
    n=sys.argv[1];a=list(map(float,sys.argv[2:5]));rr=list(map(float,sys.argv[5:8]))
    sc=np.arange(a[0],a[1]+1e-9,a[2]);ro=np.arange(rr[0],rr[1]+1e-9,rr[2])
    print(n,fit(n,sc,ro))
