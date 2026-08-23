# Default Editorial Best Practices

Use this profile only after the user says they have no preferred practice.

## Story

- Define one memorable core idea and a beginning, development, turn, and
  resolution.
- Let evidence lead the script. Never invent a shot, quote, location, person,
  or event.
- Open with a meaningful change, question, action, or emotional contrast.
- Alternate information, action, reaction, and atmosphere.

## Rhythm

- Match shot duration to information density and emotion, not a fixed number.
- Use shorter cuts for action or discovery and longer holds for performance,
  landscape, tension, or reflection.
- Protect breathing room after dense narration.
- Prefer motivated J-cuts/L-cuts and natural-sound bridges.

## 气口处理（Breathing / Pacing — 可操作实现）

> **此节必须有具体操作，不能只写原则。** 气口不是"每句加固定空档"，而是
> 基于**真正开口时间**和**话隙（speech gap）**的规则化处理。推荐复用
> `talking-head-cleanup` skill（本机已装），它是专门的气口清理方案；以下
> 是可直接落地的规则，供在 `director_to_blueprint` 或建草稿前应用。

### 输入
- 每段源素材的 **word-level 逐句时间戳**（用 whisper 生成，见下）。
- 源素材的 **silence scan**：`ffmpeg -i <src> -af "silencedetect=noise=-35dB:d=0.2" -f null -`。

### 话隙阈值（Cut modes）
- `tight_reel`（紧凑，适合快节奏卖货/短视频）：移除几乎所有 restart、填充词、
  思考停顿、重复铺垫、死空间；**检查每个 >250ms 的话隙**，保留 >350ms 需写 QC 理由。
- `natural_explainer`（自然，适合解释/口播）：保留足够节奏让人听感自然清晰，
  但仍删思考停顿/假开始/重复；**检查每个 >450ms 的话隙**，保留 >650ms 需写 QC 理由。

### 处理步骤
1. **去杂质**：识别并删除 "3 2 1 开始"、"可以"、"呃/嗯/啊"等开场/填充/重复口播。
2. **定位真正开口时间**：不是用 whisper 的粗切时间，而是用 word 级时间戳 +
   silence scan 找**说话音真正开始/结束**的边界（去掉前后静音）。
3. **隐藏停顿与断句**：*句内*长话隙（>阈值且同一句内）→ 如果停顿破坏连贯则缩短；
   *句间*话隙 → 按 mode 保留成自然气口，不要归零（话赶话）也不要过大（拖沓）。
4. **重复口播检查**：同段素材里重复说的内容（如 m4 里重复"用硫磺熏出来的"）
   删除冗余那一句，避免啰嗦。
5. **QC**：跑 `ffmpeg silencedetect` 复查输出成片，确认没有过长死空间/被掐断的字。

### 与剪映蓝图的衔接
把处理后的**干净时间轴**（每句的 source_in/out + timeline_in/out）写入
`edit-blueprint.json` 的 clips。**timeline 句间保留自然气口（0.1~0.3s），
不要再机械归零**。字幕（captions）对齐每句真正的开口时间。

### 推荐命令（调用 talking-head-cleanup）
```bash
cd ~/.agents/skills/talking-head-cleanup
npm run talking-head:prepare -- \
  --edit-dir <run_root>/presenter_edit --source <raw> \
  --mode tight_reel --transcriber local-whisper --transcribe-model medium
```
然后用其产出的 `takes_packed.md` / `edl_final.json` 作为精剪时间轴，
转入 `director_to_blueprint` 建剪映草稿。

## Coverage

- Review every source family independently.
- Do not let the easiest long camera files dominate the first cut.
- Use alternate cameras for people, reactions, process, context, and texture.
- Track counts and duration by source group. An available complementary group
  at 0% requires deliberate justification.

## Audio

- Dialogue/narration intelligibility comes first.
- Preserve useful natural sound.
- Add BGM only with current-task authorization.
- Do not claim automatic ducking or normalization succeeded without readback
  or audible verification.

## Revisions

- Preserve approved versions.
- Make structural changes in a new timeline.
- Re-audit boundaries between sections; duplicate-source errors often occur
  across section edges.
