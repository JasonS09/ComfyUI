from comfy import model_management
import torch
import comfy.utils

MAX_RESOLUTION=8192

class ImageUpscaleWithModelTo:
    crop_methods = ["disabled", "center"]

    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "width": ("INT", {"default": 512, "min": 64, "max": MAX_RESOLUTION, "step": 8}),
                              "height": ("INT", {"default": 512, "min": 64, "max": MAX_RESOLUTION, "step": 8}),
                              "crop": (s.crop_methods,),
                              "upscale_model": ("UPSCALE_MODEL",),
                              "image": ("IMAGE",),
                              }}
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upscale"

    CATEGORY = "comfyui_krita_plugin"

    def upscale(self, width, height, crop, upscale_model, image):
        def crop_input(in_img):
            if crop == "center":
                old_width = in_img.shape[3]
                old_height = in_img.shape[2]
                old_aspect = old_width / old_height
                new_aspect = width / height
                x = 0
                y = 0
                if old_aspect > new_aspect:
                    x = round((old_width - old_width * (new_aspect / old_aspect)) / 2)
                elif old_aspect < new_aspect:
                    y = round((old_height - old_height * (old_aspect / new_aspect)) / 2)
                return in_img[:,:,y:old_height-y,x:old_width-x]
            else:
                return in_img

        device = model_management.get_torch_device()
        upscale_model.to(device)
        in_img = crop_input(image.movedim(-1,-3).to(device))

        tile = 128 + 64
        overlap = 8
        steps = in_img.shape[0] * comfy.utils.get_tiled_scale_steps(in_img.shape[3], in_img.shape[2], tile_x=tile, tile_y=tile, overlap=overlap)
        pbar = comfy.utils.ProgressBar(steps)
        s = comfy.utils.tiled_scale(in_img, lambda a: upscale_model(a), tile_x=tile, tile_y=tile, overlap=overlap, upscale_amount=width/in_img.shape[3], pbar=pbar)
        upscale_model.cpu()
        s = torch.clamp(s.movedim(-3,-1), min=0, max=1.0)
        return (s,)
    
NODE_CLASS_MAPPINGS = {
    "ImageUpscaleWithModelTo": ImageUpscaleWithModelTo,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageUpscaleWithModelTo": "Upscale image with model",
}