# 내려찍기 자세 풀이(10-19 15:15): 원화 팔 길이·공 손목으로 G·자루 각도를 고름 — cd tools/solve && python3 -c "from ball import *; print(srch(26,(107,-79),(-34,-157),(40,-6),[.3,.4],ground=True))"
from key1 import *
def face_hit(G, a, sF):
    U = np.array([math.cos(a), math.sin(a)]); pts = [np.array(G, float), np.array(G, float) + U * sF]
    return sum(1 for p in pts if -60 < p[0] < 140 and -340 < p[1] < -130)
def srch(sF, SN, SF, pref, sas, lim=60, top=4, ground=False, face=False, wp=.3, xr=(-260, 260), yr=(-420, 160)):
    out = []
    for a in sas:
        for x in range(xr[0], xr[1], 4):
            for y in range(yr[0], yr[1], 4):
                if face and face_hit((x, y), a, sF): continue
                f, n = ev((x, y), a, sF, SN, SF)
                if not (f['ok'] and n['ok']) or f['cross'] > .15 or n['cross'] > .15: continue
                m = max(abs(f['bend']), abs(n['bend']))
                if m > lim: continue
                c = m * .5 + wp * math.hypot(x - pref[0], y - pref[1]) + (abs(y + 340 * math.sin(a) - 128) * .5 if ground else 0)
                out.append((round(c), a, (x, y), show((x, y), a, sF, SN, SF)))
    out.sort(key=lambda r: r[0]); return out[:top]
def rot(p, t): return (p[0]*math.cos(t) - p[1]*math.sin(t), p[0]*math.sin(t) + p[1]*math.cos(t))
