"""조각을 기준 그림(ref1024)에 템플릿 매칭: 크기·각도 탐색 → 조각→기준 변환 행렬.  python3 -I match_parts.py WORKDIR"""
import cv2,numpy as np,json,sys,os
from PIL import Image
W=sys.argv[1]
ref=np.asarray(Image.open(os.path.join(W,'ref1024.png')).convert('RGBA')).astype(np.float32)
ref[...,:3]*=ref[...,3:4]/255.0
small=lambda im,f:cv2.resize(im,None,fx=f,fy=f,interpolation=cv2.INTER_AREA)
def xform(img,s,deg):
    h,w=img.shape[:2];c=(w/2,h/2);M=cv2.getRotationMatrix2D(c,deg,s)
    cos,sin=abs(M[0,0]),abs(M[0,1]);nw=int(h*sin+w*cos)+4;nh=int(h*cos+w*sin)+4
    M[0,2]+=nw/2-c[0];M[1,2]+=nh/2-c[1]
    out=cv2.warpAffine(img,M,(nw,nh),flags=cv2.INTER_AREA,borderValue=(0,0,0,0));out[...,:3]*=out[...,3:4]/255.0
    return out,M
def match(img,roi,scales,rots,f=.5):
    R=small(ref[roi[1]:roi[3],roi[0]:roi[2]],f);best=None
    for s in scales:
        for d in rots:
            T,M=xform(img,s*f,d);mask=(T[...,3]>128).astype(np.float32)
            if T.shape[0]>=R.shape[0] or T.shape[1]>=R.shape[1] or mask.sum()<50:continue
            res=cv2.matchTemplate(R,T,cv2.TM_SQDIFF,mask=np.dstack([mask]*4))/mask.sum()
            mn,_,loc,_=cv2.minMaxLoc(res)
            if best is None or mn<best[0]:best=(mn,s,d,loc,M)
    mn,s,d,loc,M=best;M=M.copy();M/=f;M[:,:2]*=f   # 축소 공간 → 원래 공간
    M=np.array(cv2.getRotationMatrix2D((0,0),d,s));
    return mn,s,d,loc
def full(img,roi,s0,d0):
    # 정밀: 원 해상도에서 좁은 범위
    best=None
    for s in np.linspace(s0*.94,s0*1.06,7):
        for d in np.arange(d0-4,d0+4.1,2):
            T,M=xform(img,s,d);R=ref[roi[1]:roi[3],roi[0]:roi[2]];mask=(T[...,3]>128).astype(np.float32)
            if T.shape[0]>=R.shape[0] or T.shape[1]>=R.shape[1]:continue
            res=cv2.matchTemplate(R,T,cv2.TM_SQDIFF,mask=np.dstack([mask]*4))/mask.sum()
            mn,_,loc,_=cv2.minMaxLoc(res)
            if best is None or mn<best[0]:best=(mn,s,d,loc,M)
    mn,s,d,loc,M=best;M=M.copy();M[0,2]+=loc[0]+roi[0];M[1,2]+=loc[1]+roi[1]
    return dict(score=float(mn),s=float(s),deg=float(d),M=M.tolist())
jobs=json.load(open(os.path.join(W,'match_jobs.json')))
out={}
for name,j in jobs.items():
    img=np.asarray(Image.open(os.path.join(W,j['file'])).convert('RGBA')).astype(np.float32)
    sc=np.arange(j['s'][0],j['s'][1]+1e-6,j['s'][2]);rt=np.arange(j['r'][0],j['r'][1]+1e-6,j['r'][2])
    mn,s,d,loc=match(img,j['roi'],sc,rt)
    out[name]=full(img,j['roi'],s,d)|{'file':j['file']};print(name,round(out[name]['score']),round(out[name]['s'],3),out[name]['deg'])
json.dump(out,open(os.path.join(W,'match_result.json'),'w'),indent=1)
