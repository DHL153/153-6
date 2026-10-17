import sys,json,numpy as np,cv2
from PIL import Image
REF=Image.open('work/ref1024.png').convert('RGBA');M=json.load(open('work/match.json'))
out=sys.argv[1];names=sys.argv[2:]
tiles=[]
for n in names:
    P=np.array(Image.open(f'pieces/{n}.png').convert('RGBA'));W=cv2.warpAffine(P,np.array(M[n]['M']),(1024,1024),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
    a=W[...,3]>128;ys,xs=np.where(a);x0,y0,x1,y1=max(0,xs.min()-30),max(0,ys.min()-30),min(1024,xs.max()+30),min(1024,ys.max()+30)
    bg=Image.new('RGBA',(1024,1024),(255,255,255,255));bg.alpha_composite(REF);r=np.array(bg)
    blend=r.copy();blend[a]=(0.5*r[a]+0.5*W[a]).astype(np.uint8)
    edge=cv2.Canny(a.astype(np.uint8)*255,50,100)>0;blend[edge]=[255,0,0,255]
    A=Image.fromarray(r).crop((x0,y0,x1,y1));B=Image.fromarray(blend).crop((x0,y0,x1,y1))
    t=Image.new('RGB',(A.width*2+10,A.height),'white');t.paste(A,(0,0));t.paste(B,(A.width+10,0));tiles.append(t)
H=max(t.height for t in tiles);Wd=sum(t.width for t in tiles)+20*len(tiles)
o=Image.new('RGB',(Wd,H),'white');x=0
for t in tiles:o.paste(t,(x,0));x+=t.width+20
if o.width>2400:o=o.resize((2400,int(o.height*2400/o.width)))
o.save(out)
