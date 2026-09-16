# Benchmark Report: qwen3.8-27b-mtp4


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp4 | 899 ± 5.7 | 900 | 67.3 ± 12 | 63.4 | 72.4 ± 13 | 70.4 |
| llamafile-mtp4 | 869 ± 6.8 | 870 | 58.0 ± 8.5 | 57.1 | 70.3 ± 11 | 71.8 |
| ollama-mtp4 | 1034 ± 11 | 1034 | 69.4 ± 9.1 | 72.3 | 76.8 ± 6.6 | 77.9 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp4 | 1235 ± 6.6 | 1234 | 61.7 ± 9.8 | 64.7 | 72.4 ± 7.9 | 71.7 |
| llamafile-mtp4 | 1189 ± 7.6 | 1188 | 58.4 ± 8.9 | 58.1 | 64.4 ± 12 | 62.5 |
| ollama-mtp4 | 1380 ± 9.5 | 1379 | 73.1 ± 11 | 72.7 | 72.8 ± 7.6 | 72.1 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp4 | 1529 ± 6.7 | 1528 | 60.6 ± 11 | 59.9 | 71.3 ± 10 | 72.5 |
| llamafile-mtp4 | 1476 ± 11 | 1477 | 59.4 ± 8.3 | 57.8 | 75.8 ± 11 | 77.4 |
| ollama-mtp4 | 1625 ± 10 | 1626 | 65.9 ± 7.1 | 65.6 | 68.7 ± 7.7 | 67.8 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp4 | 1705 ± 13 | 1706 | 61.0 ± 9.5 | 59.2 | 65.1 ± 8.6 | 68.3 |
| llamafile-mtp4 | 1643 ± 7.9 | 1643 | 64.5 ± 11 | 63.6 | 72.6 ± 12 | 73.2 |
| ollama-mtp4 | 1779 ± 13 | 1780 | 65.5 ± 8.2 | 65.5 | 69.9 ± 8.5 | 68.0 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| llamafile-mtp4 | 2048 | 64 | tg_throughput | -19.5%, -19.3% | +29.1%, +46.2% |
| llama-cpp-mtp4 | 4096 | 32 | tg_throughput | -15.8%, -14.2% | +28.7%, +44.4% |
| ollama-mtp4 | 2048 | 32 | tg_throughput | -17.5%, -16.3% | +20.1%, +36.8% |
| llama-cpp-mtp4 | 8192 | 32 | tg_throughput | -35.5%, -22.9% | +14.7%, +26.5% |
| llamafile-mtp4 | 1024 | 32 | tg_throughput | -18.5%, -18.2% | +13.3%, +33.9% |
| llama-cpp-mtp4 | 1024 | 64 | tg_throughput | -21.4%, -21.3% | +28.0%, +33.5% |
| llamafile-mtp4 | 2048 | 32 | tg_throughput | -32.8%, -18.4% | +18.9%, +31.0% |
| llamafile-mtp4 | 4096 | 64 | tg_throughput | -32.7%, -18.7% | +11.2%, +15.6% |
| llamafile-mtp4 | 4096 | 32 | tg_throughput | -14.5%, -14.3% | +16.2%, +32.7% |
| llama-cpp-mtp4 | 1024 | 32 | tg_throughput | -22.9%, -21.5% | +21.4%, +31.5% |
| ollama-mtp4 | 8192 | 32 | tg_throughput | -31.0%, -21.0% | +9.3%, +17.3% |
| llamafile-mtp4 | 8192 | 32 | tg_throughput | -29.2%, -18.2% | +30.6%, +30.8% |
| ollama-mtp4 | 1024 | 32 | tg_throughput | -22.7%, -17.1% | +15.8%, +28.7% |
| llama-cpp-mtp4 | 8192 | 64 | tg_throughput | -14.8%, -14.7% | +21.5%, +28.6% |
| llama-cpp-mtp4 | 2048 | 32 | tg_throughput | -26.9%, -20.8% | +26.7%, +27.1% |
| llamafile-mtp4 | 8192 | 64 | tg_throughput | -25.6%, -25.5% | +19.6%, +26.9% |
| llamafile-mtp4 | 1024 | 64 | tg_throughput | -25.7%, -25.6% | +19.4%, +19.8% |
| llama-cpp-mtp4 | 4096 | 64 | tg_throughput | -21.3%, -18.5% | +20.7%, +25.5% |
| ollama-mtp4 | 2048 | 64 | tg_throughput | -11.9%, -8.3% | +17.7%, +24.6% |
| llama-cpp-mtp4 | 2048 | 64 | tg_throughput | -22.0%, -18.9% | +11.7%, +12.8% |
| ollama-mtp4 | 8192 | 64 | tg_throughput | -19.3%, -13.7% | +15.5%, +20.1% |
| ollama-mtp4 | 1024 | 64 | tg_throughput | -11.8%, -11.6% | +7.4%, +20.1% |
| ollama-mtp4 | 4096 | 32 | tg_throughput | -14.8%, -9.4% | +19.2%, +19.7% |
| ollama-mtp4 | 4096 | 64 | tg_throughput | -17.9%, -11.2% | +17.5%, +19.1% |
