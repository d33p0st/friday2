
# @this module uses a custom model to recognize speech
# - particularly my voice and commands

from friday2 import MODEL_PATH, MODEL_BASENAME, CONFIGURATION
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from pydub import silence, AudioSegment

import colorama
import pyaudio
import numpy
import torch
import wave
import os


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 1000
SILENCE_DURATION = 3

class STTEngine:
    
    def __init__(self, debug: bool = True) -> None:

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        if debug is True:
            print(colorama.Fore.RED + '@using' + colorama.Fore.RESET, self.device)
            print(colorama.Fore.MAGENTA + '@loading' + colorama.Fore.RESET, MODEL_BASENAME, 'model...')
        
        self.processor = WhisperProcessor.from_pretrained(MODEL_PATH)
        self.model = WhisperForConditionalGeneration.from_pretrained(MODEL_PATH).to(self.device)
        self.debug = debug

    # @method to check if currently silent
    def _is_silent(self, audio_data, threshold: int = SILENCE_THRESHOLD) -> bool:
        return numpy.max(numpy.abs(audio_data)) < threshold


    # @method to record audio with auto stopping at silence
    def _record(self):

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        frames = []
        silent_chunks = 0
        max_silent_chunks = int(SILENCE_DURATION * RATE / CHUNK)

        # @waiting for speech at this time,
        if self.debug:
            print("Friday is listening.")

        while True:
            data = stream.read(CHUNK)
            audio_data = numpy.frombuffer(data, dtype=numpy.int16)
            if not self._is_silent(audio_data):
                frames.append(data)
                # @speech is detected here
                if self.debug:
                    print(colorama.Fore.BLUE + "@speech-detected" + colorama.Fore.RESET, colorama.Fore.RED + '@recording' + colorama.Fore.RESET, end='\r')
                break
        
        # @record until silence is detected

        while True:
            data = stream.read(CHUNK)
            frames.append(data)
            audio_data = numpy.frombuffer(data, dtype=numpy.int16)

            if self._is_silent(audio_data):
                silent_chunks += 1
            else:
                silent_chunks = 0
            
            # @stop if enough silent chunks are present
            if silent_chunks >= max_silent_chunks:
                # @recording stopped here
                if self.debug:
                    print(colorama.Fore.BLUE + "@speech-detected" + colorama.Fore.RESET, colorama.Fore.RED + '@recording' + colorama.Fore.RESET, colorama.Fore.BLUE + '@silence-detected' + colorama.Fore.RESET)
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()

        # @save the audio file
        temp_file = CONFIGURATION.joinpath("tempp-friday2-stt-input.wav")
        wf = wave.open(str(temp_file), 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        if self.debug:
            print("Friday is processing inputs.")

        return temp_file


    # @method to trim trailing silence
    def _trim_silence(self, audio_file):
        
        audio = AudioSegment.from_wav(audio_file)

        non_silent = silence.detect_nonsilent(audio, min_silence_len=500, silence_thresh=40)
        
        if not non_silent:
            return audio_file
        
        # @get start and end times
        start_time = non_silent[0][0]
        end_time = non_silent[-1][1]

        # @trim the audio
        trimmed_audio = audio[start_time:end_time]

        # @save the trimmed audio
        trimmed_file = CONFIGURATION.joinpath('tempp-friday2-stt-input-trimmed.wav')
        trimmed_audio.export(trimmed_file, format='wav')

        return trimmed_file


    # @method to transcribe audio
    def _transcribe(self, audio_file):

        audio = AudioSegment.from_wav(audio_file)
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)

        # @convert to numpy array
        audio_array = numpy.array(audio.get_array_of_samples()).astype(numpy.float32) / 32768.0

        # @process with whisper
        input_features = self.processor.feature_extractor(
            audio_array,
            sampling_rate=16000,
            return_tensors='pt'
        ).input_features.to(self.device)

        # @create attention mask (fixing the attention mask issue)
        attention_mask = torch.ones_like(input_features)

        # @generate tokens with forced English language (fixing auto-detection warning)
        with torch.no_grad():
            # @set forced_decoder_ids to ensure English transcription
            forced_decoder_ids = self.processor.get_decoder_prompt_ids(
                language='en',
                task='transcribe'
            )

            # @generate with attention mask and forced decoder ids
            predicted_ids = self.model.generate(
                input_features,
                attention_mask=attention_mask,
                forced_decoder_ids=forced_decoder_ids
            )
        
        if self.debug:
            print(colorama.Fore.MAGENTA + '@transcribing' + colorama.Fore.RESET)
        # @decode the tokens
        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

        if self.debug:
            print(colorama.Fore.GREEN + '@caught' + colorama.Fore.RESET, transcription)

        return transcription

    def transcribe(self) -> any:
        try:
            audio_file = self._record()
            
            trimmed_file = self._trim_silence(audio_file)

            transcription = self._transcribe(trimmed_file)

            try:
                os.remove(audio_file)
            except FileNotFoundError:
                pass

            try:
                os.remove(trimmed_file)
            except FileNotFoundError:
                pass

            return transcription
        except KeyboardInterrupt:
            return ''