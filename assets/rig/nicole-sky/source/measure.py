"""손 조각 측정: 자루(갈색) 중심선·굵기, 주먹(피부) 중심 → 쥔 점, 팔 끝(팔꿈치) 점. python3 -I measure.py piece.png [...]"""
import sys,json,colorsys
import numpy as np
from PIL import Image
def masks(p):
    a=np.asarray(Image.open(p).convert('RGBA')).astype(float);rgb=a[...,:3]/255;al=a[...,3]>128
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2];mx=rgb.max(-1);mn=rgb.min(-1);s=(mx-mn)/np.maximum(mx,1e-6)
    h=np.zeros_like(mx);d=np.maximum(mx-mn,1e-6)
    h=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))*60
    brown=al&(h>8)&(h<40)&(s>.35)&(s<.8)&(mx>.22)&(mx<.62)
    skin=al&(h>15)&(h<40)&(s>.25)&(s<.65)&(mx>.78)
    from scipy import ndimage as nd
    def big(m,open_=2,frac=1.0):
        m=nd.binary_opening(m,iterations=open_);lb,n=nd.label(m)
        if n==0:return m
        sz=np.array(nd.sum(m,lb,range(1,n+1)));keep=np.nonzero(sz>=sz.max()*frac)[0]+1;return np.isin(lb,keep)
    brown=nd.binary_closing(big(brown,frac=.15),iterations=2);skin=nd.binary_fill_holes(nd.binary_closing(big(skin),iterations=3))
    return a,al,brown,skin
def pca(ys,xs):
    m=np.array([xs.mean(),ys.mean()]);X=np.stack([xs-m[0],ys-m[1]],1);w,v=np.linalg.eigh(X.T@X);return m,v[:,1]
def measure(p):
    a,al,brown,skin=masks(p);H,W=al.shape
    ys,xs=np.nonzero(brown);c,u=pca(ys,xs)
    if u[0]<0:u=-u                                   # 자루 방향 = 오른쪽(창끝 쪽)
    n=np.array([-u[1],u[0]])
    t=(xs-c[0])*u[0]+(ys-c[1])*u[1];o=(xs-c[0])*n[0]+(ys-c[1])*n[1]
    # 굵기: 자루 길이 방향 구간마다 수직 폭
    th=[];off=[]
    for k in np.linspace(t.min()+8,t.max()-8,40):
        sel=np.abs(t-k)<2
        if sel.sum()>5:th.append(o[sel].max()-o[sel].min());off.append((o[sel].max()+o[sel].min())/2)
    th=np.array(th);thick=float(np.percentile(th,75));c=c+n*float(np.median(off))
    sy,sx=np.nonzero(skin);fc=np.array([sx.mean(),sy.mean()])
    G=c+u*((fc-c)@u)                                   # 주먹 중심을 자루 중심선에 투영 = 쥔 점
    # 팔 끝: 피부·갈색 아닌 불투명 픽셀 중 G에서 가장 먼 쪽 끝 덩어리
    arm=al&~brown&~skin;ay,ax=np.nonzero(arm);dd=np.hypot(ax-G[0],ay-G[1]);far=dd>np.percentile(dd,93)
    E=np.array([ax[far].mean(),ay[far].mean()])
    v=E-G;ang_fs=np.degrees(np.arctan2(u[0]*v[1]-u[1]*v[0],u@v))   # 자루(창끝 방향)→팔꿈치 방향 사이 각
    return dict(file=p,size=[W,H],shaftDir=[round(float(u[0]),4),round(float(u[1]),4)],shaftAngleDeg=round(float(np.degrees(np.arctan2(-u[1],u[0]))),1),
                thick=round(thick,1),grip=[round(float(G[0]),1),round(float(G[1]),1)],elbow=[round(float(E[0]),1),round(float(E[1]),1)],
                forearmLen=round(float(np.hypot(*v)),1),angleShaftToElbow=round(float(ang_fs),1),fistW=round(float(sx.max()-sx.min()),1))
if __name__=='__main__':
    out=[measure(p) for p in sys.argv[1:]]
    for m in out:print(json.dumps(m,ensure_ascii=False))
