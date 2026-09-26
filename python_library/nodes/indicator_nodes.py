"""Indicator nodes 3.23. No extra dependencies."""
import math
from python_library.codegen import uispec as u
from python_library.nodes._base import flag, library, num, txt
nd = library("Indicator", "21. Индикаторы", color="#b07020")

def _st(fill="",stroke="#ffffff",w=2):
    return {"fill":txt(fill),"stroke":txt(stroke),"width":int(num(w,2))}

@nd("LED индикатор",
    inputs=[("x","number",40),("y","number",40),("size","number",40),
            ("on","bool",True),("color_on","text","#3cff6f"),("color_off","text","#304030"),("label","text","LED")],
    outputs=[("shapes","list")],tags=["led","indicator","light"])
def led(x,y,size,on,color_on,color_off,label):
    color=txt(color_on) if flag(on) else txt(color_off)
    r=num(size,40); cx,cy=num(x),num(y)
    shapes=[u.shape("ellipse",x=cx,y=cy,w=r,h=r,style=_st(color,"#101010",2))]
    if flag(on): shapes.append(u.shape("ellipse",x=cx+r*.15,y=cy+r*.15,w=r*.35,h=r*.35,style=_st("#ffffff","",0)))
    if txt(label): shapes.append(u.shape("text",text=txt(label),x=cx+r*.1,y=cy+r+18,size=13,style=_st("#ffffff","",0)))
    return shapes

@nd("Круговой прогресс",
    inputs=[("x","number",30),("y","number",30),("size","number",120),
            ("value","number",65),("max_val","number",100),("color","text","#3a9fff"),("label","text","")],
    outputs=[("shapes","list")],tags=["progress","ring","indicator"])
def ring(x,y,size,value,max_val,color,label):
    v=max(0.0,min(1.0,num(value)/(num(max_val,100) or 1))); s=num(size,120); cx,cy=num(x),num(y)
    pct=f"{int(v*100)}%"
    return [u.shape("ellipse",x=cx,y=cy,w=s,h=s,style=_st("","#333a44",int(s*.12))),
            u.shape("ellipse",x=cx,y=cy,w=s,h=s,style=_st("",txt(color),int(s*.12))),
            u.shape("text",text=(txt(label) or pct),x=cx+s*.28,y=cy+s*.56,size=max(12,int(s*.18)),style=_st("#ffffff","",0))]

@nd("Спидометр",
    inputs=[("x","number",20),("y","number",20),("size","number",180),
            ("value","number",50),("max_val","number",100),("title","text","Speed"),("unit","text",""),("color","text","#ff5555")],
    outputs=[("shapes","list")],tags=["gauge","dial"])
def gauge(x,y,size,value,max_val,title,unit,color):
    v=max(0.0,min(1.0,num(value)/(num(max_val,100) or 1))); s=num(size,180)
    cx=num(x)+s/2; cy=num(y)+s/2
    angle=math.radians(210-v*240)
    nx=cx+math.cos(angle)*s*.38; ny=cy-math.sin(angle)*s*.38
    return [u.shape("ellipse",x=num(x),y=num(y),w=s,h=s,style=_st("#20242c","#555",3)),
            u.shape("line",x1=cx,y1=cy,x2=nx,y2=ny,style=_st("",txt(color),4)),
            u.shape("ellipse",x=cx-5,y=cy-5,w=10,h=10,style=_st("#aaa","",0)),
            u.shape("text",text=txt(title),x=num(x)+s*.28,y=num(y)+s*.2,size=14,style=_st("#fff","",0)),
            u.shape("text",text=f"{num(value):.0f}{txt(unit)}",x=num(x)+s*.3,y=num(y)+s*.75,size=16,style=_st("#ffd","",0))]

@nd("Термометр",
    inputs=[("x","number",20),("y","number",20),("width","number",40),("height","number",160),
            ("value","number",60),("min_val","number",-40),("max_val","number",120),("color","text","#ff4040"),("label","text","T")],
    outputs=[("shapes","list")],tags=["thermometer","temperature"])
def thermometer(x,y,width,height,value,min_val,max_val,color,label):
    bx,by=num(x),num(y); bw,bh=num(width,40),num(height,160)
    mn,mx=num(min_val,-40),num(max_val,120)
    v=max(0.0,min(1.0,(num(value)-mn)/((mx-mn) or 1))); fill_h=bh*v
    return [u.shape("rect",x=bx,y=by,w=bw,h=bh,style=_st("#2a2a3a","#888",2)),
            u.shape("rect",x=bx,y=by+bh-fill_h,w=bw,h=fill_h,style=_st(txt(color),"",0)),
            u.shape("text",text=f"{num(value):.1f}°",x=bx,y=by+bh+20,size=13,style=_st("#fff","",0)),
            u.shape("text",text=txt(label),x=bx,y=by-18,size=13,style=_st("#fff","",0))]

@nd("Прогресс-бар",
    inputs=[("x","number",20),("y","number",20),("width","number",200),("height","number",28),
            ("value","number",60),("max_val","number",100),("color","text","#3a9fff"),("label","text","")],
    outputs=[("shapes","list")],tags=["progress","bar"])
def progress_bar(x,y,width,height,value,max_val,color,label):
    bx,by=num(x),num(y); bw,bh=num(width,200),num(height,28)
    v=max(0.0,min(1.0,num(value)/(num(max_val,100) or 1)))
    return [u.shape("rect",x=bx,y=by,w=bw,h=bh,style=_st("#2a2a3a","#666",1)),
            u.shape("rect",x=bx,y=by,w=bw*v,h=bh,style=_st(txt(color),"",0)),
            u.shape("text",text=(txt(label) or f"{int(v*100)}%"),x=bx+bw*.4,y=by+bh*.72,size=13,style=_st("#fff","",0))]

@nd("LCD-дисплей",
    inputs=[("x","number",20),("y","number",20),("value","any","0"),("digits","number",6),("color","text","#ff4400"),("label","text","")],
    outputs=[("shapes","list")],tags=["lcd","display"])
def lcd_display(x,y,value,digits,color,label):
    digs=max(1,int(num(digits,6))); raw=str(value).strip() if value is not None else "0"
    disp=raw[-digs:].rjust(digs," "); cw,ch=22,36; bx,by=num(x),num(y)
    shapes=[u.shape("rect",x=bx-4,y=by-4,w=cw*digs+8,h=ch+8,style=_st("#111","#333",1))]
    for i,c in enumerate(disp):
        shapes.append(u.shape("text",text=c,x=bx+i*cw+3,y=by+ch*.78,size=28,style=_st(txt(color),"",0)))
    if txt(label): shapes.append(u.shape("text",text=txt(label),x=bx,y=by+ch+20,size=12,style=_st("#aaa","",0)))
    return shapes
