from pathlib import Path
import openai

openai.base_url = "http://36.103.167.150:9997/v1/"
openai.api_key="sk-1234567890"
speech_file_path = Path(__file__).parent / "speech.mp3"
response = openai.audio.speech.create(
  model="FishSpeech-1.4",
  voice="",
  input="The quick brown fox jumped over the lazy dog."
)
response.stream_to_file(speech_file_path)
