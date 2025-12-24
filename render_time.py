import time

class RenderTime_Start:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"trigger": ("*",)}}
    RETURN_TYPES = ("RENDER_START_TIME",)
    FUNCTION = "start"
    CATEGORY = "utils/timer"
    def start(self, trigger):
        return (time.time(),)

class RenderTime_End:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "start_time": ("RENDER_START_TIME",),
                "trigger": ("*",),
            }
        }
    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("render_time_seconds",)
    FUNCTION = "end"
    CATEGORY = "utils/timer"
    def end(self, start_time, trigger):
        duration = max(0.0, time.time() - start_time)
        print(f"✅ Render selesai dalam {duration:.2f} detik")
        return (duration,)

NODE_CLASS_MAPPINGS = {
    "RenderTime_Start": RenderTime_Start,
    "RenderTime_End": RenderTime_End,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "RenderTime_Start": "⏱️ Render Time (Start)",
    "RenderTime_End": "⏱️ Render Time (End)",
}
