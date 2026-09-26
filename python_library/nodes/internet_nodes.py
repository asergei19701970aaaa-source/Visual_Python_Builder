"""Internet nodes 3.23. pip install requests"""
import json, time
from python_library.nodes._base import library, txt, num
nd = library("Net", "20. Интернет", color="#2f8f6f")

def _r():
    try: import requests; return requests
    except ImportError as e: raise ValueError("pip install requests") from e

@nd("HTTP GET",inputs=[("url","text","https://example.com"),("timeout","number",10),("headers_json","text","")],
    outputs=[("body","text"),("status","number"),("ok","bool")],tags=["web","get","http"])
def http_get(url,timeout,headers_json):
    hdrs=json.loads(txt(headers_json) or "{}") if txt(headers_json) else {}
    resp=_r().get(txt(url),timeout=num(timeout,10),headers=hdrs)
    return resp.text,float(resp.status_code),resp.ok

@nd("HTTP POST JSON",inputs=[("url","text",""),("json_text","text","{}"),("timeout","number",10),("headers_json","text","")],
    outputs=[("body","text"),("status","number"),("ok","bool")],tags=["post","api"])
def http_post_json(url,json_text,timeout,headers_json):
    data=json.loads(txt(json_text) or "{}")
    hdrs=json.loads(txt(headers_json) or "{}") if txt(headers_json) else {}
    resp=_r().post(txt(url),json=data,timeout=num(timeout,10),headers=hdrs)
    return resp.text,float(resp.status_code),resp.ok

@nd("JSON поле",inputs=[("json_text","text","{}"),("path","text","key")],
    outputs=[("value","any"),("value_str","text")],tags=["json","parse"])
def json_field(json_text,path):
    data=json.loads(txt(json_text) or "{}")
    cur=data
    for part in txt(path).split("."):
        if not part: continue
        if isinstance(cur,dict): cur=cur.get(part)
        elif isinstance(cur,list):
            try: cur=cur[int(part)]
            except: cur=None
        else: cur=None
    return cur, str(cur) if cur is not None else ""

@nd("Парсить JSON",inputs=[("json_text","text","")],outputs=[("parsed","dict")])
def parse_json(json_text): return json.loads(txt(json_text) or "{}")

@nd("В JSON-строку",inputs=[("data","any",None),("indent","number",2)],outputs=[("json_text","text")])
def to_json(data,indent): return json.dumps(data,ensure_ascii=False,indent=int(num(indent,2)))

@nd("Скачать файл",
    inputs=[("url","text",""),("out","file","download.bin"),("timeout","number",30)],
    outputs=[("result_path","text"),("size_bytes","number")],tags=["download","file"])
def download_file(url,out,timeout):
    resp=_r().get(txt(url),stream=True,timeout=num(timeout,30)); resp.raise_for_status()
    dst=txt(out) or "download.bin"; size=0
    with open(dst,"wb") as f:
        for chunk in resp.iter_content(chunk_size=8192): f.write(chunk); size+=len(chunk)
    return dst,float(size)

@nd("Проверить связь",
    inputs=[("url","text","https://www.google.com"),("timeout","number",5)],
    outputs=[("reachable","bool"),("latency_ms","number")],tags=["ping","network"])
def ping_url(url,timeout):
    t0=time.perf_counter()
    try:
        resp=_r().head(txt(url),timeout=num(timeout,5),allow_redirects=True)
        return resp.ok,(time.perf_counter()-t0)*1000
    except: return False,-1.0
