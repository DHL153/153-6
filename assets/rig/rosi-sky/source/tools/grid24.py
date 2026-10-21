# 격자 그림: grid14.py 그림.png x0 y0 x1 y1 배율 간격 출력.png  (1254 좌표)
import sys
from PIL import Image, ImageDraw, ImageFont
p,x0,y0,x1,y1,k,st,out=sys.argv[1],*map(int,sys.argv[2:6]),float(sys.argv[6]),int(sys.argv[7]),sys.argv[8]
im=Image.open(p).convert('RGBA');bg=Image.new('RGBA',im.size,(236,238,244,255));bg.alpha_composite(im)
c=bg.crop((x0,y0,x1,y1)).resize((round((x1-x0)*k),round((y1-y0)*k)),Image.LANCZOS).convert('RGB');d=ImageDraw.Draw(c)
f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',13,index=1)
for x in range((x0//st+1)*st,x1,st):
    X=(x-x0)*k;d.line([(X,0),(X,c.height)],fill=(0,170,255) if x%(st*2) else (255,0,90),width=1);d.text((X+2,2),str(x),fill=(255,0,90),font=f)
for y in range((y0//st+1)*st,y1,st):
    Y=(y-y0)*k;d.line([(0,Y),(c.width,Y)],fill=(0,170,255) if y%(st*2) else (255,0,90),width=1);d.text((2,Y+1),str(y),fill=(255,0,90),font=f)
c.save(out)
