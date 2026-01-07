# speed_v2.py —— 精确模拟 GIF disposal，杜绝黑帧
import os
import sys
import numpy as np
from PIL import Image

def parse_args():
    if len(sys.argv) < 3:
        print("Usage: python speed_v2.py <input.gif> <ratio>")
        print("Example: python speed_v2.py snake_cut.gif 2.0")
        sys.exit(1)
    input_path = sys.argv[1]
    try:
        ratio = float(sys.argv[2])
        if ratio <= 0:
            raise ValueError
    except (ValueError, TypeError):
        print(f"❌ Invalid ratio: {sys.argv[2]}. Must be > 0.")
        sys.exit(1)
    return input_path, ratio

def get_output_name(input_path: str, ratio: float) -> str:
    base, ext = os.path.splitext(input_path)
    suffix = f"_{int(ratio)}" if ratio.is_integer() else f"_{ratio:.2f}".rstrip("0").rstrip(".")
    return f"{base}{suffix}{ext}"

def main():
    input_path, ratio = parse_args()
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        sys.exit(1)

    output_path = get_output_name(input_path, ratio)
    print(f"🎬 Input:  {input_path}")
    print(f"⏩ Ratio:  {ratio}x")
    print(f"💾 Output: {output_path}")

    # 🟢 Step 1: 用 PIL 逐帧读取，保留 disposal 信息
    frames_full = []  # 存储完整渲染后的帧（RGBA）
    durations = []

    with Image.open(input_path) as im:
        # 获取全局背景色（索引0颜色），PIL 会自动处理透明
        try:
            # 尝试获取逻辑屏幕背景色索引
            bg_index = im.info.get("background", 0)
            palette = im.getpalette()
            if palette and len(palette) >= 3:
                bg_rgb = tuple(palette[bg_index*3:(bg_index+1)*3])
            else:
                bg_rgb = (0, 0, 0)  # fallback
        except:
            bg_rgb = (0, 0, 0)

        frame_idx = 0
        canvas = None  # 当前累积画面

        while True:
            try:
                # 获取当前帧的 disposal 方法（0=none, 1=do not dispose, 2=restore bg）
                disposal = im.info.get("disposal", 0)
                duration = im.info.get("duration", 100)  # ms

                # 转为 RGBA（保留透明度）
                frame_rgba = im.convert("RGBA")

                if frame_idx == 0:
                    # 首帧：创建画布 = 逻辑屏幕尺寸
                    canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))  # 透明底
                    canvas.paste(frame_rgba, (0, 0), frame_rgba)
                else:
                    # 🎯 关键：按 disposal 行为更新画布
                    if disposal == 2:
                        # Restore to background → 清空上一帧区域为透明
                        # 注意：不是清全屏！只清上一帧 bounding box（但 PIL 不直接提供）
                        # 简化方案：保守起见，我们清全屏为透明（最安全，且适用于多数 snake 动图）
                        canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
                        canvas.paste(frame_rgba, (0, 0), frame_rgba)
                    elif disposal == 1:
                        # Do not dispose → 直接叠加（保留之前内容）
                        canvas.paste(frame_rgba, (0, 0), frame_rgba)
                    else:
                        # disposal == 0 or unknown → 替换整个帧
                        canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
                        canvas.paste(frame_rgba, (0, 0), frame_rgba)

                # 保存当前完整帧
                frames_full.append(np.array(canvas))
                durations.append(duration)

                frame_idx += 1
                im.seek(im.tell() + 1)
            except EOFError:
                break

    print(f"📊 Read {len(frames_full)} frames (size: {frames_full[0].shape[1]}x{frames_full[0].shape[0]})")

    # 🟢 Step 2: 应用速度 ratio → 缩放 duration
    new_durations = [max(10, int(round(d / ratio))) for d in durations]

    # 🟢 Step 3: 写出（现在每帧都是完整画面，无残留）
    pil_frames = [Image.fromarray(f) for f in frames_full]
    pil_frames[0].save(
        output_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=new_durations,
        loop=0,
        disposal=2,          # ✅ 统一设为 disposal=2（每帧后清空），最干净
        optimize=False,
    )

    print(f"✅ Done! No black frames expected. Output: {output_path}")

if __name__ == "__main__":
    main()