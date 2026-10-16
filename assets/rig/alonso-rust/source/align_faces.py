"""표정 9칸을 기준 머리(1A 머리)에 맞추고 얼굴 부분만 오려 패치로.  python3 -I align_faces.py WORK"""
import sys,os,json,cv2,numpy as np
from PIL import Image
W=sys.argv[1]
base=np.asarray(Image.open(os.path.join(W,'rig/parts/head.png')).convert('RGBA')).astype(np.float32)
bh,bw=base.shape[:2]
def prem(a):b=a.copy();b[...,:3]*=b[...,3:4]/255;return b
B=prem(base)
# 얼굴 영역 = 기준 머리의 피부색(주황) 영역을 메워서 조금 줄인 것 (머리카락·머리띠·외곽선 제외)
r,g,b,al=base[...,0],base[...,1],base[...,2],base[...,3]
skin=(al>200)&(r>170)&(g>100)&(g<200)&(b<140)&(r-b>70)
skin=cv2.morphologyEx(skin.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(skin);big=1+np.argmax(st[1:,cv2.CC_STAT_AREA]);skin=(lab==big).astype(np.uint8)
cnts,_=cv2.findContours(skin,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);face=np.zeros_like(skin);cv2.drawContours(face,cnts,-1,1,-1)
face=cv2.erode(face,np.ones((5,5),np.uint8))
cv2.ellipse(face,(276,318),(17,28),0,0,360,1,-1)   # 먼 눈(머리카락 가장자리에 붙어 있음)도 패치 범위에
feather=cv2.GaussianBlur(face.astype(np.float32),(0,0),2.0)
Image.fromarray((face*255).astype(np.uint8)).save(os.path.join(W,'faces/face_mask.png'))
meta=json.load(open(os.path.join(W,'faces/F_meta.json')))
names=['neutral','effort','shout','happy','sad','angry','grimace','focus','relaxed']
out={}
for k,(m,name) in enumerate(zip(meta,names)):
    cell=np.asarray(Image.open(os.path.join(W,'faces',m['file'])).convert('RGBA')).astype(np.float32)
    # 머리 실루엣(알파)로 크기·위치·각도 맞춤: 축소 탐색 후 ECC 정밀
    best=None;C=prem(cell)
    for s in np.arange(.8,1.25,.02):
        for d in (-6,-3,0,3,6):
            M=cv2.getRotationMatrix2D((0,0),d,s);w=cv2.warpAffine(C,M,(bw+200,bh+200),borderValue=(0,0,0,0))
            res=cv2.matchTemplate(w,B,cv2.TM_SQDIFF) if False else None
            # 실루엣 IoU 최대화: 평행이동은 무게중심 맞춤
            a1=(w[...,3]>128).astype(np.float32);a0=(B[...,3]>128).astype(np.float32)
            if a1.sum()<100:continue
            cy1,cx1=np.argwhere(a1).mean(0);cy0,cx0=np.argwhere(a0).mean(0)
            M2=M.copy();M2[0,2]+=cx0-cx1;M2[1,2]+=cy0-cy1
            w2=cv2.warpAffine(C,M2,(bw,bh),borderValue=(0,0,0,0));a2=w2[...,3]>128
            iou=(a2&(a0>0)).sum()/((a2|(a0>0)).sum())
            if best is None or iou>best[0]:best=(iou,M2,s,d)
    iou,M,s,d=best
    # ECC 정밀: warp = 기준 좌표 → 칸 좌표 (템플릿=기준). 펼칠 때 WARP_INVERSE_MAP
    gb=cv2.cvtColor(B[...,:3].clip(0,255).astype(np.uint8),cv2.COLOR_RGB2GRAY).astype(np.float32)
    gc=cv2.cvtColor(C[...,:3].clip(0,255).astype(np.uint8),cv2.COLOR_RGB2GRAY).astype(np.float32)
    Minv=cv2.invertAffineTransform(M).astype(np.float32)
    mask8=(base[...,3]>128).astype(np.uint8)
    try:
        cc,Minv=cv2.findTransformECC(gb,gc,Minv,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,300,1e-6),(cell[...,3]>128).astype(np.uint8),5)
    except Exception as e:print('ecc fail',name,e);cc=0
    al_=cv2.warpAffine(cell,Minv,(bw,bh),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderValue=(0,0,0,0))
    gw=cv2.cvtColor(prem(al_)[...,:3].clip(0,255).astype(np.uint8),cv2.COLOR_RGB2GRAY).astype(np.float32)
    err=float(np.abs(gw-gb)[mask8>0].mean());print(name,'ecc',round(float(cc),3),'mean abs diff',round(err,1))
    patch=al_.copy();patch[...,3]=al_[...,3]*feather
    ys,xs=np.nonzero(patch[...,3]>2);x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    crop=patch[y0:y1,x0:x1].clip(0,255).astype(np.uint8)
    fn=f'face_{name}.png';Image.fromarray(crop,'RGBA').save(os.path.join(W,'rig/parts',fn))
    out[name]={'file':fn,'x0':int(x0),'y0':int(y0),'iou':round(float(iou),3),'s':round(float(s),3)}
    # 확인용 합성
    comp=Image.fromarray(base.astype(np.uint8),'RGBA');comp.alpha_composite(Image.fromarray(crop,'RGBA'),(int(x0),int(y0)))
    comp.save(os.path.join(W,'faces',f'check_{name}.png'))
json.dump(out,open(os.path.join(W,'faces/patches.json'),'w'),indent=1);print(json.dumps(out,indent=0)[:900])
