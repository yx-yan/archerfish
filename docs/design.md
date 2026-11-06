# Design

## Pipeline

Hold hotkey → record → local ASR → DeepSeek rewrite → paste at cursor. The text
is never sent automatically: a misheard word should not become an instruction.

## Latency budget

Everything after the key is released is waiting time, so this number decides
whether the tool beats typing. Initial target: median under 2 seconds for 30
seconds of speech. Over the 20 benchmark clips (3.6 to 30 seconds), speech
recognition plus rewrite took a median of 1.25 s and at most 1.57 s, without pasting.

## Speech model

Qwen3-ASR 0.6B, chosen from 20 read-aloud clips (10 Chinese, 10 English, one
speaker) on an M5 with 16 GB. Latency excludes model loading.

| Model | Chinese CER | English WER | Median latency | Latency, 30 s clip | Peak GPU memory |
|---|---|---|---|---|---|
| Qwen3-ASR 0.6B | 1.6% | 5.0% | 0.33-0.35 s | 0.93 s | 2.92 GB |
| Whisper large-v3-turbo | 3.2% | 4.4% | 0.73-0.78 s | 0.86 s | 2.04 GB |

Part of these rates comes from digits, such as "500" for "five hundred", which
are not real mistakes. Qwen also punctuates Chinese, while Whisper mostly does
not. Whisper's English was slightly better, but the gap is small for 10 clips.

The app runs an 8-bit build of that model. On the same 20 clips it gave the same
text as the 16-bit original, cut peak GPU memory while loading from 2.92 GB to 0.98 GB
and median latency by about a quarter. A 4-bit build saved only 0.05 GB more, and
English WER rose to 8.7% with errors that changed the meaning.

| Build | Chinese CER | English WER | Median latency | Footprint after 20 clips |
|---|---|---|---|---|
| 16-bit | 1.6% | 5.0% | 0.32-0.35 s | 1.72 GB |
| 8-bit | 1.6% | 5.0% | 0.24-0.27 s | 1.34 GB |
| 4-bit | 1.8% | 8.7% | 0.18-0.22 s | 1.29 GB |

If latency becomes a problem, Qwen3-ASR's streaming mode can decode while the
user is still talking. Its `context` argument is the likely way to bias
recognition toward a personal glossary.

## Audio capture

Stopping a PortAudio input stream deadlocked inside CoreAudio during testing, so
the recorder keeps one stream open and exits without closing it. macOS may also
return all-zero audio when the host app lacks microphone access, so the recorder
checks for that before asking anyone to read.

The cost of the open stream is that macOS shows its microphone indicator for as
long as the app runs, and the stream stays on the device it started with.

## Threads

The main thread runs the menu bar and the key listener, and only flips state. One
worker thread loads the model and handles every job, because MLX work stays on the
thread that loaded it. The worker never touches AppKit UI: the menu bar polls its
state ten times a second. A press while a job is running is ignored.

## Overlay

A pill at the bottom of the screen shows the waveform while recording, then folds
into a blinking cursor while working. It is a nonactivating panel that ignores the
mouse, because taking focus would send the paste to the wrong place. It waits
0.15 s before appearing so Option shortcuts do not flash it, and its 30 fps timer
only runs while it is on screen.

## Setup window

The app opens it at launch while anything is missing. macOS sends no event when a
permission changes, so it polls once a second while it is open. Documents has no
row: without that access the app cannot start from a checkout in Documents. A
missing DeepSeek key is not fatal, because the rewrite falls back to the transcript.

## Paste

The text goes through the clipboard and a simulated Cmd+V, then the old clipboard
comes back, unless the user copied something new in the meantime. Without
Accessibility access the text simply stays on the clipboard.

## App bundle

macOS grants Microphone and Accessibility to the binary that makes the call, so a
script that execs or spawns Python would ask as Python. `macos/launcher.c` embeds
Python and runs `quoth.app` in its own process instead, and it uses the checkout's
`.venv`. The bundle is ad-hoc signed, so permissions follow its hash: Python changes
keep them, but changes to the launcher, `Info.plist` or icon may not.

## Rewrite

`deepseek-flash` with thinking disabled took a median of 0.92 s (max 1.13 s) over
24 calls on short and medium transcripts. If the API fails or times out after
5 seconds, the raw transcript is used so the user never loses what they said.
