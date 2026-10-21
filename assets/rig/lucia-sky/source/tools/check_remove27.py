"""27 스카이 루시아 — 프롬프트 2(방패+가까운 주먹 지운 원화)·3(먼 팔·도끼 지운 원화) 검수 — check_remove17 구조
실행: python3 tools/check_remove27.py shield|far 받은그림.png  (source/ 에서)"""
import os, sys
import numpy as np, cv2
from PIL import Image
S=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RA=np.array(Image.open(os.path.join(S,'ref512.png')).convert('RGBA'))
rem=np.load(os.path.join(S,'work','maskN27.npy' if sys.argv[1]=='shield' else 'maskF27.npy'))
def sift(a,b):
    s=cv2.SIFT_create(); g=lambda x: cv2.cvtColor(np.ascontiguousarray(x[...,:3]),cv2.COLOR_RGB2GRAY)
    k1,d1=s.detectAndCompute(g(a),None); k2,d2=s.detectAndCompute(g(b),None)
    m=[p for p,q in cv2.BFMatcher().knnMatch(d1,d2,k=2) if p.distance<.7*q.distance]
    A,inl=cv2.estimateAffinePartial2D(np.float32([k1[x.queryIdx].pt for x in m]),np.float32([k2[x.trainIdx].pt for x in m]),ransacReprojThreshold=2)
    return len(m),int(inl.sum()),float(np.hypot(A[0,0],A[0,1])),A[:,2]
def onbg(im,c=(52,52,62)):
    b=Image.new('RGBA',(512,512),c+(255,)); b.alpha_composite(Image.fromarray(im)); return np.array(b.convert('RGB'))
path=sys.argv[2]; B=np.array(Image.open(path).convert('RGBA'))
remD=cv2.dilate(rem.astype(np.uint8),np.ones((9,9),np.uint8))>0
n,ni,sc,t=sift(RA,B)
pa=RA[...,:3].astype(float)*RA[...,3:4]/255; pb=B[...,:3].astype(float)*B[...,3:4]/255
d=np.abs(pa-pb).max(-1); da=np.abs(RA[...,3].astype(int)-B[...,3].astype(int)); ch=(d>24)|(da>40); out=ch&~remD
print(f'{os.path.basename(path)} SIFT {n}/{ni} 배율 {sc:.4f} 이동 ({t[0]:.2f},{t[1]:.2f})')
print(f'  지운 곳 밖 평균 차 {d[~remD].mean():.3f} · 밖 바뀐 px {int(out.sum())} · 지운 곳 안 새 그림 {int((rem&(B[...,3]>128)).sum())}')
if out.any():
    nl,cc,st,_=cv2.connectedComponentsWithStats(out.astype(np.uint8),8)
    print('  밖 바뀐 덩어리:',sorted([(int(st[i,4]),int(st[i,0]),int(st[i,1]),int(st[i,2]),int(st[i,3])) for i in range(1,nl)],reverse=True)[:8])
nl,cc,st,_=cv2.connectedComponentsWithStats((B[...,3]>40).astype(np.uint8),8)
print('  떨어진 작은 섬:',[(int(st[i,4]),int(st[i,0]),int(st[i,1])) for i in range(1,nl) if st[i,4]<400][:10])
r=onbg(RA).copy(); r[ch]=(r[ch]*.3+np.array([255,40,40])*.7).astype(np.uint8)
ys,xs=np.nonzero(remD); bx=(max(0,xs.min()-10),max(0,ys.min()-10),min(512,xs.max()+10),min(512,ys.max()+10))
z=Image.fromarray(onbg(B,(235,238,245))).crop(bx); zs=512/max(z.size); z=np.array(z.resize((int(z.width*zs),int(z.height*zs)),Image.LANCZOS))
zz=np.full((512,512,3),255,np.uint8); zz[:z.shape[0],:z.shape[1]]=z; sp=np.full((512,8,3),255,np.uint8)
op=os.path.join(S,'review',f'check_remove27_{os.path.splitext(os.path.basename(path))[0]}.png')
Image.fromarray(np.hstack([onbg(RA),sp,onbg(B),sp,r,sp,zz])).save(op); print('  그림',op)
