---
name: jianying-autoedit-agent
description: Create and revise JianYing video drafts from user-selected media, including source-grounded editing, vertical talking-head pacing, subtitle packaging, and saved-draft audits.
---

# JianYing AutoEdit Agent

Run a source-safe workflow from media intake to an audited JianYing draft. Use
the bundled `viral-video-writer` for scripts and the installed
`jianying-editor` skill for JianYing project operations.

For a user-led 9:16 talking-head, product-demo, exhibition, or livestream
video revision, read [references/talking-head-packaging.md](references/talking-head-packaging.md)
before building the draft. It captures the proven cut, caption, packaging, and
visual-QA decisions for this mode. Do not apply that profile to unrelated
formats such as cinematic montage, interview documentary, or landscape work
unless the user explicitly asks for it.

## Opening Message

Start by telling the user:

> 我可以检查你选择的视频、音频和图片素材，建立素材审查与标签表，发展主题和文案，可选生成配音，创建逐镜头剪辑蓝图，然后用剪映生成并审计草稿。我会在每个创作产物进入下一阶段前展示并请你确认，源素材保持不变。

Then collect only missing information:

1. Media path or paths. Accept any accessible video/audio directory or file.
2. Topic, purpose, audience, platform, target duration, aspect ratio, and
   language. Do not impose a subject.
3. Ask: "Do you have your own pacing rules, editing practices, references, or
   non-negotiables?" If yes, record them. If no, offer the best-practice
   profile in `references/editorial-best-practices.md`.
4. Ask whether narration/TTS is wanted. Do not assume it.
5. Ask whether to build a JianYing draft or deliver only a blueprint.

Summarize the brief in chat and obtain approval before writing
`project-brief.json`.

## Approval Contract

Read-only inspection does not require repeated confirmation. Before creating
or replacing an artifact, show a concise preview, list the intended path, and
ask for explicit approval.

Use these gates:

1. Project brief
2. Scan scope and exclusions
3. Material review and taxonomy
4. Story direction and script
5. TTS plan, only when enabled
6. Edit blueprint
7. JianYing draft write
8. Effects, transitions, audio, subtitles, or export operations
9. Pickup-shot and missing-material report

Approval for one gate does not authorize later gates. Never overwrite a
previous approved artifact; create a versioned run or draft unless replacement
was explicitly requested.

## Configuration

Before API-backed work, run:

```bash
python scripts/check_setup.py
```

The environment check covers Python, FFmpeg/FFprobe, optional LLM/TTS
configuration, and the locally installed `jianying-editor` skill. If an API
is missing, offer the manual or local fallback instead of silently inventing a
dependency.

- If no LLM API is configured, continue with Codex-native visual inspection or
  produce a manual review worksheet.
- If no TTS API or JianYing TTS backend is available, set `tts.enabled=false`
  and design around dialogue, natural sound, music, captions, or silence.
- If `jianying-editor` cannot be located, deliver the approved blueprint and
  explain the missing installation path; do not pretend a draft was written.

Read `references/configuration.md` before changing environment configuration.
Never print secrets, private endpoints, voice samples, or private media paths
outside the user-approved run artifacts.

## Workflow

### 1. Create the run folder

After brief approval, create:

```text
workspace/runs/<project-slug>/
  project-brief.json
  scan/
  review/
  script/
  tts/
  blueprint/
  jianying/
```

Project-specific scripts belong in the workspace run folder or project root,
not inside the installed skill directory.

### 2. Scan media

Preview the paths and extension policy, then run:

```bash
python scripts/scan_media.py --input "<path>" --output "<run>/scan"
```

Pass `--input` repeatedly for multiple roots. Accept common video, audio, and
image formats. Use FFprobe metadata when available. Do not filter by date or
camera unless the user requests it.

Review `media-manifest.json` and confirm file counts, duration by media type,
unreadable files, provisional source groups, duplicate candidates, and
explicit exclusions. Obtain approval before extracting review derivatives.

### 3. Analyze and review

For video, sample enough frames to represent scene changes and long takes. For
audio, inspect duration, channels, loudness when tooling supports it, and
transcribe only with permission. Treat images as selectable visual assets.

When an API-backed batch is approved, run:

```bash
python scripts/extract_frames.py --manifest "<run>/scan/media-manifest.json" --output "<run>/review/frames"
python scripts/analyze_frames.py --frames-index "<run>/review/frames/frames-index.json" --output "<run>/review/frame-analysis.jsonl" --topic "<user topic>"
```

Use evidence-based labels: scene, people, action, dialogue, emotion, quality,
continuity, source group, narrative use, and visible text. Never reject an
entire camera family because derivative files or early samples look weak.

Produce a review preview with the chronological inventory, strongest moments,
technical risks, usable-duration estimates, possible story beats, and
unanswered factual questions. After approval, write
`review/material-review.json` and `.md`.

### 4. Write the story

Invoke `viral-video-writer` with the approved brief and material review, not
imagined footage. Present one core idea, 2–3 story structures, the intended
emotional curve, narration policy, and title/hook options when relevant.
After the user chooses a direction, draft and show the full script; write it
only after explicit approval.

