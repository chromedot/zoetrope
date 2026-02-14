# NVIDIA GB10 (Blackwell) Optimization Guide

This document captures specific system and application-level optimizations for running ComfyUI on the NVIDIA GB10 (Grace-Blackwell) platform.

## 1. Disk I/O Optimization (Model Loading Speed)

To significantly improve the loading speed of large model checkpoints (Flux, SDXL, etc.), we increase the disk read-ahead buffer. This allows the OS to pre-fetch more data into RAM during sequential reads.

### The Command
**Target:** Set `read_ahead_kb` to `8192` (8MB) for NVMe drives or `4096` (4MB) for SSDs.

```bash
# Check current value
cat /sys/block/nvme0n1/queue/read_ahead_kb

# Set value (Temporary - resets on reboot)
sudo blockdev --setra 8192 /dev/nvme0n1
# OR
echo 8192 | sudo tee /sys/block/nvme0n1/queue/read_ahead_kb
```

*Note: Replace `nvme0n1` with your actual drive identifier (check using `lsblk`).*

### Making it Permanent
To ensure this persists across reboots, create a `udev` rule.

**File:** `/etc/udev/rules.d/99-readahead.rules`

```bash
# Content of the file
SUBSYSTEM=="block", KERNEL=="nvme*", ACTION=="add", ATTR{queue/read_ahead_kb}="8192"
SUBSYSTEM=="block", KERNEL=="sd*", ACTION=="add", ATTR{queue/read_ahead_kb}="4096"
```

## 2. ComfyUI Startup Flags

These flags are critical for stability and performance on the GB10's unified memory architecture. They are currently implemented in `./evergreen.sh`.

```bash
python main.py \
    --listen 0.0.0.0 \
    --highvram \
    --reserve-vram 15 \
    --fp8_e4m3fn-unet \
    --fp8_e4m3fn-text-enc \
    --fast
```

*   **`--highvram`**: Explicitly tells ComfyUI to leverage the massive 128GB unified memory pool.
*   **`--reserve-vram 15`**: Reserves 15GB of memory for the Host OS and Grace CPU to prevent Out-Of-Memory (OOM) crashes.
*   **`--fp8_e4m3fn-unet` / `--fp8_e4m3fn-text-enc`**: **Mandatory.** Enables native FP8 precision for the Blackwell Tensor Cores.
*   **`--fast`**: Enables optimized compute paths (CUDA graphs, etc.).

## 3. CPU Power Management

If the workload becomes GPU-bound and thermal throttling is a concern, you can cap the Grace CPU frequency to reserve power budget for the Blackwell GPU (Total TDP is shared ~140W).

```bash
# Cap CPU at 1.5GHz
sudo cpupower frequency-set -u 1.5GHz
```

