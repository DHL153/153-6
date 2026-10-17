"""배치 확인: 조각을 찾은 변환(M)으로 ref1024 위에 그려 원화와 번갈아 비교.  python3 -I place_view.py out.png name ..."""
import json, sys, numpy as np, cv2
from PIL import Image
S = json.load(open('sift_result.json')); F = json.load(open('fix_result.json'))
ref = np.asarray(Image.open('ref1024.png').convert('RGBA')).astype(np.float32)
out = sys.argv[1]; names = sys.argv[2:]
canvas = np.zeros_like(ref); tiles = []
for n in names:
    r = F.get(n) or S.get(n); M = np.array(r['M'], np.float32); im = np.asarray(Image.open(r['file']).convert('RGBA')).astype(np.float32)
    w = cv2.warpAffine(im, M, (1024, 1024), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)); a = w[..., 3:4] / 255
    canvas = canvas * (1 - a) + w * a
bg = np.full_like(ref, 255); bg[..., :3] = [235, 230, 215]
A = ref[..., 3:4] / 255; refc = bg * (1 - A) + ref * A; refc[..., 3] = 255
B = canvas[..., 3:4] / 255; plc = bg * (1 - B) + canvas * B; plc[..., 3] = 255
diff = refc.copy(); m = canvas[..., 3] > 128; diff[m, :3] = diff[m, :3] * .45 + np.array([40, 90, 255]) * .55
import os
cr = [int(v) for v in os.environ.get('CROP', '0,0,1024,1024').split(',')]; x0, y0, x1, y1 = cr
row = np.concatenate([refc[y0:y1, x0:x1], plc[y0:y1, x0:x1], diff[y0:y1, x0:x1]], 1)[..., :3].astype(np.uint8)
z = min(1800 / row.shape[1], 900 / row.shape[0]); Image.fromarray(row).resize((int(row.shape[1] * z), int(row.shape[0] * z)), Image.LANCZOS).save(out); print(out)
