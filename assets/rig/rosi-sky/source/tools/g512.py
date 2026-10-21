# 512 좌표 격자 확대: g512.py 그림 x0 y0 x1 y1 배율 출력
import sys
from PIL import Image, ImageDraw, ImageFont
p,x0,y0,x1,y1,k,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',12,index=1)
im=Image.open(p).convert('RGBA');im=im.resize((512,512),Image.LANCZOS) if im.size!=(512,512) else im
bg=Image.new('RGBA',im.size,(236,238,244,255));bg.alpha_composite(im)
c=bg.crop((x0,y0,x1,y1)).resize(((x1-x0)*k,(y1-y0)*k),Image.LANCZOS).convert('RGB');d=ImageDraw.Draw(c)
for x in range((x0//10+1)*10,x1,10):
    X=(x-x0)*k;d.line([(X,0),(X,c.height)],fill=(255,0,120) if x%50==0 else (120,200,255),width=1);d.text((X+2,2),str(x),fill=(200,0,90),font=f)
for y in range((y0//10+1)*10,y1,10):
    Y=(y-y0)*k;d.line([(0,Y),(c.width,Y)],fill=(255,0,120) if y%50==0 else (120,200,255),width=1);d.text((2,Y+1),str(y),fill=(200,0,90),font=f)
c.save(out)
