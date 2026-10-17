# 조각 ↔ 원화(ref1024) 닮음변환 찾기: 거친 탐색(배율·회전·위치, 마스크 템플릿) → ECC(유클리드+배율) 다듬기
import sys,json,math,numpy as np,cv2
from PIL import Image
REF=np.array(Image.open('work/ref1024.png').convert('RGBA')).astype(np.float32)
def comp(a):  # 흰 배경 합성
    al=a[...,3:4]/255.;return (a[...,:3]*al+255*(1-al)).astype(np.float32)
RC=comp(REF)
def warp_piece(P,s,deg):
    h,w=P.shape[:2];c=(w/2,h/2);M=cv2.getRotationMatrix2D(c,deg,s)
    cs=np.array([[0,0,1],[w,0,1],[0,h,1],[w,h,1]])@M.T;mn=cs.min(0);mx=cs.max(0);M[:,2]-=mn
    W=cv2.warpAffine(P,M,(int(mx[0]-mn[0])+1,int(mx[1]-mn[1])+1),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0));return W,M
def coarse(P,roi,scales,rots):
    x0,y0,x1,y1=roi;best=(1e18,)
    R=RC[y0:y1,x0:x1]
    for s in scales:
        for r in rots:
            W,M=warp_piece(P,s,r);h,w=W.shape[:2]
            if h>=R.shape[0] or w>=R.shape[1] or h<8 or w<8:continue
            m=(W[...,3]>200).astype(np.float32);T=comp(W)
            res=cv2.matchTemplate(R,T,cv2.TM_SQDIFF,mask=np.dstack([m]*3))/max(1,m.sum())
            mn,_,loc,_=cv2.minMaxLoc(res)
            if mn<best[0]:best=(mn,s,r,loc[0]+x0,loc[1]+y0,M)
    return best
def to_sim(best):
    _,s,r,x,y,M=best;A=np.vstack([M,[0,0,1]]);T=np.array([[1,0,x],[0,1,y],[0,0,1]]);return (T@A)[:2]
def refine(P,M0,iters=200):
    # ECC: 조각 → 기준. 템플릿=조각 회색, 입력=기준 회색, 마스크=조각 알파
    g=lambda a:cv2.cvtColor(comp(a).astype(np.uint8),cv2.COLOR_RGB2GRAY).astype(np.float32)
    tp=g(P);msk=(P[...,3]>200).astype(np.uint8);im=g(REF)
    W=M0.astype(np.float32).copy()
    try:
        cc,W=cv2.findTransformECC(tp,im,W,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,iters,1e-6),msk,5)
    except cv2.error as e: return M0,None
    # 닮음으로 투영 (배율 하나·회전)
    A=W[:,:2];U,S,Vt=np.linalg.svd(A);Rm=U@Vt;s=S.mean();Ws=np.hstack([Rm*s,W[:,2:]]);return Ws,cc
def err(P,M):
    h,w=1024,1024;Wp=cv2.warpAffine(P,M,(w,h),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0));m=(Wp[...,3]>200)&(REF[...,3]>200);mp=Wp[...,3]>200
    return float(np.abs(comp(Wp)[m]-RC[m]).mean()),float(m.sum()/max(1,mp.sum()))
if __name__=='__main__':
    spec=json.load(open('match_spec.json'));out=json.load(open('work/match.json')) if len(sys.argv)<2 or sys.argv[1]!='all' and False else {}
    try: out=json.load(open('work/match.json'))
    except: out={}
    names=sys.argv[1:] or list(spec)
    for n in names:
        sp=spec[n];P=np.array(Image.open(f'pieces/{n}.png').convert('RGBA')).astype(np.float32)
        sc=np.arange(*sp['s']);ro=np.arange(*sp['r'])
        # 거친 탐색은 절반 크기로
        b=coarse(P,sp['roi'],sc,ro)
        if len(b)<6: print(n,'no fit');continue
        M0=to_sim(b);e0=err(P,M0)
        M1,cc=refine(P,M0);e1=err(P,M1)
        M=M1 if (cc is not None and e1[0]<=e0[0]+2) else M0;e=err(P,M)
        s=math.hypot(M[0,0],M[1,0]);rot=math.degrees(math.atan2(M[1,0],M[0,0]))
        out[n]={'M':M.tolist(),'s':round(s,4),'rot':round(rot,2),'err':round(e[0],1),'cover':round(e[1],2)}
        print(n,out[n]['s'],out[n]['rot'],'err',out[n]['err'],'cover',out[n]['cover'],'(coarse',round(e0[0],1),')')
        json.dump(out,open('work/match.json','w'),indent=1)
