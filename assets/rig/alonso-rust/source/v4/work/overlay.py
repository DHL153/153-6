import json,sys,cv2,numpy as np
from PIL import Image
W='work';R=Image.open(f'{W}/ref1024.png').convert('RGBA');res=json.load(open(f'{W}/match_result.json'))
names=sys.argv[1:] or list(res)
tiles=[]
for n in names:
    r=res[n];img=np.asarray(Image.open(f"{W}/{r['file']}").convert('RGBA'));M=np.array(r['M'])
    warp=cv2.warpAffine(img,M,R.size,flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
    base=Image.new('RGBA',R.size,(255,255,255,255));g=R.copy();g.putalpha(Image.fromarray((np.asarray(R)[...,3]*.45).astype(np.uint8)));base.alpha_composite(g)
    w=warp.copy();w[...,0]=np.clip(w[...,0]*.6+100,0,255);w[...,3]=(w[...,3]*.6).astype(np.uint8)
    base.alpha_composite(Image.fromarray(w,'RGBA'));
    a=np.asarray(base.convert('RGB')).copy();cv2.putText(a,n,(8,30),cv2.FONT_HERSHEY_SIMPLEX,1,(200,0,0),2);tiles.append(a)
h=tiles[0].shape[0];row=np.concatenate(tiles,1);Image.fromarray(row).resize((row.shape[1]//2,h//2)).save(f'{W}/overlay.png')
