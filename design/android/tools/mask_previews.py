"""Launcher icon under the common masks, on a light and a dark wallpaper, plus the themed (monochrome) form."""
import math
from PIL import Image, ImageDraw
from pathlib import Path
R=Path(__file__).resolve().parent.parent/'launcher'
def masks(root, out):
    full=Image.open(root/'_full_1024.png').convert('RGBA'); mono=Image.open(root/'_mono_1024.png').convert('RGBA')
    vis=int(1024*72/108); off=(1024-vis)//2
    crop=full.crop((off,off,off+vis,off+vis)); mcrop=mono.crop((off,off,off+vis,off+vis)); big=vis
    def mask(kind):
        m=Image.new('L',(big,big),0); d=ImageDraw.Draw(m)
        if kind=='circle': d.ellipse((0,0,big-1,big-1),fill=255)
        elif kind=='rounded': d.rounded_rectangle((0,0,big-1,big-1),radius=int(big*0.18),fill=255)
        elif kind=='squircle':
            pts=[]; n=5.0; r=big/2
            for i in range(720):
                t=2*math.pi*i/720; c,s=math.cos(t),math.sin(t)
                pts.append((r+r*abs(c)**(2/n)*(1 if c>=0 else -1), r+r*abs(s)**(2/n)*(1 if s>=0 else -1)))
            d.polygon(pts,fill=255)
        elif kind=='teardrop':
            d.rounded_rectangle((0,0,big-1,big-1),radius=big//2,fill=255); d.rectangle((big//2,big//2,big-1,big-1),fill=255)
        return m
    tiles=[]
    for wall in ('#e9ecf5','#20242e'):
        for kind in ('circle','squircle','rounded','teardrop'):
            t=Image.new('RGBA',(big,big),(0,0,0,0)); t.paste(crop,(0,0),mask(kind)); tiles.append((wall,t))
        bgc,fgc=('#dfe3f2','#1a2a6b') if wall=='#e9ecf5' else ('#2b3352','#c9d3ff')
        t=Image.new('RGBA',(big,big),(0,0,0,0)); base=Image.new('RGBA',(big,big),bgc)
        base.paste(Image.new('RGBA',(big,big),fgc),(0,0),mcrop.split()[3]); t.paste(base,(0,0),mask('circle')); tiles.append((wall,t))
    cell=300; S=Image.new('RGB',(5*cell, 2*cell),'#ffffff')
    for i,(wall,t) in enumerate(tiles):
        r,c=divmod(i,5); x=c*cell; y=r*cell
        ImageDraw.Draw(S).rectangle((x,y,x+cell,y+cell),fill=wall)
        tt=t.resize((200,200),Image.LANCZOS); S.paste(tt,(x+50,y+50),tt)
    S.save(out, optimize=True)
for r in (R, R/'alternate-blue'):
    masks(r, r/'preview-masks.png'); (r/'_full_1024.png').unlink(); (r/'_mono_1024.png').unlink()
