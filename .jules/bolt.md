## 2025-02-18 - [Optimization] Skip Decoding in Video Loop
**Learning:** In video processing loops where only a subset of frames (e.g., 1 in 10) are analyzed, using `cap.read()` decodes every single frame, causing significant CPU overhead. Replacing `cap.read()` with `cap.grab()` (which only reads the frame data without full decoding) for skipped frames, and using `cap.retrieve()` only for frames to be processed, results in measurable performance gains (e.g., ~27% speedup even on simple test video).
**Action:** Always check `cv2.VideoCapture` loops for unnecessary decoding. If frames are skipped based on index or time, use `cap.grab()` and `continue` instead of `cap.read()`.

## 2025-02-18 - [Optimization] Single-Pass FFmpeg Pipeline
**Learning:** Sequential FFmpeg operations (e.g., Scale -> Burn Captions -> Mix Audio) force multiple re-encoding steps, which is extremely slow and degrades quality. Combining these into a single `ffmpeg -filter_complex` command reduces total processing time significantly (roughly 2-3x speedup for typical clips) and eliminates intermediate I/O.
**Action:** Always look for opportunities to chain FFmpeg filters into a single complex graph rather than running sequential commands. Use `try-except` fallback to the sequential method if the complex command is prone to syntax errors or filter incompatibilities.
