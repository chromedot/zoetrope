# Zoetrope

Turn a written story into a narrated video. You write scenes and narration in a JSON file; Zoetrope generates an image per scene with [ComfyUI](https://github.com/comfyanonymous/ComfyUI), narrates them with text-to-speech, mixes in sound effects, and assembles the result into an MP4 — vertical for Shorts, or landscape.

A *zoetrope* is the Victorian device that spins a sequence of still images into the illusion of motion. Same idea, more electricity.

> **Status:** working, actively developed, and specific to one machine. See [Hardware](#hardware) before investing time — the GB10 requirement is real, not aspirational.

## What it actually does

```
data/stories/my_story.story          10 scenes: description, image prompt, narration text
        │
        ├── ComfyUI (port 8188) ─────  ~40 s per image at 768×1344
        ├── edge-tts ────────────────  ~1 s per line of narration
        ├── AudioLDM2 ───────────────  sound effects per scene
        └── ffmpeg ──────────────────  ~6 s to assemble
        │
output/my_story/videos/*.mp4          1080×1920 H.264 + AAC, scene timing synced to narration
```

A ten-scene Short takes about **eight minutes end to end**, nearly all of it image generation.

## Hardware

**Required: NVIDIA GB10 (Grace-Blackwell), 128 GB unified memory.**

This is a hard requirement today, not a suggestion. The ComfyUI launch flags in `evergreen.sh` — `--highvram --reserve-vram 15 --fp8_e4m3fn-unet --fp8_e4m3fn-text-enc --fast` — are tuned for the GB10's unified-memory architecture, where VRAM *is* system RAM. On a discrete GPU with 12–24 GB, `--highvram` ranges from wasteful to fatal.

Running elsewhere means retuning those flags for your card. That's a legitimate change and contributions are welcome, but nothing here has been tested on any other hardware. See [docs/gb10-optimization.md](docs/gb10-optimization.md) for why each flag is what it is.

Also required: Python 3.12+, ffmpeg, and about 35 GB of disk for models.

## Getting started

**1. Clone, with ComfyUI inside it**

```bash
git clone https://github.com/chromedot/zoetrope.git
cd zoetrope
git clone https://github.com/comfyanonymous/ComfyUI.git
```

**2. Create the virtualenv** — one environment serves both ComfyUI and the Studio.

```bash
python3 -m venv comfyui-env
./comfyui-env/bin/pip install -r ComfyUI/requirements.txt
./comfyui-env/bin/pip install -e ".[dev]"
```

On the GB10 (aarch64), install PyTorch from NVIDIA's ARM64 CUDA builds rather than the default PyPI wheels.

**3. Download the models** — about 32 GB, and the step most likely to trip you up. Follow [docs/models.md](docs/models.md); it explains the two-model-directory trap that has cost real debugging time here.

**4. Configure** (optional)

```bash
cp .env.example .env    # only needed for the Gemini prompt-refine feature
```

**5. Run**

```bash
./evergreen.sh start          # also: stop, restart, status
```

Studio at `http://localhost:8189/gallery`, ComfyUI at `http://localhost:8188`. Set `ZOETROPE_HOST` to your machine name to print links reachable from other devices.

**6. Verify**

```bash
./comfyui-env/bin/python -m pytest      # 51 tests
```

Tests passing does *not* mean the pipeline works — nothing in the suite starts a service. To confirm the real thing, generate a scene from the Studio UI.

## Layout

| Path | What |
| :--- | :--- |
| `studio/` | FastAPI app (port 8189) — the web UI, the API, and video assembly |
| `scripts/` | Pipeline: ComfyUI submission, ffmpeg strategies, TTS and SFX |
| `data/` | `stories/*.story` (your content), `workflows/*.json` (ComfyUI recipes), SQLite database |
| `docs/` | Setup, model downloads, GB10 tuning, the current work plan |
| `.claude/` | Pre-commit gates — see [Contributing](CONTRIBUTING.md) |
| `output/` | Everything generated, per story. Not in version control |

`ComfyUI/`, `comfyui-env/`, `models/` and `output/` are all gitignored — roughly 109 GB of downloadable or regenerable data against about 1 MB of source.

## Video output

Two orientations, set with `ORIENTATION`:

- **`vertical`** (default) — generates 768×1344, delivers 1080×1920. YouTube Shorts, Reels, TikTok.
- **`landscape`** — generates 1344×768, delivers 1920×1080.

Both generate at roughly one megapixel and scale up at assembly time, which is faster and produces better composition than asking the model for a full 2 MP frame.

Transitions matter more than they look:

| Transition | Video | Audio |
| :--- | :--- | :--- |
| `none` | Hard cuts | — |
| `crossfade` | Dissolves | **None** — silent output |
| `audio_mixed` | Hard cuts | Narration + SFX |
| `audio_crossfade` | Dissolves | Narration + SFX |

For a narrated video you almost always want **`audio_crossfade`**. Picking `crossfade` and getting a silent file is an easy mistake to make.

## Licence

MIT — see [LICENSE](LICENSE).

**The models are licensed separately and more restrictively.** FLUX.1 [dev] in particular is non-commercial. If you intend to monetise what you generate, read the licence section in [docs/models.md](docs/models.md) first.

ComfyUI is GPL-3.0. Zoetrope talks to it over HTTP and does not import or link against it.
