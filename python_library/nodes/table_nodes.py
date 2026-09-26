"""Табличная обработка списков словарей."""
from python_library.nodes._base import library, lst, txt, num
nd=library('Table','24. Таблицы',color='#4b8f4b')
@nd('Фильтр строк', inputs=[('rows','list',None),('field','text',''),('equals','text','')], outputs=[('rows','list')])
def filter_rows(rows,field,equals): return [r for r in lst(rows) if isinstance(r,dict) and txt(r.get(txt(field)))==txt(equals)]
@nd('Сортировать строки', inputs=[('rows','list',None),('field','text',''),('reverse','bool',False)], outputs=[('rows','list')])
def sort_rows(rows,field,reverse): return sorted([r for r in lst(rows) if isinstance(r,dict)], key=lambda r: txt(r.get(txt(field))), reverse=bool(reverse))
@nd('Выбрать колонку', inputs=[('rows','list',None),('field','text','')], outputs=[('values','list')])
def column(rows,field): return [r.get(txt(field)) for r in lst(rows) if isinstance(r,dict)]
@nd('Группировать и считать', inputs=[('rows','list',None),('field','text','')], outputs=[('groups','dict'),('rows','list')])
def group_count(rows,field):
    d={}
    for r in lst(rows):
        if isinstance(r,dict): d[txt(r.get(txt(field)))] = d.get(txt(r.get(txt(field))),0)+1
    return d, [{'key':k,'count':v} for k,v in d.items()]
@nd('Сумма колонки', inputs=[('rows','list',None),('field','text','')], outputs=[('sum','number')])
def sum_column(rows,field): return float(sum(num(r.get(txt(field))) for r in lst(rows) if isinstance(r,dict)))
@nd('Первые N строк', inputs=[('rows','list',None),('count','number',10)], outputs=[('rows','list')])
def head_rows(rows,count): return lst(rows)[:int(num(count,10))]
