## 2025-02-18 - [Optimization] Skip Decoding in Video Loop
**Learning:** In video processing loops where only a subset of frames (e.g., 1 in 10) are analyzed, using `cap.read()` decodes every single frame, causing significant CPU overhead. Replacing `cap.read()` with `cap.grab()` (which only reads the frame data without full decoding) for skipped frames, and using `cap.retrieve()` only for frames to be processed, results in measurable performance gains (e.g., ~27% speedup even on simple test video).
**Action:** Always check `cv2.VideoCapture` loops for unnecessary decoding. If frames are skipped based on index or time, use `cap.grab()` and `continue` instead of `cap.read()`.

## 2025-02-18 - [Optimization] Single-Pass FFmpeg Pipeline
**Learning:** Video processing pipelines that invoke FFmpeg sequentially for each operation (e.g., crop -> subtitle -> audio mix) re-encode the video stream multiple times, leading to severe performance degradation. Combining these operations into a single `-filter_complex` graph allows FFmpeg to process the video in one pass, eliminating intermediate re-encodings and disk I/O.
**Action:** When performing multiple video transformations, always strive to construct a single FFmpeg command with a complex filter graph instead of chaining multiple subprocess calls.
