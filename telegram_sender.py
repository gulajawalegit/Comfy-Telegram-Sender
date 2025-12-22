import requests
import os

class TelegramSendVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": ("VHS_FILENAMES",),  # Tipe khusus dari VideoHelperSuite
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
        # Handle output format from VideoHelperSuite: (should_preview: bool, filenames: list)
        if isinstance(video_paths, tuple) and len(video_paths) == 2:
            _, file_list = video_paths
        elif isinstance(video_paths, list):
            file_list = video_paths
        elif isinstance(video_paths, str):
            file_list = [video_paths]
        else:
            raise TypeError(f"Unsupported input type for video_paths: {type(video_paths)}")

        if not file_list:
            raise FileNotFoundError("No files provided in video_paths")

        # Prioritize actual video files (filter out images like .png, .jpg)
        VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.mkv', '.gif'}
        video_path = None

        # Search from the end (VideoHelperSuite usually puts .mp4 last)
        for path in reversed(file_list):
            if os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS:
                video_path = path
                break

        # Fallback: use last file if no known video extension found
        if video_path is None:
            video_path = file_list[-1]

        if not isinstance(video_path, str):
            raise TypeError(f"Expected string path, got: {type(video_path)}")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at path: {video_path}")

        # Prepare caption
        caption = (
            "🎬 Video Generated Successfully\n\n"
            "📝 Prompt Used:\n"
            f"{prompt_text[:900]}"
        )

        # ✅ Fixed Telegram API URL — no extra spaces!
        url = f"https://api.telegram.org/bot{bot_token}/sendVideo"

        # Send video via Telegram Bot API
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
