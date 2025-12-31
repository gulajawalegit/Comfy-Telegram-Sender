import requests
import os

class TelegramSendMedia:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "media_paths": ("VHS_FILENAMES",),  # Bisa video atau image
                "prompt_text": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "bot_token": ("STRING", {
                    "default": ""
                }),
                "chat_id": ("STRING", {
                    "default": ""
                }),
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
    FUNCTION = "send_media"
    OUTPUT_NODE = True
    CATEGORY = "utils/telegram"

    # -------------------------

    def format_render_time(self, seconds):
        if seconds <= 0:
            return "⏱️ Waktu render tidak tersedia"
        total_sec = int(seconds)
        mins, secs = divmod(total_sec, 60)
        if mins > 0:
            return f"⏱️ Waktu Render: {mins} menit {secs} detik"
        return f"⏱️ Waktu Render: {secs} detik"

    # -------------------------

    def send_media(self, media_paths, prompt_text, bot_token, chat_id, render_time_seconds=0.0):
        if not bot_token or not chat_id:
            raise ValueError("❌ bot_token dan chat_id wajib diisi!")

        # Extract file list dari VHS_FILENAMES
        if isinstance(media_paths, tuple) and len(media_paths) == 2:
            _, file_list = media_paths
        elif isinstance(media_paths, list):
            file_list = media_paths
        elif isinstance(media_paths, str):
            file_list = [media_paths]
        else:
            raise TypeError(f"Unsupported input type: {type(media_paths)}")

        if not file_list:
            raise FileNotFoundError("❌ Tidak ada file media.")

        VIDEO_EXT = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
        IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}

        media_path = None
        media_type = None

        # Prioritaskan file terakhir (umumnya output final ComfyUI)
        for path in reversed(file_list):
            ext = os.path.splitext(path)[1].lower()
            if ext in VIDEO_EXT:
                media_path = path
                media_type = "video"
                break
            if ext in IMAGE_EXT:
                media_path = path
                media_type = "image"
                break

        if media_path is None:
            raise ValueError("❌ Tidak ditemukan file video atau image yang didukung.")

        if not os.path.exists(media_path):
            raise FileNotFoundError(f"❌ File tidak ditemukan: {media_path}")

        # Telegram bot limit ±50MB
        size_mb = os.path.getsize(media_path) / (1024 * 1024)
        if size_mb > 50:
            raise ValueError(f"❌ File terlalu besar: {size_mb:.1f} MB (Limit 50 MB)")

        # Caption
        time_info = self.format_render_time(render_time_seconds)
        caption = (
            "🎬 Media Generated Successfully\n\n"
            f"{time_info}\n\n"
            "📝 Prompt Used:\n"
            f"{prompt_text[:900]}"
        )

        # Endpoint & payload
        if media_type == "video":
            url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
            files_key = "video"
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            files_key = "photo"

        # Kirim ke Telegram
        try:
            with open(media_path, "rb") as media_file:
                response = requests.post(
                    url,
                    data={
                        "chat_id": chat_id,
                        "caption": caption,
                    },
                    files={
                        files_key: media_file
                    },
                    timeout=120
                )
        except Exception as e:
            raise RuntimeError(f"❌ Gagal mengirim media: {str(e)}")

        if response.status_code != 200:
            raise RuntimeError(
                f"❌ Telegram API Error {response.status_code}: {response.text}"
            )

        print(f"✅ {media_type.upper()} berhasil dikirim: {os.path.basename(media_path)}")
        return {}
