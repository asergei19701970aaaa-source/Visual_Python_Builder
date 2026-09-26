"""Дополнительные файловые ноды."""
import os, glob, shutil
from python_library.nodes._base import library, txt
nd=library("FileExtra","7. Файлы",color="#607080")
@nd("Список файлов", inputs=[('folder','file','.'),('mask','text','*.*')], outputs=[('files','list')])
def list_files(folder,mask): return glob.glob(os.path.join(txt(folder) or '.', txt(mask) or '*'))
@nd("Прочитать текст", inputs=[('path','file','')], outputs=[('text','text')])
def read_text(path):
    with open(txt(path),'r',encoding='utf-8') as f: return f.read()
@nd("Записать текст", inputs=[('path','file','out.txt'),('text','text','')], outputs=[('file','file')])
def write_text(path,text):
    with open(txt(path),'w',encoding='utf-8') as f: f.write(txt(text)); return txt(path)
@nd("Копировать файл", inputs=[('src','file',''),('dst','file','')], outputs=[('file','file')])
def copy_file(src,dst): shutil.copy2(txt(src),txt(dst)); return txt(dst)
@nd("Создать папку", inputs=[('path','file','new_folder')], outputs=[('folder','file')])
def mkdir(path): os.makedirs(txt(path),exist_ok=True); return txt(path)
