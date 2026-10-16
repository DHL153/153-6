"""알론소 리그 조립: 조각 배치(매칭 행렬 또는 두 점 대응) → rig.json + parts/.  python3 -I build_alonso.py WORK OUTDIR"""
import json,math,os,shutil,sys
import numpy as np
from PIL import Image
W,OUT=sys.argv[1],sys.argv[2];os.makedirs(os.path.join(OUT,'parts'),exist_ok=True)
J=lambda f:os.path.join(W,f)
match=json.load(open(J('match_result.json')))
O=np.array([720.,955.])                      # 뿌리(발이 땅에 닿는 점) = 기준 그림(1024) 좌표
def sim2(p1,p2,r1,r2):                         # 두 점 대응 → 닮음변환 (조각 px → 기준 px)
    p1,p2,r1,r2=map(np.array,(p1,p2,r1,r2));vp=p2-p1;vr=r2-r1
    s=np.linalg.norm(vr)/np.linalg.norm(vp);phi=math.atan2(vr[1],vr[0])-math.atan2(vp[1],vp[0])
    c,sn=math.cos(phi)*s,math.sin(phi)*s;M=np.array([[c,-sn,0],[sn,c,0]]);M[:,2]=r1-M[:,:2]@p1;return M
def fromMatch(name):return np.array(match[name]['M'])
def info(M):s=math.hypot(M[0,0],M[1,0]);phi=math.atan2(M[1,0],M[0,0]);return s,phi
inv=lambda M,r:np.linalg.solve(M[:,:2],np.array(r)-M[:,2])
apply=lambda M,p:M[:,:2]@np.array(p)+M[:,2]
P=lambda f:J(f)
# ---- 관절(기준 그림 좌표) ----
H=(720,690);NECK=(728,470)
SH_F=(598,492);EL_F=(530,566);WR_F=(514,648);GRIP=(532,686);POMMEL=(600,628);TIP=(16,972)   # 칼 팔(앞)
SH_N=(828,500);EL_N=(868,598);WR_N=(895,690)                                                  # 주먹 팔(뒤)
parts={}   # name -> dict(file, M, pivotRef)
parts['torso']=dict(file='parts1A/A_04.png',M=fromMatch('torso'),at=H)
parts['head']=dict(file='parts1A/A_01.png',M=fromMatch('head'),at=NECK)
parts['skirt']=dict(file='parts1B/B_02.png',M=fromMatch('hem'),at=(720,628))
parts['scarf']=dict(file='parts1A/A_05.png',M=sim2((10,40),(240,95),(640,450),(812,490)),at=(728,470))
parts['cape']=dict(file='parts1A/A_02.png',M=sim2((65,12),(80,350),(700,452),(640,690)),at=(700,452))
parts['pauldron']=dict(file='parts1A/A_07.png',M=sim2((10,60),(170,60),(792,482),(858,505)),at=SH_N)          # 뒤 어깨 갑옷 (자유 팔)
parts['armU']=dict(file='parts1A/A_09.png',M=sim2((45,25),(115,172),SH_N,EL_N),at=SH_N)
parts['armL']=dict(file='parts1A/A_11.png',M=sim2((40,22),(100,182),EL_N,WR_N),at=EL_N)
parts['fistN']=dict(file='parts1A/A_15.png',M=sim2((40,8),(95,8),(874,684),(918,690)),at=WR_N)
parts['armF']=dict(file='parts1A/A_08.png',M=sim2((105,25),(40,172),SH_F,EL_F),at=SH_F)
parts['foreF']=dict(file='parts1A/A_10.png',M=sim2((55,22),(108,182),EL_F,WR_F),at=EL_F)
parts['fistF']=dict(file='parts1A/A_16.png',M=sim2((35,10),(70,140),(500,646),(548,722)),at=WR_F)
parts['weapon']=dict(file='parts1B/B_01.png',M=sim2((138,910),(145,5),POMMEL,TIP),at=GRIP)
parts['pauldronF']=dict(file='parts1A/A_06.png',M=fromMatch('pauldronA'),at=SH_F)
bones=[('root',None),('hip','root'),('torso','hip'),('skirt','hip'),('cape','torso'),('scarf','torso'),('head','torso'),
       ('armU','torso'),('armL','armU'),('fistN','armL'),('pauldron','torso'),
       ('armF','torso'),('foreF','armF'),('fistF','foreF'),('weapon','fistF'),('pauldronF','armF')]
