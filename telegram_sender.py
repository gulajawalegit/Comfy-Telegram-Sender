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
PHOTO_LIMIT = 10 * 1024 * 1024      # 10 MB
BOT_LIMIT   = 50 * 1024 * 1024      # 50 MB


# ===================== DEPENDENCY =====================
def ensure_pillow():
    try:
        from PIL import Image
        return True
    except ImportError:
        print("📦 Pillow not found, installing...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pillow"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            from PIL import Image
            print("✅ Pillow installed")
            return True
        except Exception as e:
            print(f"❌ Pillow install failed: {e}")
            return False


def install_oxipng():
    system = platform.system().lower()

    try:
        # ---------- LINUX ----------
        if system == "linux":
            print("📦 Installing oxipng via apt (Linux)")
            subprocess.run(
                ["sudo", "apt", "install", "-y", "oxipng"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return shutil.which("oxipng") is not None

        # ---------- WINDOWS ----------
        if system == "windows":
            url = (
                "https://github.com/shssoichiro/oxipng/releases/latest/"
                "download/oxipng-x86_64-pc-windows-msvc.zip"
            )
            install_dir = os.path.join(os.getcwd(), "bin")
            os.makedirs(install_dir, exist_ok=True)

            zip_path = os.path.join(install_dir, "oxipng.zip")
            exe_path = os.path.join(install_dir, "oxipng.exe")

            if not os.path.exists(exe_path):
                print("📥 Downloading oxipng...")
                urllib.request.urlretrieve(url, zip_path)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(install_dir)

                os.remove(zip_path)

            os.environ["PATH"] += os.pathsep + install_dir
            return shutil.which("oxipng") is not None

        print(f"⚠️ Unsupported OS for oxipng: {system}")
        return False

    except Exception as e:
        print(f"❌ oxipng install failed: {e}")
        return False


def ensure_oxipng():
    if shutil.which("oxipng"):
        return True

    print("📦 oxipng not found, attempting install...")
    if install_oxipng():
        return True

    print("⚠️ oxipng unavailable, fallback to Pillow")
    return False


# ===================== PNG OPTIMIZER =====================
def optimize_png_auto(input_path, oxipng_level=6, min_size_mb=1.0):
    if not input_path.lower().endswith(".png"):
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
            oxi_path = os.path.join(
                tmp_dir, f"oxipng_{os.path.basename(input_path)}"
            )
            try:
                subprocess.run(
                    [
                        "oxipng",
                        "-o", str(oxipng_level),
                        "--strip", "all",
                        "--quiet",
                        input_path,
                        "-o", oxi_path
                    ],
                    check=True
                )
                oxi_size = os.path.getsize(oxi_path)
                if oxi_size < best_size:
                    best_path, best_size = oxi_path, oxi_size
            except Exception as e:
                print(f"⚠️ oxipng error: {e}")

        # ---------- PILLOW FALLBACK ----------
        if ensure_pillow():
            try:
                from PIL import Image
                pil_path = os.path.join(
                    tmp_dir, f"pillow_{os.path.basename(input_path)}"
                )
                with Image.open(input_path) as img:
                    img.save(
                        pil_path,
                        format="PNG",
                        optimize=True,
                        compress_level=9
                    )
                pil_size = os.path.getsize(pil_path)
                if pil_size < best_size:
                    best_path, best_size = pil_path, pil_size
            except Exception as e:
                print(f"⚠️ Pillow error: {e}")

        if best_path != input_path:
            print(
                f"🧠 PNG optimized: "
                f"{original_size/1024/1024:.2f}MB → "
                f"{best_size/1024/1024:.2f}MB"
            )

        return best_path

    except Exception as e:
        print(f"⚠️ PNG optimization skipped: {e}")
        return input_path


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
                "prompt_text": ("STRING", {"multiline": True, "default": ""}),
                "bot_token": ("STRING", {"default": ""}),
                "chat_id": ("STRING", {"default": ""}),
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
        image_path = optimize_png_auto(normalize_path(image_path))

        size = os.path.getsize(image_path)
        caption = (
            "🖼️ Image Generated Successfully\n\n"
            f"{format_render_time(render_time_seconds)}\n\n"
            "📝 Prompt Used:\n"
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
        elif size <= BOT_LIMIT:
            r = send_document(bot_token, chat_id, image_path, caption)
        else:
            raise ValueError("❌ Image > 50MB")

        if r.status_code != 200:
            raise RuntimeError(r.text)

        print(f"✅ Image sent: {os.path.basename(image_path)}")
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
            "📝 Prompt Used:\n"
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

        print(f"✅ Video sent: {os.path.basename(video_path)}")
        return {}
