import tkinter as tk
from PIL import ImageGrab
import easyocr
import datetime
import cv2
import numpy as np

# Khởi tạo EasyOCR Reader chỉ một lần
reader = easyocr.Reader(['en'], gpu=False)

class TransparentOverlay:
    def __init__(self):
        self.start_x = None
        self.start_y = None
        self.rect = None

        self.root = tk.Tk()
        self.root.attributes("-alpha", 0.1)         # Độ trong suốt
        self.root.attributes("-topmost", True)      # Luôn trên cùng
        self.root.attributes("-fullscreen", True)   # Toàn màn hình
        self.root.configure(bg='black')             # Màu nền mờ

        self.canvas = tk.Canvas(self.root, cursor="cross", bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )

    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        top = int(min(self.start_y, end_y))
        left = int(min(self.start_x, end_x))
        width = int(abs(end_x - self.start_x))
        height = int(abs(end_y - self.start_y))

        region = {
            'top': top,
            'left': left,
            'width': width,
            'height': height
        }

        # Chụp ảnh vùng đã chọn
        img = ImageGrab.grab(bbox=(left, top, left + width, top + height))
        # image = cv2.imread(img)
        img_np = np.array(img)
        # Nhận diện chữ bằng EasyOCR
        results = reader.readtext(img_np)

        # Gộp nội dung nhận dạng
        ocr_text = ' '.join([text for _, text, _ in results])

        # Ghi ra file
        self.save_result(region, ocr_text)

        print("Region:", region)
        print("Text:", ocr_text)
        print("=" * 50)

        # Cho phép chọn tiếp
        self.canvas.delete(self.rect)
        self.rect = None

    def save_result(self, region, text):
        with open("regions.txt", "a", encoding='utf-8') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} | region = {region} | text = \"{text}\"\n")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    overlay = TransparentOverlay()
    overlay.run()
