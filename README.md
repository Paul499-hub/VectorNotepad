# VeNote
A local Markdown note-management application with semantic and keyword search.

## First-time setup
1. Download or clone the project into a permanent folder.
2. Start Docker Desktop and wait until it is ready.
3. In the project folder, copy `.env.example` and rename the copy to `.env`.


## Start VeNote
Double-click **`start_venote.bat`**.
You can also open the application manually once it is ready:
http://127.0.0.1:48721/ui/home

## Stop VeNote
Double-click **`stop_venote.bat`**.
Closing the browser does not stop VeNote.


## System requirements

### Windows setup
- Windows 11, 64-bit, on an Intel or AMD processor.
- Docker Desktop installed and running.
- Docker Desktop configured to use **Linux containers and the WSL2 backend**.
- Hardware virtualization enabled.
- A compatible NVIDIA GPU and a current NVIDIA Windows driver.

### GPU compatibility
The current Docker configuration uses **PyTorch 2.5.1 with CUDA 12.1**.
| GPU | Current configuration |
| --- | --- |
| NVIDIA RTX 20-, 30-, 40-series | Expected compatibility targets; individual models have not all been tested |
| NVIDIA RTX 50-series / Blackwell | Requires a newer PyTorch/CUDA configuration |
| Older NVIDIA GPUs | Not validated |
| AMD, Intel, Apple GPUs | Not supported by this NVIDIA CUDA configuration |

The application currently loads both an embedding model and
**Qwen2.5-3B-Instruct** for vector-variant generation.

**Suggested hardware:** 12 GB GPU VRAM and 32 GB system RAM.
These are recommendations, not measured minimum requirements. Memory usage
depends on model selection, input lengths, and generation settings.

Internet access is required for the initial image build and model downloads.





