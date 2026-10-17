# 그림에 좌표 격자를 그려 저장 (점 찍기용). 사용: grid.py 입력 출력 [확대] [x0 y0 x1 y1] [간격]
import sys
from PIL import Image,ImageDraw
src,out=sys.argv[1],sys.argv[2];k=float(sys.argv[3]) if len(sys.argv)>3 else 1
im=Image.open(src).convert('RGBA')
if len(sys.argv)>7: x0,y0,x1,y1=map(int,sys.argv[4:8])
else: x0,y0,x1,y1=0,0,im.width,im.height
st=int(sys.argv[8]) if len(sys.argv)>8 else 20
c=im.crop((x0,y0,x1,y1));bg=Image.new('RGBA',c.size,(255,255,255,255));bg.alpha_composite(c);bg=bg.resize((int(c.width*k),int(c.height*k)),Image.LANCZOS)
d=ImageDraw.Draw(bg)
for x in range((x0//st)*st,x1,st):
    X=(x-x0)*k
    if X<0:continue
    d.line([(X,0),(X,bg.height)],fill=(255,0,0,110) if x%(st*5) else (255,0,0,220));
    if x%(st*5)==0:d.text((X+2,2),str(x),fill=(200,0,0))
for y in range((y0//st)*st,y1,st):
    Y=(y-y0)*k
    if Y<0:continue
    d.line([(0,Y),(bg.width,Y)],fill=(0,0,255,110) if y%(st*5) else (0,0,255,220))
    if y%(st*5)==0:d.text((2,Y+2),str(y),fill=(0,0,200))
bg.convert('RGB').save(out)
