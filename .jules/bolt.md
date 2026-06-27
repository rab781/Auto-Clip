---
name: Bolt
---
## 2024-06-27 - Concurrent API Dispatch

**Learning:** When making batch API calls to an LLM service (like Chutes.ai), processing the batches sequentially inside a loop creates a severe O(batches) bottleneck due to blocking network I/O.
**Action:** Use `concurrent.futures.ThreadPoolExecutor.map` combined with a pre-configured global connection pool (`requests.Session`) to dispatch independent batches concurrently. Ensure the mapping preserves the original execution order before reassembling the results, reducing wait time to O(1) bounded by available threads and network bandwidth.
