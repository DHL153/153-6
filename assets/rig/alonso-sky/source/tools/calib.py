# 칼 손잡이 키 보정: 실제 G(프로브)와 키(세계 좌표)의 차이를 gripFix에 누적 → 다시 빌드. 2~3번 반복
import json,subprocess,os
H=os.path.dirname(os.path.abspath(__file__));KP=os.path.join(H,'..','attack_keys.json')
for it in range(3):
    subprocess.run(['python3','-I','build_sky.py'],cwd=os.path.join(H,'..'),check=True,capture_output=True)
    subprocess.run(['python3','atkprobe.py'],cwd=H,check=True,capture_output=True)
    P=json.load(open('/tmp/claude-0/-home-claude/c76b6f25-7843-5cc6-b177-7797dcb3a853/scratchpad/atkp.json'))
    K=json.load(open(KP));F=K.setdefault('gripFix',{});worst=0
    for t,X,Y,A,*e in K['grip']:
        if not (0.25 <= t <= 0.66) or t in (0.41,):continue   # 섞는 구간(w<1)·아주 빠른 키는 제외
        r=min((r for r in P if r[0] is not None),key=lambda r:abs(r[0]-t))
        if abs(r[0]-t)>0.012 or not r[7]:continue
        dx,dy=X-r[7][0],Y-r[7][1];f=F.get(str(t),[0,0]);F[str(t)]=[round(f[0]+dx,1),round(f[1]+dy,1)];worst=max(worst,abs(dx),abs(dy))
    json.dump(K,open(KP,'w'),ensure_ascii=False,indent=1);print('iter',it,'worst',round(worst,1))
subprocess.run(['python3','-I','build_sky.py'],cwd=os.path.join(H,'..'),check=True,capture_output=True)
