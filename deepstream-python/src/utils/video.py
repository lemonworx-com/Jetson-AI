import tkinter as tk
from tkinter import filedialog

def select_video_file():
  root = tk.Tk()
  root.withdraw()  # Hide the root window
  file_path = filedialog.askopenfilename(
    title="Select Video File",
    filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
  )
  return file_path