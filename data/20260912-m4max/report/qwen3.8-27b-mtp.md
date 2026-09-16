# Benchmark Report: qwen3.8-27b-mtp


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp | 219 ± 0.6 | 219 | 22.9 ± 2.3 | 22.7 | 24.0 ± 1.8 | 23.9 |
| llamafile-mtp | 218 ± 0.9 | 218 | 21.9 ± 2.3 | 21.6 | 25.4 ± 2.0 | 25.5 |
| lm-studio | 221 ± 2.5 | 222 | 25.6 ± 3.3 | 25.1 | 24.3 ± 2.3 | 24.3 |
| ollama-mtp | 226 ± 0.3 | 226 | 22.5 ± 2.4 | 22.9 | 23.7 ± 0.8 | 23.9 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp | 228 ± 0.4 | 228 | 23.1 ± 2.8 | 23.3 | 22.9 ± 2.2 | 22.9 |
| llamafile-mtp | 228 ± 0.3 | 228 | 22.5 ± 1.8 | 22.8 | 24.0 ± 2.1 | 24.3 |
| lm-studio | 229 ± 1.5 | 229 | 22.4 ± 2.6 | 22.0 | 24.2 ± 3.1 | 23.4 |
| ollama-mtp | 233 ± 0.2 | 234 | 24.3 ± 2.8 | 24.9 | 24.0 ± 1.3 | 23.9 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp | 231 ± 0.3 | 231 | 22.5 ± 2.3 | 22.6 | 23.8 ± 2.1 | 24.1 |
| llamafile-mtp | 231 ± 0.1 | 231 | 22.2 ± 3.0 | 21.9 | 22.9 ± 2.3 | 23.1 |
| lm-studio | 231 ± 0.8 | 232 | 23.5 ± 2.9 | 24.0 | 23.8 ± 2.1 | 23.8 |
| ollama-mtp | 236 ± 0.2 | 236 | 23.7 ± 1.6 | 23.7 | 23.8 ± 1.7 | 24.0 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp-mtp | 229 ± 0.2 | 229 | 22.3 ± 2.3 | 22.3 | 24.7 ± 1.7 | 25.1 |
| llamafile-mtp | 229 ± 0.1 | 229 | 21.1 ± 2.8 | 20.0 | 22.9 ± 2.2 | 23.3 |
| lm-studio | 229 ± 0.4 | 229 | 24.4 ± 3.0 | 24.0 | 24.3 ± 2.1 | 23.8 |
| ollama-mtp | 233 ± 0.2 | 233 | 21.3 ± 2.1 | 21.4 | 23.8 ± 1.8 | 23.7 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| lm-studio | 4096 | 32 | tg_throughput | -17.9%, -13.5% | +20.2%, +29.2% |
| llamafile-mtp | 8192 | 32 | tg_throughput | -19.1%, -10.5% | +20.4%, +27.9% |
| llamafile-mtp | 4096 | 32 | tg_throughput | -20.4%, -18.1% | +19.3%, +27.4% |
| lm-studio | 2048 | 64 | tg_throughput | -13.9%, -12.2% | +20.5%, +26.1% |
| lm-studio | 8192 | 32 | tg_throughput | -13.2%, -12.6% | +21.5%, +24.2% |
| llamafile-mtp | 2048 | 32 | tg_throughput | -7.4%, -7.3% | +7.3%, +24.0% |
| lm-studio | 2048 | 32 | tg_throughput | -12.6%, -10.7% | +20.7%, +24.0% |
| llama-cpp-mtp | 2048 | 32 | tg_throughput | -23.9%, -23.8% | +13.3%, +16.1% |
| ollama-mtp | 2048 | 32 | tg_throughput | -22.4%, -20.3% | +13.7%, +16.7% |
| lm-studio | 1024 | 32 | tg_throughput | -22.4%, -18.6% | +18.7%, +18.8% |
| llama-cpp-mtp | 1024 | 32 | tg_throughput | -21.4%, -18.0% | +14.8%, +17.7% |
| ollama-mtp | 1024 | 32 | tg_throughput | -21.0%, -16.0% | +15.7%, +15.8% |
| llamafile-mtp | 1024 | 32 | tg_throughput | -19.3%, -11.8% | +17.0%, +17.5% |
| lm-studio | 1024 | 64 | tg_throughput | -19.1%, -18.6% | +10.4%, +13.2% |
| ollama-mtp | 8192 | 32 | tg_throughput | -11.5%, -11.4% | +18.5%, +18.6% |
| llama-cpp-mtp | 2048 | 64 | tg_throughput | -13.4%, -11.2% | +16.0%, +18.3% |
| lm-studio | 4096 | 64 | tg_throughput | -18.1%, -11.8% | +11.2%, +13.0% |
| llama-cpp-mtp | 4096 | 32 | tg_throughput | -16.5%, -14.1% | +12.5%, +17.8% |
| llama-cpp-mtp | 8192 | 32 | tg_throughput | -16.7%, -13.9% | +16.4%, +16.5% |
| llamafile-mtp | 4096 | 64 | tg_throughput | -15.7%, -15.5% | +13.6%, +16.4% |
| llama-cpp-mtp | 1024 | 64 | tg_throughput | -7.9%, -4.8% | +16.3%, +16.3% |
| llamafile-mtp | 1024 | 64 | tg_throughput | -16.3%, -15.4% | +5.1%, +13.6% |
| lm-studio | 8192 | 64 | tg_throughput | -16.1%, -13.5% | +10.8%, +11.1% |
| llamafile-mtp | 8192 | 64 | tg_throughput | -15.9%, -12.0% | +12.7%, +16.0% |
| llama-cpp-mtp | 8192 | 64 | tg_throughput | -14.8%, -11.0% | +4.9%, +11.8% |
| ollama-mtp | 4096 | 64 | tg_throughput | -14.5%, -8.3% | +11.5%, +11.6% |
| llama-cpp-mtp | 4096 | 64 | tg_throughput | -14.0%, -12.6% | +9.4%, +10.7% |
| ollama-mtp | 4096 | 32 | tg_throughput | -13.6%, -7.5% | +8.6%, +11.0% |
| llamafile-mtp | 2048 | 64 | tg_throughput | -12.7%, -11.7% | +10.6%, +13.4% |
| ollama-mtp | 8192 | 64 | tg_throughput | -12.4%, -11.7% | +11.5%, +11.6% |
| ollama-mtp | 2048 | 64 | tg_throughput | -9.6%, -7.2% | +8.4%, +9.9% |
| ollama-mtp | 1024 | 64 | tg_throughput | -6.5%, -3.6% | +4.9%, +5.9% |
