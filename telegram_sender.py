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

    def send_video(self, video_paths, prompt_text, bot_token, chat_id):

        # Handle LIST output from Video Combine
        if isinstance(video_paths, list):
            video_path = video_paths[-1]
        else:
            video_path = video_paths

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
                f"Telegram Error {response.status_code}: {response.text}"
            )

        print(f"✅ Video sent to Telegram: {video_path}")
        return ()
