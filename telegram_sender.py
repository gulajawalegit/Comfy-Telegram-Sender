import requests
import os

# ================= IMAGE =================
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

    def format_render_time(self, seconds):
        if seconds <= 0:
            return "⏱️ Render time not available"
        mins, secs = divmod(int(seconds), 60)
        return f"⏱️ Render Time: {mins}m {secs}s" if mins else f"⏱️ Render Time: {secs}s"

    def send_image(self, image_path, prompt_text, bot_token, chat_id, render_time_seconds=0.0):
        if not bot_token or not chat_id:
            raise ValueError("bot_token & chat_id required")

        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)

        if os.path.getsize(image_path) > 50 * 1024 * 1024:
            raise ValueError("Image > 50MB")

        caption = (
            "🖼️ Image Generated\n\n"
            f"{self.format_render_time(render_time_seconds)}\n\n"
            f"📝 Prompt:\n{prompt_text[:900]}"
        )

        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

        with open(image_path, "rb") as f:
            r = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption},
                files={"photo": f},
                timeout=120
            )

        if r.status_code != 200:
            raise RuntimeError(r.text)

        print(f"✅ Image sent: {os.path.basename(image_path)}")
        return {}

# ================= VIDEO =================
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

    def format_render_time(self, seconds):
        if seconds <= 0:
            return "⏱️ Render time not available"
        mins, secs = divmod(int(seconds), 60)
        return f"⏱️ Render Time: {mins}m {secs}s" if mins else f"⏱️ Render Time: {secs}s"

    def send_video(self, video_paths, prompt_text, bot_token, chat_id, render_time_seconds=0.0):
        if isinstance(video_paths, tuple):
            _, files = video_paths
        else:
            files = video_paths if isinstance(video_paths, list) else [video_paths]

        video_path = files[-1]
        if not os.path.exists(video_path):
            raise FileNotFoundError(video_path)

        if os.path.getsize(video_path) > 50 * 1024 * 1024:
            raise ValueError("Video > 50MB")

        caption = (
            "🎬 Video Generated\n\n"
            f"{self.format_render_time(render_time_seconds)}\n\n"
            f"📝 Prompt:\n{prompt_text[:900]}"
        )

        url = f"https://api.telegram.org/bot{bot_token}/sendVideo"

        with open(video_path, "rb") as f:
            r = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption},
                files={"video": f},
                timeout=120
            )

        if r.status_code != 200:
            raise RuntimeError(r.text)

        print(f"✅ Video sent: {os.path.basename(video_path)}")
        return {}
