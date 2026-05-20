import tkinter as tk
import json
import os
import pyautogui
from PIL import ImageGrab, ImageTk
import threading
from pynput import keyboard
from control import LoadSequence, TestLogger, TestSequenceItem_t

# Cấu hình file
lable_name_db = "TN3"
sequence_path = "test_sequence/debug.xlsx"
LABEL_FILE = f'region/{lable_name_db}.json'
ASSETS_DIR = "assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

class LabelingTool:
    def __init__(self):
        self.labels_id = 0
        self.start_x = self.start_y = self.rect = None
        self.labels = []
        
    
        self.box_items = [] 
        
        # CÁC BIẾN TRẠNG THÁI
        self.alt_pressed = False
        self.is_boxes_visible = True 
        self.is_text_visible = False # Mặc định KHÔNG hiện chữ cho đỡ rối

        # KHỞI TẠO GIAO DIỆN
        self.root = tk.Tk()
        self.root.attributes("-topmost", True)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.configure(bg='black')

        self.canvas = tk.Canvas(self.root, cursor="cross", bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # BIND CHUỘT
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.root.bind("<Double-Button-1>", self.on_double_click)
        
        # BIND BÀN PHÍM
        self.root.bind("<Control-s>", self.on_ctrl_s)
        self.root.bind("<Control-S>", self.on_ctrl_s)
        self.root.bind("<F4>", lambda e: self.root.destroy())
        self.root.bind("<Alt_L>", self.toggle_visibility)
        
        # Phím tắt UI (H để ẩn khung, T để ẩn/hiện chữ)
        self.root.bind("h", self.toggle_boxes)
        self.root.bind("H", self.toggle_boxes)
        self.root.bind("t", self.toggle_text_global)
        self.root.bind("T", self.toggle_text_global)

        # Nghe phím C để chụp ảnh
        threading.Thread(target=self.start_key_listener, daemon=True).start()
        
        self.logger = TestLogger(loglevel='INFO', savelog='True', display='True')
        self.loadSequenceObj = LoadSequence(ExcellPath=sequence_path, sheetName="f6e_dl_bft_0822", logger=self.logger)
        self.__testSequence = self.loadSequenceObj.LoadTestSequence()
        self.load_labels()

    # ==========================================
    # CÁC TÍNH NĂNG HOTKEY (ALT, C, H, T)
    # ==========================================
    def toggle_visibility(self, event=None):
        self.root.iconify()
        self.alt_pressed = True
        print("🟡 Đã minimize Tool (Nhấn 'C' để chụp lại màn hình mới)")

    def start_key_listener(self):
        def on_press(key):
            try:
                if key.char == 'c' and self.alt_pressed and self.root.state() == "iconic":
                    print("📸 Đang chụp lại màn hình...")
                    self.capture_screen()
            except AttributeError:
                pass
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def capture_screen(self, event=None):
        img = ImageGrab.grab()
        screen_width, screen_height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        img = img.resize((screen_width, screen_height))
        
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all") 
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.3)
        self.alt_pressed = False
        
        self.box_items.clear()
        for region in self.labels: self.draw_label(region)
        print("🟢 Đã restore Tool")

    def toggle_boxes(self, event=None):
        self.is_boxes_visible = not self.is_boxes_visible
        rect_state = tk.NORMAL if self.is_boxes_visible else tk.HIDDEN
        for region, rect_id, text_id, bg_id in self.box_items:
            self.canvas.itemconfig(rect_id, state=rect_state)
            self.canvas.itemconfig(text_id, state=tk.HIDDEN) 
            self.canvas.itemconfig(bg_id, state=tk.HIDDEN)
        print("HIỆN KHUNG" if self.is_boxes_visible else "ẨN KHUNG")

    def toggle_text_global(self, event=None):
        if not self.is_boxes_visible: return
        self.is_text_visible = not self.is_text_visible
        text_state = tk.NORMAL if self.is_text_visible else tk.HIDDEN
        for region, rect_id, text_id, bg_id in self.box_items:
            self.canvas.itemconfig(text_id, state=text_state)
            self.canvas.itemconfig(bg_id, state=text_state)

    # ==========================================
    # HIỆU ỨNG GHOST MODE & SPOTLIGHT HOVER
    # ==========================================
    def draw_label(self, region):
        x1, y1 = region['left'], region['top']
        x2, y2 = x1 + region['width'], y1 + region['height']
        
        # Ghost Mode: Khung màu đỏ sẫm, rất mỏng
        rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline='#8B0000', width=1)
        
        # Khung nền đen và chữ vàng (Mặc định ẩn)
        bg_id = self.canvas.create_rectangle(x1, y1 - 18, x1 + len(region['label'])*8, y1, fill='black', outline='black', state=tk.HIDDEN)
        text_id = self.canvas.create_text(x1 + 2, y1 - 16, anchor='nw', text=region['label'], fill='#FFFF00', font=("Consolas", 10, "bold"), state=tk.HIDDEN)
        
        self.box_items.append((region, rect_id, text_id, bg_id))

        def on_enter(event, r_id=rect_id, t_id=text_id, b_id=bg_id):
            if self.is_boxes_visible: 
                self.canvas.tag_raise(r_id)
                self.canvas.tag_raise(b_id)
                self.canvas.tag_raise(t_id)
                self.canvas.itemconfig(r_id, width=3, outline='#00FF00') # Sáng xanh neon
                self.canvas.itemconfig(t_id, state=tk.NORMAL)           
                self.canvas.itemconfig(b_id, state=tk.NORMAL)           

        def on_leave(event, r_id=rect_id, t_id=text_id, b_id=bg_id):
            if self.is_boxes_visible:
                self.canvas.itemconfig(r_id, width=1, outline='#8B0000')    
                if not self.is_text_visible:
                    self.canvas.itemconfig(t_id, state=tk.HIDDEN)           
                    self.canvas.itemconfig(b_id, state=tk.HIDDEN)           

        self.canvas.tag_bind(rect_id, '<Enter>', on_enter)
        self.canvas.tag_bind(rect_id, '<Leave>', on_leave)
        self.canvas.tag_bind(text_id, '<Enter>', on_enter)
        self.canvas.tag_bind(bg_id, '<Enter>', on_enter)

    # ==========================================
    # CÁC THAO TÁC KHOANH VÙNG, CLICK, XÓA
    # ==========================================
    def on_press(self, event):
        if not self.is_boxes_visible: return 
        self.start_x, self.start_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)

    def on_drag(self, event):
        if not self.is_boxes_visible or not self.rect: return
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

    def on_release(self, event):
        if not self.is_boxes_visible or not self.rect: return
        
        end_x, end_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        top, left = int(min(self.start_y, end_y)), int(min(self.start_x, end_x))
        width, height = int(abs(end_x - self.start_x)), int(abs(end_y - self.start_y))
        
        if width < 15 or height < 15:
            self.canvas.delete(self.rect)
            return

        self.labels_id += 1
        label_info = self.ask_label_dialog(f'LB{self.labels_id:05d}')
        
        self.root.deiconify()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        
        if label_info:
            mode = label_info['mode']
            
            # ---> NẾU CHỌN VISUAL LOCATE: CẮT ẢNH VÀ LƯU <---
            if mode in ["image_locate", "image_scroll"]:
                img_name = label_info.get('imageFileName', f'img_{self.labels_id:03d}.png')
                if not img_name.endswith('.png'): img_name += '.png'
                
          
                cropped = ImageGrab.grab(bbox=(left, top, left + width, top + height))
                cropped.save(os.path.join(ASSETS_DIR, img_name))
                print(f"📸 Đã cắt và lưu ảnh: {img_name}")

            # NẾU CHỌN OCR: LƯU TỌA ĐỘ VÀO JSON
            elif mode != 'delay': 
                region = {'top': top, 'left': left, 'width': width, 'height': height, 'label': label_info['label'], 'mode': mode}
                self.labels.append(region)
                self.draw_label(region)
                self.save_labels()
            
            # GHI LỆNH VÀO EXCEL
            self.__testSequence.addSequence(TestSequenceItem_t(logger=self.logger, 
                                            testCaseName=label_info['testCaseName'], testItemName=label_info['testCaseName'], 
                                            testStepName=label_info['testCaseName'], equalValues=label_info['equalValues'],
                                            pythonMethod=label_info['pythonMethod'], methodArg1=label_info['methodArg1']))

        self.canvas.delete(self.rect)
        self.rect = None

    def on_right_click(self, event):
        if not self.is_boxes_visible: return 
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        # Chú ý unpacking 4 phần tử
        for i, (region, rect_id, text_id, bg_id) in enumerate(self.box_items):
            if region['left'] <= x <= region['left'] + region['width'] and region['top'] <= y <= region['top'] + region['height']:
                label_info = self.ask_label_dialog(self.labels[i]["label"])
                
                self.root.deiconify()
                self.root.attributes("-fullscreen", True)
                self.root.attributes("-alpha", 0.3)
                
                if label_info:
                    self.__testSequence.addSequence(TestSequenceItem_t(logger=self.logger, 
                                                    testCaseName=label_info['testCaseName'], testItemName=label_info['testCaseName'], 
                                                    testStepName=label_info['testCaseName'], equalValues=label_info['equalValues'],
                                                    pythonMethod=label_info['pythonMethod'], methodArg1=label_info['methodArg1']))
                break

    def on_double_click(self, event):
        if not self.is_boxes_visible: return 
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        # Chú ý unpacking 4 phần tử
        for i, (region, rect_id, text_id, bg_id) in enumerate(self.box_items):
            if region['left'] <= x <= region['left'] + region['width'] and region['top'] <= y <= region['top'] + region['height']:
                self.canvas.delete(rect_id)
                self.canvas.delete(text_id)
                self.canvas.delete(bg_id)
                del self.labels[i]
                del self.box_items[i]
                self.save_labels()
                print(f"Đã xóa Label: {region['label']}")
                break

    # ==========================================
    # FILE I/O VÀ HỘP THOẠI DIALOG
    # ==========================================
    def save_labels(self):
        with open(LABEL_FILE, "w", encoding='utf-8') as f: json.dump(self.labels, f, ensure_ascii=False, indent=4)

    def load_labels(self):
        if os.path.exists(LABEL_FILE):
            with open(LABEL_FILE, "r", encoding='utf-8') as f:
                self.labels = json.load(f)
            for region in self.labels:
                if region['label'].startswith("LB"):
                    n = int(region['label'][2:])
                    if n > self.labels_id: self.labels_id = n
                self.draw_label(region)

    def ask_label_dialog(self, lable_name):
        self.root.iconify()
        dialog = tk.Toplevel(self.root)
        dialog.title("Make Test Item Dialog")
        dialog.grab_set()

        label_var = tk.StringVar(value=lable_name)
        mode_var = tk.StringVar(value="image_locate") # Mặc định gợi ý dùng Visual Locate
        cb_value = tk.StringVar()
        image_name_var = tk.StringVar(value=f"img_{self.labels_id:03d}.png")

        tk.Label(dialog, text="Area lable").pack(padx=10, pady=2)
        tk.Entry(dialog, textvariable=label_var, width=100).pack(padx=10, pady=2)
        
        frame = tk.Frame(dialog)
        frame.pack(pady=5)
        
        tk.Label(dialog, text="Input value / Extra Arg (Ví dụ: HZ25 hoặc 'vung_cuon.png')").pack(padx=10, pady=2)
        tk.Entry(dialog, textvariable=cb_value, width=100).pack(padx=10, pady=2)
        
        tk.Label(dialog, text="TÊN FILE ẢNH SẼ LƯU (Chỉ dùng cho Image Locate)").pack(padx=10, pady=2)
        tk.Entry(dialog, textvariable=image_name_var, width=100, bg='lightyellow').pack(padx=10, pady=2)

        tk.Label(frame, text="-- KIỂU MỚI (CHỤP ẢNH / VISUAL) --", fg='blue', font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=(0,5))
        tk.Radiobutton(frame, text="1. Click vào Ảnh này", variable=mode_var, value="image_locate").grid(row=1, column=0, sticky='w')
        tk.Radiobutton(frame, text="2. Cuộn tìm Ảnh này", variable=mode_var, value="image_scroll").grid(row=1, column=1, sticky='w')

        tk.Label(frame, text="-- KIỂU CŨ (OCR / TỌA ĐỘ JSON) --", fg='gray').grid(row=2, column=0, columnspan=2, pady=(15,5))
        tk.Radiobutton(frame, text="Click Region", variable=mode_var, value="click").grid(row=3, column=0, sticky='w')
        tk.Radiobutton(frame, text="Select Dropdown (OCR)", variable=mode_var, value="select_dropdown").grid(row=3, column=1, sticky='w')

        result = {}
        def on_ok(event=None):
            mode = mode_var.get()
            result["label"] = label_var.get().strip()
            result["mode"] = mode
            result["testCaseName"] = "Test Case"
            result["equalValues"] = "OK"
            result["imageFileName"] = image_name_var.get().strip()

            # GHÉP LỆNH PYTHON CHUẨN XÁC
            if mode == "image_locate":
                result["pythonMethod"] = "act.click_by_image"
                result["methodArg1"] = f"'{result['imageFileName']}'" # Có dấu nháy đơn
            elif mode == "image_scroll":
                result["pythonMethod"] = "act.find_and_click_with_scroll"
                result["methodArg1"] = f"'{result['imageFileName']}', '{cb_value.get()}'"
            elif mode == "select_dropdown":
                result["pythonMethod"] = "act.select_combobox"
                result["methodArg1"] = f"lables_data_name='{lable_name_db}', region_lable='{result['label']}', cb_value='{cb_value.get()}'"
            elif mode == "click":
                result["pythonMethod"] = "act.mouse_click_region"
                result["methodArg1"] = f"lables_data_name='{lable_name_db}', region_lable='{result['label']}'"
                
            dialog.destroy()
        
        tk.Button(dialog, text="Xác nhận (Enter)", command=on_ok, bg='lightgreen', font=("Arial", 10, "bold")).pack(pady=10)
        dialog.bind("<Return>", on_ok)
        self.root.wait_window(dialog)
        return result

    def on_ctrl_s(self, event):
        self.loadSequenceObj.save_to_excel_file(self.__testSequence, sequence_path)
        print(f"✅ Đã lưu chuỗi Test Sequence vào: {sequence_path}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    tool = LabelingTool()
    tool.run()