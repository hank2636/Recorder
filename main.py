import cv2
import numpy as np
import mss
import pyautogui
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import sys
import os

def resource_path(relative_path):
    """取得打包後資源路徑"""
    try:
        # PyInstaller 解包後臨時資料夾
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

record_path = resource_path("record.png")
recording_path = resource_path("recording.png")

class ScreenRecorderApp:
    def __init__(self):
        self.recording = False
        self.out = None
        self.stop_flag = False
        self.fps = 20
        self.output = ""
        self.start_time = None

        self.root = tk.Tk()
        self.root.title("Screen Recorder")
        self.root.geometry("350x80+100+500")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)  # 半透明效果
        self.root.configure(bg='#222222')     # 深灰黑背景

        self.canvas = tk.Canvas(self.root, width=350, height=80, bg='#222222', highlightthickness=0)
        self.canvas.pack()

        img_record_pil = Image.open(record_path).resize((30, 30), Image.Resampling.LANCZOS)
        img_recording_pil = Image.open(recording_path).resize((30, 30), Image.Resampling.LANCZOS)

        self.img_record = ImageTk.PhotoImage(img_record_pil)
        self.img_recording = ImageTk.PhotoImage(img_recording_pil)

        self.root.iconphoto(False, self.img_record)  # 工作列圖示設定

        self.button_img_id = self.canvas.create_image(45, 35, image=self.img_record)
        self.canvas.tag_bind(self.button_img_id, "<Button-1>", self.toggle_recording)

        self.time_text = self.canvas.create_text(180, 35, text="00:00:00", fill="white", font=("Consolas", 18))

        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

        self._offset_x = 0
        self._offset_y = 0

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.update_time()
        self.root.mainloop()

    def start_move(self, event):
        self._offset_x = event.x_root - self.root.winfo_x()
        self._offset_y = event.y_root - self.root.winfo_y()

    def do_move(self, event):
        x = event.x_root - self._offset_x
        y = event.y_root - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def toggle_recording(self, event=None):
        if not self.recording:
            threading.Thread(target=self.screen_record, daemon=True).start()
            self.canvas.itemconfig(self.button_img_id, image=self.img_recording)
        else:
            self.stop_flag = True
            self.canvas.itemconfig(self.button_img_id, image=self.img_record)

    def screen_record(self):
        self.recording = True
        self.start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.output = f"SR_{timestamp}.mp4"
        screen_size = pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.out = cv2.VideoWriter(self.output, fourcc, self.fps, screen_size)

        with mss.mss() as sct:
            monitor = {"top": 0, "left": 0, "width": screen_size[0], "height": screen_size[1]}

            while not self.stop_flag:
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                mouse_x, mouse_y = pyautogui.position()
                cv2.circle(frame, (mouse_x, mouse_y), radius=5, color=(255, 255, 255), thickness=-1)

                self.out.write(frame)

        self.out.release()
        self.recording = False
        self.stop_flag = False
        self.canvas.itemconfig(self.button_img_id, image=self.img_record)
        messagebox.showinfo("完成", f"影片儲存為 {self.output}")

    def update_time(self):
        if self.recording and self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            self.canvas.itemconfig(self.time_text, text=time_str)
        else:
            self.canvas.itemconfig(self.time_text, text="00:00:00")
        self.root.after(1000, self.update_time)

    def on_close(self):
        if self.recording:
            messagebox.showwarning("警告", "請先停止錄影！")
        else:
            self.root.destroy()

if __name__ == "__main__":
    ScreenRecorderApp()


# pyinstaller --noconsole --onefile --hidden-import=cv2 --add-data "record.png;." --add-data "recording.png;." --add-data "record.ico;." main.py

