# Benchmark Report: qwen3.8-27b-all-servers


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 225 ± 0.8 | 225 | 23.4 ± 0.0 | 23.4 | 23.4 ± 0.0 | 23.4 |
| llamafile | 224 ± 1.0 | 224 | 23.3 ± 0.0 | 23.3 | 23.4 ± 0.1 | 23.4 |
| ollama | 231 ± 0.2 | 231 | 23.4 ± 0.0 | 23.4 | 23.4 ± 0.0 | 23.4 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 234 ± 0.3 | 234 | 23.2 ± 0.0 | 23.2 | 23.2 ± 0.0 | 23.2 |
| llamafile | 234 ± 0.4 | 234 | 23.2 ± 0.0 | 23.2 | 23.2 ± 0.0 | 23.2 |
| ollama | 238 ± 0.2 | 238 | 23.3 ± 0.0 | 23.3 | 23.3 ± 0.0 | 23.3 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 238 ± 0.3 | 238 | 23.0 ± 0.0 | 23.0 | 23.0 ± 0.0 | 23.0 |
| llamafile | 237 ± 0.1 | 237 | 23.0 ± 0.0 | 23.0 | 23.0 ± 0.0 | 23.0 |
| ollama | 241 ± 0.2 | 241 | 23.1 ± 0.0 | 23.1 | 23.1 ± 0.0 | 23.1 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 236 ± 0.2 | 236 | 22.6 ± 0.0 | 22.6 | 22.6 ± 0.0 | 22.6 |
| llamafile | 235 ± 0.1 | 235 | 22.6 ± 0.0 | 22.6 | 22.6 ± 0.0 | 22.6 |
| ollama | 238 ± 0.1 | 238 | 22.7 ± 0.0 | 22.7 | 22.7 ± 0.0 | 22.7 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

All discarded runs were within 5% of their cell's trimmed mean.

