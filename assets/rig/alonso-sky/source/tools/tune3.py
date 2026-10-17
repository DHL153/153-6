import json,itertools,urllib.parse,math,probe
w=lambda a:(a+180)%360-180
def metr(R):
    o={}
    for s in ['near','far']:
        ks=[w(r[s]['k']) for r in R];st=[r[s]['a'][1]<-67.5 for r in R]
        ground=sum(1 for r in R if r[s]['a'][1]>-67.6)/len(R)
        land=[]  # 착지 때 발 x - 엉덩이 x
        for i in range(1,len(R)):
            if R[i][s]['a'][1]>-67.6 and R[i-1][s]['a'][1]<=-67.6: land.append(round(R[i][s]['a'][0]-R[i][s]['hip'][0],1))
        o[s]=dict(step=round(max(abs(w(ks[i+1]-ks[i])) for i in range(len(ks)-1)),1),kmin=round(min(ks),1),ground=round(ground,2),land=land[:2])
    hy=[r['near']['hip'][1] for r in R]
    return o,round(max(abs(hy[i+1]-hy[i]) for i in range(len(hy)-1)),1)
for hx,(sb,sk) in itertools.product([(-54,46),(-34,30),(-20,18)],[(30,.12),(45,.12)]):
    g={'strideBase':sb,'strideK':sk,'kneeLift':.5,'heelKick':.3}
    L={'near':{'hipX':hx[0]},'far':{'hipX':hx[1]}}
    o,hs=metr(probe.run('gait='+urllib.parse.quote(json.dumps(g))+'&legs='+urllib.parse.quote(json.dumps(L))))
    print(hx,sb,sk,'hipStep',hs,o)
