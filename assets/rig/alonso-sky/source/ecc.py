# 조각 → 원화(ref1024) 아핀 맞춤: 두 점으로 시작 → ECC(아핀) → 가로·세로 배율·회전·기울임으로 나눠 보여줌
import sys,json,math,numpy as np,cv2
from PIL import Image
REF=np.array(Image.open('work/ref1024.png').convert('RGBA')).astype(np.float32)
comp=lambda a:(a[...,:3]*(a[...,3:4]/255.)+255*(1-a[...,3:4]/255.))
gray=lambda a:cv2.cvtColor(comp(a).astype(np.uint8),cv2.COLOR_RGB2GRAY).astype(np.float32)
def sim2(p1,p2,r1,r2):
    p1,p2,r1,r2=map(np.array,(p1,p2,r1,r2));vp=p2-p1;vr=r2-r1;s=np.linalg.norm(vr)/np.linalg.norm(vp);phi=math.atan2(vr[1],vr[0])-math.atan2(vp[1],vp[0])
    c,sn=math.cos(phi)*s,math.sin(phi)*s;M=np.array([[c,-sn,0],[sn,c,0]],np.float32);M[:,2]=r1-M[:,:2]@p1;return M
def decomp(M):
    A=M[:,:2];sx=math.hypot(A[0,0],A[1,0]);rot=math.atan2(A[1,0],A[0,0]);R=np.array([[math.cos(rot),math.sin(rot)],[-math.sin(rot),math.cos(rot)]]);U=R@A
    return dict(sx=round(sx,3),sy=round(U[1,1],3),shear=round(U[0,1]/U[1,1],3),rot=round(math.degrees(rot),1))
def run(name,p1,p2,r1,r2,mode='affine',blur=5,iters=300):
    P=np.array(Image.open(f'pieces/{name}.png').convert('RGBA')).astype(np.float32)
    M0=sim2(p1,p2,[2*r1[0],2*r1[1]],[2*r2[0],2*r2[1]])   # 원화 512 좌표 → ref1024
    mt={'affine':cv2.MOTION_AFFINE,'sim':cv2.MOTION_EUCLIDEAN}[mode]
    C=np.zeros((1024,1024,4),np.float32);h,w=P.shape[:2];C[:min(h,1024),:min(w,1024)]=P[:1024,:1024]
    Wp=cv2.warpAffine(P,M0,(1024,1024),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0));msk=(cv2.erode((Wp[...,3]>200).astype(np.uint8),np.ones((5,5),np.uint8)))
    Inv=cv2.invertAffineTransform(M0).astype(np.float32)
    try:
        cc,Wi=cv2.findTransformECC(gray(REF),gray(C),Inv,mt,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,iters,1e-6),msk,blur)
        W=cv2.invertAffineTransform(Wi).astype(np.float32)
    except cv2.error as e: print("ECCERR",str(e)[:200]);cc=None;W=M0
    return M0,W,cc
def overlay(name,M,out):
    P=np.array(Image.open(f'pieces/{name}.png').convert('RGBA'));Wp=cv2.warpAffine(P,M,(1024,1024),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
    a=Wp[...,3]>128;ys,xs=np.where(a);x0,y0,x1,y1=max(0,xs.min()-40),max(0,ys.min()-40),min(1024,xs.max()+40),min(1024,ys.max()+40)
    r=comp(REF).astype(np.uint8);bl=r.copy();bl[a]=(0.5*r[a]+0.5*Wp[a][:,:3]).astype(np.uint8);e=cv2.Canny(a.astype(np.uint8)*255,50,100)>0;bl[e]=[255,0,0]
    A=Image.fromarray(r).crop((x0,y0,x1,y1));B=Image.fromarray(bl).crop((x0,y0,x1,y1));t=Image.new('RGB',(A.width*2+10,A.height),'white');t.paste(A,(0,0));t.paste(B,(A.width+10,0));t.save(out)
if __name__=='__main__':
    n=sys.argv[1];v=list(map(float,sys.argv[2:10]));mode=sys.argv[10] if len(sys.argv)>10 else 'affine'
    M0,W,cc=run(n,v[0:2],v[2:4],v[4:6],v[6:8],mode)
    print(n,'init',decomp(M0),'ecc',cc,decomp(W))
    overlay(n,W if cc else M0,'/tmp/claude-0/-home-claude/c76b6f25-7843-5cc6-b177-7797dcb3a853/scratchpad/ecc_'+n+'.png')
    try:o=json.load(open('work/affine.json'))
    except:o={}
    o[n]={'M':(W if cc else M0).tolist(),'cc':cc,**decomp(W if cc else M0)};json.dump(o,open('work/affine.json','w'),indent=1)
