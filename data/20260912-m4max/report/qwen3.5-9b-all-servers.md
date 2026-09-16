# Benchmark Report: qwen3.5-9b-all-servers


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 778 ± 3.3 | 778 | 67.2 ± 0.5 | 67.1 | 67.3 ± 0.2 | 67.2 |
| llamafile | 782 ± 2.3 | 782 | 66.5 ± 0.2 | 66.4 | 66.6 ± 0.1 | 66.6 |
| lm-studio | 728 ± 3.0 | 729 | 77.8 ± 1.2 | 77.4 | 70.7 ± 0.8 | 70.6 |
| ollama | 777 ± 0.6 | 778 | 65.3 ± 0.2 | 65.3 | 65.1 ± 0.5 | 65.1 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 805 ± 1.2 | 805 | 66.9 ± 0.5 | 66.8 | 67.1 ± 0.2 | 67.2 |
| llamafile | 807 ± 1.4 | 807 | 66.4 ± 0.2 | 66.4 | 66.4 ± 0.1 | 66.4 |
| lm-studio | 777 ± 2.5 | 777 | 77.0 ± 1.5 | 77.0 | 70.4 ± 0.9 | 70.4 |
| ollama | 807 ± 0.5 | 807 | 64.9 ± 0.5 | 64.9 | 64.9 ± 0.3 | 65.0 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 812 ± 1.0 | 812 | 65.8 ± 0.2 | 65.8 | 65.8 ± 0.3 | 65.9 |
| llamafile | 813 ± 0.8 | 813 | 65.3 ± 0.2 | 65.3 | 65.3 ± 0.1 | 65.3 |
| lm-studio | 798 ± 1.3 | 798 | 75.4 ± 1.9 | 75.7 | 68.9 ± 0.5 | 68.9 |
| ollama | 816 ± 0.4 | 816 | 64.1 ± 0.2 | 64.0 | 64.1 ± 0.4 | 64.1 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 801 ± 0.4 | 801 | 64.5 ± 0.1 | 64.5 | 64.7 ± 0.2 | 64.7 |
| llamafile | 801 ± 0.4 | 801 | 64.1 ± 0.2 | 64.1 | 64.1 ± 0.1 | 64.0 |
| lm-studio | 793 ± 0.8 | 793 | 73.2 ± 1.7 | 73.6 | 67.7 ± 0.9 | 67.5 |
| ollama | 805 ± 0.2 | 805 | 62.5 ± 0.3 | 62.5 | 62.6 ± 0.3 | 62.6 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| lm-studio | 4096 | 32 | tg_throughput | -5.1%, -2.4% | +3.6%, +4.3% |
