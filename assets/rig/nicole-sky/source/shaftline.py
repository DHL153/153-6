"""자루 중심선: 갈색 픽셀을 열마다 훑어 위·아래 끝의 가운데 → 직선 맞춤(중앙값 잔차로 이상치 제거). 굵기 = 열 높이 중앙값×cos."""
import sys,json
import numpy as np
from scipy import ndimage as nd
sys.path.insert(0,__file__.rsplit('/',1)[0])
from measure import masks
def shaft(p):
    a,al,brown,skin=masks(p);H,W=al.shape;xs=[];ys=[];hs=[]
    for x in range(W):
        c=np.nonzero(brown[:,x])[0]
        if len(c)<6:continue
        # 가장 긴 연속 구간
        runs=np.split(c,np.nonzero(np.diff(c)>1)[0]+1);r=max(runs,key=len)
        if len(r)<6:continue
        xs.append(x);ys.append((r[0]+r[-1])/2);hs.append(r[-1]-r[0]+1)
    xs=np.array(xs,float);ys=np.array(ys);hs=np.array(hs,float)
    med=np.median(hs);ok=np.abs(hs-med)<med*.25
    for it in range(3):
        A=np.stack([xs[ok],np.ones(ok.sum())],1);k,b=np.linalg.lstsq(A,ys[ok],rcond=None)[0]
        res=np.abs(ys-(k*xs+b));ok=ok&(res<max(2,np.median(res[ok])*3))
    th=float(np.median(hs[ok]))*np.cos(np.arctan(k))
    U=np.array([1,k]);U/=np.linalg.norm(U)
    sy,sx=np.nonzero(skin);fc=np.array([sx.mean(),sy.mean()]);C=np.array([0,b]);G=C+U*((fc-C)@U)
    return dict(file=p,shaftAngleDeg=round(float(-np.degrees(np.arctan(k))),2),shaftDir=[round(float(U[0]),4),round(float(U[1]),4)],thick=round(th,1),grip=[round(float(G[0]),1),round(float(G[1]),1)],fistW=int(np.ptp(sx)),fistC=[round(float(fc[0]),1),round(float(fc[1]),1)])
if __name__=='__main__':
    for p in sys.argv[1:]:print(json.dumps(shaft(p)))
