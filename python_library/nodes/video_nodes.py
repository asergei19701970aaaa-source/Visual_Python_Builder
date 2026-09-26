"""Video nodes 3.23. pip install opencv-python; optional moviepy"""
from python_library.nodes._base import library, num, txt
nd = library("Video", "19. Видео", color="#4a7a8f")

def _cv2():
    try: import cv2; return cv2
    except ImportError as e: raise ValueError("pip install opencv-python") from e
def _moviepy():
    try: from moviepy.editor import VideoFileClip; return VideoFileClip
    except ImportError as e: raise ValueError("pip install moviepy") from e

@nd("Инфо видео",inputs=[("path","file","")],
    outputs=[("frames","number"),("fps","number"),("seconds","number"),("width","number"),("height","number")])
def video_info(path):
    cv2=_cv2(); cap=cv2.VideoCapture(txt(path))
    if not cap.isOpened(): raise ValueError("Не удалось открыть видео")
    fr=cap.get(cv2.CAP_PROP_FRAME_COUNT); fps=cap.get(cv2.CAP_PROP_FPS) or 0
    w=cap.get(cv2.CAP_PROP_FRAME_WIDTH); h=cap.get(cv2.CAP_PROP_FRAME_HEIGHT); cap.release()
    return float(fr),float(fps),float(fr/fps) if fps else 0.0,float(w),float(h)

@nd("Извлечь кадр",
    inputs=[("path","file",""),("frame_no","number",0),("out","file","frame.jpg")],
    outputs=[("result_path","text")])
def extract_frame(path,frame_no,out):
    cv2=_cv2(); cap=cv2.VideoCapture(txt(path))
    cap.set(cv2.CAP_PROP_POS_FRAMES,int(num(frame_no)))
    ret,frame=cap.read(); cap.release()
    if not ret: raise ValueError(f"Кадр {int(num(frame_no))} не найден")
    dst=txt(out) or "frame.jpg"; cv2.imwrite(dst,frame); return dst

@nd("Количество кадров",inputs=[("path","file","")],outputs=[("count","number")])
def frame_count(path):
    cv2=_cv2(); cap=cv2.VideoCapture(txt(path)); c=cap.get(cv2.CAP_PROP_FRAME_COUNT); cap.release(); return float(c)

@nd("Обрезать видео",
    inputs=[("path","file",""),("start","number",0),("end","number",10),("out","file","clip.mp4")],
    outputs=[("result_path","text")])
def trim_video(path,start,end,out):
    VFC=_moviepy(); clip=VFC(txt(path)).subclip(num(start),num(end))
    dst=txt(out) or "clip.mp4"; clip.write_videofile(dst,logger=None); return dst

@nd("Извлечь звук из видео",
    inputs=[("path","file",""),("out","file","audio.mp3")],outputs=[("result_path","text")])
def extract_audio(path,out):
    VFC=_moviepy(); clip=VFC(txt(path)); dst=txt(out) or "audio.mp3"
    clip.audio.write_audiofile(dst,logger=None); return dst
