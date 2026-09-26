"""Изображения. Для части нод нужен Pillow: pip install pillow."""
from python_library.nodes._base import library, num, txt
nd=library("Image","17. Изображения",color="#7a4a9e")
@nd("Размер изображения", inputs=[("path","file","")], outputs=[("width","number"),("height","number")], tags=["pillow","image"])
def image_size(path):
    try: from PIL import Image
    except ImportError as exc: raise ValueError("Установите Pillow: pip install pillow") from exc
    with Image.open(txt(path)) as img: return float(img.width), float(img.height)
@nd("Изменить размер изображения", inputs=[("src","file",""),("dst","file","out.png"),("width","number",800),("height","number",600)], outputs=[("file","file")])
def image_resize(src,dst,width,height):
    try: from PIL import Image
    except ImportError as exc: raise ValueError("Установите Pillow") from exc
    with Image.open(txt(src)) as img: img.resize((int(num(width)),int(num(height)))).save(txt(dst))
    return txt(dst)

@nd("Изображение в серое", inputs=[("src","file",""),("dst","file","gray.png")], outputs=[("file","file")])
def image_grayscale(src,dst):
    try: from PIL import Image
    except ImportError as exc: raise ValueError("Установите Pillow") from exc
    with Image.open(txt(src)) as img: img.convert('L').save(txt(dst))
    return txt(dst)
@nd("Повернуть изображение", inputs=[("src","file",""),("dst","file","rotated.png"),("angle","number",90)], outputs=[("file","file")])
def image_rotate(src,dst,angle):
    try: from PIL import Image
    except ImportError as exc: raise ValueError("Установите Pillow") from exc
    with Image.open(txt(src)) as img: img.rotate(num(angle), expand=True).save(txt(dst))
    return txt(dst)
@nd("Обрезать изображение", inputs=[("src","file",""),("dst","file","crop.png"),("x","number",0),("y","number",0),("w","number",100),("h","number",100)], outputs=[("file","file")])
def image_crop(src,dst,x,y,w,h):
    try: from PIL import Image
    except ImportError as exc: raise ValueError("Установите Pillow") from exc
    with Image.open(txt(src)) as img: img.crop((int(num(x)),int(num(y)),int(num(x)+num(w)),int(num(y)+num(h)))).save(txt(dst))
    return txt(dst)
