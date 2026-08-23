# Vertical Talking-Head Editing And Packaging

Use this profile for Chinese 9:16 direct-to-camera, product-demo, exhibition,
or livestream-style footage when the user wants a concise, natural edit in
JianYing. It records tested operating guidance rather than a mandatory visual
style; the user's reference video and review notes always win.

## Cut the spoken performance, not merely the waveform

1. Review each source clip around its beginning and end. Exclude slate/count-in
   talk such as "3, 2, 1, 开始", camera directions, crew chatter, false starts,
   and empty lead-in before the on-camera speaker begins.
2. Remove dead air, repeated starts, abandoned phrasing, and off-topic material.
   Preserve the content that completes the speaker's meaning and any useful
   gesture or product reveal.
3. At a speech edit, leave only a short connective breath. For normal Chinese
   promotional speech, begin around 0.10–0.25 seconds; use a little more only
   when punctuation, a reveal, or emotion needs it. Do not leave a conspicuous
   pause just because the speaker took a breath, and do not cut so tightly that
   words collide or the thought becomes abrupt.
4. Judge each join in playback. A good join sounds continuous, remains
   grammatically and logically complete, and does not jump in a distracting
   way. Rework joins that feel like a missing clause, a response without its
   setup, or a clipped consonant.
5. Maintain versioned drafts. Do not overwrite an approved cut while trying a
   new timing or packaging choice.

## Subtitle system: one readable layer

Use one spoken-caption track only. Do not stack a second auto-caption layer,
small disclaimer-like subtitle, or duplicate sentence unless the user has
explicitly asked for a separate editorial graphic.

- Use bold white Chinese captions with a black outline and modest shadow as a
  reliable default. Place them in the lower safe area, below the speaker's
  face and above platform UI; test actual frames because the correct vertical
  position varies by composition.
- Keep every glyph inside the 9:16 image, including outlines. For the local
  JianYing wrapper and large outlined text, six Chinese characters per display
  unit is a conservative safe limit. Split at natural semantic boundaries and
  never truncate a word at the edge of frame.
- Size by visual balance, not a fixed numeric field. Verify on a face shot,
  a product close-up, and a busy background. The subtitle must be instantly
  readable without covering the mouth, product, or badge.
- If the user plans to correct transcription typos later, preserve timing and
  visual structure rather than guessing a rewrite.

## Keyword highlighting without broken rich text

Highlight meaningful product, event, benefit, warning, and CTA terms only.
The desired treatment is yellow fill with black outline (and, if useful, a
subtle shadow), at the same scale as the surrounding captions. It must not be
enlarged beyond the canvas merely to appear important.

In the local `pyJianYingDraft` workflow, avoid mixed yellow/white `rich_text`
within the same caption segment: some JianYing versions can render the
uncoloured tail at the wrong size. Instead:

1. split the line into short sequential display units;
2. render a highlighted word or phrase as its own yellow/black-outlined text
   segment;
3. render adjacent non-keyword units as white/black-outlined text segments;
4. keep them on the same `Subtitles` track with contiguous timing.

This produces the reference-style colour replacement while avoiding duplicate
layers, cropped characters, and inconsistent glyph sizes.

## Light packaging

- Keep dialogue intelligible. When a music bed is authorised, start at roughly
  15–25% of its source level and adjust by playback; add a short fade-in and
  fade-out. Do not claim ducking worked unless it was audibly checked.
- Add an opening hook only when it reinforces the message. Place a compact
  yellow/black-outlined art-text title in the upper safe area for a brief
  moment, leaving the bottom area for spoken captions. Do not cover the face
  or use oversized text that exits the frame.
- Use transitions, stickers, effects, and sound effects sparingly. Each must
  support a verbal beat, product reveal, or location change. Avoid decorative
  motion that makes a direct-to-camera video feel less coherent.

## Required visual and timeline audit

After `project.save()`, inspect the saved draft and open it in JianYing. Check
the opening, at least one mid-video keyword, each important splice, and the
final CTA in the actual preview.

- Confirm only the intended video, BGM, subtitle, and optional hook-title
  tracks exist.
- Confirm no count-in, crew instruction, false start, or unused silence made
  it into the final timeline.
- Confirm captions are single-layered, legible, lower-safe, and entirely
  within the image; inspect highlighted and ordinary units separately.
- Confirm key phrases remain in the correct spoken order and the colour
  treatment does not change their timing.
- Confirm music supports rather than masks the voice, and fades at the ends.
- Report the exact versioned draft path. Do not claim an exported MP4 until
  the export file itself exists and has been checked.
