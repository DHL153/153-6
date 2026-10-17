import json,itertools,urllib.parse,math,probe
w=lambda a:(a+180)%360-180
def metr(R):
    o={}
    for s in ['near','far']:
        ks=[w(r[s]['k']) for r in R]
        o[s]=(max(abs(w(ks[i+1]-ks[i])) for i in range(len(ks)-1)),min(ks),sum(k>2 for k in ks),max(math.hypot(r[s]['a'][0]-r[s]['hip'][0],r[s]['a'][1]-r[s]['hip'][1]) for r in R))
    hy=[r['near']['hip'][1] for r in R];hs=max(abs(hy[i+1]-hy[i]) for i in range(len(hy)-1))
    return o,hs,max(hy)-min(hy)
res=[]
for sb,sk,kl,hk in itertools.product([30,45],[0.08,0.12,0.16],[0.5,0.6],[0.3]):
    g={'strideBase':sb,'strideK':sk,'kneeLift':kl,'heelKick':hk}
    o,hs,hr=metr(probe.run('gait='+urllib.parse.quote(json.dumps(g))))
    ks=max(o['near'][0],o['far'][0]);km=min(o['near'][1],o['far'][1]);fl=o['near'][2]+o['far'][2];dm=max(o['near'][3],o['far'][3])
    print(g,'kneeStep',round(ks,1),'kneeMin',round(km,1),'flip',fl,'reach',round(dm,1),'hipStep',round(hs,1),'hipRange',round(hr,1))
