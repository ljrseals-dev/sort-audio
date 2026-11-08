Creating a complete technical manual for the tool.

<write_to_file>
<path>Technical Manual.md</path>
<content># Audio Sample Quality Organizer — Technical Manual

Version: 1.0
Platform: Windows (folder coloring), cross-platform for core analysis
Language: Python 3.10+
Standards basis: IASA TC-03, EBU R128

---

1. Overview

The Audio Sample Quality Organizer is a command-line tool that scans a folder
of audio samples, evaluates each file against broadcast-style quality
thresholds, renames each file with its measured metrics embedded in the
filename, sorts samples alphabetically, and places them into color-coded
output folders for quick visual reference in Windows Explorer.

1.1 Purpose

Radio and broadcast production requires fast triage of large sample libraries.
A producer needs to know, at a glance:

· Which samples meet broadcast quality and are safe to air.
· Which are borderline and usable with caution.
· Which fail and should be replaced.

This tool automates that triage and encodes the result directly into the file
system via naming and folder color.

1.2 Design goals

Goal How it's met
Non-destructive by default Files are copied, not moved (--move opts in)
Transparent grading Every decision is printed with a human-readable reason
Configurable All thresholds, names, and templates live in config.yaml
Format-aware Bit depth is graded only where it is meaningful (PCM)
No external binaries required Uses pure-Python mutagen, no FFmpeg dependency

---

2. Requirements

2.1 Runtime

· Python 3.10 or newer (uses X | None type syntax)
· Windows 10/11 for folder coloring (core analysis runs on any OS)

2.2 Dependencies

Package Purpose
mutagen>=1.47.0 Reads audio metadata across formats
PyYAML>=6.0 Parses config.yaml

Install:

```cmd
pip install -r requirements.txt
```

---

3. Architecture

3.1 Module map

```
main.py          CLI parsing, orchestration, reporting
   |
   +-- scanner.py     Find audio files, alphabetical sort
   +-- metadata.py    Extract bitrate / sample rate / bit depth / channels
   +-- quality.py     Grade each sample PASS / MARGINAL / FAIL
   +-- renamer.py     Render filename template, handle collisions
   +-- organizer.py   Create folders, copy or move files
   +-- tagger.py      Write desktop.ini to color folders (Windows)
```

3.2 Data flow

```
raw samples
     |
     v
[ scanner ] --> sorted list of Path objects
     |
     v
[ metadata ] --> AudioInfo dataclass (per file)
     |
     v
[ quality ] --> GradeResult (grade + reasons)
     |
     v
[ renamer ] --> new filename string
     |
     v
[ organizer ] --> file placed in grade folder with new name
     |
     v
[ tagger ] --> desktop.ini written, folder colored
```

3.3 Data model

AudioInfo (from metadata.py)

Field Type Meaning
path Path Original file location
bitrate_kbps int \| None Estimated/measured bitrate
sample_rate_hz int \| None Sample rate in Hz
bit_depth int \| None PCM bit depth (lossless only)
channels int \| None Channel count
duration_sec float \| None Length in seconds
format str Extension without dot (e.g. wav)
error str \| None Populated if the file could not be read

Derived properties: is_lossless, sample_rate_khz, bitrate_display,
bit_depth_display.

GradeResult (from quality.py)

Field Type Meaning
grade Grade Enum: PASS, MARGINAL, FAIL
reasons List[str] Human-readable explanations

---

4. Quality Model

4.1 Metrics and thresholds

Thresholds are defined in config.yaml and follow IASA TC-03 / EBU R128
recommendations for broadcast audio.

Metric Pass Marginal Fail
Sample rate = 48000 Hz = 44100 Hz < 44100 Hz
Bit depth (PCM only) = 24 bit = 16 bit < 16 bit
Bitrate = 192 kbps = 128 kbps < 128 kbps
Channels 1 or 2 — anything else

4.2 Grading algorithm

For each file:

1. If the file failed to read (info.error is set), grade is FAIL.
2. Grade sample rate, bitrate, and channels independently.
3. Grade bit depth only if the format is lossless PCM
   (.wav, .aiff, .aif, .flac). For lossy formats the bit depth
   metric is treated as not-applicable and excluded from the decision.
4. Combine:
   · PASS if every applicable metric is PASS.
   · FAIL if any applicable metric is FAIL.
   · MARGINAL otherwise.

4.3 Why bit depth is skipped for lossy formats

Lossy codecs (MP3, AAC, M4A, OGG, Opus) do not store PCM samples, so there is
no bit depth to measure. mutagen returns None. If bit depth were graded
for these formats, every lossy file would be forced to FAIL regardless of its
actual audible quality, which is incorrect. The engine therefore treats bit
depth as not-applicable for lossy files, and bitrate carries the weight.

4.4 Example outcomes

File SR BD BR Channels Grade
kick.wav 48000 24 2304 2 PASS
vox.aiff 44100 16 1411 1 MARGINAL
loop.mp3 44100 n/a 320 2 PASS
old.mp3 22050 n/a 96 2 FAIL

---

5. Naming Convention

5.1 Template

```
{index}_{name}_{sr}kHz_{bd}bit_{br}kbps_{grade}.{ext}
```

5.2 Tokens

Token Expands to Example
{index} Zero-padded sequence (3 digits) 001
{name} Original filename stem, sanitized kick_drum
{sr} Sample rate in kHz 48
{bd} Bit depth, or unknown 24
{br} Bitrate in kbps, or lossless 1411
{grade} PASS / MARGINAL / FAIL PASS
{ext} Lowercase extension wav

5.3 Resulting examples

```
001_kick_drum_48kHz_24bit_2304kbps_PASS.wav
002_vinyl_riser_44.1kHz_16bit_128kbps_MARGINAL.mp3
003_noise_bed_22.05kHz_unknownbit_96kbps_FAIL.wav
```

5.4 Sanitization rules

Any character not in [A-Za-z0-9_\-.] or space is replaced with _.
Leading/trailing dots and spaces are stripped (illegal on Windows).

5.5 Collision handling

If a target filename already exists, _1, _2, ... is appended to the stem
until a free name is found. No file is ever overwritten.

---

6. Output Layout

```
<output_dir>/
    01_PASS/        green folder icon
    02_MARGINAL/    yellow folder icon
    03_FAIL/        red folder icon
```

Files inside each folder are the renamed copies. Original files remain
untouched unless --move is used.

---

7. Command-Line Interface

```
python main.py [options]
```

Flag Short Description
--input PATH -i Folder containing raw samples
--output PATH -o Folder for organized output
--config PATH -c Config file (default config.yaml)
--dry-run  Analyze and report only; write nothing
--no-color  Skip Windows folder coloring
--move  Move instead of copy (destructive)

7.1 Common invocations

Standard non-destructive run:

```cmd
python main.py --input "C:\Samples\Raw" --output "C:\Samples\Organized"
```

Preview only:

```cmd
python main.py -i "C:\Samples\Raw" -o "C:\Samples\Organized" --dry-run
```

Destructive move:

```cmd
python main.py -i "C:\Samples\Raw" -o "C:\Samples\Organized" --move
```

7.2 Exit codes

Code Meaning
0 Success (including "no files found")
2 Input error (missing directory, invalid path)

---

8. Configuration Reference

All behavior is driven by config.yaml.

8.1 Keys

Key Type Description
input_dir string Default input when --input is omitted
output_dir string Default output when --output is omitted
thresholds map Pass/marginal values per metric
rename_template string Filename pattern with tokens
folders map Grade -> folder name
folder_icons map Grade -> imageres.dll resource index
supported_extensions list Extensions to scan
copy_instead_of_move bool Global default for copy vs move
skip_already_renamed bool Reserved for future use

8.2 Threshold block

```yaml
thresholds:
  sample_rate:
    pass: 48000
    marginal: 44100
  bit_depth:
    pass: 24
    marginal: 16
  bitrate:
    pass: 192
    marginal: 128
  channels:
    allowed: [1, 2]
```