### 5. Decide TTS and captions

If narration is disabled, skip TTS and design around dialogue, natural sound,
music, captions, or silence.

If narration is enabled, confirm speaker, language, segmentation,
pronunciation, and output directory. Preview `tts-plan.json` before generation.
For JianYing-native narration plus aligned subtitles, the operator may use:

```python
project.add_narrated_subtitles(
    text="已批准的旁白",
    speaker="zh_female_xiaopengyou",
    start_time="0s",
    track_name="Subtitles",
)
```

For pre-generated audio, import it with `add_audio_safe()` and add approved
caption segments with `add_text_simple()` or import an approved SRT. Audit
duration, clipping, pronunciation, segment order, and subtitle alignment.

### 6. Build the JianYing blueprint

Create a source-grounded JSON blueprint following
`references/blueprint-schema.md`. Every clip must identify an absolute source
path, source in/out, timeline in/out, track name, purpose, audio policy, and
confidence. Keep source media read-only.

Audit before presenting:

- target duration and pacing
- source ranges within probed durations
- no accidental adjacent repetition across section boundaries
- meaningful source/camera diversity where available
- dialogue/narration synchronization
- still-image duration handling
- explicit authorization for music, effects, transitions, and export

Write the blueprint only after approval and validate it:

```bash
python scripts/validate_blueprint.py "<run>/blueprint/edit-blueprint.json"
```

### 7. Build a JianYing draft

Invoke `jianying-draft-operator` and use the installed `jianying-editor`
runtime. Before writing, state the exact draft name, drafts root, resolution,
tracks, media paths, captions, audio, effects, and export intent. Use a new
draft name for substantial revisions.

The generic builder is:

```bash
python scripts/build_jianying_draft.py "<run>/blueprint/edit-blueprint.json" --report "<run>/jianying/build-report.json"
```

Its implementation must follow the JianYing skill rules:

- locate `jianying-editor/scripts/jy_wrapper.py` through `JY_SKILL_ROOT` or
  standard local skill paths;
- initialize `JyProject` with the approved width and height;
- import video and images with `project.add_media_safe()` and audio with
  `project.add_audio_safe()`;
- put BGM on an audio track and keep narration separate when requested;
- use `add_narrated_subtitles()`, `add_text_simple()`, or `import_srt()` only
  for approved text/caption operations;
- search effect/transition names before applying them; never guess IDs;
- call `project.save()` and read the draft back before reporting success.

### 8. Audit the saved draft

The builder report is valid only when the current draft was actually saved.
Verify:

```bash
python <JY_SKILL_ROOT>/scripts/draft_inspector.py summary --name "<DraftName>"
python <JY_SKILL_ROOT>/scripts/draft_inspector.py show --name "<DraftName>" --kind content --json
```

Check the draft directory, project identity, at least one video segment, source
paths and source ranges, timeline gaps/overlaps, adjacent repeated sources,
track roles, BGM placement, narration/subtitle alignment, offline materials,
and any requested effects or transitions. A measurement or partially written
JSON file is not delivery.

On macOS, JianYing export is normally completed manually in the app. Do not
claim an MP4 exists unless the output file has been checked. On Windows, the
JianYing skill's `auto_exporter.py` may be used only when its documented
version constraints are satisfied.

### Direct revision mode

When the user is reviewing an existing cut and asks for a concrete change
(for example, trimming a breath, fixing subtitle placement, or adding
packaging), keep the approved edit as the source of truth and create a new
versioned JianYing draft. Read the talking-head reference when relevant, make
only the requested next change plus necessary verification, then open the
new draft in JianYing and inspect the affected timestamps. Do not silently
redo the whole cut or overwrite the user's current draft.

### 9. Recommend pickup shots

After the draft audit, compare the approved script, the saved JianYing draft,
and the complete reviewed inventory. Identify only necessary missing material:

- `P0 Required`: the cut is misleading, unclear, unsupported, or incomplete;
- `P1 Strongly Recommended`: comprehension or emotional payoff is materially
  weaker;
- `P2 Optional Enhancement`: texture, rhythm, variety, or polish.

Use `references/pickup-shot-report.md`. Check unused reviewed media before
requesting a reshoot, and propose a graphic, caption, existing cutaway,
voiceover rewrite, or script deletion when reshooting is unnecessary or
impossible. Preview findings in chat and obtain approval before writing the
report.

## Source safety

- Treat original media as immutable.
- Write derivatives only under the approved run folder or staging directory.
- Never delete or overwrite a user's existing JianYing draft without explicit
  approval.
- Stop and inspect running FFmpeg/Python jobs after interruptions.
- Never expose API keys, private endpoints, personal paths, or voice samples.

## References

- Configuration: `references/configuration.md`
- Best-practice edit profile: `references/editorial-best-practices.md`
- Blueprint schema: `references/blueprint-schema.md`
- JianYing pitfalls and audits: `references/jianying-pitfalls.md`
- Pickup-shot report: `references/pickup-shot-report.md`
