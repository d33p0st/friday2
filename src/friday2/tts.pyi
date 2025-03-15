"""tts [`Module`].

This module contains friday's voice engine (mouth).
"""

class VoiceEngine:
    """VoiceEngine [`Mouth`].
    
    This class helps friday to speak any string given to
    it.
    """
    def __init__(self, rate: int = 150) -> None:
        """Create an instance of VoiceEngine.
        
        ``Rate`` is the words per minute.
        """

    def speak(self, message: str, debug: bool = True) -> None:
        """Speak any given text."""