class ConditioningToString:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conditioning": ("CONDITIONING",),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "convert"
    CATEGORY = "Utils"

    def convert(self, conditioning):
        # Biasanya conditioning adalah list of tuples, kita ambil teksnya
        if isinstance(conditioning, list) and len(conditioning) > 0:
            # Ambil elemen pertama, lalu teksnya
            first_cond = conditioning[0]
            if isinstance(first_cond, tuple) and len(first_cond) >= 2:
                # Format: (pooled_output, text) — ambil text
                text = first_cond[1] if len(first_cond) > 1 else ""
                return (str(text),)
        return ("",)