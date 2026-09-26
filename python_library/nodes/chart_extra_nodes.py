"""Дополнительные диаграммы."""
from python_library.codegen import uispec as u
from python_library.nodes._base import library, lst, txt
nd=library("ChartExtra","23. Диаграммы",color="#20a0b0")
@nd("Данные диаграммы", inputs=[('labels','list',None),('values','list',None),('title','text','Диаграмма'),('kind','text','bar')], outputs=[('chart','chart')])
def chart_data(labels,values,title,kind):
    return {'chart':txt(kind) or 'bar','labels':[txt(x) for x in lst(labels)],'values':[float(x) for x in lst(values)],'title':txt(title)}
@nd("Виджет диаграммы", inputs=[('chart','chart',None),('name','text','chart')], outputs=[('widget','widget')])
def chart_widget(chart,name):
    w=u.widget('ChartView',name=txt(name) or 'chart',helper='ChartView',module=''); w['extra']['chart']=chart if isinstance(chart,dict) else {}; w['calls'].append('setMinimumSize(420,260)'); return w
