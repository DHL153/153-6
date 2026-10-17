# 쥔 팔 조각 각도(rel) 풀기: 키 시각의 어깨(프로브) · 손잡이 자리 · 칼 각도에서 윗팔 길이가 맞는 팔꿈치를 찾고, 그 팔꿈치가 나오는 rel 각도를 계산
import json,math,sys,numpy as np
K=json.load(open('../attack_keys.json'));P=json.load(open('/tmp/claude-0/-home-claude/c76b6f25-7843-5cc6-b177-7797dcb3a853/scratchpad/atkp.json'))
FIST_S=1.24;L=95;INSET=10
FISTS={'gNv':dict(grip=(60,80),sd=(0,-1),wrist=(10,88)),'gFv':dict(grip=(46,80),sd=(0,-1),wrist=(116,90)),'gFvM':dict(grip=(77,80),sd=(0,-1),wrist=(7,90)),'gNhM':dict(grip=(114,52),sd=(1,0),wrist=(24,48))}
LU={'carry':127.0,'near':97.0}
def v_of(fist,rel):
    F=FISTS[fist];g=np.array(F['grip'],float);w=np.array(F['wrist'],float);asd=math.atan2(F['sd'][1],F['sd'][0])
    d=np.array([math.cos(asd+math.radians(rel)),math.sin(asd+math.radians(rel))]);return (w-g)*FIST_S+d*(L-INSET),asd
def at(t):
    return min(P,key=lambda r:abs((r[0] if r[0] is not None else 9)-t))
def solve(t,fist,which,G,a,s,pref):
    r=at(t);S=np.array(r[9] if which=='carry' else r[10],float)
    U=np.array([math.cos(a),math.sin(a)]);Gs=np.array(G,float)+U*s
    best=None
    for rel in range(-180,180,1):
        v,asd=v_of(fist,rel);rho=a-asd;R=np.array([[math.cos(rho),-math.sin(rho)],[math.sin(rho),math.cos(rho)]]);E=Gs+R@v
        dl=np.linalg.norm(E-S)/LU[which]
        # bend: 팔꿈치가 어깨-주먹 선의 어느 쪽(+1 = 화면 아래/바깥)
        mid=(Gs+S)/2;cost=abs(dl-1.0)+(0 if np.dot(E-mid,np.array(pref,float))>0 else 1)
        if best is None or cost<best[0]:best=(cost,rel,round(dl,2),E.round(0).tolist(),S.tolist())
    return best
for name,t,fist,which,G,a,s,pref in json.load(open(sys.argv[1])):
    print(name,t,solve(t,fist,which,G,a,s,pref))
