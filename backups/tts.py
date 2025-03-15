
import pyttsx3
import colorama

from friday2 import VOICE_CODE

class VoiceEngine:
    def __init__(self, rate: int = 160) -> None:
        self.engine = pyttsx3.init()

        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', 1.0)

        self.voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', self.voices[VOICE_CODE].id)

        self.debug_name = colorama.Fore.GREEN + 'friday:' + colorama.Fore.RESET

    def speak(self, message: str, debug: bool = True) -> None:
        if debug:
            print(self.debug_name, message)
        self.engine.say(message)
        self.engine.runAndWait()