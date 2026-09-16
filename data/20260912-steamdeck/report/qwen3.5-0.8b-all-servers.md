# Benchmark Report: qwen3.5-0.8b-all-servers


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 671 ± 2.4 | 671 | 59.8 ± 1.4 | 60.3 | 59.6 ± 1.2 | 59.5 |
| llamafile | 861 ± 4.8 | 862 | 65.0 ± 1.3 | 65.0 | 65.0 ± 1.0 | 64.9 |
| lm-studio | 667 ± 2.8 | 667 | 49.0 ± 0.6 | 49.0 | 48.5 ± 0.5 | 48.5 |
| ollama | 756 ± 12 | 755 | 48.6 ± 0.6 | 48.6 | 48.1 ± 0.6 | 48.1 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 701 ± 1.8 | 701 | 60.2 ± 1.4 | 60.3 | 59.1 ± 1.0 | 59.2 |
| llamafile | 897 ± 2.2 | 897 | 64.1 ± 0.7 | 64.1 | 64.3 ± 0.7 | 64.3 |
| lm-studio | 699 ± 1.8 | 699 | 47.8 ± 0.8 | 47.7 | 47.9 ± 1.4 | 47.7 |
| ollama | 813 ± 1.6 | 813 | 46.1 ± 1.1 | 45.4 | 47.7 ± 1.3 | 47.6 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 675 ± 0.9 | 675 | 59.7 ± 0.6 | 59.7 | 58.5 ± 2.0 | 58.9 |
| llamafile | 845 ± 1.2 | 845 | 62.9 ± 1.5 | 62.9 | 61.9 ± 2.7 | 62.8 |
| lm-studio | 675 ± 1.0 | 675 | 47.8 ± 0.7 | 47.5 | 48.0 ± 0.8 | 48.6 |
| ollama | 758 ± 7.2 | 758 | 47.0 ± 1.0 | 47.1 | 46.5 ± 0.6 | 46.5 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 586 ± 0.9 | 586 | 58.9 ± 1.7 | 59.0 | 57.0 ± 1.7 | 56.8 |
| llamafile | 697 ± 1.8 | 696 | 59.5 ± 1.3 | 59.6 | 60.2 ± 0.5 | 60.2 |
| lm-studio | 585 ± 1.4 | 585 | 46.8 ± 0.7 | 46.9 | 45.9 ± 1.2 | 46.5 |
| ollama | 633 ± 1.3 | 633 | 44.5 ± 1.4 | 44.8 | 45.0 ± 1.2 | 45.1 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| llama-cpp | 8192 | 32 | tg_throughput | -9.2%, -2.9% | +1.6%, +3.4% |
| llamafile | 4096 | 32 | tg_throughput | -8.0%, -3.8% | +0.9%, +1.2% |
| llamafile | 4096 | 64 | tg_throughput | -8.0%, -7.7% | +2.8%, +2.9% |
| llama-cpp | 1024 | 64 | tg_throughput | -0.7%, -0.7% | +0.7%, +7.4% |
| lm-studio | 8192 | 64 | tg_throughput | -7.3%, -2.7% | +1.7%, +1.8% |
| llama-cpp | 8192 | 64 | tg_throughput | -7.3%, -1.4% | +4.9%, +6.4% |
| ollama | 8192 | 64 | tg_throughput | -6.6%, -3.3% | +2.0%, +2.1% |
| llamafile | 8192 | 32 | tg_throughput | -6.5%, -4.2% | +1.5%, +1.7% |
| llamafile | 1024 | 32 | tg_throughput | -6.4%, -1.5% | +1.9%, +2.4% |
| llama-cpp | 4096 | 64 | tg_throughput | -5.2%, -4.7% | +3.9%, +6.0% |
| ollama | 8192 | 32 | tg_throughput | -5.9%, -4.8% | +3.0%, +4.4% |
| llama-cpp | 2048 | 32 | tg_throughput | -5.6%, -2.2% | +2.0%, +5.3% |
| ollama | 4096 | 32 | tg_throughput | -5.5%, -2.4% | +3.7%, +3.8% |
| lm-studio | 2048 | 64 | tg_throughput | -5.3%, -5.2% | +4.3%, +4.5% |
| ollama | 2048 | 64 | tg_throughput | -5.1%, -4.9% | +4.8%, +4.9% |
