# VeNote
A local Markdown note-management application with semantic and keyword search.

## First-time setup
1. Download or clone the project into a permanent folder.
2. Start Docker Desktop and wait until it is ready.
3. Choose a setup (cpu or gpu) and copy its environment template to the filename shown below. Keep both files in the project folder.
4. Double-click the matching start file. The first launch builds the Docker image and downloads the embedding model.

| Setup | Copy this template | To this filename | Start | Stop | Browser address |
| --- | --- | --- | --- | --- | --- |
| CPU | `.env.cpu.example` | `.env.cpu` | `start_venote_cpu.bat` | `stop_venote_cpu.bat` | <http://127.0.0.1:48725/ui/home> |
| NVIDIA CUDA | `.env.example` | `.env` | `start_venote.bat` | `stop_venote.bat` | <http://127.0.0.1:48721/ui/home> |

Use the matching stop file to shut down VeNote. Closing the browser leaves the containers running.

## System requirements

### Windows setup
- Windows 11, 64-bit, on an Intel or AMD processor.
- Docker Desktop installed and running.
- Docker Desktop configured to use **Linux containers and the WSL2 backend**.
- Hardware virtualization enabled.
- Internet access for the initial image build and model download.

The **CPU setup** uses CPU-only PyTorch and defaults to `sentence-transformers/all-MiniLM-L6-v2`. It runs on Intel or AMD CPUs without a dedicated GPU. The **NVIDIA CUDA setup** requires a compatible NVIDIA GPU and driver.

### GPU compatibility
The current Docker configuration uses **PyTorch 2.5.1 with CUDA 12.1**.
| GPU | Current configuration |
| --- | --- |
| NVIDIA RTX 20-, 30-, 40-series | Expected compatibility targets; individual models have not all been tested |
| NVIDIA RTX 50-series / Blackwell | Requires a newer PyTorch/CUDA configuration |
| Older NVIDIA GPUs | Not validated |
| AMD, Intel, Apple GPUs | Not supported by this NVIDIA CUDA configuration |

The application loads the configured embedding model at startup. The CUDA reranker loads on demand when a request asks for reranking and finds candidates. Browser searches currently use vector scores alone.

**Suggested hardware for the NVIDIA setup** is 12 GB GPU VRAM and 32 GB system RAM.
These are recommendations, not measured minimum requirements. Memory usage
depends on model selection, input lengths, and generation settings.






