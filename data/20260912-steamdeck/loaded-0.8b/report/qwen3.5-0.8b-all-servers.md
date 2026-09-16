# Benchmark Report: qwen3.5-0.8b-all-servers


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 448 ± 9.0 | 450 | 57.5 ± 0.7 | 57.7 | 58.3 ± 0.4 | 58.3 |
| llamafile | 527 ± 10.0 | 526 | 59.0 ± 0.3 | 58.9 | 59.5 ± 0.1 | 59.5 |
| lm-studio | 439 ± 10 | 432 | 45.8 ± 0.9 | 45.8 | 48.8 ± 1.3 | 48.8 |
| ollama | 507 ± 16 | 510 | 47.1 ± 1.4 | 46.9 | 48.3 ± 1.1 | 48.3 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 540 ± 5.9 | 540 | 55.8 ± 0.6 | 55.8 | 56.9 ± 0.5 | 57.0 |
| llamafile | 659 ± 4.1 | 660 | 58.1 ± 0.2 | 58.1 | 58.5 ± 0.1 | 58.5 |
| lm-studio | 535 ± 7.4 | 534 | 45.8 ± 1.2 | 45.3 | 47.3 ± 1.2 | 47.7 |
| ollama | 591 ± 10 | 588 | 45.8 ± 1.1 | 45.1 | 46.8 ± 1.1 | 47.4 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 579 ± 3.2 | 578 | 55.2 ± 0.1 | 55.3 | 55.6 ± 0.4 | 55.5 |
| llamafile | 703 ± 5.5 | 703 | 56.6 ± 0.3 | 56.6 | 56.6 ± 0.2 | 56.6 |
| lm-studio | 577 ± 278 | 578 | 47.7 ± 1.7 | 47.2 | 47.1 ± 1.2 | 47.2 |
| ollama | 634 ± 3.2 | 634 | 47.9 ± 1.3 | 47.9 | 47.2 ± 0.9 | 46.9 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 534 ± 1.7 | 534 | 52.5 ± 0.1 | 52.5 | 52.6 ± 0.2 | 52.6 |
| llamafile | 624 ± 1.9 | 624 | 53.4 ± 0.4 | 53.3 | 53.5 ± 0.2 | 53.5 |
| lm-studio | 532 ± 1.7 | 532 | 45.9 ± 1.6 | 45.3 | 46.2 ± 0.9 | 46.7 |
| ollama | 570 ± 1.9 | 570 | 44.7 ± 1.5 | 44.6 | 45.4 ± 1.2 | 45.0 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| lm-studio | 4096 | 64 | pp_throughput | -1.5%, -1.5% | +0.4%, +258.0% |
| lm-studio | 4096 | 64 | tg_throughput | -8.6%, -5.5% | +0.7%, +0.8% |
| ollama | 8192 | 64 | tg_throughput | -7.4%, -2.1% | +2.2%, +2.5% |
| lm-studio | 4096 | 32 | tg_throughput | -7.1%, -5.8% | +3.8%, +3.9% |
| lm-studio | 1024 | 32 | tg_throughput | -1.3%, -0.7% | +2.8%, +6.9% |
| lm-studio | 1024 | 64 | tg_throughput | -6.6%, -5.4% | +3.6%, +3.6% |
| ollama | 4096 | 32 | tg_throughput | -6.5%, -6.1% | +1.8%, +1.8% |
| lm-studio | 8192 | 32 | tg_throughput | -6.3%, -5.8% | +3.2%, +5.9% |
| llamafile | 1024 | 64 | pp_throughput | -6.2%, -1.5% | +0.6%, +0.8% |
| ollama | 1024 | 64 | tg_throughput | -5.7%, -5.5% | +1.4%, +3.6% |
| ollama | 8192 | 32 | tg_throughput | -5.3%, -4.3% | +3.9%, +4.3% |
| lm-studio | 2048 | 32 | tg_throughput | -2.2%, -2.1% | +4.8%, +5.2% |
| lm-studio | 2048 | 64 | tg_throughput | -4.4%, -4.3% | +1.2%, +5.0% |
