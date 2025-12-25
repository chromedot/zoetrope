# ComfyUI Custom Setup Documentation

This document outlines the custom configuration for this ComfyUI instance, specifically regarding the separation of user data (workflows, output) from the core application code.

## Directory Structure

We have configured ComfyUI to store user-specific data in `/data/comfy`, keeping the `ComfyUI` git repository clean.

- **Project Root:** `/data/comfy`
- **ComfyUI Application:** `/data/comfy/ComfyUI` (Git Repository)
- **User Data Directory:** `/data/comfy`
    - **Workflows:** `/data/comfy/default/workflows` (Moved from `ComfyUI/user/default/workflows`)
    - **Output:** `/data/comfy/output`

## Startup Configuration

The `startup-comfy.sh` script has been modified to use the `--user-directory` flag.

**Startup Command:**
```bash
python main.py --listen 0.0.0.0 --fp8_e4m3fn-unet --fp8_e4m3fn-text-enc --output-directory /data/comfy/output --user-directory /data/comfy
```

**Key Flags:**
- `--user-directory /data/comfy`: Tells ComfyUI to look for the `user` folder (containing workflows, etc.) in `/data/comfy` instead of inside the `ComfyUI` folder.
- `--output-directory /data/comfy/output`: explicitly sets the output path.

## Maintenance & Recovery

### Recreating the Setup
If you need to reinstall ComfyUI:

1.  Clone the repository into `ComfyUI`.
2.  Ensure your `startup-comfy.sh` includes the `--user-directory /data/comfy` argument.
3.  Ensure your workflows are located in `/data/comfy/default/workflows`.

### Updating ComfyUI
Since user data is outside the repo, you can safely update the ComfyUI code without affecting your workflows.

**To Update:**
1.  Navigate to `ComfyUI`.
2.  Check your branch status (you are currently on a specific tag `v0.5.1`).
3.  Run `git pull` (or checkout main/master first if you want the latest nightly).
4.  Update dependencies if necessary (`pip install -r requirements.txt`).
