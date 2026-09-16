# Benchmark Report: qwen3.8-27b-mtp


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp | 913 ± 5.7 | 912 | 66.7 ± 7.0 | 67.3 | 62.3 ± 5.8 | 62.1 |
| llamafile-mtp | 877 ± 4.7 | 877 | 64.4 ± 6.6 | 64.9 | 65.6 ± 6.5 | 64.9 |
| lm-studio | 904 ± 8.8 | 901 | 49.9 ± 6.1 | 49.2 | 56.2 ± 7.6 | 57.1 |
| ollama-mtp | 1045 ± 12 | 1045 | 65.1 ± 5.8 | 65.6 | 68.2 ± 5.1 | 67.9 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp | 1247 ± 11 | 1248 | 62.1 ± 6.3 | 62.2 | 67.9 ± 4.7 | 68.3 |
| llamafile-mtp | 1203 ± 5.5 | 1202 | 57.8 ± 6.9 | 56.8 | 63.7 ± 4.8 | 63.8 |
| lm-studio | 1241 ± 8.2 | 1242 | 49.6 ± 6.4 | 48.8 | 52.0 ± 7.0 | 52.5 |
| ollama-mtp | 1397 ± 9.0 | 1396 | 65.4 ± 4.6 | 65.0 | 70.2 ± 2.6 | 70.5 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp | 1552 ± 7.2 | 1553 | 62.0 ± 5.2 | 61.3 | 65.4 ± 4.2 | 65.2 |
| llamafile-mtp | 1488 ± 10.0 | 1487 | 59.9 ± 5.4 | 59.8 | 63.4 ± 5.3 | 63.9 |
| lm-studio | 1540 ± 6.1 | 1539 | 48.8 ± 4.9 | 49.2 | 54.1 ± 5.4 | 53.7 |
| ollama-mtp | 1642 ± 13 | 1642 | 68.8 ± 4.3 | 67.3 | 69.2 ± 4.9 | 68.6 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp | 1718 ± 13 | 1720 | 62.9 ± 3.7 | 61.5 | 67.8 ± 6.3 | 69.5 |
| llamafile-mtp | 1663 ± 7.1 | 1662 | 60.3 ± 5.5 | 59.6 | 60.8 ± 3.2 | 60.4 |
| lm-studio | 1704 ± 20 | 1702 | 49.1 ± 4.3 | 49.2 | 51.3 ± 5.6 | 51.7 |
| ollama-mtp | 1779 ± 16 | 1776 | 60.6 ± 4.8 | 60.8 | 69.2 ± 3.2 | 69.7 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| lm-studio | 2048 | 32 | tg_throughput | -16.7%, -8.4% | +25.7%, +31.8% |
| llamafile-mtp | 2048 | 32 | tg_throughput | -13.2%, -8.9% | +20.4%, +31.5% |
| lm-studio | 8192 | 32 | tg_throughput | -10.4%, -6.4% | +5.4%, +28.5% |
| lm-studio | 4096 | 32 | tg_throughput | -13.5%, -10.8% | +11.2%, +26.0% |
| llamafile-mtp | 8192 | 32 | tg_throughput | -7.9%, -7.9% | +13.6%, +23.5% |
| lm-studio | 2048 | 64 | tg_throughput | -20.1%, -17.8% | +18.1%, +23.5% |
| lm-studio | 1024 | 64 | tg_throughput | -20.8%, -19.6% | +14.7%, +23.4% |
| lm-studio | 1024 | 32 | tg_throughput | -14.3%, -13.2% | +19.9%, +22.3% |
| ollama-mtp | 1024 | 32 | tg_throughput | -15.0%, -14.0% | +4.9%, +22.2% |
| llamafile-mtp | 1024 | 32 | tg_throughput | -22.1%, -10.8% | +18.2%, +18.4% |
| llama-cpp-mtp | 1024 | 32 | tg_throughput | -21.9%, -18.1% | +9.3%, +9.6% |
| lm-studio | 8192 | 64 | tg_throughput | -19.6%, -15.4% | +14.5%, +21.7% |
| llamafile-mtp | 4096 | 32 | tg_throughput | -20.9%, -6.8% | +14.9%, +15.6% |
| llamafile-mtp | 4096 | 64 | tg_throughput | -20.0%, -17.3% | +7.5%, +8.8% |
| llamafile-mtp | 1024 | 64 | tg_throughput | -19.0%, -16.4% | +11.1%, +14.7% |
| lm-studio | 4096 | 64 | tg_throughput | -18.1%, -13.8% | +17.2%, +17.2% |
| ollama-mtp | 8192 | 32 | tg_throughput | -6.0%, -5.6% | +17.0%, +18.0% |
| llamafile-mtp | 2048 | 64 | tg_throughput | -9.6%, -6.7% | +13.1%, +17.2% |
| llama-cpp-mtp | 8192 | 64 | tg_throughput | -16.9%, -16.2% | +11.8%, +16.0% |
| llama-cpp-mtp | 2048 | 32 | tg_throughput | -16.7%, -12.3% | +15.9%, +16.3% |
| llama-cpp-mtp | 1024 | 64 | tg_throughput | -14.9%, -9.4% | +15.4%, +15.4% |
| ollama-mtp | 4096 | 32 | tg_throughput | -15.4%, -10.4% | +5.7%, +6.0% |
| llama-cpp-mtp | 2048 | 64 | tg_throughput | -15.1%, -12.2% | +8.1%, +9.0% |
| llama-cpp-mtp | 4096 | 32 | tg_throughput | -12.7%, -12.0% | +8.1%, +14.5% |
| ollama-mtp | 1024 | 64 | tg_throughput | -14.0%, -8.9% | +10.4%, +10.4% |
| llama-cpp-mtp | 8192 | 32 | tg_throughput | -9.9%, -9.3% | +5.2%, +12.7% |
| llama-cpp-mtp | 4096 | 64 | tg_throughput | -9.3%, -6.8% | +8.2%, +12.6% |
| ollama-mtp | 8192 | 64 | tg_throughput | -12.6%, -6.5% | +5.2%, +5.8% |
| ollama-mtp | 2048 | 32 | tg_throughput | -11.1%, -10.3% | +11.2%, +11.7% |
| ollama-mtp | 4096 | 64 | tg_throughput | -11.3%, -11.0% | +7.5%, +10.9% |
| llamafile-mtp | 8192 | 64 | tg_throughput | -9.6%, -7.1% | +6.8%, +7.6% |
| ollama-mtp | 2048 | 64 | tg_throughput | -8.2%, -4.9% | +2.4%, +6.0% |
