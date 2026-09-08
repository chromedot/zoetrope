# Zoetrope

Turn a written story into a narrated video. You write scenes and narration in a JSON file; Zoetrope generates each scene as a video clip with synchronized audio using [LTX-2.5](https://huggingface.co/Lightricks/LTX-2.5) through [ComfyUI](https://github.com/comfyanonymous/ComfyUI), narrates it with text-to-speech, and assembles the result into an MP4, vertical for Shorts or landscape.

A *zoetrope* is the Victorian device that spins a sequence of still images into the illusion of motion. Same idea, more electricity.

> **Status:** working, actively developed, and specific to one machine. See [Hardware](#hardware) before investing time — the GB10 requirement is real, not aspirational.
>
> **In transition.** This describes where the project is going. An earlier stills path — Flux images assembled with crossfades — remains in the code and is currently the only route to a fully assembled film, because clip assembly is not built yet. It is being retired as LTX-2.5 takes over, not maintained alongside.

## What it actually does

```
data/stories/my_story.story          10 scenes: description, prompt, narration text
        │
        ├── LTX-2.5 via ComfyUI :8188  ~44 s per 4-second 576×1024 clip.
        │                              Video and synchronized audio in one pass
        ├── edge-tts ────────────────  ~1 s per line of narration
        └── ffmpeg ──────────────────  assembly
        │
output/my_story/videos/*.mp4          1080×1920 H.264 + AAC
```

Roughly 11× realtime, so a ten-scene short is about **eight minutes** of generation.

LTX-2.5 produces its own ambient audio and effects per clip. Narration stays with
edge-tts, because a voiceover has to say exactly what the story says rather than
something plausible.

### The continuity problem, and how this handles it

Ten independently generated clips do not look like the same story — the face drifts,
the light changes, the world resets on every cut. Stitching them afterwards is where
that becomes obvious.

LTX-2.5 has **native multishot**: one generation emits several connected shots that
hold character, environment, lighting and voice across the cuts between them. It is
driven by prompt structure — you describe the cuts — rather than by a separate model
or a reference-image pipeline.

**This is the intended path and it is not wired up yet.** See
[issue #11](https://github.com/chromedot/zoetrope/issues/11). Today the app generates
one clip per scene; assembling clips into a single film is unimplemented, because
multishot may make a conventional stitcher unnecessary.

## Hardware

**Required: NVIDIA GB10 (Grace-Blackwell), 128 GB unified memory.**

This is a hard requirement today, not a suggestion. The ComfyUI launch flags in `evergreen.sh` — `--highvram --reserve-vram 15 --fp8_e4m3fn-unet --fp8_e4m3fn-text-enc --fast` — are tuned for the GB10's unified-memory architecture, where VRAM *is* system RAM. On a discrete GPU with 12–24 GB, `--highvram` ranges from wasteful to fatal.

Running elsewhere means retuning those flags for your card. That's a legitimate change and contributions are welcome, but nothing here has been tested on any other hardware. See [docs/gb10-optimization.md](docs/gb10-optimization.md) for why each flag is what it is — including why `nvidia-smi` reports `N/A` for memory on this platform and there is nothing to fix.

Also required: Python 3.12+, ffmpeg, and **about 40 GB of disk** for the LTX-2.5 model set.

## Getting started

**1. Clone, with ComfyUI inside it**

```bash
git clone https://github.com/chromedot/zoetrope.git
cd zoetrope
git clone https://github.com/comfyanonymous/ComfyUI.git
git -C ComfyUI checkout v0.34.6
```

Pin a release rather than tracking `master`. **LTX-2.5 needs ComfyUI ≥ v0.32.0** — that is where the `LTXAV` audio-video model support landed.

**2. Create the virtualenv** — one environment serves both ComfyUI and the Studio.

```bash
python3 -m venv comfyui-env
./comfyui-env/bin/pip install -r ComfyUI/requirements.txt
./comfyui-env/bin/pip install -e ".[dev]"
```

On the GB10 (aarch64), install PyTorch from NVIDIA's ARM64 CUDA builds rather than the default PyPI wheels.

**3. Download the models** — about 40 GB, scripted:

```bash
./comfyui-env/bin/hf auth login     # LTX-2.5 is a gated repo
./scripts/download_ltx25.sh
```

You must also accept the LTX-2.x Community License on the [model page](https://huggingface.co/Lightricks/LTX-2.5) with the same account, or the download returns 403 rather than a useful error.

The script fetches the **NVFP4** transformer rather than the int8 build ComfyUI's
official template references. On the GB10 it measured 8% faster and 2.6 GB smaller,
and `supports_nvfp4_compute()` returns true on this hardware. See the comment at the
top of the script for the numbers, and use int8 on a card where that check fails.

**4. Configure** (optional)

Nothing here is required to generate clips, narrate them, or assemble a video.

| Variable | Effect |
| :--- | :--- |
| `GEMINI_API_KEY` | Enables the Studio's "refine prompt" button. Without it that one endpoint returns a friendly error |
| `ORIENTATION` | `vertical` (default) or `landscape` |
| `ZOETROPE_HOST` | Machine name to print in links, for reaching the Studio from another device |
| `COMFY_URL` | Defaults to `http://127.0.0.1:8188/prompt` |

Put them in a `.env` file at the repo root, or export them.

**5. Run**

```bash
./evergreen.sh start          # also: stop, restart, status
```

Studio at `http://localhost:8189/gallery`, ComfyUI at `http://localhost:8188`.

**6. Verify**

```bash
./comfyui-env/bin/python -m pytest      # 60 tests
```

Tests passing does *not* mean the pipeline works — nothing in the suite starts a service. To confirm the real thing, generate a scene from the Studio UI and look at the output.

## Layout

| Path | What |
| :--- | :--- |
| `studio/` | FastAPI app (port 8189) — the web UI, the API, and video assembly |
| `scripts/` | Pipeline: ComfyUI submission, ffmpeg strategies, TTS and SFX, model downloads |
| `data/` | `stories/*.story` (your content), `workflows/*.json` (ComfyUI recipes) |
| `docs/` | Setup, model downloads, GB10 tuning, style guides |
| `.claude/` | Pre-commit gates — see [Contributing](CONTRIBUTING.md) |
| `output/` | Everything generated, per story. Not in version control |

`ComfyUI/`, `comfyui-env/`, `models/` and `output/` are all gitignored — roughly 105 GB of downloadable or regenerable data against about 1 MB of source. The SQLite database is also untracked: it holds generation history, which is content rather than software, and `init_db()` creates it on first run.

## Video output

Two orientations, set with `ORIENTATION`:

| | Generated | Delivered |
| :--- | :--- | :--- |
| `vertical` (default) | 576×1024 | 1080×1920 — Shorts, Reels, TikTok |
| `landscape` | 1024×576 | 1920×1080 |

Clips generate below delivery size and scale up at assembly. A clip is ~100 frames
rather than one image, so generating at delivery resolution costs far more than it
returns — the upscale is a clean 9:16 resize with no crop.

Frame count must satisfy `frames % 8 == 1` and both dimensions must be multiples of
32. The default is 97 frames at 24 fps — four seconds.

## Licence

MIT — see [LICENSE](LICENSE).

**The model is licensed separately.** LTX-2.5 is free for commercial and production
use below $10M annual revenue; above that it requires a paid agreement from
Lightricks. Verify current terms on the [model page](https://huggingface.co/Lightricks/LTX-2.5)
yourself — licences change and nothing here is legal advice.

ComfyUI is GPL-3.0. Zoetrope talks to it over HTTP and does not import or link
against it.
