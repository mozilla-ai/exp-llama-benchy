# Benchmark Report: qwen3.8-27b-mlx


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| lm-studio | 245 ± 0.9 | 246 | 31.5 ± 0.5 | 31.2 | 30.1 ± 0.2 | 30.1 |
| ollama | 248 ± 0.6 | 248 | 54.9 ± 5.5 | 55.2 | 58.3 ± 3.9 | 57.0 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| lm-studio | 250 ± 0.2 | 250 | 31.0 ± 0.0 | 31.0 | 29.9 ± 0.2 | 29.9 |
| ollama | 251 ± 0.4 | 251 | 55.6 ± 5.3 | 55.3 | 55.5 ± 4.7 | 56.2 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| lm-studio | 251 ± 0.1 | 251 | 30.3 ± 0.3 | 30.3 | 29.2 ± 0.0 | 29.2 |
| ollama | 250 ± 0.2 | 250 | 57.8 ± 5.6 | 58.6 | 55.2 ± 4.5 | 55.0 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| lm-studio | 249 ± 0.1 | 249 | 29.6 ± 0.1 | 29.6 | 28.5 ± 0.1 | 28.5 |
| ollama | 247 ± 0.1 | 247 | 54.4 ± 7.1 | 53.5 | 52.3 ± 4.4 | 51.8 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| ollama | 8192 | 32 | tg_throughput | -24.0%, -7.1% | +21.0%, +31.9% |
| ollama | 1024 | 32 | tg_throughput | -22.7%, -14.4% | +9.3%, +15.1% |
| ollama | 4096 | 32 | tg_throughput | -22.1%, -15.7% | +8.4%, +12.4% |
| ollama | 2048 | 64 | tg_throughput | -10.2%, -10.2% | +13.6%, +19.6% |
| ollama | 2048 | 32 | tg_throughput | -19.0%, -12.9% | +13.2%, +13.7% |
| ollama | 8192 | 64 | tg_throughput | -9.5%, -9.2% | +15.8%, +16.4% |
| ollama | 4096 | 64 | tg_throughput | -14.8%, -12.0% | +12.7%, +15.0% |
| ollama | 1024 | 64 | tg_throughput | -11.1%, -6.3% | +9.7%, +14.9% |
