"""Read-only environment metadata for the offline contour/descriptor reports."""
import platform
import subprocess
import numpy as np

def environment():
    return dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform(),
                arithmetic="IEEE-754 binary64; numpy.linalg.solve/eig",
                git_head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip())
