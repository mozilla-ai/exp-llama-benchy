# Benchmark Report: qwen3.5-0.8b-all-servers


## Results by prompt size

Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell the first run is dropped as warm-up, then the 2 slowest and 2 fastest of the rest; the mean is of the runs that remain, the ± is the standard deviation of *all* post-warm-up runs, so it shows the raw spread. **med** is the median of the same runs -- an untuned check that should match the trimmed mean within about a percent. **PP** is pooled across the tg runs (prefill completes before generation starts, so tg cannot affect it). **TG** is listed per tg because speculative decoding makes it depend on output length.


### pp=1024

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 7143 ± 287 | 7225 | 227 ± 10 | 225 | 234 ± 12 | 230 |
| llamafile | 7343 ± 38 | 7344 | 241 ± 3.2 | 241 | 242 ± 2.0 | 242 |
| lm-studio | 5849 ± 153 | 5870 | 261 ± 7.1 | 258 | 237 ± 6.6 | 235 |
| ollama | 7171 ± 145 | 7244 | 204 ± 9.6 | 203 | 220 ± 13 | 222 |

### pp=2048

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 7621 ± 179 | 7653 | 241 ± 14 | 246 | 252 ± 9.9 | 252 |
| llamafile | 7687 ± 17 | 7688 | 239 ± 2.9 | 239 | 239 ± 2.7 | 239 |
| lm-studio | 6685 ± 107 | 6668 | 254 ± 15 | 257 | 243 ± 6.1 | 246 |
| ollama | 7696 ± 47 | 7703 | 234 ± 3.8 | 234 | 228 ± 8.5 | 230 |

### pp=4096

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 7531 ± 140 | 7549 | 234 ± 12 | 232 | 237 ± 12 | 244 |
| llamafile | 7642 ± 20 | 7645 | 235 ± 2.8 | 234 | 235 ± 1.0 | 236 |
| lm-studio | 7046 ± 76 | 7034 | 253 ± 12 | 257 | 235 ± 5.7 | 234 |
| ollama | 7758 ± 37 | 7756 | 222 ± 6.0 | 221 | 228 ± 6.1 | 228 |

### pp=8192

| Server | PP | med | TG tg=32 | med | TG tg=64 | med |
|--------|----|-----|--------|-----|--------|-----|
| llama-cpp | 7127 ± 37 | 7136 | 229 ± 10 | 227 | 235 ± 9.9 | 239 |
| llamafile | 7132 ± 8.8 | 7132 | 226 ± 3.0 | 226 | 227 ± 2.0 | 226 |
| lm-studio | 6817 ± 38 | 6813 | 244 ± 14 | 245 | 224 ± 5.4 | 223 |
| ollama | 7277 ± 18 | 7278 | 212 ± 4.9 | 211 | 216 ± 7.6 | 221 |

## Trimmed runs

Runs discarded by the symmetric trim, as % deviation from the cell's trimmed mean; only cells where a discarded run is more than 5% off are listed.

| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |
|--------|----|----|--------|-------------------|-------------------|
| llama-cpp | 2048 | 64 | tg_throughput | -13.8%, -7.1% | +0.8%, +0.8% |
| ollama | 1024 | 64 | tg_throughput | -12.8%, -9.2% | +5.0%, +8.9% |
| ollama | 1024 | 32 | tg_throughput | -5.5%, -3.8% | +10.6%, +12.1% |
| llama-cpp | 8192 | 64 | tg_throughput | -11.9%, -6.5% | +1.9%, +2.0% |
| llama-cpp | 2048 | 32 | tg_throughput | -11.7%, -10.7% | +4.5%, +4.7% |
| lm-studio | 2048 | 32 | tg_throughput | -9.9%, -9.9% | +5.1%, +5.4% |
| llama-cpp | 8192 | 32 | tg_throughput | -9.6%, -9.3% | +3.7%, +3.8% |
| lm-studio | 4096 | 32 | tg_throughput | -9.5%, -9.5% | +2.1%, +4.3% |
| llama-cpp | 1024 | 32 | tg_throughput | -5.3%, -4.1% | +8.9%, +9.5% |
| llama-cpp | 4096 | 32 | tg_throughput | -9.2%, -9.1% | +4.6%, +4.9% |
| llama-cpp | 4096 | 64 | tg_throughput | -9.1%, -8.6% | +3.4%, +3.7% |
| ollama | 2048 | 64 | tg_throughput | -8.2%, -7.6% | +2.4%, +2.5% |
| llama-cpp | 1024 | 64 | tg_throughput | -8.2%, -6.9% | +7.5%, +7.8% |
| llama-cpp | 1024 | 32 | pp_throughput | -7.9%, -6.4% | +2.8%, +3.7% |
| lm-studio | 8192 | 32 | tg_throughput | -6.1%, -6.1% | +5.7%, +7.7% |
| llama-cpp | 2048 | 64 | pp_throughput | -7.7%, -3.4% | +0.6%, +0.8% |
| llama-cpp | 1024 | 64 | pp_throughput | -7.4%, -7.0% | +3.5%, +4.6% |
| ollama | 4096 | 64 | tg_throughput | -7.0%, -6.7% | +1.3%, +1.6% |
| lm-studio | 1024 | 64 | tg_throughput | -1.7%, -1.7% | +5.9%, +6.4% |
| lm-studio | 1024 | 32 | tg_throughput | -4.3%, -1.7% | +3.6%, +6.2% |
| llama-cpp | 2048 | 32 | pp_throughput | -5.7%, -5.4% | +1.3%, +1.4% |
| ollama | 4096 | 32 | tg_throughput | -3.7%, -2.9% | +4.0%, +5.6% |
| lm-studio | 1024 | 64 | pp_throughput | -5.5%, -4.5% | +1.9%, +4.8% |
| lm-studio | 8192 | 64 | tg_throughput | -1.4%, -1.3% | +5.3%, +5.5% |
| ollama | 8192 | 64 | tg_throughput | -5.3%, -5.3% | +2.8%, +3.2% |
