"""3 산초 표정 맞춤: 시트 face_<이름> 조각 → 원화 얼굴 아핀(원화 얼굴 피부 영역에서 흐린 그림 차이 최소 — 격자 탐색 + Nelder-Mead).
실행: python3 -I face_fit.py neutral  → Mface_neutral.npy·fopt_neutral.png(현재 폴더). 결과 M 은 geom.json faceNeutral 에 적음(10-19: sx 0.926 sy 0.944)
ECC 는 그림이 다시 그려진 머리라 수렴 안 함(NaN)."""
import numpy as np, cv2, json, sys
from PIL import Image
from scipy import ndimage as nd, optimize as op
import os; S=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
RA=np.array(Image.open(S+'ref512.png').convert('RGBA'))
nm=sys.argv[1] if len(sys.argv)>1 else 'neutral'
N=np.array(Image.open(S+f'pieces/face_{nm}.png').convert('RGBA'))
bg=np.array([150,150,150.])
comp=lambda a: (a[...,:3].astype(np.float32)*a[...,3:]/255+bg*(1-a[...,3:]/255)).astype(np.float32)
hsv=cv2.cvtColor(RA[...,:3],cv2.COLOR_RGB2HSV)
skin=(hsv[...,0]>=5)&(hsv[...,0]<=25)&(hsv[...,1]>80)&(hsv[...,2]>140)&(RA[...,3]>200)
fm=np.zeros_like(skin); fm[262:332,268:356]=skin[262:332,268:356]; lb,n=nd.label(fm); sz=nd.sum(fm,lb,range(1,n+1))
face=nd.binary_fill_holes(lb==(np.argmax(sz)+1))
mask=cv2.dilate(face.astype(np.uint8),np.ones((5,5),np.uint8))>0
A=cv2.GaussianBlur(comp(RA),(0,0),1.2); ys,xs=np.nonzero(mask)
Nc=comp(N)
def cost(p, blur=1.2):
  M=np.float32([[p[0],p[1],p[2]],[p[3],p[4],p[5]]])
  w=cv2.warpAffine(Nc,M,(512,512),flags=cv2.INTER_LINEAR,borderValue=(150,150,150))
  w=cv2.GaussianBlur(w,(0,0),blur)
  return float(np.abs(w[ys,xs]-A[ys,xs]).mean())
p0=np.array([1,0,221.1,0,1,164.2],float)
# coarse grid over tx,ty,scale,rot
best=(1e9,None)
for s in [0.94,0.98,1.02,1.06]:
  for r in np.radians([-2,0,2,4]):
    for dx in range(-6,7,2):
      for dy in range(-6,7,2):
        c,sn=s*np.cos(r),s*np.sin(r); cx,cy=78.2,136
        # keep near eye anchored then offset
        tx=299.3+dx-(c*cx-sn*cy); ty=300.2+dy-(sn*cx+c*cy)
        p=np.array([c,-sn,tx,sn,c,ty]); v=cost(p)
        if v<best[0]: best=(v,p)
print('grid',round(best[0],2),np.round(best[1],4).tolist())
r=op.minimize(cost,best[1],method='Nelder-Mead',options=dict(xatol=1e-4,fatol=1e-3,maxiter=4000,initial_simplex=None))
r2=op.minimize(lambda p: cost(p,0.6),r.x,method='Nelder-Mead',options=dict(xatol=1e-4,fatol=1e-3,maxiter=4000))
M=r2.x.reshape(2,3); print(nm,'cost',round(r.fun,2),round(r2.fun,2),'M',np.round(M,4).tolist(),'sx',round(np.hypot(M[0,0],M[1,0]),3),'sy',round(np.hypot(M[0,1],M[1,1]),3))
np.save(f'Mface_{nm}.npy',M)
w=cv2.warpAffine(N,M.astype(np.float32),(512,512),flags=cv2.INTER_LANCZOS4)
x0,y0,x1,y1=255,255,365,340; k=4; g2=np.array([120,200,120.])
c2=lambda a: (a[...,:3].astype(float)*a[...,3:]/255+g2*(1-a[...,3:]/255))
ca=c2(RA[y0:y1,x0:x1]); cb=c2(w[y0:y1,x0:x1]); m3=mask[y0:y1,x0:x1,None]
o=np.concatenate([ca,cb,(ca+cb)/2,np.where(m3,np.abs(ca-cb).mean(2,keepdims=True)*2,30).repeat(3,2)],1)
Image.fromarray(np.clip(o,0,255).astype(np.uint8)).resize((o.shape[1]*k,o.shape[0]*k),Image.NEAREST).save(f'fopt_{nm}.png')
