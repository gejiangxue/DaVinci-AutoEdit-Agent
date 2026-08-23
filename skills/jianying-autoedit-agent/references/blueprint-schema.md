# JianYing Edit Blueprint Schema

Use UTF-8 JSON with this minimum shape:

```json
{
  "schema_version": "jianying-1.0",
  "project": {
    "name": "Example",
    "width": 1920,
    "height": 1080,
    "target_duration_seconds": 60
  },
  "clips": [
    {
      "id": "clip-001",
      "media_type": "video",
      "source_path": "/absolute/path/source.mp4",
      "source_in_seconds": 12.5,
      "source_out_seconds": 19.0,
      "timeline_in_seconds": 0.0,
      "timeline_out_seconds": 6.5,
      "track_name": "VideoTrack",
      "purpose": "Open on the central action",
      "audio_policy": "keep_source_audio",
      "source_group": "camera-a",
      "confidence": 0.9
    }
  ],
  "narration": [],
  "music": [],
  "captions": [],
  "effects": [],
  "transitions": [],
  "notes": []
}
```

Rules:

- Use absolute source paths at build time.
- `source_out_seconds` must be within the probed media duration.
- Every clip needs positive source and timeline duration.
- Source and timeline durations must match unless an explicitly supported
  `speed` operation is declared; the current generic builder reports speed
  changes as unsupported rather than guessing.
- Use `track_name` for video/PIP/audio placement. For backward compatibility,
  `video_track` and `audio_track` may be used by validation but should not be
  preferred in new blueprints.
- Declare `audio_policy` explicitly: `keep_source_audio`, `mute_source_audio`,
  or `manual_review`.
- A music item uses `source_path` or an approved `cloud_id`, plus start and
  duration. BGM must land on an audio track.
- A caption item uses `text`, `start_time_seconds`, and
  `duration_seconds`; an approved SRT can be declared with `srt_path`.
- A narration item may use `text` and `speaker` for JianYing-native TTS, or
  `audio_path` for pre-generated narration. Do not generate TTS without the
  TTS approval gate.
- Effects and transitions must use names found through `asset_search.py`; do
  not guess JianYing asset IDs.
