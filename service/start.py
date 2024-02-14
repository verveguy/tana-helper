
from pathlib import Path
import uvicorn
import os
# these imports are to satisfy PyInstaller's dependency finder
# since they appear to be "hidden" from it for unknown reasons
import service.main
import onnxruntime, tokenizers, tqdm
    
if __name__ == "__main__":
    cwd = Path(__file__).parent.resolve()
    uvicorn.run("service.main:app", port=8000, log_level="info")
