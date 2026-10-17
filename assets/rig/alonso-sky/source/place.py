# 조각 놓기: 조각 점 p → 원화(512) 점 r, 배율 s(512 기준), 회전 deg. 결과 행렬(ref1024)을 work/place.json 에 저장 + 겹침 그림
import sys,json,math,numpy as np
sys.argv=[a for a in sys.argv]
from ecc import overlay
n=sys.argv[1];px,py,rx,ry,s,deg=map(float,sys.argv[2:8])
a=math.radians(deg);c,sn=math.cos(a)*s*2,math.sin(a)*s*2;M=np.array([[c,-sn,0],[sn,c,0]],np.float32);M[:,2]=np.array([rx*2,ry*2])-M[:,:2]@np.array([px,py])
try:o=json.load(open('work/place.json'))
except:o={}
o[n]={'M':M.tolist(),'p':[px,py],'r':[rx,ry],'s':s,'deg':deg};json.dump(o,open('work/place.json','w'),indent=1)
overlay(n,M,'/tmp/claude-0/-home-claude/c76b6f25-7843-5cc6-b177-7797dcb3a853/scratchpad/pl_'+n+'.png');print(n,'ok')
