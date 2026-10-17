import json,sys,math,numpy as np
exec(open('solve2.py').read().split("if __name__")[0])
FISTS['cFist']=dict(grip=(205,80),wrist=(180,82),sd=(-0.49,-0.87),k=1.24,c=-61)
FISTS['cArt']['sd']=(-0.93,-0.37)
def solveL(t,f,which,G,a,s,pref,Ls=(95,)):
    global L
    best=None
    for l in Ls:
        L=l;r=solve(t,f,which,G,a,s,pref)
        if best is None or r[0]<best[0]:best=r+(l,)
    L=95;return best
def scan(t,a,cf,nf,cpref,npref,GX,GY,SF,LsC=(95,115),face=None,extra=None):
    res=[]
    for gx in GX:
        for gy in GY:
            for sf in SF:
                c=solveL(t,cf,'carry',[gx,gy],a,0,cpref,LsC);n=solveL(t,nf,'near',[gx,gy],a,sf,npref)
                cost=c[0]+n[0]
                if extra:cost+=extra(c,n,gx,gy,sf)
                res.append((round(cost,2),gx,gy,sf,c,n))
    res.sort(key=lambda r:r[0]);return res[:3]
