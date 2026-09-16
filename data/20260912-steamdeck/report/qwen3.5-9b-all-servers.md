# Benchmark Report: qwen3.5-9b-all-servers


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 66.6 ± 0.2 | 66.6 | 11.6 ± 0.0 | 11.6 | 11.6 ± 0.0 | 11.6 |
| llamafile | 109 ± 0.6 | 109 | 13.6 ± 0.0 | 13.6 | 13.7 ± 0.1 | 13.7 |
| lm-studio | 66.1 ± 1.0 | 66.1 | 11.0 ± 0.1 | 11.1 | 11.0 ± 0.1 | 11.0 |
| ollama | 107 ± 0.3 | 107 | 12.8 ± 0.0 | 12.8 | 12.8 ± 0.1 | 12.8 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 67.6 ± 0.1 | 67.5 | 11.5 ± 0.0 | 11.5 | 11.4 ± 0.0 | 11.4 |
| llamafile | 111 ± 0.2 | 111 | 13.6 ± 0.0 | 13.6 | 13.6 ± 0.0 | 13.6 |
| lm-studio | 66.6 ± 1.0 | 66.8 | 11.0 ± 0.1 | 11.0 | 10.8 ± 0.1 | 10.8 |
| ollama | 109 ± 0.1 | 109 | 12.8 ± 0.1 | 12.8 | 12.8 ± 0.1 | 12.8 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 66.8 ± 0.1 | 66.8 | 11.4 ± 0.0 | 11.4 | 11.4 ± 0.0 | 11.4 |
| llamafile | 109 ± 0.1 | 109 | 13.4 ± 0.1 | 13.4 | 13.5 ± 0.0 | 13.5 |
| lm-studio | 66.2 ± 0.7 | 65.9 | 10.7 ± 0.1 | 10.7 | 10.9 ± 0.1 | 10.9 |
| ollama | 107 ± 0.5 | 107 | 12.5 ± 0.1 | 12.5 | 12.6 ± 0.1 | 12.6 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 64.0 ± 0.1 | 64.0 | 11.1 ± 0.0 | 11.1 | 11.1 ± 0.0 | 11.1 |
| llamafile | 102 ± 0.1 | 102 | 13.1 ± 0.0 | 13.1 | 13.1 ± 0.1 | 13.1 |
| lm-studio | 63.9 ± 0.1 | 63.9 | 10.7 ± 0.1 | 10.7 | 10.7 ± 0.1 | 10.7 |
| ollama | 101 ± 0.1 | 101 | 12.4 ± 0.1 | 12.3 | 12.3 ± 0.1 | 12.3 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| lm-studio | 1024 | 64 | pp_throughput | -6.2%, -4.8% | +0.3%, +0.3% |
