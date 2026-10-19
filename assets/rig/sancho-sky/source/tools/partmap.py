import json, numpy as np, cv2, sys
from PIL import Image, ImageDraw
import os; S=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
P=json.load(open(S+'polys.json')); RA=np.array(Image.open(S+'ref512.png').convert('RGBA')); AL=RA[...,3]>0
def pm(n):
    m=Image.new('L',(512,512),0); ImageDraw.Draw(m).polygon([tuple(p) for p in P[n]],fill=255); return np.array(m)>0
ero=lambda m,r: cv2.erode(m.astype(np.uint8),np.ones((2*r+1,2*r+1),np.uint8))>0
mk={n:pm(n) for n in P if not n.startswith('_')}
und=lambda m,*tops: m & ~np.logical_or.reduce([ero(t,3) for t in tops])
A={}
A['farFore']=mk['farFore']; A['nearFore']=und(mk['nearFore'],A['farFore']); A['nearUp']=und(mk['nearUp'],mk['nearFore'],A['farFore'])
A['pauldron']=und(mk['pauldron'],A['farFore']); A['farUp']=und(mk['farUp'],mk['pauldron'],A['farFore'])
ARMS=np.logical_or.reduce(list(A.values()))
A['head']=mk['head']&~ARMS; A['torso']=mk['torso']&~ARMS&~mk['head']; A['hips']=mk['hips']&~A['torso']&~ARMS
for n in ['thighN','shinN','bootN','thighF','shinF','bootF']: A[n]=mk[n]&~A['hips']
cols={'head':(255,220,0),'nearFore':(255,0,0),'nearUp':(255,120,0),'farFore':(0,90,255),'farUp':(0,200,255),'pauldron':(160,0,255),'torso':(0,200,0),'hips':(120,120,0),
      'thighN':(255,0,180),'shinN':(255,100,220),'bootN':(150,0,80),'thighF':(0,160,160),'shinF':(80,220,200),'bootF':(0,90,90)}
o=RA[...,:3].astype(float)*0.45+255*0.55
for n,m in A.items():
    mm=m&AL; o[mm]=o[mm]*0.35+np.array(cols[n])*0.65
cov=np.zeros(AL.shape,bool)
for m in A.values(): cov|=m
gap=(RA[...,3]>200)&~cov; o[gap]=(0,0,0)
print('uncovered opaque px', int(gap.sum()))
Image.fromarray(o.astype(np.uint8)).crop((160,140,420,500)).resize((780,1080),Image.NEAREST).save(sys.argv[1])
