# Benchmark Report: idot-ab-9b


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 66.6 ± 0.2 | 66.6 | 11.5 ± 0.0 | 11.5 | 11.6 ± 0.0 | 11.6 |
| llama-cpp-idot | 109 ± 0.8 | 109 | 13.7 ± 0.0 | 13.7 | 13.7 ± 0.0 | 13.7 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 67.6 ± 0.1 | 67.6 | 11.5 ± 0.0 | 11.5 | 11.5 ± 0.1 | 11.5 |
| llama-cpp-idot | 111 ± 0.3 | 111 | 13.6 ± 0.0 | 13.6 | 13.6 ± 0.0 | 13.6 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 66.8 ± 0.1 | 66.8 | 11.3 ± 0.0 | 11.3 | 11.3 ± 0.0 | 11.3 |
| llama-cpp-idot | 109 ± 0.1 | 109 | 13.3 ± 0.1 | 13.3 | 13.4 ± 0.1 | 13.4 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 64.0 ± 0.0 | 64.0 | 11.1 ± 0.0 | 11.1 | 11.1 ± 0.0 | 11.1 |
| llama-cpp-idot | 102 ± 0.1 | 102 | 13.0 ± 0.0 | 13.0 | 13.0 ± 0.0 | 13.0 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

All discarded runs were within 5% of their cell's trimmed mean.

