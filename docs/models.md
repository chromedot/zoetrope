# Downloading the models

Zoetrope ships no model weights. You need roughly **32 GB** before the first image will generate, and there is no way around it — this is the longest step in setup by a wide margin.

There are **two separate model trees**, and mixing them up is the most common way to get stuck. Read the next section before downloading anything.

## The two model directories

| Directory | Read by | Holds |
| :--- | :--- | :--- |
| `ComfyUI/models/` | **ComfyUI, by default** | The Flux stack — this is the one that matters |
| `models/` (repo root) | Nothing, currently | Z-Image Turbo and friends |

ComfyUI reads its own `ComfyUI/models/` tree without any configuration. The `models/` directory at the repo root is *supposed* to be wired in by `ComfyUI/extra_model_paths.yaml`, but that file currently points at a stale absolute path, so **everything in the root `models/` is invisible to a running ComfyUI**.

Put the required files in `ComfyUI/models/`. If a model appears missing despite being on disk, check which of the two trees you put it in — that mistake has cost real debugging time on this project.

## Required — the Flux stack (~31.7 GB)

Everything the default workflow (`data/workflows/flux_photoreal_api.json`) needs.

```bash
cd ComfyUI/models

# 22.1 GB — the image model itself
curl -L -o unet/flux1-dev.safetensors \
  https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors

# 9.1 GB — T5 text encoder (this is what reads your prompt)
curl -L -o clip/t5xxl_fp16.safetensors \
  https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors

# 0.2 GB — CLIP text encoder
curl -L -o clip/clip_l.safetensors \
  https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors

# 0.3 GB — VAE (decodes latents into pixels)
curl -L -o vae/ae.safetensors \
  https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors
```

`FLUX.1-dev` is a gated repository on Hugging Face. You must accept its licence on the model page while signed in, then authenticate — either `huggingface-cli login`, or by adding `-H "Authorization: Bearer $HF_TOKEN"` to the two `black-forest-labs` downloads above.

### Licence — read this before monetising anything

**FLUX.1 [dev] is released under a non-commercial licence.** Zoetrope exists to produce videos for publication, and publishing monetised videos made with a non-commercial model is a problem you want to discover now rather than after a channel starts earning.

Two alternatives worth considering, both of which drop into the same workflow:

- **FLUX.1 [schnell]** — Apache-2.0, commercially usable, and *faster* (a distilled few-step model). Swap `flux1-dev.safetensors` for `flux1-schnell.safetensors` and reduce the step count.
- **Z-Image Turbo** — already sitting in the root `models/` directory on this machine. Check its licence terms on the model card.

Verify current terms on the model cards yourself; licences change, and nothing here is legal advice.

## Optional — Z-Image Turbo (~18.8 GB)

A faster, turbo-distilled alternative. Present in the root `models/` on this machine but not currently reachable by ComfyUI (see above). To actually use it, put it under `ComfyUI/models/` instead:

```bash
cd ComfyUI/models

curl -L -o diffusion_models/z_image_turbo_bf16.safetensors \
  https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors

curl -L -o text_encoders/qwen_3_4b.safetensors \
  https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors
```

It reuses the same `ae.safetensors` VAE as Flux. There is no Zoetrope workflow template for it yet — `data/workflows/` contains Flux templates only.

## Narration and sound effects

Narration needs **no model download**. `edge-tts` streams from Microsoft's endpoint and is already a declared dependency — this is why narration takes about a second per line while an image takes about 40.

Sound effects use AudioLDM2 through the `ComfyUI_AudioLDM` custom node, which fetches its own weights on first use.

## Verifying

With ComfyUI running (`./evergreen.sh start`), ask it what it can actually see:

```bash
curl -s http://127.0.0.1:8188/object_info/UNETLoader \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['UNETLoader']['input']['required']['unet_name'][0])"
```

The list it prints is the ground truth. If a file you downloaded isn't in it, ComfyUI cannot use it — nearly always because it landed in the root `models/` instead of `ComfyUI/models/`.
