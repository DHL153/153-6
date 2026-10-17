# 쥔 팔 조각 각도 풀기 v2: 주먹마다 '자연스러운 손목 꺾임 범위'(중심 ±40°) 안에서만 찾음 + 기본 어깨(늘이기 전) 사용
#  입력 JSON: [[이름, 시각, 주먹, 'carry'|'near', [Gx,Gy], 칼각, 손잡이위치 s, 팔꿈치쪽 [x,y]], ...]
import json,math,sys,numpy as np
P=json.load(open('/tmp/claude-0/-home-claude/c76b6f25-7843-5cc6-b177-7797dcb3a853/scratchpad/atkp.json'))
UAX=None
FISTS={  # grip·wrist: 그림 px, sd: 칼끝 방향(그림), k: 그림 px → 리그 단위, c: 자연스러운 손목→팔꿈치 각도(칼끝 방향 기준, 시계 +)
 'cArt':dict(grip=(37,37),wrist=(25,86),sd=(-0.93,-0.37),k=2.0,c=-102),
 'gNv':dict(grip=(60,80),wrist=(10,88),sd=(0,-1),k=1.24,c=-90),
 'gNh':dict(grip=(85,52),wrist=(175,48),sd=(-1,0),k=1.24,c=180),
 'gFv':dict(grip=(46,80),wrist=(116,90),sd=(0,-1),k=1.24,c=90),
 'gF45':dict(grip=(68,68),wrist=(122,72),sd=(-0.707,-0.707),k=1.24,c=145),
}
L=95;INSET=10;LU={'carry':127.0,'near':97.0}
def v_of(f,rel):
    F=FISTS[f];g=np.array(F['grip'],float);w=np.array(F['wrist'],float);sd=np.array(F['sd'],float);sd/=np.linalg.norm(sd);asd=math.atan2(sd[1],sd[0])
    d=np.array([math.cos(asd+math.radians(rel)),math.sin(asd+math.radians(rel))]);return (w-g)*F['k']+d*(L-INSET),asd
def at(t): return min(P,key=lambda r:abs((r[0] if r[0] is not None else 9)-t))
def solve(t,f,which,G,a,s,pref,span=40):
    r=at(t);S=np.array(r[9] if which=='carry' else r[10],float);U=np.array([math.cos(a),math.sin(a)]);Gs=np.array(G,float)+U*s
    best=None;c=FISTS[f]['c']
    for rel in range(c-span,c+span+1):
        v,asd=v_of(f,rel);rho=a-asd;R=np.array([[math.cos(rho),-math.sin(rho)],[math.sin(rho),math.cos(rho)]]);E=Gs+R@v
        dl=np.linalg.norm(E-S)/LU[which];mid=(Gs+S)/2;side=np.dot(E-mid,np.array(pref,float))
        cost=abs(dl-1.0)+(0 if side>0 else 0.5)+abs(rel-c)/400
        if best is None or cost<best[0]:best=(round(cost,2),((rel+180)%360)-180,round(dl,2),E.round(0).tolist(),Gs.round(0).tolist(),S.tolist())
    return best
if __name__=='__main__':
    for row in json.load(open(sys.argv[1])):
        print(row[0],row[2],solve(*row[1:]))
