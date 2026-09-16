# Benchmark Report: idot-ab-0.8b


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 673 ± 1.8 | 673 | 59.9 ± 1.5 | 60.6 | 59.8 ± 0.7 | 59.8 |
| llama-cpp-idot | 852 ± 22 | 853 | 60.3 ± 1.2 | 60.5 | 59.5 ± 0.8 | 59.7 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 703 ± 1.3 | 703 | 60.2 ± 1.6 | 60.7 | 59.3 ± 1.3 | 59.3 |
| llama-cpp-idot | 900 ± 12 | 900 | 60.8 ± 0.6 | 60.9 | 58.7 ± 1.3 | 58.9 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 676 ± 1.0 | 676 | 59.7 ± 1.4 | 59.9 | 59.3 ± 1.2 | 59.3 |
| llama-cpp-idot | 847 ± 1.4 | 847 | 59.3 ± 1.2 | 59.3 | 57.9 ± 1.4 | 58.1 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 587 ± 0.7 | 587 | 57.3 ± 2.0 | 57.8 | 56.8 ± 1.5 | 56.8 |
| llama-cpp-idot | 698 ± 0.9 | 698 | 57.1 ± 0.8 | 56.9 | 56.5 ± 1.6 | 56.3 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| llama-cpp-idot | 1024 | 32 | pp_throughput | -13.7%, -0.6% | +0.3%, +0.5% |
| llama-cpp | 8192 | 32 | tg_throughput | -7.6%, -6.0% | +2.3%, +3.6% |
| llama-cpp-idot | 4096 | 64 | tg_throughput | -3.7%, -2.2% | +0.9%, +7.4% |
| llama-cpp-idot | 2048 | 32 | pp_throughput | -6.9%, -0.3% | +0.2%, +0.2% |
| llama-cpp | 8192 | 64 | tg_throughput | -6.7%, -4.2% | +1.3%, +5.1% |
| llama-cpp-idot | 8192 | 64 | tg_throughput | -5.9%, -1.0% | +4.5%, +5.8% |
| llama-cpp | 2048 | 64 | tg_throughput | -3.6%, -1.4% | +3.6%, +5.6% |
| llama-cpp | 4096 | 64 | tg_throughput | -5.4%, -2.6% | +2.3%, +2.7% |
| llama-cpp | 4096 | 32 | tg_throughput | -5.1%, -4.4% | +1.5%, +4.5% |
