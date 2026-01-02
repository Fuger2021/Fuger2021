# cut.py
import os
import sys
import numpy as np
from PIL import Image

# ====== 配置区（可改）======
SRC = "snake.gif"
DST = "snake_cut.gif"
START = 0.0      # 起始时间（秒）
END = 19.67      # 结束时间（秒）
# ==========================

def ensure_no_black_frames_and_cut(input_path, output_path, start_sec, end_sec):
    """
    精准裁剪 GIF 时间段，并确保无黑帧：
    - 模拟 disposal 行为逐帧渲染完整画面
    - 仅保留 [start_sec, end_sec) 区间内帧
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input not found: {input_path}")

    frames_full = []   # 存储完整渲染后的帧（RGBA numpy array）
    durations_ms = []  # 对应帧延迟（ms）
    frame_start_times = [0.0]  # 每帧开始时刻（秒）

    with Image.open(input_path) as im:
        canvas = None
        current_time = 0.0
        frame_idx = 0

        while True:
            try:
                # 获取当前帧元数据
                disposal = im.info.get("disposal", 0)  # 0=none, 1=keep, 2=restore bg
                duration = im.info.get("duration", 100)  # ms
                duration_sec = duration / 1000.0

                # 计算本帧时间区间 [current_time, current_time + duration_sec)
                frame_start = current_time
                frame_end = current_time + duration_sec

                # 转 RGBA 帧
                frame_rgba = im.convert("RGBA")

                # 🎯 模拟 disposal 渲染完整画面
                if frame_idx == 0:
                    canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
                    canvas.paste(frame_rgba, (0, 0), frame_rgba)
                else:
                    if disposal == 2:
                        # 清空 → 新透明画布 + 贴当前帧
                        canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
                        canvas.paste(frame_rgba, (0, 0), frame_rgba)
                    elif disposal == 1:
                        # 保留上一帧 → 叠加
                        canvas.paste(frame_rgba, (0, 0), frame_rgba)
                    else:
                        # 替换整帧
                        canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
                        canvas.paste(frame_rgba, (0, 0), frame_rgba)

                # ✅ 仅当本帧与 [start_sec, end_sec) 有交集时才保留
                if frame_end > start_sec and frame_start < end_sec:
                    frames_full.append(np.array(canvas))
                    # 计算本帧**在新 GIF 中应显示的时长**
                    show_start = max(start_sec, frame_start)
                    show_end = min(end_sec, frame_end)
                    show_duration_sec = max(0.01, show_end - show_start)  # ≥10ms
                    durations_ms.append(int(round(show_duration_sec * 1000)))

                # 更新时间 & 下一帧
                current_time = frame_end
                frame_start_times.append(current_time)
                frame_idx += 1
                im.seek(im.tell() + 1)

            except EOFError:
                break

    if not frames_full:
        raise ValueError(f"No frames in time range [{start_sec}, {end_sec})s")

    print(f"✂️ Kept {len(frames_full)} frames from [{start_sec}, {end_sec})s")

    # 🟢 写出——统一使用 disposal=2（最干净结尾）
    pil_frames = [Image.fromarray(f) for f in frames_full]
    pil_frames[0].save(
        output_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=durations_ms,
        loop=0,
        disposal=2,       # ⭐ 关键：每帧后恢复背景 → 结尾无残留
        optimize=False,
    )
    print(f"✅ Saved to {output_path}")


def main():
    print(f"✂️ Cutting: {SRC}")
    print(f"⏱  Time: [{START}, {END}) seconds")
    print(f"💾 Output: {DST}")
    ensure_no_black_frames_and_cut(SRC, DST, START, end_sec=END)


if __name__ == "__main__":
    main()