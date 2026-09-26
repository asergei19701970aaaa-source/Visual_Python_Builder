"""AI nodes 3.23. pip install requests"""
import json, os
from python_library.nodes._base import library, txt, num
nd = library("AI", "22. Искусственный интеллект", color="#9a5cff")
OAI_URL = "https://api.openai.com/v1/chat/completions"

def _r():
    try: import requests; return requests
    except ImportError as e: raise ValueError("pip install requests") from e

def _key(env):
    k=os.environ.get(txt(env) or "OPENAI_API_KEY")
    if not k: raise ValueError("Нет API-ключа в " + (txt(env) or "OPENAI_API_KEY"))
    return k

def _oai(key, messages, model="gpt-4o-mini", timeout=60):
    resp=_r().post(OAI_URL, headers={"Authorization": "Bearer "+key, "Content-Type": "application/json"},
                   data=json.dumps({"model": model, "messages": messages}), timeout=timeout)
    if resp.status_code>=400: raise ValueError(f"OpenAI {resp.status_code}: {resp.text[:400]}")
    return resp.json()["choices"][0]["message"]["content"]

@nd("Промпт",inputs=[("text","text","Hello"),("system","text","Ты помощник")],outputs=[("prompt","dict")])
def prompt(text,system): return {"text":txt(text),"system":txt(system)}

@nd("OpenAI Chat",
    inputs=[("prompt","dict",None),("model","text","gpt-4o-mini"),("api_key_env","text","OPENAI_API_KEY"),("timeout","number",60)],
    outputs=[("answer","text"),("tokens_used","number")],tags=["ai","openai","gpt"])
def openai_chat(prompt,model,api_key_env,timeout):
    key=_key(api_key_env)
    pr=prompt if isinstance(prompt,dict) else {"text":txt(prompt),"system":"Ты помощник"}
    payload={"model":txt(model) or "gpt-4o-mini",
             "messages":[{"role":"system","content":pr.get("system","")},{"role":"user","content":pr.get("text","")}]}
    resp=_r().post(OAI_URL,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},
                   data=json.dumps(payload),timeout=num(timeout,60))
    if resp.status_code>=400: raise ValueError(f"OpenAI {resp.status_code}: {resp.text[:400]}")
    data=resp.json(); answer=data["choices"][0]["message"]["content"]
    return answer,float(data.get("usage",{}).get("total_tokens",0))

@nd("Local AI Chat (Ollama)",
    inputs=[("text","text","Hello!"),("system","text","Ты помощник"),("model","text","llama3"),("base_url","text","http://localhost:11434"),("timeout","number",120)],
    outputs=[("answer","text")],tags=["ai","ollama","local","llm"])
def local_ai_chat(text,system,model,base_url,timeout):
    url=txt(base_url).rstrip("/")+"/v1/chat/completions"
    resp=_r().post(url,json={"model":txt(model),"messages":[{"role":"system","content":txt(system)},{"role":"user","content":txt(text)}]},timeout=num(timeout,120))
    if resp.status_code>=400: raise ValueError(f"Local AI {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"]

@nd("Оценка тона",inputs=[("text","text",""),("api_key_env","text","OPENAI_API_KEY")],
    outputs=[("sentiment","text"),("score","number")],tags=["sentiment","nlp"])
def sentiment(text,api_key_env):
    key=_key(api_key_env)
    raw=_oai(key,[{"role":"system","content":'Reply ONLY with JSON: {"sentiment":"positive|negative|neutral","score":0.0}'},
                  {"role":"user","content":txt(text)}],timeout=30)
    parsed=json.loads(raw)
    return parsed.get("sentiment","neutral"),float(parsed.get("score",0.5))

@nd("Суммаризировать текст",
    inputs=[("text","text",""),("max_sentences","number",3),("api_key_env","text","OPENAI_API_KEY")],
    outputs=[("summary","text")],tags=["summarize","nlp"])
def summarize(text,max_sentences,api_key_env):
    n=int(num(max_sentences,3))
    return _oai(_key(api_key_env),[{"role":"system","content":f"Summarize in {n} sentences. Reply with summary ONLY."},
                                    {"role":"user","content":txt(text)}],timeout=30)
