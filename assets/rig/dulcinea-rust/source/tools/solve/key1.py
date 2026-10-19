from arm import *
import sys
def ev(G, a, sF, SN, SF):
    near['s'] = sF; f, n = both(G, a, SN, SF); near['s'] = 82; return f, n
def show(G, a, sF, SN, SF):
    f, n = ev(G, a, sF, SN, SF)
    s = lambda c: f"ok b{c['bend']:.0f} cr{c['cross']:.2f}" if c['ok'] else f"GAP {c['gap']:.0f}"
    return f'far {s(f)} | near {s(n)}'
def best(a, sF, SN, SF, pref, lim=35, farOnly=False, w=.3, top=4, sas=None):
    out = []
    for aa in (sas or [a]):
        for x in range(-260, 260, 4):
            for y in range(-420, 120, 4):
                f, n = ev((x, y), aa, sF, SN, SF)
                if not f['ok'] or f['cross'] > .15 or abs(f['bend']) > lim: continue
                if not farOnly and (not n['ok'] or n['cross'] > .15 or abs(n['bend']) > lim): continue
                m = abs(f['bend']) if farOnly else max(abs(f['bend']), abs(n['bend']))
                out.append((round(m + w * math.hypot(x - pref[0], y - pref[1])), aa, (x, y), show((x, y), aa, sF, SN, SF)))
    out.sort(key=lambda r: r[0]); return out[:top]
