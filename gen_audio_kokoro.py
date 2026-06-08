"""Synthesise every scene in a script.json using Kokoro (local, MIT-licensed).

SNP demo: two scripts in one repo (club + mobile). Pass `--script` to choose:

    python3.11 gen_audio_kokoro.py --script script-club.json
    python3.11 gen_audio_kokoro.py --script script-mobile.json

Each scene's MP3 is written to audio/<subdir>/scene-NN.mp3 where <subdir> is
derived from the script filename (`script-club` → `audio/club/`).

Voices: af_bella, af_nicole, af_sarah, af_sky, am_adam, am_michael, am_eric,
bf_emma, bf_isabella, bm_george, bm_lewis.

Defaults to am_adam (clean professional narrator) for SNP unless the script
overrides via the `voiceCode` field.
"""

import argparse
import json
import sys
from pathlib import Path

import soundfile as sf
from kokoro import KPipeline

HERE = Path(__file__).parent

KOKORO_VOICES = {
    'af_bella', 'af_nicole', 'af_sarah', 'af_sky',
    'am_adam', 'am_michael', 'am_eric',
    'bf_emma', 'bf_isabella', 'bm_george', 'bm_lewis',
}
# Legacy NovelAI codes (in case scripts inherit them from the Oomfy template)
LEGACY_FALLBACK = {
    'am_cyllene': 'am_adam',
    'am_leucosia': 'am_eric',
    'am_hespe': 'am_michael',
    'am_crina': 'am_adam',
}


def resolve_voice(code: str) -> str:
    if code in KOKORO_VOICES:
        return code
    if code in LEGACY_FALLBACK:
        return LEGACY_FALLBACK[code]
    return 'am_adam'


def synthesise_script(script_path: Path):
    script = json.loads(script_path.read_text())
    voice_code = resolve_voice(script.get('voiceCode', 'am_adam'))
    scenes = script.get('scenes', [])

    # audio/<club|mobile>/ — derived from script filename
    stem = script_path.stem  # e.g. "script-club" → "club"
    subdir = stem.replace('script-', '').replace('script_', '')
    outdir = HERE / 'audio' / subdir
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Script:  {script_path.name}  ({len(scenes)} scenes)")
    print(f"Voice:   {voice_code}")
    print(f"Output:  audio/{subdir}/")
    print()

    pipeline = KPipeline(lang_code='a')  # 'a' = American English phonemizer

    import numpy as np
    for scene in scenes:
        order = scene['order']
        text = scene['narration'].strip()
        out_path = outdir / f"scene-{order:02d}.mp3"
        print(f"  [{order:02d}] {text[:60]}...")

        audio_chunks = []
        for _, _, audio in pipeline(text, voice=voice_code, speed=1.0):
            audio_chunks.append(audio)

        if not audio_chunks:
            print(f"      WARNING: no audio generated")
            continue

        merged = np.concatenate(audio_chunks)
        sf.write(str(out_path), merged, 24000, format='MP3')

    print()
    print(f"✓ Wrote {len(scenes)} MP3s to audio/{subdir}/")


def main():
    parser = argparse.ArgumentParser(description="SNP demo audio synth (Kokoro)")
    parser.add_argument('--script', required=True, help='Path to script-{club,mobile}.json')
    args = parser.parse_args()
    script_path = Path(args.script)
    if not script_path.is_absolute():
        script_path = HERE / script_path
    if not script_path.exists():
        print(f"ERROR: {script_path} not found")
        sys.exit(1)
    synthesise_script(script_path)


if __name__ == '__main__':
    main()
