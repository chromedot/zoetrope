# NVIDIA GB10 (Blackwell) Optimization Guide

This document captures specific system and application-level optimizations for running ComfyUI on the NVIDIA GB10 (Grace-Blackwell) platform.

## 0. Hardware Architecture (the "SoC" reality)

*   **Architecture:** Grace CPU (ARM) + Blackwell GPU in a unified package.
*   **Memory:** 128GB LPDDR5X, **unified** — VRAM *is* system RAM. No PCIe transfer bottleneck between host and device, and no separate VRAM pool to budget against.
*   **Power:** ~140W total TDP, shared between CPU and GPU. Power taken back from one side is available to the other (see §3).
*   **Tensor Cores:** Blackwell introduced 5th-generation Tensor Cores with native hardware acceleration for 4-bit floating point (NVFP4) — more efficient still than the FP8 path this project currently uses.

Two consequences worth internalizing, because they drive the flags in §2: unified
memory is why `--highvram` is correct here and would be reckless on a discrete
card, and shared TDP is why capping the CPU can *raise* GPU throughput.

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


## 4. Attention Backend

*   **SageAttention 3** is the high-speed attention path for Blackwell — worth using where the workflow supports it.

## 5. Environment Notes

*   **Docker (if containerising):** use `nvcr.io/nvidia/pytorch:24.10-py3` or newer for GB10 on ARM64. Older images predate Blackwell support.
*   **`--reserve-vram 15` is safe and effective for Flux here.** Because memory is unified, that 15GB is reserved for the Grace CPU and the OS out of the same 128GB pool the GPU draws from — it prevents system-level OOM rather than capping model size the way a discrete-GPU VRAM reservation would.

---

*Sections 6-9 were salvaged in September 2026 from a separate text-to-video lab that
ran on this same GB10 through December 2025. That lab drove the hardware harder than
Zoetrope does — longer sustained generations, video models rather than single frames —
so it hit limits this project has not yet reached. Reproduced here because the findings
are about the machine, and apply to anyone running this software on this hardware.*

## 6. Why you cannot read VRAM on this machine

`nvidia-smi --query-gpu=memory.used,memory.free` returns `[N/A]` on the GB10, and
`nvtop`'s header gauge shows `MEM[ N/A]`. **The driver is not broken and there is
nothing to fix.** The GB10 is an SoC: the Blackwell GPU reaches memory over
NVLink-C2C rather than PCIe, and there is no separate VRAM pool to report — VRAM
*is* the 128 GB of system RAM.

Consequences worth knowing before you go looking for a problem:

*   `nvtop` also misreports the link as `PCIe GEN 1@ 1x`. Also a placeholder, also
    not real.
*   `nvtop`'s **process list still shows true per-process memory** even when the
    header gauge does not. That is the reliable read.
*   So does `pynvml` via `nvmlDeviceGetMemoryInfo` on the process handle.

Filed upstream and resolved.

## 7. FP8 precision — pick E4M3 deliberately

The `--fp8_e4m3fn-unet` / `--fp8_e4m3fn-text-enc` flags in §2 name **E4M3**
specifically, and the choice matters:

*   **E4M3** — more mantissa, less exponent range. Correct for inference.
*   **E5M2** — more range, less precision. Intended for gradients in training.
*   **FP16** — carries a real NaN risk on these models at this scale.
*   **FP32** — pure memory waste on a unified-memory system where you are already
    sharing the pool with the OS.

Note the live SFX bug is a precision-mixing failure of exactly this kind:
`mat1 and mat2 must have the same dtype, but got Half and Float8_e4m3fn`. Loading
weights as fp8 does not make the surrounding compute fp8.

## 8. Reaching the FP4 tensor cores

Blackwell's 5th-generation tensor cores accelerate **NVFP4** natively — more
efficient than the FP8 path §2 currently uses. **Stock PyTorch does not target them
by default.**

*   **SageAttention 3**, branch `sageattention3_blackwell`, dynamically quantizes
    attention Q,K to FP4 at runtime. This is the documented route; the generic
    SageAttention package is not the same thing.
*   Graph compilation: `torch.compile(mode="max-autotune")` targeting `sm_100`, or
    TensorRT-LLM.

Not currently used by Zoetrope. Worth knowing the ceiling exists — the LTX-2.3
weights that came off the same machine are NVFP4, so the hardware path is real.

## 9. Sustained I/O has a thermal ceiling

The Southbridge / NVMe controller throttles above roughly **100 W of sustained
write**. A generation loop that writes every frame as it is produced will hit this
during long runs.

The lab's fix was a **compute-then-write** cadence: the inference loop writes frames
into an in-memory `collections.deque`, and a separate low-priority thread — pinned
to the Cortex-A725 efficiency cores — flushes to disk only after the heavy GPU phase
finishes.

Zoetrope has not hit this: it writes one PNG per scene with ~37 s of compute between
writes. It becomes relevant if batch generation or video output ever lands.

### ARMv9 CPU (SVE2)

The Grace CPU is an SVE2 part, and generic ARM builds leave real throughput unused.
If you ever compile FFmpeg or OpenCV from source for this machine:

```
-mcpu=neoverse-v2 -march=armv9-a+sve2 -O3 -ftree-vectorize
```

Zoetrope uses distro FFmpeg and assembles a ten-scene video in about six seconds, so
this is not currently worth doing. It is the lever if assembly ever becomes the
bottleneck.
