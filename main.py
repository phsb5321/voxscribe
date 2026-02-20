import os
import logging
from concurrent.futures import ThreadPoolExecutor
import speech_recognition as sr
from pydub import AudioSegment
import socket
import time
import dns.resolver  # Add this to requirements.txt

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
SUPPORTED_AUDIO_FORMATS = (".mp3", ".wav", ".flac", ".ogg")
OUTPUT_FORMAT = "wav"
LANGUAGE = "pt-BR"
MAX_RETRIES = 3
RETRY_DELAY = 2


def setup_dns():
    """Configure DNS resolution"""
    dns_servers = os.environ.get("DNS_SERVERS", "8.8.8.8 8.8.4.4").split()
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [socket.gethostbyname(ns) for ns in dns_servers]
    return resolver


class AudioTranscriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.dns_resolver = setup_dns()

    def convert_audio(self, input_file):
        """Convert audio file to WAV format if necessary."""
        file_name, file_extension = os.path.splitext(input_file)
        if file_extension.lower() == f".{OUTPUT_FORMAT}":
            return input_file

        output_file = f"{file_name}.{OUTPUT_FORMAT}"
        try:
            audio = AudioSegment.from_file(input_file, format=file_extension[1:])
            audio.export(output_file, format=OUTPUT_FORMAT)
            logger.info(f"Converted {input_file} to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error converting {input_file}: {e}")
            return None

    def resolve_google_speech_api(self):
        """Resolve Google Speech API domain"""
        try:
            answers = self.dns_resolver.resolve("speech.googleapis.com", "A")
            return str(answers[0])
        except Exception as e:
            logger.error(f"DNS resolution error: {e}")
            return None

    def transcribe_audio(self, file_path):
        """Transcribe audio file to text with retries."""
        for attempt in range(MAX_RETRIES):
            try:
                # Resolve API endpoint before making the request
                api_ip = self.resolve_google_speech_api()
                if not api_ip:
                    raise Exception("Could not resolve Google Speech API")

                with sr.AudioFile(file_path) as source:
                    audio_data = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(
                        audio_data, language=LANGUAGE
                    )
                    return text
            except sr.RequestError as e:
                logger.warning(
                    f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return f"Network error after {MAX_RETRIES} attempts: {str(e)}"
            except sr.UnknownValueError:
                logger.warning(f"Audio could not be understood: {file_path}")
                return "Audio could not be understood"
            except Exception as e:
                logger.error(f"Error transcribing {file_path}: {e}")
                return f"Error transcribing audio: {str(e)}"

    def process_file(self, audio_file):
        """Process a single audio file."""
        logger.info(f"Processing {audio_file}")
        wav_file = self.convert_audio(audio_file)
        if wav_file:
            transcription = self.transcribe_audio(wav_file)
            logger.info(f"Transcription for {audio_file}:\n{transcription}\n")
            return audio_file, transcription
        return audio_file, "Conversion failed"


def get_audio_files(directory):
    """Get all supported audio files from the specified directory."""
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith(SUPPORTED_AUDIO_FORMATS)
    ]


def main():
    transcriber = AudioTranscriber()
    audio_directory = "./DATA"
    audio_files = get_audio_files(audio_directory)

    if not audio_files:
        logger.warning(f"No supported audio files found in {audio_directory}")
        return

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(transcriber.process_file, audio_files))

    for audio_file, transcription in results:
        print(f"Transcription for {audio_file}:")
        print(transcription)
        print("\n")


if __name__ == "__main__":
    main()
