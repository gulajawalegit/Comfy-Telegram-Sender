import os
import sys
import requests
import subprocess
import shutil
import tempfile
import platform
import zipfile
import urllib.request

# ===================== SIZE LIMIT =====================
PHOTO_LIMIT = 10 * 1024 * 1024
BOT_LIMIT   = 50 * 1024 * 1024


# ===================== DEPENDENCY =====================
def ensure_pillow():
    try:
        from PIL import Image
        return True
    except ImportError:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pillow"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            from PIL import Image
            return True
        except Exception:
            return False


def install_oxipng():
    system = platform.system().lower()
    try:
        if system == "linux":
            subprocess.run(
                ["apt", "install", "-y", "oxipng"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return shutil.which("oxipng") is not None

        if system == "windows":
            url = "https://github.com/shssoichiro/oxipng/releases/latest/download/oxipng-x86_64-pc-windows-msvc.zip"
            install_dir = os.path.join(os.getcwd(), "bin")
            os.makedirs(install_dir, exist_ok=True)

            zip_path = os.path.join(install_dir, "oxipng.zip")
            exe_path = os.path.join(install_dir, "oxipng.exe")

            if not os.path.exists(exe_path):
                urllib.request.urlretrieve(url, zip_path)
                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(install_dir)
                os.remove(zip_path)

            os.environ["PATH"] += os.pathsep + install_dir
            return shutil.which("oxipng") is not None

        return False
    except Exception:
        return False


def ensure_oxipng():
    if shutil.which("oxipng"):
        return True
    return install_oxipng()


# ===================== PATH NORMALIZER (FIX UTAMA) =====================
def normalize_path(path):
    """
    Normalize ANY ComfyUI output to valid file path string
    """
    while isinstance(path, (list, tuple)):
        if not path:
            raise ValueError("❌ Empty path list")
        path = path[-1]

    if isinstance(path, dict):
        for v in path.values():
            try:
                return normalize_path(v)
            except Exception:
                pass
        raise TypeError("❌ Dict does not contain valid path")

    if isinstance(path, os.PathLike):
        return os.fspath(path)

    if isinstance(path, str):
        return path

    raise TypeError(f"❌ Unsupported path type: {type(path)}")


# ===================== PNG OPTIMIZER =====================
def optimize_png_auto(input_path, min_size_mb=1.0):
    input_path = normalize_path(input_path)

    if not input_path.lower().endswith(".png"):
        return input_path

    if not os.path.exists(input_path):
        return input_path

    try:
        original_size = os.path.getsize(input_path)
        if original_size < min_size_mb * 1024 * 1024:
            return input_path

        best_path = input_path
        best_size = original_size
        tmp_dir = tempfile.gettempdir()

        # ---------- OXIPNG ----------
        if ensure_oxipng():
            oxi_path = os.path.join(tmp_dir, f"oxipng_{os.path.basename(input_path)}")
            try:
                subprocess.run(
                    ["oxipng", "-o", "6", "--strip", "all", "--quiet", input_path, "-o", oxi_path],
                    check=True
                )
                size = os.path.getsize(oxi_path)
                if size < best_size:
                    best_path, best_size = oxi_path, size
            except Exception:
                pass

        # ---------- PILLOW ----------
        if ensure_pillow():
            try:
                from PIL import Image
                pil_path = os.path.join(tmp_dir, f"pillow_{os.path.basename(input_path)}")
                with Image.open(input_path) as img:
                    img.save(pil_path, optimize=True, compress_level=9)
                size = os.path.getsize(pil_path)
                if size < best_size:
                    best_path, best_size = pil_path, size
            except Exception:
                pass

        return best_path

    except Exception:
        return input_path


# ===================== UTIL =====================
def format_render_time(seconds):
    if seconds <= 0:
        return ""
    m, s = divmod(int(seconds), 60)
    return f"⏱️ Render Time: {m}m {s}s" if m else f"⏱️ Render Time: {s}s"


def send_document(bot_token, chat_id, file_path, caption):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(file_path, "rb") as f:
        return requests.post(
            url,
            data={"chat_id": chat_id, "caption": caption},
            files={"document": f},
            timeout=300
        )


# ===================== IMAGE NODE =====================
class TelegramSendImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_path": ("STRING",),
                "prompt_text": ("STRING", {"multiline": True}),
                "bot_token": ("STRING",),
                "chat_id": ("STRING",),
            },
            "optional": {
                "render_time_seconds": ("FLOAT", {"default": 0.0}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_image"
    OUTPUT_NODE = True
    CATEGORY = "utils/telegram"

    def send_image(self, image_path, prompt_text, bot_token, chat_id, render_time_seconds=0.0):
        image_path = optimize_png_auto(image_path)
        size = os.path.getsize(image_path)

        caption = (
            "🖼️ Image Generated Successfully\n\n"
            f"{format_render_time(render_time_seconds)}\n\n"
            f"{prompt_text[:900]}"
        )

        if size <= PHOTO_LIMIT:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            with open(image_path, "rb") as f:
                r = requests.post(
                    url,
                    data={"chat_id": chat_id, "caption": caption},
                    files={"photo": f},
                    timeout=120
                )
        else:
            r = send_document(bot_token, chat_id, image_path, caption)

        if r.status_code != 200:
            raise RuntimeError(r.text)

        return {}


# ===================== VIDEO NODE =====================
class TelegramSendVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": ("VHS_FILENAMES",),
                "prompt_text": ("STRING", {"multiline": True}),
                "bot_token": ("STRING",),
                "chat_id": ("STRING",),
            },
            "optional": {
                "render_time_seconds": ("FLOAT", {"default": 0.0}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_video"
    OUTPUT_NODE = True
    CATEGORY = "utils/telegram"

    def send_video(self, video_paths, prompt_text, bot_token, chat_id, render_time_seconds=0.0):
        video_path = normalize_path(video_paths)
        size = os.path.getsize(video_path)

        caption = (
            "🎬 Video Generated Successfully\n\n"
            f"{format_render_time(render_time_seconds)}\n\n"
            f"{prompt_text[:900]}"
        )

        if size <= BOT_LIMIT:
            url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
            with open(video_path, "rb") as f:
                r = requests.post(
                    url,
                    data={"chat_id": chat_id, "caption": caption},
                    files={"video": f},
                    timeout=300
                )
        else:
            r = send_document(bot_token, chat_id, video_path, caption)

        if r.status_code != 200:
            raise RuntimeError(r.text)

        return {}
