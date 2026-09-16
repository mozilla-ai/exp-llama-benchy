# Benchmark Report: qwen3.5-0.8b-all-servers


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 11717 ± 565 | 11741 | 361 ± 0.9 | 361 | 367 ± 1.0 | 367 |
| llamafile | 10162 ± 137 | 10112 | 373 ± 0.9 | 373 | 379 ± 0.6 | 379 |
| lm-studio | 10794 ± 137 | 10788 | 237 ± 2.4 | 237 | 236 ± 8.6 | 236 |
| ollama | 11394 ± 368 | 11373 | 227 ± 3.8 | 227 | 224 ± 6.0 | 223 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 16652 ± 320 | 16680 | 360 ± 0.9 | 360 | 365 ± 1.8 | 365 |
| llamafile | 15003 ± 86 | 15000 | 373 ± 1.3 | 373 | 377 ± 0.4 | 377 |
| lm-studio | 15702 ± 182 | 15686 | 238 ± 8.0 | 237 | 237 ± 7.5 | 237 |
| ollama | 15854 ± 854 | 15843 | 226 ± 7.5 | 225 | 224 ± 6.2 | 224 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 21080 ± 299 | 21089 | 354 ± 2.1 | 354 | 360 ± 1.6 | 360 |
| llamafile | 19577 ± 116 | 19559 | 366 ± 1.1 | 366 | 372 ± 0.8 | 372 |
| lm-studio | 20478 ± 174 | 20470 | 239 ± 9.5 | 237 | 234 ± 8.4 | 234 |
| ollama | 19770 ± 975 | 19955 | 223 ± 5.3 | 224 | 233 ± 11 | 228 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 24166 ± 193 | 24171 | 343 ± 2.2 | 344 | 348 ± 1.7 | 348 |
| llamafile | 22809 ± 93 | 22811 | 353 ± 0.7 | 353 | 358 ± 1.5 | 358 |
| lm-studio | 23601 ± 143 | 23590 | 233 ± 9.7 | 231 | 240 ± 9.8 | 239 |
| ollama | 21908 ± 416 | 21888 | 231 ± 10 | 236 | 229 ± 10 | 229 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| llama-cpp | 1024 | 32 | pp_throughput | -23.3%, -1.8% | +1.4%, +1.5% |
| ollama | 2048 | 32 | pp_throughput | -18.5%, -11.6% | +3.8%, +4.5% |
| ollama | 1024 | 32 | pp_throughput | -12.0%, -6.2% | +1.9%, +2.6% |
| ollama | 4096 | 64 | pp_throughput | -11.7%, -10.8% | +3.5%, +6.3% |
| ollama | 1024 | 64 | tg_throughput | -1.1%, -1.1% | +1.2%, +10.0% |
| lm-studio | 4096 | 64 | tg_throughput | -2.2%, -2.0% | +8.9%, +10.0% |
| llama-cpp | 1024 | 64 | pp_throughput | -9.9%, -0.8% | +1.1%, +1.7% |
| ollama | 2048 | 64 | tg_throughput | -2.8%, -2.0% | +1.5%, +9.6% |
| lm-studio | 1024 | 64 | tg_throughput | -4.3%, -4.1% | +8.2%, +9.3% |
| lm-studio | 2048 | 32 | tg_throughput | -3.2%, -1.4% | +8.2%, +9.2% |
| ollama | 2048 | 32 | tg_throughput | -2.6%, -1.8% | +8.0%, +8.8% |
| lm-studio | 2048 | 64 | tg_throughput | -1.7%, -1.3% | +8.0%, +8.8% |
| ollama | 8192 | 32 | tg_throughput | -8.2%, -5.4% | +3.9%, +5.0% |
| ollama | 4096 | 32 | tg_throughput | -2.0%, -1.8% | +1.3%, +8.1% |
| ollama | 1024 | 64 | pp_throughput | -8.0%, -3.7% | +1.2%, +1.4% |
| lm-studio | 8192 | 32 | tg_throughput | -3.8%, -3.1% | +7.0%, +7.9% |
| ollama | 4096 | 32 | pp_throughput | -7.6%, -5.2% | +5.1%, +5.6% |
| ollama | 2048 | 64 | pp_throughput | -7.6%, -5.3% | +4.4%, +4.9% |
| lm-studio | 4096 | 32 | tg_throughput | -6.8%, -2.5% | +6.5%, +6.7% |
| llama-cpp | 2048 | 32 | pp_throughput | -6.6%, -1.5% | +0.9%, +1.2% |
| ollama | 4096 | 64 | tg_throughput | -5.7%, -4.8% | +5.5%, +6.4% |
| ollama | 8192 | 64 | tg_throughput | -6.1%, -5.4% | +4.7%, +5.1% |
| llama-cpp | 2048 | 64 | pp_throughput | -6.1%, -2.5% | +1.4%, +1.6% |
| llama-cpp | 4096 | 64 | pp_throughput | -5.3%, -0.8% | +0.6%, +1.1% |
| lm-studio | 8192 | 64 | tg_throughput | -5.0%, -5.0% | +4.3%, +4.4% |
