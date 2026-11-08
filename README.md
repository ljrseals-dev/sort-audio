# Audio Sample Quality Organizer

Analyzes audio samples against broadcast-style quality thresholds (sample
rate, bit depth, bitrate, channels), renames them with embedded quality
metrics, sorts them alphabetically, and color-codes the output folders in
Windows Explorer.

## Features

- Reads `bitrate`, `sample_rate`, `bit_depth`, and `channels` via `mutagen`
- Grades each sample as **PASS / MARGINAL / FAIL**
- Renames files with a structured template, e.g.
  `001_kick_48kHz_24bit_1411kbps_PASS.wav`
- Sorts output alphabetically by original filename, then by grade folder
- Color-codes output folders on Windows via `desktop.ini` + `imageres.dll`
- Non-destructive by default (copies files; use `--move` to relocate)

## Install

    pip install -r requirements.txt

## Usage

    python main.py --input "C:\Samples\Raw" --output "C:\Samples\Organized"

Preview without writing anything:

    python main.py -i "C:\Samples\Raw" -o "C:\Samples\Organized" --dry-run

Move instead of copy (destructive):

    python main.py -i "C:\Samples\Raw" -o "C:\Samples\Organized" --move

## Output layout

    Organized/
      01_PASS/       <- green folder icon
      02_MARGINAL/   <- yellow folder icon
      03_FAIL/       <- red folder icon

## Configuration

Edit `config.yaml` to change thresholds, folder names, icons, or the rename
template.

| Metric | Pass | Marginal |
|---|---|---|
| Sample rate | 48000 Hz | 44100 Hz |
| Bit depth (lossless formats only) | 24 bit | 16 bit |
| Bitrate | 192 kbps | 128 kbps |

**Bit depth only applies to lossless PCM formats** (wav/aiff/flac). Lossy
formats (mp3/aac/m4a/ogg/opus) don't have a real bit depth, so that metric
is skipped for them and grading falls back to sample rate + bitrate +
channels.

## Modules

| File | Responsibility |
|---|---|
| `main.py` | CLI, orchestration |
| `scanner.py` | Recursive file discovery |
| `metadata.py` | mutagen metadata extraction |
| `quality.py` | Grading engine |
| `renamer.py` | Template-based renaming |
| `organizer.py` | Folder creation + copy/move |
| `tagger.py` | Windows folder coloring |

## Notes

- Folder coloring only works on Windows (uses `ctypes` + `imageres.dll`).
- The exact icon resource IDs (`-3`, `-4`, `-5`) vary slightly between
  Windows builds. If a color doesn't appear, try other negative indices.
- On non-Windows systems, use `--no-color` or the coloring step is skipped
  automatically.

## Changelog vs. original version

- **Fixed:** `quality.py` no longer auto-fails every lossy file (mp3, aac,
  m4a, ogg, opus). Previously, bit depth was graded for all formats, but
  mutagen can't report a bit depth for lossy codecs, so `bit_depth=None`
  meant every non-wav/aiff/flac file scored FAIL regardless of actual
  quality. Bit depth is now skipped (not counted) for lossy formats.
- Removed a redundant in-function `import` in `main.py` (functionality
  unchanged).
