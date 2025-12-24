import requests
import os

class TelegramSendVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": ("VHS_FILENAMES",),  # Output dari VideoHelperSuite
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
    FUNCTION = "send_video"
    OUTPUT_NODE = True
    CATEGORY = "utils/telegram"

    def format_render_time(self, seconds):
        if seconds <= 0:
            return "⏱️ Waktu render tidak tersedia"
        total_sec = int(seconds)
        mins, secs = divmod(total_sec, 60)
        if mins > 0:
            time_str = f"{mins} menit {secs} detik"
        else:
            time_str = f"{secs} detik"
        return f"⏱️ Waktu Render: {time_str}"

    def send_video(self, video_paths, prompt_text, bot_token, chat_id, render_time_seconds=0.0):
        # Validasi token dan chat_id
        if not bot_token or not chat_id:
            raise ValueError("❌ bot_token dan chat_id wajib diisi!")

        # Ekstrak daftar file dari format VHS_FILENAMES: (should_preview, [file1, file2, ...])
        if isinstance(video_paths, tuple) and len(video_paths) == 2:
            _, file_list = video_paths
        elif isinstance(video_paths, list):
            file_list = video_paths
        elif isinstance(video_paths, str):
            file_list = [video_paths]
        else:
            raise TypeError(f"Unsupported input type for video_paths: {type(video_paths)}")

        if not file_list:
            raise FileNotFoundError("❌ Tidak ada file video yang diberikan.")

        # Prioritaskan ekstensi video (urut dari akhir, karena VHS sering simpan .mp4 terakhir)
        VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.mkv'}
        video_path = None
        for path in reversed(file_list):
            if os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS:
                video_path = path
                break

        # Fallback: gunakan file terakhir jika tidak ada ekstensi dikenal
        if video_path is None:
            video_path = file_list[-1]

        if not isinstance(video_path, str):
            raise TypeError(f"Expected string path, got: {type(video_path)}")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"❌ File video tidak ditemukan: {video_path}")

        # Periksa ukuran file (batas Telegram: 50 MB untuk bot biasa)
        file_size = os.path.getsize(video_path)
        if file_size > 50 * 1024 * 1024:
            raise ValueError(f"❌ File terlalu besar ({file_size / (1024*1024):.1f} MB). Batas Telegram: 50 MB.")

        # Format caption
        time_info = self.format_render_time(render_time_seconds)
        caption = (
            "🎬 Video Generated Successfully\n\n"
            f"{time_info}\n\n"
            "📝 Prompt Used:\n"
            f"{prompt_text[:900]}"
        )

        # ✅ URL Telegram yang BENAR — TANPA SPASI!
        url = f"https://api.telegram.org/bot{bot_token}/sendVideo"

        # Kirim ke Telegram
        try:
            with open(video_path, "rb") as video_file:
                response = requests.post(
                    url,
                    data={
                        "chat_id": chat_id,
                        "caption": caption,
                    },
                    files={
                        "video": video_file
                    },
                    timeout=120
                )
        except Exception as e:
            raise RuntimeError(f"❌ Gagal mengirim ke Telegram: {str(e)}")

        if response.status_code != 200:
            raise RuntimeError(
                f"❌ Telegram API Error {response.status_code}: {response.text}"
            )

        print(f"✅ Video berhasil dikirim ke Telegram! ({os.path.basename(video_path)})")
        return {}
