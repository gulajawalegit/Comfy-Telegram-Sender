import requests
import os

# ===================== UTIL =====================
def normalize_path(input_path):
    """
    Normalize ComfyUI path input:
    - string
    - list[str]
    - tuple
    """
    if isinstance(input_path, list):
        if not input_path:
            raise ValueError("❌ Path list kosong")
        return input_path[-1]

    if isinstance(input_path, tuple):
        return normalize_path(list(input_path))

    if isinstance(input_path, str):
        return input_path

    raise TypeError(f"❌ Unsupported path type: {type(input_path)}")


def format_render_time(seconds: float) -> str:
    if seconds <= 0:
        return "⏱️ Render time not available"
    total = int(seconds)
    mins, secs = divmod(total, 60)
    return f"⏱️ Render Time: {mins}m {secs}s" if mins else f"⏱️ Render Time: {secs}s"


# ===================== IMAGE NODE =====================
class TelegramSendImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_path": ("STRING",),
                "prompt_text": ("STRING", {"multiline": True, "default": ""}),
                "bot_token": ("STRING", {"default": ""}),
                "chat_id": ("STRING", {"default": ""}),
            },
            "optional": {
                "render_time_seconds": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 0.1
                }),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_image"
    OUTPUT_NODE = True
    CATEGORY = "utils/telegram"

    def send_image(
        self,
        image_path,
        prompt_text,
        bot_token,
        chat_id,
        render_time_seconds=0.0
    ):
        if not bot_token or not chat_id:
            raise ValueError("❌ bot_token dan chat_id wajib diisi")

        image_path = normalize_path(image_path)

        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)

        file_size = os.path.getsize(image_path)
        if file_size > 50 * 1024 * 1024:
            raise ValueError(f"❌ Image terlalu besar ({file_size / 1024 / 1024:.1f} MB)")

        caption = (
            "🖼️ Image Generated Successfully\n\n"
            f"{format_render_time(render_time_seconds)}\n\n"
            "📝 Prompt Used:\n"
            f"{prompt_text[:900]}"
        )

        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

        with open(image_path, "rb") as image_file:
            response = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "caption": caption
                },
                files={
                    "photo": image_file
                },
                timeout=120
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"❌ Telegram API Error {response.status_code}: {response.text}"
            )

        print(f"✅ Image terkirim: {os.path.basename(image_path)}")
        return {}


# ===================== VIDEO NODE =====================
class TelegramSendVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": ("VHS_FILENAMES",),
                "prompt_text": ("STRING", {"multiline": True, "default": ""}),
                "bot_token": ("STRING", {"default": ""}),
                "chat_id": ("STRING", {"default": ""}),
            },
            "optional": {
                "render_time_seconds": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 0.1
                }),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_video"
    OUTPUT_NODE = True
    CATEGORY = "utils/telegram"

    def send_video(
        self,
        video_paths,
        prompt_text,
        bot_token,
        chat_id,
        render_time_seconds=0.0
    ):
        if not bot_token or not chat_id:
            raise ValueError("❌ bot_token dan chat_id wajib diisi")

        # Normalize VHS_FILENAMES
        if isinstance(video_paths, tuple) and len(video_paths) == 2:
            _, file_list = video_paths
        elif isinstance(video_paths, list):
            file_list = video_paths
        elif isinstance(video_paths, str):
            file_list = [video_paths]
        else:
            raise TypeError(f"❌ Unsupported video_paths type: {type(video_paths)}")

        if not file_list:
            raise FileNotFoundError("❌ Tidak ada file video")

        video_path = normalize_path(file_list)

        if not os.path.exists(video_path):
            raise FileNotFoundError(video_path)

        file_size = os.path.getsize(video_path)
        if file_size > 50 * 1024 * 1024:
            raise ValueError(f"❌ Video terlalu besar ({file_size / 1024 / 1024:.1f} MB)")

        caption = (
            "🎬 Video Generated Successfully\n\n"
            f"{format_render_time(render_time_seconds)}\n\n"
            "📝 Prompt Used:\n"
            f"{prompt_text[:900]}"
        )

        url = f"https://api.telegram.org/bot{bot_token}/sendVideo"

        with open(video_path, "rb") as video_file:
            response = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "caption": caption
                },
                files={
                    "video": video_file
                },
                timeout=120
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"❌ Telegram API Error {response.status_code}: {response.text}"
            )

        print(f"✅ Video terkirim: {os.path.basename(video_path)}")
        return {}
