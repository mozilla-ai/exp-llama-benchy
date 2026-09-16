# Benchmark Report: qwen3.8-27b-all-servers


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 1024 ± 9.3 | 1023 | 37.5 ± 0.0 | 37.5 | 37.8 ± 0.1 | 37.8 |
| llamafile | 1006 ± 8.7 | 1006 | 38.1 ± 0.0 | 38.1 | 38.2 ± 0.0 | 38.2 |
| ollama | 1179 ± 11 | 1182 | 37.9 ± 0.1 | 37.9 | 38.0 ± 0.0 | 38.0 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 1389 ± 13 | 1391 | 37.5 ± 0.1 | 37.5 | 37.6 ± 0.1 | 37.6 |
| llamafile | 1365 ± 12 | 1362 | 37.9 ± 0.0 | 37.9 | 38.0 ± 0.0 | 38.0 |
| ollama | 1552 ± 5.8 | 1550 | 37.6 ± 0.1 | 37.5 | 37.9 ± 0.1 | 37.9 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 1662 ± 11 | 1662 | 37.1 ± 0.0 | 37.1 | 37.3 ± 0.0 | 37.3 |
| llamafile | 1642 ± 15 | 1645 | 37.6 ± 0.0 | 37.6 | 37.7 ± 0.0 | 37.7 |
| ollama | 1781 ± 11 | 1782 | 37.3 ± 0.1 | 37.3 | 37.6 ± 0.1 | 37.6 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 1819 ± 15 | 1821 | 36.5 ± 0.1 | 36.5 | 36.7 ± 0.0 | 36.7 |
| llamafile | 1801 ± 15 | 1804 | 36.9 ± 0.0 | 36.9 | 37.1 ± 0.0 | 37.1 |
| ollama | 1912 ± 21 | 1912 | 36.7 ± 0.1 | 36.7 | 36.9 ± 0.0 | 36.9 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

All discarded runs were within 5% of their cell's trimmed mean.

