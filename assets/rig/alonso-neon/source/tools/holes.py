# 틈 찾기: holes.py '쿼리' 출력.png — 투명 배경으로 그려 알파 닫힘(closing) − 알파 = 조각 사이 틈(배경이 비치는 곳)
import sys,subprocess,numpy as np,cv2
from PIL import Image
q=sys.argv[1]+'&bg=0';out=sys.argv[2]
import os;subprocess.run(['python3','shot.py',q,out],check=True,capture_output=True,env=dict(os.environ,RAW='1'))
a=np.array(Image.open(out).convert('RGBA'));al=a[...,3].astype(np.uint8)
on=(al>40).astype(np.uint8);cl=cv2.morphologyEx(on,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
weak=(al<200)&(cl>0)   # 닫으면 채워지는데 실제로는 반투명·빈 곳
weak&=cv2.erode(cl,np.ones((5,5),np.uint8))>0   # 바깥 가장자리 제외
ys,xs=np.nonzero(weak);print('holes',len(ys))
v=np.dstack([a[...,:3],np.full(al.shape,255,np.uint8)]);bg=np.full_like(v,255);f=al[...,None]/255.;img=(a[...,:3]*f+255*(1-f)).astype(np.uint8)
img[weak]=(255,0,255);Image.fromarray(img).save(out.replace('.png','_holes.png'))
if len(ys): print('bbox',xs.min(),ys.min(),xs.max(),ys.max())
