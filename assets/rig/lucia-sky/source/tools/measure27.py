# 27 스카이 루시아 관절 1차: 7 러스트 joints7(27 자세로 다시 그린 원화)을 SIFT 닮음으로 옮겨 그림에 찍어 봄
import cv2, json, numpy as np, sys
R='/home/claude/153-6/assets/rig/lucia-rust/source/'
a=cv2.imread(R+'ref512.png',-1); b=cv2.imread('ref512.png',-1)
def g(x):
    x=x.astype(float); al=x[...,3:4]/255; return (x[...,:3]*al+235*(1-al)).astype(np.uint8)
ga,gb=[cv2.cvtColor(g(x),cv2.COLOR_BGR2GRAY) for x in (a,b)]
s=cv2.SIFT_create(); ka,da=s.detectAndCompute(ga,None); kb,db=s.detectAndCompute(gb,None)
m=cv2.BFMatcher().knnMatch(da,db,k=2); good=[p for p,q in m if p.distance<.7*q.distance]
M,inl=cv2.estimateAffinePartial2D(np.float32([ka[p.queryIdx].pt for p in good]),np.float32([kb[p.trainIdx].pt for p in good]),ransacReprojThreshold=3)
print('matches',len(good),'inl',int(inl.sum()),'M',M.round(3).tolist())
J=json.load(open(R+'joints7.json'))
def T(p): return [round(float(M[0,0]*p[0]+M[0,1]*p[1]+M[0,2]),1),round(float(M[1,0]*p[0]+M[1,1]*p[1]+M[1,2]),1)]
pts={k:T(J[k]) for k in ['O','HIP','NECK','SH_F','EL_F','WR_F','G','FIST_N']}
for side in ('near','far'):
    for j in 'hka': pts[f'{side}_{j}']=T(J['legs'][side][j])
pts['pommel']=T(J['AXE']['pommel']); pts['collar']=T(J['AXE']['collar'])
print(json.dumps(pts))
im=cv2.resize(g(b),None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
for k,(x,y) in pts.items():
    cv2.circle(im,(int(x*2),int(y*2)),5,(0,0,255),-1); cv2.putText(im,k,(int(x*2)+6,int(y*2)-4),0,.45,(0,0,200),1)
cv2.imwrite('work/j27_from7.png',im)
