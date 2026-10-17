import json,itertools,urllib.parse,sys
sys.path.insert(0,'.')
from playwright.sync_api import sync_playwright
import probe
w=lambda a:(a+180)%360-180
def score(R):
    bad=0;st={}
    for s in ['near','far']:
        ks=[w(r[s]['k']) for r in R];fs=[r[s]['f'] for r in R]
        flip=sum(1 for k in ks if k>2)        # 무릎이 반대로 꺾임
        kj=max(abs(w(ks[i+1]-ks[i])) for i in range(len(ks)-1));fj=max(abs(fs[i+1]-fs[i]) for i in range(len(fs)-1))
        lift=min(r[s]['a'][1] for r in R)
        st[s]=dict(flip=flip,kneeStep=round(kj,1),footStep=round(fj,1),kneeMin=round(min(ks),1),lift=round(lift,1))
    return st
cands=[]
for kl,hk,sb in itertools.product([0.45,0.6,0.75],[0.25,0.4,0.55],[50,70]):
    g={'kneeLift':kl,'heelKick':hk,'strideBase':sb}
    R=probe.run('gait='+urllib.parse.quote(json.dumps(g)));s=score(R)
    tot=s['near']['flip']+s['far']['flip'];mk=max(s['near']['kneeStep'],s['far']['kneeStep']);mf=max(s['near']['footStep'],s['far']['footStep'])
    cands.append((tot,mk,mf,g,s));print(g,tot,mk,mf,s['near']['kneeMin'],s['far']['kneeMin'],s['near']['lift'])
