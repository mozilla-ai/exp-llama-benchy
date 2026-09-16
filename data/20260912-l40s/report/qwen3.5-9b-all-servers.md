# Benchmark Report: qwen3.5-9b-all-servers


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 3685 ± 31 | 3684 | 105 ± 0.3 | 105 | 106 ± 0.4 | 106 |
| llamafile | 3614 ± 32 | 3608 | 109 ± 0.1 | 109 | 109 ± 0.1 | 109 |
| lm-studio | 3596 ± 27 | 3598 | 94.2 ± 1.4 | 93.6 | 93.3 ± 0.3 | 93.3 |
| ollama | 3535 ± 32 | 3535 | 91.2 ± 1.3 | 91.3 | 92.1 ± 0.4 | 92.1 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 4842 ± 36 | 4833 | 105 ± 0.3 | 105 | 106 ± 0.4 | 107 |
| llamafile | 4793 ± 24 | 4792 | 108 ± 0.1 | 108 | 109 ± 0.2 | 109 |
| lm-studio | 4770 ± 39 | 4775 | 93.5 ± 1.4 | 93.0 | 93.6 ± 1.4 | 93.1 |
| ollama | 4623 ± 78 | 4606 | 91.8 ± 1.0 | 91.7 | 92.0 ± 1.0 | 92.0 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 5742 ± 15 | 5743 | 104 ± 0.3 | 104 | 104 ± 0.6 | 104 |
| llamafile | 5684 ± 22 | 5683 | 107 ± 0.2 | 107 | 108 ± 0.0 | 108 |
| lm-studio | 5742 ± 16 | 5741 | 92.9 ± 1.4 | 92.4 | 93.4 ± 1.5 | 92.4 |
| ollama | 5590 ± 41 | 5589 | 91.0 ± 1.3 | 90.6 | 91.4 ± 1.7 | 90.8 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 6268 ± 23 | 6274 | 102 ± 0.6 | 102 | 103 ± 0.5 | 102 |
| llamafile | 6201 ± 19 | 6201 | 104 ± 0.1 | 104 | 105 ± 0.1 | 105 |
| lm-studio | 6269 ± 23 | 6274 | 93.1 ± 1.2 | 93.3 | 92.6 ± 1.4 | 93.5 |
| ollama | 6122 ± 32 | 6120 | 91.0 ± 1.5 | 90.7 | 90.1 ± 1.6 | 89.4 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

All discarded runs were within 5% of their cell's trimmed mean.

