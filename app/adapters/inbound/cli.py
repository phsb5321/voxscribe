"""CLI adapter for backward compatibility with the original transcription tool.

Usage:
    python -m app.adapters.inbound.cli DIRECTORY [--language LANG] [--engine ENGINE]
"""

import argparse
import os
import sys

from app.application.dto import SubmitTranscriptionRequest
from app.bootstrap import bootstrap
from app.domain.value_objects.audio_format import AudioFormat


def _find_audio_files(directory: str) -> list[str]:
    """Find all supported audio files in a directory."""
    extensions = {fmt.value for fmt in AudioFormat}
    files = []
    for entry in sorted(os.listdir(directory)):
        ext = os.path.splitext(entry)[1].lower().lstrip(".")
        if ext in extensions:
            files.append(os.path.join(directory, entry))
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe audio files in a directory"
    )
    parser.add_argument("directory", help="Directory containing audio files")
    parser.add_argument(
        "--language", default="pt-BR", help="Language code (default: pt-BR)"
    )
    parser.add_argument(
        "--engine",
        default=None,
        help="Transcription engine (default: from TRANSCRIPTION_ENGINE env var)",
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a directory", file=sys.stderr)
        return 1

    # Set engine override if provided
    if args.engine:
        os.environ["TRANSCRIPTION_ENGINE"] = args.engine

    container = bootstrap()

    audio_files = _find_audio_files(args.directory)
    if not audio_files:
        print(f"No audio files found in {args.directory}", file=sys.stderr)
        return 1

    print(f"Found {len(audio_files)} audio file(s) in {args.directory}")
    print(f"Engine: {container.engine.engine_name}")
    print(f"Language: {args.language}")
    print()

    for filepath in audio_files:
        filename = os.path.basename(filepath)
        print(f"Processing: {filename}")

        with open(filepath, "rb") as f:
            file_data = f.read()

        try:
            request = SubmitTranscriptionRequest(
                filename=filename,
                file_data=file_data,
                language=args.language,
            )
            response = container.submit_transcription.execute(request)

            # Process synchronously (no queue) for CLI use
            container.process_transcription.execute(response.job_id)

            # Get result
            result = container.get_job_status.get_result(response.job_id)
            if result and result.full_text:
                print(f"\n--- {filename} ---")
                print(result.full_text)
                print()
            else:
                print(f"  Warning: No transcription result for {filename}")

        except Exception as e:
            print(f"  Error processing {filename}: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
