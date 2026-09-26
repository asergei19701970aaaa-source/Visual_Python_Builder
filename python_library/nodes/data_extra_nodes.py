"""Данные: CSV/JSON."""
import csv, json
from python_library.nodes._base import library, txt, lst
nd=library("DataExtra","5. Данные",color="#8f6f2f")
@nd("Прочитать JSON", inputs=[("path","file","")], outputs=[("data","dict")])
def read_json(path):
    with open(txt(path),'r',encoding='utf-8') as f: return json.load(f)
@nd("Записать JSON", inputs=[("path","file","data.json"),("data","any",None)], outputs=[("file","file")])
def write_json(path,data):
    with open(txt(path),'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    return txt(path)
@nd("Прочитать CSV", inputs=[("path","file","")], outputs=[("rows","list")])
def read_csv(path):
    with open(txt(path),'r',encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
@nd("Записать CSV", inputs=[("path","file","data.csv"),("rows","list",None)], outputs=[("file","file")])
def write_csv(path,rows):
    data=[r for r in lst(rows) if isinstance(r,dict)]
    keys=sorted({k for r in data for k in r})
    with open(txt(path),'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(data)
    return txt(path)
