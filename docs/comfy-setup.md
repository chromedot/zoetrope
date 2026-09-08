# ComfyUI setup

Zoetrope talks to a ComfyUI instance over HTTP (port 8188) for every image and sound effect — see the pipeline in the [README](../README.md#what-it-actually-does). This document covers how that instance is installed and wired into the repo. For the model weights it needs, see [models.md](models.md); for why its startup flags are what they are, see [gb10-optimization.md](gb10-optimization.md).

## Installing it

ComfyUI is not part of this repository — you clone it into the repo root yourself, as covered in the README's [Getting started](../README.md#getting-started):

```bash
cd zoetrope
git clone https://github.com/comfyanonymous/ComfyUI.git
```

`ComfyUI/` is fully gitignored. Nothing about that checkout — its code, its git history, which tag it's on — is Zoetrope's to track; treat it as a vendored dependency you can delete and re-clone whenever you like (see [Reinstalling](#reinstalling) below).

Two custom nodes live under `ComfyUI/custom_nodes/` and matter to Zoetrope:

- **ComfyUI-Manager** ([ltdrdata/ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)) — a node/model installer reachable from the ComfyUI web UI. Easiest way to install the node below, and anything else you add later.
- **ComfyUI_AudioLDM** — provides the `AudioLDM` / `SaveAudioLDM` node types that `data/workflows/audioldm2_fp8.json` uses for sound effects. Without it, everything works except SFX generation.

Both live inside the gitignored `ComfyUI/` tree, so a fresh clone starts without them — install Manager first, then use it to pull in AudioLDM.

## Where things actually live

Zoetrope never lets ComfyUI write into its own repo. `evergreen.sh` starts it with two flags that redirect its state to paths derived from the project root, not hardcoded to any one machine:

```bash
python main.py ... --output-directory "$COMFY_ROOT/output" --user-directory "$COMFY_ROOT/user"
```

| Directory | What | In git? |
| :--- | :--- | :--- |
| `user/` | ComfyUI's own state: workflows saved from its web UI (`user/default/workflows/`), its settings and prompt-history DB, and ComfyUI-Manager's cache/config (`user/__manager/`) | No — regenerated at runtime |
| `output/` | Every image, video, and SFX file ComfyUI renders | No |
| `data/workflows/` | Zoetrope's own workflow templates, loaded and edited by Python and submitted straight to ComfyUI's API | Yes |

The point of pulling `user/` and `output/` out of `ComfyUI/`: that directory is disposable, so anything worth keeping has to live outside it.

## Two things are called "workflows" here — don't mix them up

- **`data/workflows/*.json`** — API-format graphs that `scripts/story_manager.py` and `scripts/audio_utils.py` load, edit (prompt text, seed, filename) and POST directly to ComfyUI. This is what actually runs when the Studio generates a scene. Edit these to change the pipeline itself.
- **`user/default/workflows/`** — whatever you've saved from the ComfyUI web UI at `http://localhost:8188`, in the UI's own format. Handy for interactively building or debugging a graph, but nothing in Zoetrope's pipeline reads from here.

To bring a UI-built graph into the pipeline: export it in API format from ComfyUI (look under the Workflow menu; enable Dev Mode in Settings if you don't see the option), save it into `data/workflows/`, and point `scripts/story_manager.py` at it with `WORKFLOW_TEMPLATE` in `.env` (see `.env.example`).

## Running it

Not a standalone script — `evergreen.sh` starts ComfyUI and the Studio together:

```bash
./evergreen.sh start     # also: stop, restart, status
```

ComfyUI comes up at `http://localhost:8188`. Its logs go to `logs/comfyui.log`, its PID to `pids/comfyui.pid`. The full startup flag set — and why each flag is there — is in [gb10-optimization.md](gb10-optimization.md#2-comfyui-startup-flags).

## Reinstalling

`ComfyUI/` is disposable by design — none of `user/`, `output/`, or `data/` depend on which checkout is running.

1. `rm -rf ComfyUI`, then re-clone as in [Installing it](#installing-it).
2. Reinstall ComfyUI-Manager and ComfyUI_AudioLDM into `ComfyUI/custom_nodes/`.
3. Re-download the models — a separate ~32 GB tree, also gitignored, untouched by re-cloning ComfyUI. See [models.md](models.md).
4. `./comfyui-env/bin/pip install -r ComfyUI/requirements.txt`.
5. `./evergreen.sh restart`.

Your saved UI workflows, generated output, and the workflow templates the pipeline actually runs all live outside `ComfyUI/`, so none of this touches them.

## Updating ComfyUI

```bash
cd ComfyUI
git fetch
git checkout <newer-tag>   # or a release branch, for the nightly
cd ..
./comfyui-env/bin/pip install -r ComfyUI/requirements.txt
./evergreen.sh restart
```

The GB10 startup flags in `evergreen.sh` (`--highvram`, `--fp8_e4m3fn-unet`, and friends) are pinned to this hardware, not to a ComfyUI version, so they shouldn't need to change on update. If generation breaks after one, check `logs/comfyui.log` first.