8.3 Tuning tips

· Stricter mastering check: raise bit_depth.pass to 32 and
  sample_rate.pass to 96000.
· Podcast workflow: lower bitrate.marginal to 96 if you accept
  mono voice at low bitrate.
· Lossless-only library: set supported_extensions to
  [".wav", ".flac", ".aiff"].

---

9. Windows Folder Coloring

9.1 Mechanism

Windows lets a folder carry a custom icon through a desktop.ini file placed
inside it. The icon is referenced by a DLL and a resource index. The tool
writes desktop.ini and sets the correct attributes:

· desktop.ini -> hidden + system
· the folder itself -> read-only + system

Both attribute changes are required for Explorer to honor the icon.

9.2 Icon resource IDs

The icons come from %SystemRoot%\System32\imageres.dll. Negative indices
select the built-in folder color variants:

Index Color
-2 blue
-3 yellow
-4 green
-5 red

These IDs can vary by Windows build. If a folder does not change color, try
other negative indices in folder_icons.

9.3 Non-Windows systems

colorize_folder returns False on non-Windows platforms and the step is
silently skipped. Use --no-color to skip explicitly and avoid the message.

---

10. Error Handling

10.1 Unreadable files

read_metadata never raises. Any failure is captured in AudioInfo.error,
and the sample is graded FAIL with the error text as its reason. This keeps
a single corrupt file from aborting a batch.

10.2 Missing input

If the input directory is missing or not a directory, the tool prints an
error and exits with code 2.

10.3 Partial failures

If a copy or move fails mid-batch, the exception propagates and the run
stops. Already-processed files remain in place. Re-running the tool is safe
because of collision handling and the copy-by-default behavior.

---

11. Extending the Tool

11.1 Adding a new metric

1. Add the field to AudioInfo in metadata.py and populate it in
   read_metadata.
2. Add grading logic in quality.py::grade_sample.
3. Optionally add it to config.yaml thresholds and the rename template in
   renamer.py::build_name.

11.2 Loudness (EBU R128 / LUFS)

True EBU R128 loudness measurement requires full PCM decoding and
gating, which mutagen does not provide. To add it, integrate a library
such as pyloudnorm with an audio decoder (soundfile or audioread),
compute integrated LUFS, then add a threshold block. This is a deliberate
future extension, not part of v1.0.

11.3 Custom folder colors

Replace the icon path in tagger.py::_IMAGERES with a custom .ico
file and set folder_icons to index 0:

```yaml
folder_icons:
  PASS: "0"
```

and point IconResource at your .ico path.

---

12. File-by-File Reference

File Responsibility
main.py CLI parsing, config load, orchestration, report output
scanner.py Recursive discovery, alphabetical sort, extension filter
metadata.py AudioInfo model, mutagen extraction, bitrate estimation
quality.py Grade enum, threshold comparison, overall verdict
renamer.py Template rendering, sanitization, collision resolution
organizer.py Folder creation, copy/move execution
tagger.py desktop.ini writing, Windows attribute flags
config.yaml All tunable parameters
requirements.txt Python dependencies

---

13. Glossary

Term Definition
Sample rate Samples per second (Hz). 48000 Hz is broadcast standard.
Bit depth Bits per PCM sample. Higher = more dynamic range.
Bitrate Data per second (kbps). Relevant mainly for lossy codecs.
PCM Pulse-code modulation; uncompressed digital audio.
Lossless Format preserving exact samples (WAV, FLAC, AIFF).
Lossy Format discarding data (MP3, AAC, OGG, Opus).
LUFS Loudness Units Full Scale; EBU R128 loudness measure.
IASA TC-03 IASA technical guideline for audio preservation.
EBU R128 European broadcast loudness recommendation.
desktop.ini Windows per-folder settings file (icons, view state).

---

14. Changelog

Version Change
1.0 Initial release. Bit depth graded only for lossless formats.

</content>
</write_to_file>

<attempt_completion>
<options>["supabase"]</options>
</attempt_completion>
