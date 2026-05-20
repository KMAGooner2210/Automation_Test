from .logger import TestLogger
import pyautogui
import time
import os
import json
import pyperclip
import keyboard

class MouseKeysControl:
    '''
    Controls the mouse and keyboard, and performs Image Locate
    '''
    def __init__(self, logger):
        self.logger = logger
        self.lable_folder = "region"
        
        # Thêm thư mục chứa ảnh mẫu (assets)
        self.assets_dir = "assets"
        os.makedirs(self.assets_dir, exist_ok=True)

    # ========================================================
    # CÁC HÀM MỚI: XỬ LÝ BẰNG HÌNH ẢNH (VISUAL LOCATE)
    # ========================================================
    def click_by_image(self, image_name, confidence=0.8):
        """ Tìm hình ảnh trên màn hình và click vào tâm """
        # Lột bỏ dấu nháy (nếu có) do Excel truyền vào
        image_name = image_name.strip("'").strip('"')
        img_path = os.path.join(self.assets_dir, image_name)
        
        self.logger.info(f"Looking for image: {img_path}")
        if not os.path.exists(img_path):
            self.logger.error(f"Image not found: {img_path}")
            return "FAIL_NOT_FOUND"

        try:
            pos = pyautogui.locateCenterOnScreen(img_path, confidence=confidence)
            if pos:
                pyautogui.moveTo(pos.x, pos.y, duration=0.2)
                pyautogui.click()
                time.sleep(0.4)
                return "OK"
            return "FAIL"
        except Exception as e:
            self.logger.error(f"Lỗi Locate: {e}")
            return "FAIL_EXCEPTION"

    def verify_image_state(self, image_name, confidence=0.8):
        """ Kiểm tra xem hình ảnh (vd: Checkbox ON) có đang hiển thị không """
        image_name = image_name.strip("'").strip('"')
        img_path = os.path.join(self.assets_dir, image_name)
        try:
            if pyautogui.locateOnScreen(img_path, confidence=confidence):
                return "OK"
            return "FAIL"
        except:
            return "FAIL"

    def find_and_click_with_scroll(self, target_image, scroll_area_image, max_scrolls=20, confidence=0.8):
        """ Tự động cuộn để tìm ảnh bị khuất """
        target_image = target_image.strip("'").strip('"')
        scroll_area_image = scroll_area_image.strip("'").strip('"')
        target_path = os.path.join(self.assets_dir, target_image)
        scroll_path = os.path.join(self.assets_dir, scroll_area_image)

        scroll_pos = pyautogui.locateCenterOnScreen(scroll_path, confidence=confidence)
        if scroll_pos:
            pyautogui.moveTo(scroll_pos)
            time.sleep(0.2)

        for i in range(max_scrolls):
            target_pos = pyautogui.locateCenterOnScreen(target_path, confidence=confidence)
            if target_pos:
                pyautogui.click(target_pos)
                return "OK"
            pyautogui.scroll(-100) # Cuộn xuống
            time.sleep(0.3)
        return "FAIL_NOT_FOUND"

    # ========================================================
    # CÁC HÀM CŨ CỦA BẠN (GIỮ NGUYÊN 100%)
    # ========================================================
    def mouse_scroll(self, **kwargs):
        lables_data_name = kwargs.get("lables_data_name", "home_default")
        region_lable = kwargs.get("region_lable", "HOME")
        wheel = kwargs.get("wheel", 1)
        lables_data_name = lables_data_name + '.json'
        lables_data_name = os.path.join(self.lable_folder, lables_data_name)
        labels = []
        if os.path.exists(lables_data_name):
            with open(lables_data_name, "r", encoding='utf-8') as f:
                labels = json.load(f)
            for region in labels:
                mode = region.get("label")
                if mode is None: continue
                elif mode == region_lable:
                    self.logger.info(f'Click to lable: {region_lable}')
                    x1, y1 = region['left'], region['top']
                    x, y = x1 + region['width']/2, y1 + region['height']/2
                    pyautogui.moveTo(x, y)
                    time.sleep(0.2)
                    pyautogui.scroll(wheel)
                    time.sleep(0.2)
                    return "OK"
        return "FAIL"

    def delay_s(self, **kwargs):
        delay_time = kwargs.get("delay_time", 1)
        self.logger.info(f'delay_s: {delay_time}')
        time.sleep(float(delay_time))
        return "OK"

    def mouse_click_region(self, **kwargs):
        lables_data_name = kwargs.get("lables_data_name", "home_default")
        region_lable = kwargs.get("region_lable", "HOME")
        lables_data_name = lables_data_name + '.json'
        lables_data_name = os.path.join(self.lable_folder, lables_data_name)
        labels = []
        if os.path.exists(lables_data_name):
            with open(lables_data_name, "r", encoding='utf-8') as f:
                labels = json.load(f)
            for region in labels:
                mode = region.get("label")
                if mode is None: continue
                elif mode == region_lable:
                    self.logger.info(f'Click to lable: {region_lable}')
                    x1, y1 = region['left'], region['top']
                    x, y = x1 + region['width']/2, y1 + region['height']/2
                    pyautogui.click(x=x, y=y, interval=0.25, duration=0.25)
                    time.sleep(0.4)
                    return "OK"
        return "FAIL"
    
    def mouse_move(self, **kwargs):
        lables_data_name = kwargs.get("lables_data_name", "home_default")
        region_lable = kwargs.get("region_lable", "HOME")
        lables_data_name = lables_data_name + '.json'
        lables_data_name = os.path.join(self.lable_folder, lables_data_name)
        labels = []
        if os.path.exists(lables_data_name):
            with open(lables_data_name, "r", encoding='utf-8') as f:
                labels = json.load(f)
            for region in labels:
                mode = region.get("label")
                if mode is None: continue
                elif mode == region_lable:
                    self.logger.info(f'Move to lable: {region_lable}')
                    x1, y1 = region['left'], region['top']
                    x, y = x1 + region['width']/2, y1 + region['height']/2
                    pyautogui.moveTo(x, y)
                    time.sleep(0.2)
                    return "OK"
        return "FAIL"

    def type_in(self, **kwargs):
        lables_data_name = kwargs.get("lables_data_name", "home_default")
        region_lable = kwargs.get("region_lable")
        text = kwargs.get("cb_value") or kwargs.get("input_value") or ""
        lables_data_name = lables_data_name + ".json"
        path = os.path.join(self.lable_folder, lables_data_name)
        region = None
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                labels = json.load(f)
                for r in labels:
                    if r.get("label") == region_lable:
                        region = r
                        break
        if region is None:
            self.logger.error(f"Region '{region_lable}' not found in {lables_data_name}")
            return "FAIL"
            
        time.sleep(1)
        for i in range(30):
            keyboard.press_and_release("backspace")
            time.sleep(0.02)

        print(text)
        keyboard.write(text)
        self.logger.info(f"Typed '{text}' in region '{region_lable}'")
        return "OK"