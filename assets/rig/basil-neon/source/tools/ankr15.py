# 쉴 때(엔진) 쪽별 정강이-부츠 각 r = atan2(발목-무릎) − 90° − 부츠 각 → work/ankr.json (build_basil15 가 발목 범위 가운데로 씀)
# 사용: ANK_MEASURE=1 ANK=9 python3 build_basil15.py && python3 tools/ankr15.py && python3 build_basil15.py
import json,os,subprocess,sys
H=os.path.dirname(os.path.abspath(__file__))
js="(()=>{const P=window.__rig.legPose,o={};for(const s of ['near','far']){const p=P[s];let r=Math.atan2(p.ankle[1]-p.knee[1],p.ankle[0]-p.knee[0])-Math.PI/2-p.foot;r=Math.atan2(Math.sin(r),Math.cos(r));o[s]=+r.toFixed(4)}return JSON.stringify(o)})()"
out=subprocess.run(['python3',os.path.join(H,'dbg.py'),'mode=idle&pre=60',js],capture_output=True,text=True).stdout.strip()
print(out);json.dump(json.loads(out),open(os.path.join(H,'..','work','ankr.json'),'w'))
