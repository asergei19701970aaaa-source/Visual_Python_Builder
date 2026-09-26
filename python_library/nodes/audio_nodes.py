"""Audio nodes 3.23. pip install sounddevice soundfile pydub"""
import wave
from python_library.nodes._base import library, num, txt
nd = library("Audio", "18. Аудио", color="#8f4a7a")

@nd("Длительность WAV",
    inputs=[("path","file","")],
    outputs=[("seconds","number"),("frames","number"),("channels","number"),("rate","number")],
    tags=["wav","audio","duration"])
def wav_duration(path):
    with wave.open(txt(path),"rb") as h:
        rate=float(h.getframerate() or 1); frames=float(h.getnframes()); ch=float(h.getnchannels())
    return frames/rate, frames, ch, rate

@nd("Инфо WAV",inputs=[("path","file","")],outputs=[("info","text")])
def wav_info(path):
    with wave.open(txt(path),"rb") as h:
        rate=h.getframerate(); frames=h.getnframes(); ch=h.getnchannels(); bits=h.getsampwidth()*8
    return f"Каналов: {ch}, Частота: {rate} Гц, {bits} бит, {frames/(rate or 1):.2f} с"

def _sd():
    try: import sounddevice as sd; return sd
    except ImportError as e: raise ValueError("pip install sounddevice soundfile") from e
def _sf():
    try: import soundfile as sf; return sf
    except ImportError as e: raise ValueError("pip install soundfile") from e
def _pydub():
    try: from pydub import AudioSegment; return AudioSegment
    except ImportError as e: raise ValueError("pip install pydub") from e

@nd("Воспроизвести аудио",
    inputs=[("path","file",""),("blocking","bool",True)],outputs=[("done","bool")])
def play_audio(path,blocking):
    sf=_sf(); sd=_sd(); data,rate=sf.read(txt(path),dtype="float32"); sd.play(data,rate)
    if blocking: sd.wait()
    return True

@nd("Список аудио-устройств",inputs=[],outputs=[("info","text")])
def list_audio_devices(): return str(_sd().query_devices())

@nd("Конвертировать аудио",
    inputs=[("src","file",""),("dst","file","out.mp3"),("fmt","text","mp3")],
    outputs=[("result_path","text")])
def convert_audio(src,dst,fmt):
    AS=_pydub(); seg=AS.from_file(txt(src)); out=txt(dst)
    seg.export(out,format=txt(fmt) or "mp3"); return out

@nd("Обрезать аудио",
    inputs=[("src","file",""),("start_ms","number",0),("end_ms","number",5000),("dst","file","clip.wav")],
    outputs=[("result_path","text")])
def trim_audio(src,start_ms,end_ms,dst):
    AS=_pydub(); seg=AS.from_file(txt(src)); clip=seg[int(num(start_ms)):int(num(end_ms))]
    out=txt(dst); clip.export(out); return out

@nd("Громкость dB",inputs=[("path","file","")],outputs=[("dBFS","number")])
def audio_loudness(path): return float(_pydub().from_file(txt(path)).dBFS)
