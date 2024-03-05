import sys
import os

from pathlib import Path
import uvicorn

# these imports are to satisfy PyInstaller's dependency finder
# since they appear to be "hidden" from it for unknown reasons
import service.main
import onnxruntime, tokenizers, tqdm

# workaround for Windows --noconsole mode
# let's ensure stdout and stderr are not None
# see https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html?highlight=windowed
if sys.stdin is None:
  sys.stdin = open(os.devnull, "r")
if sys.stdout is None:
  sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
  sys.stderr = open(os.devnull, "w")

if __name__ == "__main__":
    cwd = Path(__file__).parent.resolve()
    uvicorn.run("service.main:app", port=8000, log_level="info", reload=True)
