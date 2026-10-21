# 편집 툴용 rig.def.js 한 파일(조각 그림 data URI + 원화 1024 webp = MR_REF_ART) — 편집 툴 파일 수 한도 511 (7 루시아 것 그대로)
# python3 -I pack_editor.py 출력경로   (원본 = ../../rig.json · ../../parts · ../ref512.png)
import base64, io, json, os, sys
from PIL import Image
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = os.path.dirname(S)
rig = json.load(open(os.path.join(R, 'rig.json'))); rid = rig['name']
for k, p in rig['parts'].items():
    if isinstance(p.get('src'), str) and p['src'].startswith('parts/'):
        if os.environ.get('WEBP'):   # 편집 툴 파일 크기 한도(16MB) — 무손실 WebP(픽셀 그대로, PNG 보다 약 30% 작음)
            bio2 = io.BytesIO(); Image.open(os.path.join(R, p['src'])).save(bio2, 'WEBP', lossless=True, method=4); p['src'] = 'data:image/webp;base64,' + base64.b64encode(bio2.getvalue()).decode()
        else: p['src'] = 'data:image/png;base64,' + base64.b64encode(open(os.path.join(R, p['src']), 'rb').read()).decode()
art = Image.open(os.path.join(S, 'ref512.png')).convert('RGBA').resize((1024, 1024), Image.LANCZOS); bio = io.BytesIO(); art.save(bio, 'WEBP', quality=90)
out = ("// 편집기용: " + rid + " rig.json + 조각 그림 + 원화 기준 그림(1024, MR_REF_ART)을 data URI 로 담음 — 편집기 파일 수 한도 511. 원본 = assets/rig/" + rid + "/rig.json\n"
       "window.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_REF_ART=window.MR_REF_ART||{};\n"
       "window.MR_REF_ART['" + rid + "']='data:image/webp;base64," + base64.b64encode(bio.getvalue()).decode() + "';\n"
       "window.MR_RIG_DEFS['" + rid + "']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
os.makedirs(os.path.dirname(os.path.abspath(sys.argv[1])), exist_ok=True); open(sys.argv[1], 'w').write(out); print('packed', rid, rig['version'], len(out) // 1024, 'KB')
