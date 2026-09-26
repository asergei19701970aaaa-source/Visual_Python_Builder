"""Дополнительные текстовые ноды."""
import re
from python_library.nodes._base import library, txt, num
nd=library('TextExtra','2. Текст',color='#8f5a3f')
@nd('Регулярное выражение', inputs=[('text','text',''),('pattern','text','\\d+')], outputs=[('matches','list')])
def regex_find(text,pattern): return re.findall(txt(pattern), txt(text))
@nd('Заменить regex', inputs=[('text','text',''),('pattern','text',''),('replace','text','')], outputs=[('text','text')])
def regex_replace(text,pattern,replace): return re.sub(txt(pattern), txt(replace), txt(text))
@nd('Разделить строки', inputs=[('text','text',''),('keep_empty','bool',False)], outputs=[('lines','list')])
def split_lines(text,keep_empty):
    lines=txt(text).splitlines(); return lines if keep_empty else [x for x in lines if x.strip()]
@nd('Шаблон format', inputs=[('template','text','Привет, {name}!'),('data','dict',None)], outputs=[('text','text')])
def format_template(template,data): return txt(template).format(**(data if isinstance(data,dict) else {}))
@nd('Обрезать текст', inputs=[('text','text',''),('length','number',100),('suffix','text','…')], outputs=[('text','text')])
def truncate(text,length,suffix):
    t=txt(text); n=int(num(length,100)); return t if len(t)<=n else t[:max(0,n-len(txt(suffix)))] + txt(suffix)
