import requests
import os
import textwrap

class TelegramSendVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {}),
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

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        # Telegram caption limit = 1024 chars
        prompt_text = prompt_text.strip()

        caption_header = "🎬 Video Generated Successfully\n\n📝 Prompt Used:\n"
        max_prompt_length = 900  # safe limit

        if len(prompt_text) > max_prompt_length:
            prompt_text = prompt_text[:max_prompt_length] + "\n...\n[Prompt Truncated]"

        caption = caption_header + prompt_text

        url = f"https://api.telegram.org/bot{bot_token}/sendVideo"

        with open(video_path, "rb") as video_file:
            response = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "HTML"
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

        print("✅ Video + Prompt sent to Telegram successfully")
        return ()
