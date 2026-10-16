"""니콜 스카이 리그 조립. python3 -I build_sky.py WORK OUTDIR"""
import json,math,os,shutil,sys
import numpy as np
from PIL import Image
W,OUT=sys.argv[1],sys.argv[2];os.makedirs(os.path.join(OUT,'parts'),exist_ok=True)
J=lambda f:os.path.join(W,f)
match=json.load(open(J('match_result.json')))
O=np.array([500.,950.])
def sim2(p1,p2,r1,r2,s=None):
    p1,p2,r1,r2=map(lambda v:np.array(v,float),(p1,p2,r1,r2));vp=p2-p1;vr=r2-r1
    if s is None:s=np.linalg.norm(vr)/np.linalg.norm(vp)
    phi=math.atan2(vr[1],vr[0])-math.atan2(vp[1],vp[0]);c,sn=math.cos(phi)*s,math.sin(phi)*s
    M=np.array([[c,-sn,0],[sn,c,0]]);M[:,2]=r1-M[:,:2]@p1;return M
info=lambda M:(math.hypot(M[0,0],M[1,0]),math.atan2(M[1,0],M[0,0]))
inv=lambda M,r:np.linalg.solve(M[:,:2],np.array(r,float)-M[:,2])
app=lambda M,p:M[:,:2]@np.array(p,float)+M[:,2]
fm=lambda n:np.array(match[n]['M'])
A='parts_s1A_a/A_';B='parts_s1B/B_'
# 비율을 바꿔 다시 그린 조각 (치마·망토: 시트가 원본보다 길쭉함)
def refit(src,dst,size):
    Image.open(J(src)).resize(size,Image.LANCZOS).save(os.path.join(OUT,'parts',dst));return dst
H=(505,645);NECK=(505,478)
SA=0.55   # 팔·손 그림 배율
SH_F=(565,530);EL_F=(610,615);SH_N=(425,528);EL_N=(390,598)
parts={}
parts['torso']=dict(file=A+'03.png',M=fm('torso'),at=H)
parts['head']=dict(file=A+'01.png',M=fm('head'),at=NECK)
parts['pony']=dict(file=A+'02.png',M=fm('pony'),at=(365,380))
parts['pauldron']=dict(file=A+'04.png',M=fm('pauldronN'),at=SH_N)
parts['pauldronF']=dict(file=A+'05.png',M=sim2((40,60),(170,120),(540,505),(600,545)),at=SH_F)
# 팔 (먼 팔 = 창 앞손, 가까운 팔 = 창 뒷손)
parts['armF']=dict(file=A+'07.png',M=sim2((45,30),(140,195),SH_F,EL_F,SA),at=SH_F)
parts['foreF']=dict(file=A+'09.png',M=sim2((40,40),(115,205),EL_F,(668,555),SA),at=EL_F)
parts['armU']=dict(file=A+'06.png',M=sim2((115,30),(40,195),SH_N,EL_N,SA),at=SH_N)
parts['armL']=dict(file=A+'08.png',M=sim2((45,45),(130,210),EL_N,(402,672),SA),at=EL_N)
WR_F=tuple(app(parts['foreF']['M'],(115,205)));WR_N=tuple(app(parts['armL']['M'],(130,210)))
parts['fistF']=dict(file=A+'13.png',M=sim2((40,30),(110,30),(WR_F[0]-8,WR_F[1]-14),(WR_F[0]+28,WR_F[1]-40),SA),at=WR_F)
parts['fistN']=dict(file=A+'12.png',M=sim2((30,30),(110,30),(WR_N[0]-24,WR_N[1]-6),(WR_N[0]+20,WR_N[1]-20),SA),at=WR_N)
GRIP=(694,530);TIP=(1008,318);BUTT=(108,858)
parts['weapon']=dict(file=B+'01.png',M=sim2((61,8),(61,948),TIP,BUTT),at=GRIP)
bones=[('root',None),('hip','root'),('torso','hip'),('skirt','hip'),('cape','torso'),('head','torso'),('pony','head'),
       ('armU','torso'),('armL','armU'),('fistN','armL'),('pauldron','torso'),
       ('armF','torso'),('foreF','armF'),('fistF','foreF'),('weapon','fistF'),('pauldronF','torso')]
