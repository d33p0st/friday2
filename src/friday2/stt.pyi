

class STTEngine:
    """STTEngine [`Speech Recognition Module`]

    Friday uses a dedicated trained model to recognize
    commands and speech.
    """
    def __init__(self, debug: bool = True) -> None:
        """Create an instance of STTEngine."""


    def transcribe(self) -> str:
        """Goes into listening mode and records
        as soon as speech is detected. uses Friday2 STT
        FTWB model for speech detection and transcription"""