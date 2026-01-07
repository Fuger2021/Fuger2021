import os
import sys
try:
    from moviepy.editor import VideoFileClip
except ModuleNotFoundError:
    print("moviepy not found for this Python interpreter.")
    print(f"Python executable: {sys.executable}")
    print(f'Try reinstalling with: "{sys.executable}" -m pip install moviepy')
    sys.exit(1)

SRC = "snake.gif"
DST = "snake_cut.gif"
START = 0.0
END = 19.67

def main():
    if not os.path.exists(SRC):
        raise FileNotFoundError(f"{SRC} not found in current directory")
    with VideoFileClip(SRC) as clip:
        clip.subclip(START, END).write_gif(DST, program="ffmpeg")
    print(f"Trimmed GIF saved to {DST}")

if __name__ == "__main__":
    main()
