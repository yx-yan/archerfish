# voxprompt

A macOS tool for talking to AI assistants: hold a key, speak Chinese or English,
and a cleaned-up prompt lands at your cursor. Speech recognition runs locally;
only the transcript is sent to DeepSeek for rewriting. Nothing is sent
automatically, so you can check the text before pressing Enter.

Status: early, in daily testing. See [docs/design.md](docs/design.md).

## Setup

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev,bench]"
cp .env.example .env   # then add your DeepSeek key
```

## Run the app

```bash
macos/build.sh
open /Applications/VoxPrompt.app
```

This builds a small native launcher (needs the Xcode Command Line Tools) and installs
`VoxPrompt.app`, which you can then open from Spotlight. To start it at login, add it
under System Settings > General > Login Items. Allow Documents, Microphone,
Accessibility and Input Monitoring for VoxPrompt, then reopen it.

When the menu bar icon shows 🎙️, click into any text box, hold the right Option key,
speak, and let go. Press Enter yourself to send. Errors go to
`~/Library/Logs/VoxPrompt.log`.

The app runs Python from this checkout, so code changes only need a restart. Moving the
checkout or changing anything in `macos/` may mean granting the permissions again.

The microphone stays open while the app runs, so macOS shows its recording
indicator the whole time. Audio is only kept while the key is held. Restart the app
after changing the input device.

To run without the app, use `.venv/bin/voxprompt-app` from Terminal.app and grant the
same permissions to Terminal.

## Clean up a recording

```bash
.venv/bin/voxprompt recording.wav
```

The prompt goes to stdout and timings go to stderr. Input must be 16 kHz mono WAV.

## Benchmarks

```bash
.venv/bin/python evals/record_samples.py        # read 20 scripts aloud
.venv/bin/python evals/bench_asr.py --backend qwen
.venv/bin/python evals/bench_asr.py --backend whisper
.venv/bin/python evals/bench_rewrite.py         # calls the DeepSeek API
```

Run the recorder from Terminal.app: macOS may give apps without microphone access
silent audio. Recordings and results stay in `evals/samples/` and `evals/results/`,
which git ignores.