world={'root':(O,0.0),'hip':(np.array(H,float),0.0)}
dp={};ob=[]
# 치마: 원본 상자 (262,640)-(742,945)에 맞춰 다시 그림, 축 = 허리 가운데
sk=refit(B+'03.png','skirt.png',(480,305));dp['skirt']={'src':'parts/skirt.png','pivot':[250,6],'scale':1.0,'mesh':{'cols':8,'rows':9}}
world['skirt']=(np.array((512,646.)),0.0)
cp=refit(B+'02.png','cape.png',(430,250));dp['cape']={'src':'parts/cape.png','pivot':[400,12],'scale':1.0,'mesh':{'cols':7,'rows':7}}
world['cape']=(np.array((455,528.)),0.0)
for name,parent in bones:
    if name in parts:
        p=parts[name];s,phi=info(p['M']);piv=inv(p['M'],p['at']);world[name]=(np.array(p['at'],float),phi)
        fn=name+'.png';shutil.copy(J(p['file']),os.path.join(OUT,'parts',fn))
        dp[name]={'src':'parts/'+fn,'pivot':[round(float(piv[0]),1),round(float(piv[1]),1)],'scale':round(s,4)}
    if parent is None:ob.append({'name':'root','parent':None,'pos':[0,0]});continue
    (pw,pa),(cw,ca)=world[parent],world[name];d=cw-pw;c,sn=math.cos(-pa),math.sin(-pa)
    b={'name':name,'parent':parent,'pos':[round(c*d[0]-sn*d[1],1),round(sn*d[0]+c*d[1],1)]}
    if abs(ca-pa)>1e-4:b['rot']=round(ca-pa,4)
    if name in dp:b['part']=name
    ob.append(b)
tp=inv(parts['weapon']['M'],TIP);dp['weapon']['tips']=[[round(float(tp[0])-14,1),round(float(tp[1])+10,1)],[round(float(tp[0])+14,1),round(float(tp[1])+10,1)]]
for n,f in [('thigh','04'),('shin','06'),('boot','05'),('bootB','07')]:shutil.copy(J(B+f+'.png'),os.path.join(OUT,'parts',n+'.png'))
dp['thigh']={'src':'parts/thigh.png','pivot':[55,20],'scale':1};dp['shin']={'src':'parts/shin.png','pivot':[45,15],'scale':1}
dp['boot']={'src':'parts/boot.png','pivot':[40,30],'scale':0.62};dp['bootB']={'src':'parts/bootB.png','pivot':[40,30],'scale':0.62}
legs={'hip':[0,20],'thigh':120,'shin':118,'thighImg':{'part':'thigh','a':[55,20],'b':[55,165],'w':1.0},'shinImg':{'part':'shin','a':[45,15],'b':[45,170],'w':0.95},
      'boot':{'part':'boot','back':'bootB','sole':[[-28,100],[-20,104],[110,104],[128,94]],'ankleRange':[-0.45,0.4]},
      'near':{'x':-60,'shade':0},'far':{'x':55,'shade':0.3}}
draw=['cape','armF','foreF','pauldronF','legFar','legNear','skirt','torso','pony','head','weapon','fistF','armU','armL','fistN','pauldron']
ROOM=dict(TOP=0.24,FOOT=0.94)
rig={'name':'nicole-sky','version':1,'units':'rig px (reference x2)','refOrigin':[O[0]/2,O[1]/2],'refScale':2.0,'refLift':0,
 'parts':dp,'bones':ob,'legs':legs,'draw':draw,'drawSmash':draw,'hidden':[],'faces':{},
 'metrics':{'bodyHeight':round((ROOM['FOOT']-ROOM['TOP'])*1024),'note':'(MRRoomFit FOOT-TOP)*1024'},
 'gait':{'stance':0.31,'strideBase':78,'strideK':0.21,'hipBase':5,'bob':10,'lean':0.28,'armSwing':0.68,'elbowRun':1.5,'kneeLift':1.12,'heelKick':1.08,'dropCap':46},
 'hemRun':{'lift':34,'knee':1.6,'heel':1.1,'reach':0.5},
 'twoHand':{'gap':336},'smashHand2':336,'smashShoulder':[0,0],'cutHold':0.42,
 'ui':{'attack':'spearThrust','touch':'hop'},'note':'28번 니콜 스카이. 먼 팔 = 창 앞손(몸 뒤), 가까운 팔 = 창 뒷손(몸 앞). 평소에도 두 손으로 창을 듦(twoHand)'}
json.dump(rig,open(os.path.join(OUT,'rig.json'),'w'),ensure_ascii=False,indent=1);print('ok',len(dp))
