"""Runtime source embedded into generated applications for custom instruments."""
INSTRUMENT_RUNTIME_SOURCE = r'''
class InstrumentWidget(QWidget):
    valueChanged = Signal(float)
    alarmChanged = Signal(bool)

    def __init__(self, mode="gauge", parent=None):
        super().__init__(parent)
        self.mode = mode
        self.minimum, self.maximum, self._value = 0.0, 100.0, 0.0
        self.warning, self.critical = 70.0, 90.0
        self.title, self.unit, self.precision = mode.title(), "", 1
        self.history, self.history_size, self._alarm = [0.0], 80, False
        self.points, self.heat_cells, self.timeline = [], {}, []
        self.series = {}
        self.series_palette = ["#35C2FF","#FFB020","#59FF88","#FF5FA2","#B18CFF","#FFFFFF"]
        self.x_axis_title, self.y_axis_title = "X", "Y"
        self.show_legend, self.auto_scale, self.legend_position = True, True, "TopRight"
        self.last_x, self.last_y = 0.0, 0.0
        self.latitude, self.longitude, self.map_zoom = 55.7558, 37.6173, 8
        self.grid_rows, self.grid_columns, self.line_width = 8, 12, 2
        self.bands, self.segments, self.digits = 24, 14, 8
        self.design = {"shape":"dial","show_value":True,"ticks":10}
        self.colors = {"primary":"#35C2FF","secondary":"#26364A","needle":"#FF5252","background":"#101820","text":"#F4F7FB","warning":"#FFB020","alarm":"#FF3B30","border":"#52667A"}
        self.setMinimumSize(60, 40)
        if mode == "clock":
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._tick)
            self._timer.start(1000)

    def value(self): return float(self._value)
    def isAlarm(self): return bool(self._alarm)
    def ratio(self): return max(0.0, min(1.0, (self._value-self.minimum)/(self.maximum-self.minimum)))
    def setRange(self, minimum, maximum):
        self.minimum = float(minimum); self.maximum = max(float(maximum), self.minimum+1e-9); self.setValue(self._value)
    def setTitle(self, value): self.title = str(value); self.update()
    def setUnit(self, value): self.unit = str(value); self.update()
    def setColors(self, **values): self.colors.update({k:str(v) for k,v in values.items() if v}); self.update()
    def setValue(self, value):
        value = max(self.minimum, min(self.maximum, float(value)))
        changed = value != self._value; self._value = value
        alarm = value >= self.critical
        if alarm != self._alarm: self._alarm = alarm; self.alarmChanged.emit(alarm)
        if changed:
            self.history.append(value); self.history = self.history[-self.history_size:]
            self.valueChanged.emit(value)
        self.update()
    def appendValue(self, value): self.setValue(value)
    def appendPoint(self, x, y):
        self.last_x, self.last_y = float(x), float(y); self.points.append((self.last_x,self.last_y)); self.points=self.points[-self.history_size:]; self.setValue(y)
    def appendSeriesPoint(self, name, x, y):
        name=str(name or "Серия 1"); point=(float(x),float(y)); self.series.setdefault(name,[]).append(point); self.series[name]=self.series[name][-self.history_size:]; self.last_x,self.last_y=point; self.setValue(y)
    def setSeriesData(self, name, data):
        name=str(name or "Серия 1")
        try: values=json.loads(data) if isinstance(data,str) else list(data)
        except Exception: values=[]
        points=[]
        for i,value in enumerate(values):
            try:
                if isinstance(value,(list,tuple)) and len(value)>=2: points.append((float(value[0]),float(value[1])))
                else: points.append((float(i),float(value)))
            except (TypeError,ValueError): pass
        self.series[name]=points[-self.history_size:]
        if points: self.last_x,self.last_y=points[-1]; self.setValue(self.last_y)
        self.update()
    def clearSeries(self): self.series={}; self.points=[]; self.update()
    def seriesCount(self): return len(self.series)
    def exportImage(self,path): return bool(path) and self.grab().save(str(path),"PNG")
    def configurePlot(self, **values):
        for key,value in values.items():
            if key=="series_palette": self.series_palette=[v for v in str(value).split("|") if v]
            else: setattr(self,key,value)
        self.update()
    def setHeatCell(self, row, column, intensity):
        self.heat_cells[(int(row),int(column))]=float(intensity); self.setValue(intensity)
    def appendTimeline(self, timestamp, text, value=0):
        self.timeline.append((str(timestamp),str(text),float(value))); self.timeline=self.timeline[-self.history_size:]; self.setValue(value)
    def setPosition(self, latitude, longitude, zoom=None):
        self.latitude=max(-90,min(90,float(latitude))); self.longitude=max(-180,min(180,float(longitude))); self.map_zoom=int(zoom if zoom is not None else self.map_zoom); self.update()
    def setDesign(self, value):
        try: self.design=json.loads(value) if isinstance(value,str) else dict(value)
        except Exception: self.design={"shape":"dial","show_value":True,"ticks":10}
        self.update()
    def configureAdvanced(self, **values):
        for key,value in values.items(): setattr(self,key,value)
        self.update()
    def xValue(self): return float(self.last_x)
    def yValue(self): return float(self.last_y)
    def reset(self): self.history=[self.minimum]; self.points=[]; self.heat_cells={}; self.timeline=[]; self.setValue(self.minimum)
    def _tick(self):
        now=QTime.currentTime(); self._value=now.hour()*3600+now.minute()*60+now.second(); self.valueChanged.emit(self._value); self.update()
    def activeColor(self):
        return QColor(self.colors["alarm"] if self._alarm else self.colors["warning"] if self._value >= self.warning else self.colors["primary"])
    def label(self, p, r):
        p.setPen(QColor(self.colors["text"])); p.drawText(r.adjusted(6,5,-6,-5), Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter, self.title)
        if self.mode != "clock": p.drawText(r.adjusted(6,5,-6,-7), Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter, f"{self._value:.{self.precision}f} {self.unit}".strip())

    def paintEvent(self, event):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r=self.rect().adjusted(4,4,-4,-4); p.fillRect(self.rect(),QColor(self.colors["background"])); p.setPen(QPen(QColor(self.colors["border"]),2)); p.drawRoundedRect(QRectF(r),8,8)
        if self.mode in ("gauge","speedometer","tachometer","knob"): self.paintDial(p,r)
        elif self.mode=="thermometer": self.paintThermometer(p,r)
        elif self.mode=="level": self.paintLevel(p,r)
        elif self.mode=="led": self.paintLed(p,r)
        elif self.mode=="compass": self.paintCompass(p,r)
        elif self.mode=="battery": self.paintBattery(p,r)
        elif self.mode=="signal": self.paintSignal(p,r)
        elif self.mode=="sparkline": self.paintSparkline(p,r)
        elif self.mode=="clock": self.paintClock(p,r)
        elif self.mode in ("linechart","oscilloscope"): self.paintLineChart(p,r,self.mode=="oscilloscope")
        elif self.mode=="barchart": self.paintBarChart(p,r)
        elif self.mode=="piechart": self.paintPieChart(p,r)
        elif self.mode=="radarchart": self.paintRadarChart(p,r)
        elif self.mode=="vumeter": self.paintVUMeter(p,r)
        elif self.mode=="sevensegment": self.paintSevenSegment(p,r)
        elif self.mode=="ledmatrix": self.paintLEDMatrix(p,r)
        elif self.mode=="xyplot": self.paintXYPlot(p,r)
        elif self.mode=="heatmap": self.paintHeatMap(p,r)
        elif self.mode=="timeline": self.paintTimeline(p,r)
        elif self.mode=="waterfall": self.paintWaterfall(p,r)
        elif self.mode=="geomap": self.paintGeoMap(p,r)
        elif self.mode=="waveform": self.paintWaveform(p,r)
        elif self.mode=="spectrum": self.paintSpectrum(p,r)
        elif self.mode=="multisegment": self.paintMultiSegment(p,r)
        elif self.mode=="custom": self.paintCustom(p,r)
        p.end()

    def paintDial(self,p,r):
        self.label(p,r); side=min(r.width(),r.height())*.68; c=r.center(); box=QRectF(c.x()-side/2,c.y()-side/2,side,side)
        p.setPen(QPen(QColor(self.colors["secondary"]),max(7,int(side*.08)))); p.drawArc(box,225*16,-270*16)
        p.setPen(QPen(self.activeColor(),max(7,int(side*.08)))); p.drawArc(box,225*16,int(-270*16*self.ratio()))
        a=math.radians(225-270*self.ratio()); tip=QPointF(c.x()+math.cos(a)*side*.34,c.y()-math.sin(a)*side*.34)
        p.setPen(QPen(QColor(self.colors["needle"]),3)); p.drawLine(c,tip); p.setBrush(QColor(self.colors["needle"])); p.drawEllipse(c,5,5)
    def paintThermometer(self,p,r):
        self.label(p,r); x=r.center().x(); top=r.top()+35; bottom=r.bottom()-35
        p.setPen(QPen(QColor(self.colors["secondary"]),14)); p.drawLine(QPointF(x,top),QPointF(x,bottom))
        y=bottom-(bottom-top)*self.ratio(); p.setPen(QPen(self.activeColor(),10)); p.drawLine(QPointF(x,bottom),QPointF(x,y)); p.setBrush(self.activeColor()); p.drawEllipse(QPointF(x,bottom),12,12)
    def paintLevel(self,p,r):
        self.label(p,r); box=QRectF(r.left()+18,r.top()+38,r.width()-36,r.height()-75); p.setPen(QPen(QColor(self.colors["secondary"]),2)); p.drawRoundedRect(box,5,5)
        fill=QRectF(box.left()+3,box.bottom()-(box.height()-6)*self.ratio(),box.width()-6,(box.height()-6)*self.ratio()); p.fillRect(fill,self.activeColor())
    def paintLed(self,p,r):
        self.label(p,r); radius=min(r.width(),r.height())*.22; c=r.center(); color=self.activeColor() if self._value>self.minimum else QColor(self.colors["secondary"])
        p.setBrush(color); p.setPen(QPen(color.lighter(150),3)); p.drawEllipse(c,radius,radius)
    def paintCompass(self,p,r):
        self.label(p,r); side=min(r.width(),r.height())*.62; c=r.center(); p.setPen(QPen(QColor(self.colors["text"]),2)); p.drawEllipse(c,side/2,side/2)
        for text,dx,dy in (("N",0,-1),("E",1,0),("S",0,1),("W",-1,0)): p.drawText(QPointF(c.x()+dx*side*.41-5,c.y()+dy*side*.41+5),text)
        a=math.radians(90-self._value); tip=QPointF(c.x()+math.cos(a)*side*.38,c.y()-math.sin(a)*side*.38); p.setPen(QPen(QColor(self.colors["needle"]),4)); p.drawLine(c,tip)
    def paintBattery(self,p,r):
        self.label(p,r); box=QRectF(r.left()+22,r.center().y()-25,r.width()-55,50); p.setPen(QPen(QColor(self.colors["text"]),3)); p.drawRoundedRect(box,5,5); p.fillRect(QRectF(box.right(),box.center().y()-9,9,18),QColor(self.colors["text"])); inner=box.adjusted(5,5,-5,-5); inner.setWidth(inner.width()*self.ratio()); p.fillRect(inner,self.activeColor())
    def paintSignal(self,p,r):
        self.label(p,r); base=r.bottom()-30; w=(r.width()-45)/5
        for i in range(5):
            h=(i+1)*(r.height()-70)/5; bar=QRectF(r.left()+15+i*(w+3),base-h,w,h); p.fillRect(bar,self.activeColor() if self.ratio()>i/5 else QColor(self.colors["secondary"]))
    def paintSparkline(self,p,r):
        self.label(p,r); box=r.adjusted(12,32,-12,-28); values=self.history[-self.history_size:]
        if len(values)<2: return
        points=[QPointF(box.left()+i*box.width()/(len(values)-1),box.bottom()-max(0,min(1,(v-self.minimum)/(self.maximum-self.minimum)))*box.height()) for i,v in enumerate(values)]
        p.setPen(QPen(self.activeColor(),2)); p.drawPolyline(QPolygonF(points))
    def paintClock(self,p,r):
        side=min(r.width(),r.height())*.68; c=r.center(); p.setPen(QPen(QColor(self.colors["text"]),2)); p.drawEllipse(c,side/2,side/2); now=QTime.currentTime()
        for value,length,width,color,step in (((now.hour()%12)+now.minute()/60,side*.23,4,self.colors["text"],30),(now.minute()+now.second()/60,side*.34,3,self.colors["primary"],6),(now.second(),side*.38,1,self.colors["needle"],6)):
            a=math.radians(90-value*step); p.setPen(QPen(QColor(color),width)); p.drawLine(c,QPointF(c.x()+math.cos(a)*length,c.y()-math.sin(a)*length))
        p.setPen(QColor(self.colors["text"])); p.drawText(r.adjusted(5,5,-5,-5),Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter,self.title)
    def paintLineChart(self,p,r,scope=False):
        self.label(p,r); box=r.adjusted(12,32,-12,-28); p.setPen(QPen(QColor("#29445A"),1))
        for i in range(1,5): p.drawLine(QPointF(box.left(),box.top()+box.height()*i/5),QPointF(box.right(),box.top()+box.height()*i/5))
        values=self.history[-self.history_size:];
        if len(values)<2: return
        points=[QPointF(box.left()+i*box.width()/(len(values)-1),box.bottom()-max(0,min(1,(v-self.minimum)/(self.maximum-self.minimum)))*box.height()) for i,v in enumerate(values)]
        p.setPen(QPen(self.activeColor(),2)); p.drawPolyline(QPolygonF(points))
        if scope: p.setPen(QPen(QColor("#59FF88"),1)); p.drawLine(QPointF(box.left(),box.center().y()),QPointF(box.right(),box.center().y()))
    def paintBarChart(self,p,r):
        self.label(p,r); box=r.adjusted(12,35,-12,-28); values=(self.history[-8:] or [self._value]); w=box.width()/max(1,len(values))
        for i,v in enumerate(values):
            ratio=max(0,min(1,(v-self.minimum)/(self.maximum-self.minimum))); bar=QRectF(box.left()+i*w+2,box.bottom()-ratio*box.height(),max(2,w-4),ratio*box.height()); p.fillRect(bar,self.activeColor())
    def paintPieChart(self,p,r):
        self.label(p,r); side=min(r.width(),r.height())*.58; c=r.center(); box=QRectF(c.x()-side/2,c.y()-side/2,side,side); p.setBrush(QColor(self.colors["secondary"])); p.drawEllipse(box); p.setBrush(self.activeColor()); p.drawPie(box,90*16,int(-360*16*self.ratio()))
    def paintRadarChart(self,p,r):
        self.label(p,r); c=r.center(); radius=min(r.width(),r.height())*.3; count=6; p.setPen(QPen(QColor(self.colors["secondary"]),1))
        axes=[]
        for i in range(count):
            a=-math.pi/2+2*math.pi*i/count; pt=QPointF(c.x()+math.cos(a)*radius,c.y()+math.sin(a)*radius); axes.append(pt); p.drawLine(c,pt)
        vals=(self.history[-count:]+[self._value]*count)[-count:]; pts=[]
        for i,v in enumerate(vals):
            a=-math.pi/2+2*math.pi*i/count; rr=radius*max(0,min(1,(v-self.minimum)/(self.maximum-self.minimum))); pts.append(QPointF(c.x()+math.cos(a)*rr,c.y()+math.sin(a)*rr))
        poly=QPolygonF(pts); p.setPen(QPen(self.activeColor(),2)); p.setBrush(QColor(self.colors["primary"]+"66")); p.drawPolygon(poly)
    def paintVUMeter(self,p,r):
        self.label(p,r); box=r.adjusted(16,38,-16,-30); bars=16; gap=2; w=(box.width()-gap*(bars-1))/bars
        for i in range(bars):
            color=QColor(self.colors["alarm"] if i>13 else self.colors["warning"] if i>10 else self.colors["primary"]); color= color if self.ratio()>i/bars else QColor(self.colors["secondary"]); p.fillRect(QRectF(box.left()+i*(w+gap),box.top(),w,box.height()),color)
    def paintSevenSegment(self,p,r):
        self.label(p,r); p.setPen(self.activeColor()); font=p.font(); font.setFamily("Consolas"); font.setBold(True); font.setPixelSize(max(18,int(r.height()*.34))); p.setFont(font); p.drawText(r.adjusted(8,25,-8,-18),Qt.AlignmentFlag.AlignCenter,f"{self._value:.{self.precision}f}")
    def paintLEDMatrix(self,p,r):
        self.label(p,r); box=r.adjusted(15,35,-15,-25); rows,cols=5,8; size=min(box.width()/cols,box.height()/rows)*.7; seed=int(abs(self._value))
        for y in range(rows):
            for x in range(cols):
                on=((seed>>(x%8))&1) if y in (1,2,3) else ((x+y+seed)%5==0); c=QPointF(box.left()+(x+.5)*box.width()/cols,box.top()+(y+.5)*box.height()/rows); p.setBrush(self.activeColor() if on else QColor(self.colors["secondary"])); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(c,size/2,size/2)

    def _plotBox(self,p,r):
        self.label(p,r); box=r.adjusted(36,32,-14,-42); p.setPen(QPen(QColor(self.colors["secondary"]),1))
        for i in range(1,5):
            p.drawLine(QPointF(box.left(),box.top()+box.height()*i/5),QPointF(box.right(),box.top()+box.height()*i/5))
            p.drawLine(QPointF(box.left()+box.width()*i/5,box.top()),QPointF(box.left()+box.width()*i/5,box.bottom()))
        p.setPen(QColor(self.colors["text"])); p.drawText(QRectF(box.left(),box.bottom()+5,box.width(),18),Qt.AlignmentFlag.AlignCenter,str(self.x_axis_title))
        p.save(); p.translate(13,box.center().y()); p.rotate(-90); p.drawText(QRectF(-box.height()/2,-9,box.height(),18),Qt.AlignmentFlag.AlignCenter,str(self.y_axis_title)); p.restore()
        return box
    def _drawSeries(self,p,box,series):
        valid={str(k):list(v) for k,v in series.items() if len(v)>=1}
        if not valid: return
        allpts=[pt for values in valid.values() for pt in values]
        xs=[v[0] for v in allpts]; ys=[v[1] for v in allpts]
        xmin,xmax=min(xs),max(xs); ymin,ymax=min(ys),max(ys); xmax=xmax if xmax>xmin else xmin+1; ymax=ymax if ymax>ymin else ymin+1
        for index,(name,values) in enumerate(valid.items()):
            color=QColor(self.series_palette[index%len(self.series_palette)] if self.series_palette else self.colors["primary"])
            pts=[QPointF(box.left()+(x-xmin)/(xmax-xmin)*box.width(),box.bottom()-(y-ymin)/(ymax-ymin)*box.height()) for x,y in values]
            p.setPen(QPen(color,self.line_width));
            if len(pts)>1: p.drawPolyline(QPolygonF(pts))
            p.setBrush(color)
            for pt in pts: p.drawEllipse(pt,2.5,2.5)
            if self.show_legend:
                lx=box.right()-105; ly=box.top()+8+index*17; p.fillRect(QRectF(lx,ly,12,3),color); p.setPen(QColor(self.colors["text"])); p.drawText(QRectF(lx+17,ly-7,86,16),Qt.AlignmentFlag.AlignVCenter,str(name)[:16])
    def paintXYPlot(self,p,r):
        box=self._plotBox(p,r); series=self.series or {"Серия 1":(self.points or [(i,v) for i,v in enumerate(self.history[-12:])])}; self._drawSeries(p,box,series)
    def paintHeatMap(self,p,r):
        self.label(p,r); box=r.adjusted(12,32,-12,-28); rows=max(2,int(self.grid_rows)); cols=max(2,int(self.grid_columns)); seed=int(abs(self._value))
        for yy in range(rows):
            for xx in range(cols):
                v=self.heat_cells.get((yy,xx),((xx*17+yy*11+seed*3)%100)); ratio=max(0,min(1,float(v)/max(1,self.maximum))); color=QColor.fromHsvF((.66*(1-ratio)),.85,.35+.65*ratio); p.fillRect(QRectF(box.left()+xx*box.width()/cols,box.top()+yy*box.height()/rows,box.width()/cols+.5,box.height()/rows+.5),color)
    def paintTimeline(self,p,r):
        self.label(p,r); box=r.adjusted(14,34,-14,-30); y=box.center().y(); p.setPen(QPen(QColor(self.colors["secondary"]),3)); p.drawLine(QPointF(box.left(),y),QPointF(box.right(),y)); events=self.timeline or [(str(i),"",v) for i,v in enumerate(self.history[-8:])]
        for i,item in enumerate(events[-8:]):
            x=box.left()+(i+.5)*box.width()/max(1,len(events[-8:])); p.setBrush(self.activeColor()); p.setPen(QPen(self.activeColor(),2)); p.drawEllipse(QPointF(x,y),5,5); p.drawLine(QPointF(x,y),QPointF(x,y-14 if i%2==0 else y+14))
    def paintWaterfall(self,p,r):
        self.label(p,r); box=r.adjusted(12,32,-12,-28); values=(self.history[-18:] or [0]); h=box.height()/max(1,len(values))
        for i,v in enumerate(reversed(values)): ratio=max(0,min(1,(v-self.minimum)/(self.maximum-self.minimum))); color=QColor.fromHsvF(.62*(1-ratio),.85,.35+.65*ratio); p.fillRect(QRectF(box.left(),box.top()+i*h,box.width()*ratio,h+.5),color)
    def paintGeoMap(self,p,r):
        self.label(p,r); box=r.adjusted(12,32,-12,-28); p.fillRect(box,QColor("#18334A")); p.setPen(QPen(QColor("#2E5B70"),1))
        for i in range(1,6): p.drawLine(QPointF(box.left()+box.width()*i/6,box.top()),QPointF(box.left()+box.width()*i/6,box.bottom()))
        for i in range(1,4): p.drawLine(QPointF(box.left(),box.top()+box.height()*i/4),QPointF(box.right(),box.top()+box.height()*i/4))
        x=box.left()+(self.longitude+180)/360*box.width(); y=box.top()+(90-self.latitude)/180*box.height(); p.setBrush(QColor(self.colors["alarm"])); p.setPen(QPen(QColor("#FFFFFF"),2)); p.drawEllipse(QPointF(x,y),6,6)
    def paintWaveform(self,p,r):
        box=self._plotBox(p,r); values=self.history[-self.history_size:]; values=values if len(values)>2 else [math.sin(i*.55+self._value*.03)*45+50 for i in range(24)]; pts=[QPointF(box.left()+i*box.width()/(len(values)-1),box.bottom()-max(0,min(1,(v-self.minimum)/(self.maximum-self.minimum)))*box.height()) for i,v in enumerate(values)]; p.setPen(QPen(self.activeColor(),self.line_width)); p.drawPolyline(QPolygonF(pts))
    def paintSpectrum(self,p,r):
        self.label(p,r); box=r.adjusted(12,32,-12,-28); count=max(4,int(self.bands)); w=box.width()/count
        for i in range(count): level=(.15+.85*abs(math.sin(i*.39+self._value*.04)))*(1-i/(count*1.6)); p.fillRect(QRectF(box.left()+i*w+1,box.bottom()-box.height()*level,max(1,w-2),box.height()*level),QColor.fromHsvF(.35-.3*i/count,.85,.95))
    def paintMultiSegment(self,p,r):
        self.label(p,r); font=p.font(); font.setFamily("Consolas"); font.setBold(True); font.setPixelSize(max(15,int(r.height()*.3))); p.setFont(font); p.setPen(self.activeColor()); text=f"{self._value:.{self.precision}f}"[:max(1,int(self.digits))]; p.drawText(r.adjusted(8,24,-8,-18),Qt.AlignmentFlag.AlignCenter,text); p.setPen(QPen(QColor(self.colors["secondary"]),1,Qt.PenStyle.DashLine)); p.drawRect(r.adjusted(12,35,-12,-30))
    def paintCustom(self,p,r):
        shape=str(self.design.get("shape","dial")).lower()
        if shape=="bar": self.paintLevel(p,r)
        elif shape=="ring": self.paintDial(p,r)
        elif shape=="digital": self.paintSevenSegment(p,r)
        elif shape=="graph": self.paintWaveform(p,r)
        else: self.paintDial(p,r)

    def mouseMoveEvent(self,event):
        if self.mode=="knob" and event.buttons() & Qt.MouseButton.LeftButton:
            ratio=max(0,min(1,1-event.position().y()/max(1,self.height()))); self.setValue(self.minimum+ratio*(self.maximum-self.minimum)); return
        super().mouseMoveEvent(event)


class DashboardCanvasWidget(QWidget):
    sceneChanged = Signal(int)
    def __init__(self,parent=None):
        super().__init__(parent); self.items=[]; self.zoom=1.0; self.show_grid=True; self.grid_size=20; self.antialiasing=True; self.background_color="#101820"; self.grid_color="#26364A"; self.setMinimumSize(80,60); self._animation_clock=0
        self._animation_timer=QTimer(self); self._animation_timer.setInterval(16); self._animation_timer.timeout.connect(self._animate)
    def _animate(self):
        self._animation_clock += self._animation_timer.interval(); self.update()
    def _sync_animation(self):
        active=any(isinstance(v.get("animation"),dict) and v.get("animation",{}).get("type") not in (None,"","none") for v in self.items)
        if active and not self._animation_timer.isActive(): self._animation_timer.start()
        elif not active: self._animation_timer.stop()
    def setScene(self,value):
        try: data=json.loads(value) if isinstance(value,str) else list(value); self.items=[dict(v) for v in data if isinstance(v,dict)]
        except Exception: self.items=[]
        self._sync_animation(); self.update(); self.sceneChanged.emit(len(self.items))
    def sceneJson(self): return json.dumps(self.items,ensure_ascii=False,separators=(",",":"))
    def itemCount(self): return len(self.items)
    def addShape(self,kind="rect",x=10,y=10,w=80,h=50,text="",color="#35C2FF",rotation=0,layer=0,group="",locked=False,animation=None):
        self.items.append({"type":str(kind),"x":float(x),"y":float(y),"w":float(w),"h":float(h),"text":str(text),"color":str(color),"rotation":float(rotation),"layer":int(layer),"group":str(group),"locked":bool(locked),"animation":dict(animation or {})}); self._sync_animation(); self.update(); self.sceneChanged.emit(len(self.items))
    def removeLast(self):
        if self.items: self.items.pop(); self._sync_animation(); self.update(); self.sceneChanged.emit(len(self.items))
    def clearScene(self): self.items=[]; self._sync_animation(); self.update(); self.sceneChanged.emit(0)
    def setZoom(self,value): self.zoom=max(.1,min(8.0,float(value))); self.update()
    def exportImage(self,path): return bool(path) and self.grab().save(str(path),"PNG")
    def _animation_state(self,item):
        animation=item.get("animation") if isinstance(item.get("animation"),dict) else {}
        kind=str(animation.get("type","none")); duration=max(100,int(animation.get("duration",1200) or 1200)); loop=bool(animation.get("loop",True)); phase=self._animation_clock/duration
        if loop: phase=phase%1.0
        else: phase=min(1.0,phase)
        return kind,phase
    def paintEvent(self,event):
        p=QPainter(self)
        if self.antialiasing: p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(),QColor(self.background_color)); p.scale(self.zoom,self.zoom)
        view_w=self.width()/self.zoom; view_h=self.height()/self.zoom
        if self.show_grid:
            p.setPen(QPen(QColor(self.grid_color),1,Qt.PenStyle.DotLine)); step=max(5,int(self.grid_size))
            for x in range(0,int(view_w)+step,step): p.drawLine(QPointF(x,0),QPointF(x,view_h))
            for y in range(0,int(view_h)+step,step): p.drawLine(QPointF(0,y),QPointF(view_w,y))
        for item in sorted(self.items,key=lambda v:int(v.get("layer",0))):
            kind=str(item.get("type","rect")).lower(); x=float(item.get("x",0)); y=float(item.get("y",0)); w=max(1,float(item.get("w",80))); h=max(1,float(item.get("h",50))); color=QColor(str(item.get("color","#35C2FF"))); text=str(item.get("text","")); rotation=float(item.get("rotation",0)); box=QRectF(-w/2,-h/2,w,h); animation,phase=self._animation_state(item)
            p.save(); p.translate(x+w/2,y+h/2)
            if animation=="pulse": scale=1.0+.08*math.sin(phase*math.tau); p.scale(scale,scale)
            elif animation=="rotate": rotation += phase*360.0
            elif animation=="blink": p.setOpacity(.2+.8*(.5+.5*math.sin(phase*math.tau)))
            elif animation=="slide": p.translate(math.sin(phase*math.tau)*12.0,0)
            p.rotate(rotation); p.setPen(QPen(color.lighter(140),2)); p.setBrush(QBrush(color))
            if kind in ("ellipse","circle"): p.drawEllipse(box)
            elif kind=="line": p.drawLine(QPointF(-w/2,-h/2),QPointF(w/2,h/2))
            elif kind=="arrow":
                p.drawLine(QPointF(-w/2,0),QPointF(w/2,0)); p.drawLine(QPointF(w/2,0),QPointF(w/2-12,-7)); p.drawLine(QPointF(w/2,0),QPointF(w/2-12,7))
            elif kind=="text": p.setPen(color); p.setBrush(Qt.BrushStyle.NoBrush); font=p.font(); font.setPointSize(max(6,int(item.get("font_size",14) or 14))); p.setFont(font); p.drawText(box,Qt.AlignmentFlag.AlignCenter,text)
            else: p.drawRoundedRect(box,6,6); p.setPen(QColor("#FFFFFF")); p.drawText(box.adjusted(5,5,-5,-5),Qt.AlignmentFlag.AlignCenter,text)
            p.restore()
        p.end()


class GridCanvasWidget(QWidget):
    cellClicked = Signal(int, int, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid = []
        self._palette = {}
        self._last_column = -1
        self._last_row = -1
        self._last_value = None
        self.columns = 10
        self.rows = 20
        self.cell_size = 24
        self.fit_to_widget = True
        self.show_grid = True
        self.show_values = False
        self.interactive = True
        self.empty_value = "0"
        self.background_color = "#101820"
        self.grid_color = "#26364A"
        self._fallback_colors = (
            "#35C2FF", "#FFB020", "#59FF88", "#FF5FA2",
            "#B18CFF", "#FF7043", "#26C6DA", "#EC407A",
        )
        self.setMinimumSize(80, 80)

    def _empty_grid(self):
        return [
            [self.empty_value for _column in range(max(1, int(self.columns)))]
            for _row in range(max(1, int(self.rows)))
        ]

    def setGrid(self, value):
        try:
            data = json.loads(value) if isinstance(value, str) else value
        except Exception:
            data = None
        if not isinstance(data, (list, tuple)):
            data = self._empty_grid()
        rows = []
        for row in data:
            if isinstance(row, (list, tuple)):
                rows.append(list(row))
        self._grid = rows or self._empty_grid()
        self.rows = len(self._grid)
        self.columns = max((len(row) for row in self._grid), default=1)
        self.update()

    def grid(self):
        return [list(row) for row in self._grid]

    def setPalette(self, value):
        try:
            data = json.loads(value) if isinstance(value, str) else dict(value)
        except Exception:
            data = {}
        self._palette = {
            str(key): str(color)
            for key, color in data.items()
            if QColor(str(color)).isValid()
        } if isinstance(data, dict) else {}
        self.update()

    def clearGrid(self):
        self._grid = self._empty_grid()
        self.update()

    def currentColumn(self): return int(self._last_column)
    def currentRow(self): return int(self._last_row)
    def currentValue(self): return self._last_value
    def rowCount(self): return len(self._grid)
    def columnCount(self):
        return max((len(row) for row in self._grid), default=0)

    def _metrics(self):
        columns = max(1, self.columnCount() or int(self.columns))
        rows = max(1, self.rowCount() or int(self.rows))
        if self.fit_to_widget:
            cell = max(1.0, min(self.width() / columns, self.height() / rows))
        else:
            cell = max(2.0, float(self.cell_size))
        width, height = columns * cell, rows * cell
        return columns, rows, cell, (self.width() - width) / 2, (self.height() - height) / 2

    def _cell_color(self, value):
        if str(value) == str(self.empty_value) or value in (None, False, ""):
            return QColor(self.background_color)
        configured = self._palette.get(str(value))
        if configured:
            return QColor(configured)
        try:
            index = abs(int(value)) - 1
        except (TypeError, ValueError):
            index = sum(ord(char) for char in str(value))
        return QColor(self._fallback_colors[index % len(self._fallback_colors)])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.background_color))
        columns, rows, cell, offset_x, offset_y = self._metrics()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        font = painter.font()
        font.setPixelSize(max(7, min(18, int(cell * .42))))
        painter.setFont(font)
        for row_index in range(rows):
            row = self._grid[row_index] if row_index < len(self._grid) else []
            for column_index in range(columns):
                value = row[column_index] if column_index < len(row) else self.empty_value
                box = QRectF(
                    offset_x + column_index * cell,
                    offset_y + row_index * cell,
                    cell,
                    cell,
                )
                painter.fillRect(box, self._cell_color(value))
                if self.show_grid:
                    painter.setPen(QPen(QColor(self.grid_color), 1))
                    painter.drawRect(box)
                if self.show_values and str(value) != str(self.empty_value):
                    color = self._cell_color(value)
                    painter.setPen(QColor("#111111") if color.lightness() > 150 else QColor("#FFFFFF"))
                    painter.drawText(box, Qt.AlignmentFlag.AlignCenter, str(value))
        painter.end()

    def mousePressEvent(self, event):
        if self.interactive:
            columns, rows, cell, offset_x, offset_y = self._metrics()
            point = event.position()
            column = int((point.x() - offset_x) // cell)
            row = int((point.y() - offset_y) // cell)
            if 0 <= column < columns and 0 <= row < rows:
                values = self._grid[row] if row < len(self._grid) else []
                value = values[column] if column < len(values) else self.empty_value
                self._last_column, self._last_row, self._last_value = column, row, value
                self.cellClicked.emit(column, row, value)
        super().mousePressEvent(event)
'''
