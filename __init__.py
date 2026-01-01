from .telegram_sender import TelegramSendVideo, TelegramSendImage

NODE_CLASS_MAPPINGS = {
    "TelegramSendVideo": TelegramSendVideo,
    "TelegramSendImage": TelegramSendImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TelegramSendVideo": "Telegram Send Video",
    "TelegramSendImage": "Telegram Send Image",
}
