
from friday2.commands import CommandExecutor, CommandParser
from friday2.stt import STTEngine
from friday2.tts import VoiceEngine

TTS = VoiceEngine()
STT = STTEngine()
PARSER = CommandParser()
EXECUTOR = CommandExecutor(PARSER)

TTS.speak('booting up!')
TTS.speak('All systems online!')
TTS.speak("I'll be here if you need me sir.")

while True:
    text = STT.transcribe()
    if 'friday' in text.lower():
        break

TTS.speak('Did you call me sir!')

text = STT.transcribe()

status = EXECUTOR.execute(text)
if status['success']:
    TTS.speak("I have opened " + status['command_data']['target'])
else:
    TTS.speak("I did not quite understand what you wanted")