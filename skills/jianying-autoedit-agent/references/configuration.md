# JianYing AutoEdit Configuration

## Decision order

1. Detect local tools and configured environment variables.
2. Explain which requested stage needs each dependency.
3. Configure only what the user accepts.
4. Test without printing secrets.
5. Skip declined optional stages.

## JianYing skill location

The generic builder searches these locations, in order:

```text
JY_SKILL_ROOT
<project>/.agent/skills/jianying-editor
<project>/.trae/skills/jianying-editor
<project>/.claude/skills/jianying-editor
<project>/skills/jianying-editor
~/.codex/skills/jianying-editor
```

The selected directory must contain `scripts/jy_wrapper.py`. Set
`JY_SKILL_ROOT` when the skill is installed elsewhere. `JY_DRAFTS_ROOT` may be
used to select the JianYing drafts directory.

## Optional multimodal LLM

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=...
LLM_SUPPORTS_IMAGES=1
```

The model must support image input for frame analysis. Ask permission before a
large or billable batch. If it is not configured, use Codex-native vision or a
manual review worksheet.

## Optional TTS

The installed `jianying-editor` skill may use its configured TTS backends:

```env
TTS_BASE_URL=https://provider.example/v1
TTS_API_KEY=...
TTS_MODEL=...
TTS_REFERENCE_AUDIO=/absolute/path/to/reference.wav
```

Preview the TTS plan before generation. Never publish or bundle a user's voice
sample. When TTS is declined or unavailable, design around production sound,
music, captions, or silence.

## Local tools

- Python 3.10+
- FFmpeg and FFprobe on `PATH` (on macOS, Homebrew is commonly
  `/opt/homebrew/bin`)
- JianYing Pro installed for opening and reviewing the generated draft
- the local `jianying-editor` skill with `JyProject`/`JyWrapper`

## Export limits

The installed JianYing skill documents headless export constraints. On macOS,
plan for a manual export in the JianYing app unless a separately verified local
export tool is available. Do not report an export as successful based only on a
Python return code.
