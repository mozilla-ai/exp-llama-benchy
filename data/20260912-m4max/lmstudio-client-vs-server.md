# Why LM Studio's client-side decode numbers are inflated on macOS

Probe: `sse_probe.py` (same directory) sends the same streaming
`/v1/chat/completions` request llama-benchy sends (≈1000-token prompt,
`max_tokens` 32 or 64, `stream_options.include_usage`) and records the arrival
time of every SSE chunk. Run on the Mac Studio on 2026-09-10 against LM Studio
(`lms load qwen/qwen3.5-9b --gpu max -c 16384`, runtime metal 2.28.2) and, as a
control, against upstream llama-server b10441 with the same GGUF.

## What the wire shows

LM Studio, tg=32 (three requests, identical pattern):

```
text chunks = 31   usage.completion_tokens = 32   (token 1 = <think>, swallowed by the reasoning parser)
inter-chunk gaps (ms): 74.8, 0.1, 0.0, 0.0, 14.7, 0.1, ...   median 14.7
first text chunk -> stream end: 391 ms
```

llama-server, tg=32 (three requests):

```
text chunks = 32   usage.completion_tokens = 32
inter-chunk gaps (ms): 15.2, 14.8, 14.7, 14.8, 14.7, 14.7, ...   min 14.5, max 16.4
first text chunk -> stream end: 460 ms
```

Server-side `print_timing` for the same requests: LM Studio 472-475 ms / 32
tokens (67.4-67.8 tok/s); llama-server 459-461 ms / 32 tokens (67.3-67.5 tok/s).
The engines decode at the same speed. The two streams do not look the same.

LM Studio's stream is bursty: after the first text chunk there is a 75 ms pause
(five token-times) and then four chunks land within 0.1 ms; later, tokens often
arrive in pairs (gaps 0.0/0.1 alternating with ~15/30 ms). Its steady-state
median gap, 14.7 ms, equals the server's 14.8 ms per token exactly -- the tokens
are generated on time, they are released late and in batches by the output
post-processor (the reasoning-tag parser that turns `<think>` text into
`reasoning_content` deltas). llama-server emits one chunk per token every
14.8 ms with no burst.

## Why the formula misreads it

llama-benchy's per-request decode speed is

    tg = (tokens - 1) / (stream_end - first_text_chunk)

Anchoring on the first text chunk assumes it marks the first generated token.
For LM Studio it does not: the first chunk is released roughly k = 4-5 token-times
late, so the window is k token-times too short while the count is unchanged.
The inflation is (n - 1) / (n - k):

| n | predicted | measured (llama-benchy) | server-side |
|---|---|---|---|
| 32 | 31/27 = +15% | 76.4-77.5 tok/s vs 66.4-67 | 66.4 |
| 64 | 63/59 = +7% | 70.7-71.0 tok/s | 65.4 |
| 256 | 255/251 = +1.6% | (not run) | |

The same k explains the August numbers (77.5 / 70.8), today's (76.4 / 70.7),
and the 0.8B (client 261/239 vs server 227/224). It is not present on the
Linux pod (client 94.0 vs server 95.8 at 9B), so it is a property of LM
Studio's macOS build, not of the engine or the model.

## Why the server-side number is the one to report

1. Three independent instruments agree: llama-server client-side (67.3),
   llama-server `print_timing` (67.4), LM Studio `print_timing` (67.6). Only
   LM Studio client-side disagrees (76.7), and it disagrees by exactly the amount
   the late-first-chunk model predicts, in the direction and with the
   output-length dependence it predicts.
2. LM Studio's own steady-state inter-chunk gap (14.7 ms = 67.8 tok/s) agrees
   with its server-side figure: the client stream itself says 67-68 tok/s once
   the first-chunk anchor is discounted.
3. `print_timing` is the same code in all four servers (llama.cpp's server,
   which LM Studio and Ollama embed), measured inside the engine at the moment
   each token is sampled: one instrument, applied identically, immune to how
   each product batches its HTTP output.
4. The client-side number still matters -- for time-to-first-token and for what
   a streaming UI actually shows -- but as a decode-speed estimate it measures
   LM Studio's chunking policy, not its engine.

## Consequences for the tables

- Mac LM Studio decode: use the server-side figures from
  `lmstudio-server-logs/2026-09-10.1.log` (0.8B: 228/224, 9B: 66.4/65.4,
  27B-MTP: 22.3/23.5 tok/s for tg 32/64), not the client-side JSON.
- Everywhere else client and server agree within ~1% and either can be used.
- A client-side fix for llama-benchy would be to anchor the decode window on
  the *second* text chunk and count from there, or to use each server's
  reported timings where available (llama-server returns a `timings` object;
  Ollama's native API returns `eval_count`/`eval_duration`; LM Studio's
  OpenAI endpoint returns neither).
- Incidentally, the probe also shows LM Studio ignoring `cache_prompt: false`:
  repeated identical prompts are served from its prompt cache (prompt eval
  44 ms / 4 tokens instead of 1226 ms / 971 tokens).
