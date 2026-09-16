# Benchmark Report: qwen3.8-27b-mtp4


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp4 | 220 ± 0.7 | 220 | 14.5 ± 2.5 | 14.3 | 15.8 ± 2.9 | 16.2 |
| llamafile-mtp4 | 219 ± 0.5 | 219 | 15.1 ± 3.2 | 14.9 | 15.1 ± 2.3 | 15.7 |
| ollama-mtp4 | 225 ± 0.2 | 225 | 15.9 ± 1.9 | 16.3 | 15.5 ± 1.6 | 15.3 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp4 | 229 ± 0.6 | 229 | 13.2 ± 2.8 | 12.6 | 16.3 ± 2.6 | 16.7 |
| llamafile-mtp4 | 228 ± 0.6 | 228 | 14.5 ± 2.3 | 14.3 | 14.3 ± 2.3 | 14.0 |
| ollama-mtp4 | 233 ± 0.2 | 233 | 15.2 ± 2.3 | 14.7 | 14.1 ± 1.4 | 13.9 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp4 | 232 ± 0.2 | 232 | 13.7 ± 1.7 | 13.6 | 15.5 ± 2.9 | 15.1 |
| llamafile-mtp4 | 232 ± 0.4 | 232 | 13.6 ± 2.4 | 13.3 | 16.6 ± 2.0 | 16.2 |
| ollama-mtp4 | 235 ± 0.2 | 235 | 14.3 ± 2.0 | 14.3 | 15.5 ± 1.9 | 15.5 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp4 | 230 ± 0.2 | 230 | 14.5 ± 1.9 | 14.5 | 14.8 ± 2.6 | 14.4 |
| llamafile-mtp4 | 230 ± 0.2 | 230 | 14.1 ± 2.0 | 14.4 | 15.8 ± 2.4 | 15.9 |
| ollama-mtp4 | 233 ± 0.2 | 232 | 13.9 ± 1.8 | 13.9 | 15.2 ± 1.4 | 15.3 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| llama-cpp-mtp4 | 2048 | 32 | tg_throughput | -16.1%, -11.1% | +31.6%, +65.3% |
| llamafile-mtp4 | 1024 | 32 | tg_throughput | -27.5%, -15.4% | +35.0%, +55.1% |
| ollama-mtp4 | 2048 | 32 | tg_throughput | -21.4%, -13.2% | +16.0%, +40.7% |
| llamafile-mtp4 | 4096 | 32 | tg_throughput | -22.3%, -15.9% | +35.3%, +39.1% |
| ollama-mtp4 | 4096 | 32 | tg_throughput | -18.3%, -15.5% | +18.1%, +36.3% |
| llama-cpp-mtp4 | 1024 | 32 | tg_throughput | -33.6%, -17.2% | +25.9%, +36.0% |
| llama-cpp-mtp4 | 4096 | 64 | tg_throughput | -35.6%, -30.5% | +26.3%, +27.9% |
| llama-cpp-mtp4 | 1024 | 64 | tg_throughput | -33.8%, -25.8% | +23.1%, +31.6% |
| llama-cpp-mtp4 | 8192 | 64 | tg_throughput | -33.1%, -17.6% | +20.3%, +33.8% |
| llama-cpp-mtp4 | 8192 | 32 | tg_throughput | -32.5%, -8.5% | +19.6%, +24.2% |
| llamafile-mtp4 | 2048 | 32 | tg_throughput | -18.7%, -14.7% | +28.4%, +32.3% |
| llamafile-mtp4 | 4096 | 64 | tg_throughput | -32.1%, -12.3% | +11.1%, +14.6% |
| llamafile-mtp4 | 2048 | 64 | tg_throughput | -23.9%, -18.9% | +27.8%, +31.3% |
| llama-cpp-mtp4 | 2048 | 64 | tg_throughput | -29.5%, -26.1% | +22.5%, +23.6% |
| ollama-mtp4 | 4096 | 64 | tg_throughput | -17.0%, -12.8% | +18.2%, +28.1% |
| llamafile-mtp4 | 8192 | 64 | tg_throughput | -28.0%, -23.3% | +18.2%, +21.7% |
| llama-cpp-mtp4 | 4096 | 32 | tg_throughput | -22.9%, -19.7% | +16.0%, +26.4% |
| ollama-mtp4 | 8192 | 32 | tg_throughput | -25.2%, -16.9% | +17.7%, +25.2% |
| llamafile-mtp4 | 8192 | 32 | tg_throughput | -16.2%, -16.2% | +17.0%, +25.2% |
| llamafile-mtp4 | 1024 | 64 | tg_throughput | -24.9%, -20.2% | +17.9%, +18.9% |
| ollama-mtp4 | 8192 | 64 | tg_throughput | -14.3%, -10.9% | +8.7%, +23.8% |
| ollama-mtp4 | 1024 | 32 | tg_throughput | -23.7%, -16.7% | +14.3%, +17.6% |
| ollama-mtp4 | 2048 | 64 | tg_throughput | -15.9%, -9.7% | +16.3%, +20.4% |
| ollama-mtp4 | 1024 | 64 | tg_throughput | -20.0%, -14.3% | +10.0%, +17.8% |
