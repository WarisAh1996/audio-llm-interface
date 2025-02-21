import subprocess

try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True)
    print("FFmpeg is installed and accessible")
except FileNotFoundError:
    print("FFmpeg is not installed or not in PATH. Please install FFmpeg from: https://ffmpeg.org/download.html")
    print("Make sure to add it to your system PATH after installation.")
