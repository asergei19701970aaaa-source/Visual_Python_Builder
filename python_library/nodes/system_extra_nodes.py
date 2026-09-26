"""Дополнительные системные ноды."""
import os, platform, subprocess, time
from python_library.nodes._base import library, txt, num
nd=library("SysExtra","8. Случайное и система",color="#6f6f3a")
@nd("Сведения о системе", inputs=[], outputs=[("os","text"),("python","text"),("machine","text")])
def system_info(): return platform.platform(), platform.python_version(), platform.machine()
@nd("Переменная окружения", inputs=[("name","text","PATH")], outputs=[("value","text")])
def env(name): return os.environ.get(txt(name),"")
@nd("Запустить команду", inputs=[("command","text","echo ok"),("timeout","number",10)], outputs=[("stdout","text"),("stderr","text"),("code","number")])
def run_command(command,timeout):
    p=subprocess.run(txt(command),shell=True,capture_output=True,text=True,timeout=num(timeout,10)); return p.stdout,p.stderr,float(p.returncode)
@nd("Пауза", inputs=[("seconds","number",1)], outputs=[("done","bool")])
def sleep(seconds): time.sleep(max(0,min(60,num(seconds,1)))); return True
