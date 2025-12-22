import requests
import os

class TelegramSendVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": ("STRING", {
                    "forceInput": True
                }),
                "prompt_text": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "bot_token": ("STRING", {}),
                "chat_id": ("STRING", {}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_video"
    OUTPUT_NODE = True
    CATEGORY = "Telegram"

    def send_video(self, video_path, prompt_text, bot_token, chat_id):
    # Jika input adalah list, ambil elemen terakhir
    if isinstance(video_path, list):
        video_path = video_path[-1]

    # Jika input adalah dict (biasa dari Video Combine), coba ambil key 'filename' atau 'path'
    elif isinstance(video_path, dict):
        # Coba cari key yang umum digunakan
        if 'filename' in video_path:
            video_path = video_path['filename']
        elif 'path' in video_path:
            video_path = video_path['path']
        else:
            # Jika tidak ada, coba konversi ke string
            video_path = str(video_path)

    # Pastikan video_path adalah string
    if not isinstance(video_path, str):
        raise TypeError(f"Expected string or list/dict with path, got {type(video_path)}")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    caption = (
        "🎬 Video Generated Successfully\n\n"
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
            f"Telegram API Error {response.status_code}: {response.text}"
        )

    print(f"✅ Video sent to Telegram: {video_path}")
    return {}
