# 원화 확대 + 10px 격자(원화 좌표) — python3 tools_zoom.py x0 y0 x1 y1 k out
import sys
from PIL import Image, ImageDraw
x0,y0,x1,y1,k=map(int,sys.argv[1:6]);out=sys.argv[6]
im=Image.open('ref512.png').convert('RGBA');bg=Image.new('RGBA',im.size,(255,255,255,255));bg.alpha_composite(im)
c=bg.crop((x0,y0,x1,y1)).resize(((x1-x0)*k,(y1-y0)*k),Image.LANCZOS);d=ImageDraw.Draw(c)
for v in range((x0//10+1)*10,x1,10):
    x=(v-x0)*k;d.line([(x,0),(x,c.height)],fill=(255,0,0,255) if v%50==0 else (255,170,170,255),width=1)
    d.text((x+2,2),str(v),fill=(220,0,0))
for v in range((y0//10+1)*10,y1,10):
    y=(v-y0)*k;d.line([(0,y),(c.width,y)],fill=(255,0,0,255) if v%50==0 else (255,170,170,255),width=1)
    d.text((2,y+2),str(v),fill=(220,0,0))
c.convert('RGB').save(out)