world={'root':(np.array(O),0.0),'hip':(np.array(H,float),0.0)}
def_parts={};out_bones=[]
for name,parent in bones:
    if name in parts:
        p=parts[name];s,phi=info(p['M']);piv=inv(p['M'],p['at']);world[name]=(np.array(p['at'],float),phi)
        fn=name+'.png';shutil.copy(J(p['file']),os.path.join(OUT,'parts',fn))
        def_parts[name]={'src':'parts/'+fn,'pivot':[round(float(piv[0]),1),round(float(piv[1]),1)],'scale':round(s,4)}
    if parent is None:out_bones.append({'name':'root','parent':None,'pos':[0,0]});continue
    (pw,pa),(cw,ca)=world[parent],world[name]
    d=cw-pw;c,sn=math.cos(-pa),math.sin(-pa);loc=[c*d[0]-sn*d[1],sn*d[0]+c*d[1]]
    b={'name':name,'parent':parent,'pos':[round(loc[0],1),round(loc[1],1)]}
    if abs(ca-pa)>1e-4:b['rot']=round(ca-pa,4)
    if name in parts:b['part']=name
    out_bones.append(b)
# ---- 다리 (IK) ----
for n,f in [('thigh','parts1B/B_03.png'),('shin','parts1B/B_04.png'),('boot','parts1B/B_05.png'),('bootB','parts1B/B_06.png')]:
    shutil.copy(J(f),os.path.join(OUT,'parts',n+'.png'))
def_parts['thigh']={'src':'parts/thigh.png','pivot':[160,30],'scale':1}
def_parts['shin']={'src':'parts/shin.png','pivot':[130,30],'scale':1}
def_parts['boot']={'src':'parts/boot.png','pivot':[62,40],'scale':0.53}
def_parts['bootB']={'src':'parts/bootB.png','pivot':[62,40],'scale':0.53}
hipLegY=0;thigh=86;shin=104
legs={'hip':[0,18],'thigh':thigh,'shin':shin,
      'thighImg':{'part':'thigh','a':[160,30],'b':[115,318],'w':1.25},
      'shinImg':{'part':'shin','a':[128,28],'b':[140,282],'w':0.85},
      'boot':{'part':'boot','back':'bootB','sole':[[-58,150],[-40,160],[150,160],[190,148]],'ankleRange':[-0.45,0.4]},
      'near':{'x':-34,'shade':0},'far':{'x':40,'shade':0.3}}
draw=['cape','armU','armL','fistN','pauldron','legFar','legNear','torso','skirt','head','scarf','armF','foreF','weapon','fistF','pauldronF']
G=lambda n:world[n][0]
gtip=apply(parts['weapon']['M'],(145,5))
gp=inv(parts['weapon']['M'],TIP)
def_parts['weapon']['tips']=[[round(float(gp[0])-20,1),round(float(gp[1])+8,1)],[round(float(gp[0])+20,1),round(float(gp[1])+8,1)]]
rig={'name':'alonso-rust','version':1,'units':'rig px (reference x2)','refOrigin':[O[0]/2,O[1]/2],'refScale':2.0,'refLift':0,
     'parts':def_parts,'bones':out_bones,'legs':legs,'draw':draw,'hidden':[],'faces':{},
     'metrics':{'bodyHeight':923,'heightWithWeapon':923,'note':'rig units; head top (hair) to sole, weapon excluded'},
     'armPhase':0.5,'ui':{'attack':'smash','touch':'hop'},
     'note':'1번 알론소. 대검을 쥔 팔이 화면 앞쪽(armF 사슬), 주먹 팔이 뒤쪽(armU/armL). armPhase .5 = 자유 팔 흔들기를 반 박자 밀어 같은 쪽 팔다리가 함께 나가지 않게'}
json.dump(rig,open(os.path.join(OUT,'rig.json'),'w'),ensure_ascii=False,indent=1)
print('ok',len(def_parts),'parts')
for n in ['torso','head','armF','weapon']:print(n,def_parts[n])
