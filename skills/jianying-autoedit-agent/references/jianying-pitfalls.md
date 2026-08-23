# JianYing Pitfalls And Required Audits

- A local skill path is not proof that `jy_wrapper.py` imports. Run a real
  preflight and stop before writing if it fails.
- `project.save()` is the delivery boundary. A Python process that exits cleanly
  without a saved, inspectable draft is not success.
- Initialize the project with the approved aspect ratio. A portrait project
  should normally use `width=1080, height=1920`; a landscape project should
  normally use `width=1920, height=1080`.
- Use absolute media paths. A relative path can produce an apparently valid
  draft with offline materials.
- `add_media_safe()` detects media type, but BGM and sound effects should use
  `add_audio_safe()` explicitly so they cannot accidentally land on a video
  track.
- Track collisions can cause the wrapper to create a suffixed audio/text
  track. Read the saved draft and report the actual track names.
- Captions and TTS must be checked for alignment after the audio duration is
  known; text length is not a reliable timing measurement.
- Search effects and transitions before applying them. JianYing IDs vary by
  local cache and version; never guess one.
- Do not directly patch draft JSON unless the installed JianYing skill itself
  documents the operation. Prefer the wrapper APIs.
- Never overwrite an existing user draft during a revision. Create a new
  versioned draft and compare it with the approved blueprint.
- On macOS, UI refresh and export may require opening the draft manually.
  Verify the visible JianYing project and the output file separately.
- After interruption, inspect the drafts root and running FFmpeg/Python jobs
  before resuming. Do not reuse a half-built draft silently.
