"""마젠타 시트 → 조각별 투명 PNG + 번호 붙은 미리보기.  python3 -I split_sheet.py SHEET.png OUTDIR PREFIX"""
import sys,os,json
from PIL import Image,ImageDraw
import numpy as np
from scipy import ndimage as nd
src,out,pre=sys.argv[1],sys.argv[2],sys.argv[3];os.makedirs(out,exist_ok=True)
a=np.asarray(Image.open(src).convert('RGB')).astype(float);r,g,b=a[...,0],a[...,1],a[...,2]
bgc=np.median(a[:8,:8].reshape(-1,3),0)
s=np.minimum(r,b)-g                      # 마젠타 정도
alpha=np.clip((175-s)/(175-95),0,1)
A=alpha[...,None];col=np.clip(np.where(A>0.02,(a-(1-A)*bgc)/np.maximum(A,1e-3),0),0,255)
rgba=np.dstack([col,alpha*255]).astype(np.uint8)
lab,n=nd.label(nd.binary_dilation(alpha>0.5,iterations=3))
objs=nd.find_objects(lab);comps=[]
for i,sl in enumerate(objs):
    if sl is None:continue
    m=(lab[sl]==i+1);z=int(m.sum())
    if z<400:continue
    y0,y1,x0,x1=sl[0].start,sl[0].stop,sl[1].start,sl[1].stop
    piece=rgba[y0:y1,x0:x1].copy();piece[...,3]=(piece[...,3]*m).astype(np.uint8)
    comps.append(dict(x0=x0,y0=y0,x1=x1,y1=y1,size=z,piece=piece))
comps.sort(key=lambda c:(round(c['y0']/150),c['x0']))   # 줄 → 왼쪽부터
meta=[]
prev=Image.new('RGBA',(a.shape[1],a.shape[0]),(40,44,54,255));prev.alpha_composite(Image.fromarray(rgba,'RGBA'));d=ImageDraw.Draw(prev)
for k,c in enumerate(comps,1):
    fn=f'{pre}{k:02d}.png';Image.fromarray(c['piece'],'RGBA').save(os.path.join(out,fn))
    meta.append({k2:c[k2] for k2 in ('x0','y0','x1','y1','size')}|{'file':fn})
    d.rectangle([c['x0'],c['y0'],c['x1'],c['y1']],outline=(255,220,0,255),width=2);d.text((c['x0']+4,c['y0']+2),str(k),fill=(255,255,0,255))
json.dump(meta,open(os.path.join(out,pre+'meta.json'),'w'),indent=1)
prev.convert('RGB').save(os.path.join(out,pre+'overview.png'));print(len(comps),'pieces')
