# 24 스카이 로시 조각 시트(parts1_1133) → pieces/NN_이름.png (마젠타 → 투명, 가장자리 번짐은 외곽선 검정으로)  python3 -I tools/cut14.py
import os, json, numpy as np
from PIL import Image
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Sh = np.array(Image.open(os.path.join(H, 'sheets/parts1_1133.png')).convert('RGB')).astype(np.float32); cells = json.load(open(os.path.join(H, 'work/cells24.json')))
names = ['pose', 'head', 'happy', 'angry', 'sad', 'surprised', 'shout', 'focus', 'wink', 'half', 'closed', 'upperN', 'upperF', 'thigh', 'shin', 'boot', 'hose', 'pack', 'gun']
for i, (n, (x, y, w, h)) in enumerate(zip(names, cells)):
    m = 12; C = Sh[max(0, y - m):y + h + m, max(0, x - m):x + w + m]
    dist = np.sqrt((C[..., 0] - 255) ** 2 + C[..., 1] ** 2 + (C[..., 2] - 255) ** 2); a = np.clip((dist - 70) / 90, 0, 1)
    rgb = C.copy(); edge = a < .97; rgb[edge] = (28, 24, 28)   # 반투명 가장자리 = 외곽선 색(시트 조각은 모두 검은 외곽선)
    Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8)).save(os.path.join(H, 'pieces', f'{i + 1:02d}_{n}.png'))
print('ok')
