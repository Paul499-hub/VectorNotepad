## Cpu empty (RAM) and disk
## Disk
venote-cpu-backend    2.02GB 
qdrant/qdrant         287MB
### RAM (idle) (reranking disabled)
venote-cpu-backend-1  350.7MiB / 7.525GiB 
venote-cpu-qdrant-1   45.84MiB / 7.525GiB

### RAM (idle) (reranking enabled)
venote-cpu-backend-1  710.9MiB / 7.525GiB
venote-cpu-qdrant-1   144.3MiB / 7.525GiB 

## Set terminal scripts allowed
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```
Run script cpu with reload
```
    .\run_cpu_test.ps1 test_reranker_quality
```
## Search latency findings (2026-11-27)

- At 100 notes and 125 total chunks, median vector-only search took 61.0 ms on CPU and 73.0 ms on the GPU machine.
- With reranking on, the same workload took 34.66 s on CPU and 2.64 s on GPU (13.1× faster).
- From 50 to 100 notes, total chunks rose from 62 to 125. Reranked latency rose 2.46× on CPU and 1.44× on GPU.
- Reranking drove most of the latency growth in both runs. The growth rate differed between the two setups.

Logs: [CPU](tests/log/search_latency_20261127T171636048909Z.csv) · [GPU](tests/log/gpu/search_latency_20261127T174254618094Z.csv)
