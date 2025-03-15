

from pygdl import download

import subprocess
import colorama
import pathlib
import typing
import sys


# @helper method for easy command creation
def stringify(component: typing.List[typing.Any]) -> typing.List[str]:
    for i in range(len(component)):
        if not isinstance(component[i], str):
            component[i] = str(component[i])
    return component


# @global configurations
MODEL = 'friday2-STT-ftws.tar.gz'
MODEL_BASENAME = 'friday2-STT-ftws'


# @system specific configurations.
if sys.platform.startswith('darwin'):
    CONFIGURATION = pathlib.Path('~/Library/Application Support/Friday').expanduser().resolve()
    VOICE_CODE = 132 # samantha, earlier 14 (daniel)
    MODEL_PATH = CONFIGURATION.joinpath(MODEL_BASENAME)
    MODEL_EXTRACTION_COMMAND = stringify(['tar', '-xzf', CONFIGURATION.joinpath(MODEL), '-C', CONFIGURATION])


# @create the configuration directory if it does not exist
CONFIGURATION.mkdir(parents=True, exist_ok=True)


# @check if the model path exists.
if not MODEL_PATH.exists():

    print(colorama.Fore.RED + '@notfound' + colorama.Fore.RESET, MODEL_BASENAME)

    # @if the model path does not exist, check for any caches
    if not CONFIGURATION.joinpath(MODEL).exists():

        print(colorama.Fore.BLUE + '@need' + colorama.Fore.RESET, 'to download', MODEL)

        # @if not caches exist, download it from the github release
        downloaded, error = download(
            filename=MODEL,
            github_username='d33p0st',
            github_repository='friday2',
            output_directory=str(CONFIGURATION)
        )

        if not downloaded:
            raise RuntimeError(error)
    else:
        print(colorama.Fore.MAGENTA + '@found' + colorama.Fore.RESET, f'cached {MODEL}')
    
    MODEL_PATH.mkdir(parents=True, exist_ok=True)
    # @if any caches exist, or it has been downloaded,
    # - extract the model into MODEL_BASENAME
    subprocess.check_call(MODEL_EXTRACTION_COMMAND)
    print(colorama.Fore.GREEN + '@extracted' + colorama.Fore.RESET, "friday's customized STT model at", MODEL_PATH)