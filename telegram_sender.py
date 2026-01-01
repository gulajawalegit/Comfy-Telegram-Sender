import requests
import os

PHOTO_LIMIT = 10 * 1024 * 1024      # 10 MB
BOT_LIMIT = 50 * 1024 * 1024        # 50 MB


# ===================== UTIL =====================
def normalize_path(input_path):
    if isinstance(input_path, list):
        if not input_path:
            raise ValueError("❌ Path list kosong")
        return input_path[-1]

    if isinstance(input_path, tuple):
        return normalize_path(list(input_path))

    if isinstance(input_path, str):
        return input_path

    raise TypeError(f"❌ Unsupported path type: {type(input_path)}")


def format_render_time(seconds):
    if seconds <= 0:
        return "⏱️ Render time not available"
    mins, secs = divmod(int(seconds), 60)
    return f"⏱️ Render Time: {mins}m {secs}s" if mins else f"⏱️ Render Time: {secs}s"


def send_document(bot_token, chat_id, file_path, caption):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(file_path, "rb") as f:
        r = requests.post(
            url,
            data={"chat_id": chat_id, "caption": caption},
            files={"document": f},
            timeout=300
        )
    return r


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
                    "default": 0.0, "min": 0.0, "step": 0.1
                }),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_image"
    OUTPUT_NODE = True
    CATEGORY = "utils/telegram"

    def send_image(self, image_path, prompt_text, bot_token, chat_id, render_time_seconds=0.0):
        image_path = normalize_path(image_path)

        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)

        size = os.path.getsize(image_path)

        caption = (
            "🖼️ Image Generated Successfully\n\n"
            f"{format_render_time(render_time_seconds)}\n\n"
            "📝 Prompt Used:\n"
            f"{prompt_text[:900]}"
        )

        # =====<= 10MB : PHOTO =====
        if size <= PHOTO_LIMIT:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            with open(image_path, "rb") as f:
                r = requests.post(
                    url,
                    data={"chat_id": chat_id, "caption": caption},
                    files={"photo": f},
                    timeout=120
                )

        # =====> 10MB : DOCUMENT =====
        elif size <= BOT_LIMIT:
            r = send_document(bot_token, chat_id, image_path, caption)

        else:
            raise ValueError(f"❌ Image > 50MB ({size / 1024 / 1024:.1f} MB)")

        if r.status_code != 200:
            raise RuntimeError(f"❌ Telegram API Error: {r.text}")

        print(f"✅ Image terkirim ({'PHOTO' if size <= PHOTO_LIMIT else 'DOCUMENT'}): {os.path.basename(image_path)}")
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
                    "default": 0.0, "min": 0.0, "step": 0.1
                }),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_video"
    OUTPUT_NODE = True
    CATEGORY = "utils/telegram"

    def send_video(self, video_paths, prompt_text, bot_token, chat_id, render_time_seconds=0.0):
        if isinstance(video_paths, tuple):
            _, files = video_paths
        elif isinstance(video_paths, list):
            files = video_paths
        else:
            files = [video_paths]

        video_path = normalize_path(files)

        if not os.path.exists(video_path):
            raise FileNotFoundError(video_path)

        size = os.path.getsize(video_path)

        caption = (
            "🎬 Video Generated Successfully\n\n"
            f"{format_render_time(render_time_seconds)}\n\n"
            "📝 Prompt Used:\n"
            f"{prompt_text[:900]}"
        )

        # =====<= 50MB : VIDEO =====
        if size <= BOT_LIMIT:
            url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
            with open(video_path, "rb") as f:
                r = requests.post(
                    url,
                    data={"chat_id": chat_id, "caption": caption},
                    files={"video": f},
                    timeout=300
                )

        # =====> 50MB : DOCUMENT =====
        else:
            r = send_document(bot_token, chat_id, video_path, caption)

        if r.status_code != 200:
            raise RuntimeError(f"❌ Telegram API Error: {r.text}")

        print(
            f"✅ Video terkirim sebagai "
            f"{'VIDEO' if size <= BOT_LIMIT else 'DOCUMENT'}: "
            f"{os.path.basename(video_path)}"
        )
        return {}
