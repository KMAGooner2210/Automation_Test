import os
import easyocr
import cv2
import matplotlib.pyplot as plt
import json
from PIL import ImageGrab, ImageEnhance, Image, ImageFilter
import numpy as np
from control import TestLogger
from control import TestSequence_t
from control import TestSequenceItem_t
from control import LoadSequence
from control import MouseKeysControl
from datetime import datetime
import pyautogui
import time
import shutil
import psutil
from pywinauto import Application
from contextlib import suppress
import warnings
import keyboard
import threading

# Suppress PyTorch DataLoader warning about pin_memory
warnings.filterwarnings("ignore", message=".*pin_memory.*", category=UserWarning)

class AutomationController:
    """Controls pause/resume functionality for automation"""
    def __init__(self):
        self.is_paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start in running state
        self.listener_thread = None
        self.setup_keyboard_listener()
    
    def setup_keyboard_listener(self):
        """Setup keyboard listener for space key"""
        def on_space_press():
            if self.is_paused:
                self.resume()
            else:
                self.pause()
        
        # Register space key handler
        keyboard.on_press_key('space', lambda _: on_space_press())
        print("Automation Controller: Press SPACE to pause/resume automation")
    
    def pause(self):
        """Pause the automation"""
        if not self.is_paused:
            self.is_paused = True
            self.pause_event.clear()
            print("AUTOMATION PAUSED - Press SPACE to resume")
    
    def resume(self):
        """Resume the automation"""
        if self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            print("AUTOMATION RESUMED")
    
    def wait_if_paused(self):
        """Block execution if automation is paused"""
        if self.is_paused:
            print("Waiting for resume... (Press SPACE to continue)")
        self.pause_event.wait()  # This blocks until resumed
    
    def cleanup(self):
        """Clean up keyboard listener"""
        keyboard.unhook_all()

LABEL_FILE = r"region\GS_Config_Dropdown.json"
LABEL_FILE = r"region\GS_Config_Dropdown.json"
reader = easyocr.Reader(['en'], gpu=False)
lable_folder = "region"
image_log_dir = 'image_log'
graph_log_dir = 'graph_log'

# Development Desktop constants
DEV_DESKTOP_PROC_NAME = 'development_desktop.exe'
DEV_DESKTOP_APP_PATH = r"C:\Program Files\Bosch Sensortec\Development Desktop\DDF\development_desktop.exe"
TIMEOUT = 10

os.makedirs(image_log_dir, exist_ok=True)


def is_process_running(process_name):
    """Check if a process is running by name."""
    try:
        return any(p.name().lower() == process_name.lower() 
                  for p in psutil.process_iter(['name']))
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False


def kill_process(process_name):
    """Kill a process by name."""
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == process_name.lower():
                proc.kill()
                print(f"Killed process: {process_name}")
    except Exception as e:
        print(f"Failed to kill process {process_name}: {e}")


class DevDesktopAutomation:
    """Class to handle Development Desktop application automation."""
    
    def __init__(self):
        self.app = None
        self.main_window = None

    def connect(self):
        """Connect to or start the Development Desktop application."""
        if is_process_running(DEV_DESKTOP_PROC_NAME):
            print('Development Desktop already opened, connecting')
            try:
                self.app = Application(backend="uia").connect(path=DEV_DESKTOP_APP_PATH)
            except Exception as e:
                print(f"Failed to connect to existing application: {e}")
                # Kill existing instance and start fresh
                kill_process(DEV_DESKTOP_PROC_NAME)
                time.sleep(1)
                return self._start_new_instance()
        else:
            print('Development Desktop not opened yet, starting...')
            return self._start_new_instance()
        
        self._get_main_window()
        return self.app is not None and self.main_window is not None
    
    def _start_new_instance(self):
        """Start a new instance of the application."""
        try:
            self.app = Application(backend="uia").start(DEV_DESKTOP_APP_PATH)
            time.sleep(10)  # Allow time for app to initialize
            self._get_main_window()
            return True
        except Exception as e:
            print(f"Failed to start application: {e}")
            return False
    
    def _get_main_window(self):
        """Get the main application window."""
        try:
            self.main_window = self.app.window(title_re=".*Development Desktop Beta.*", control_type="Window")
            if not self.main_window.exists(timeout=TIMEOUT):
                print("Main window not found")
                self.main_window = None
            else:
                print("Found main window")
        except Exception as e:
            print(f"Error getting main window: {e}")
            self.main_window = None
    
    def close(self):
        """Close the application."""
        if self.app:
            with suppress(Exception):
                self.app.kill()
            print("Application closed")


def mouse_click_region(region):
    '''
    click to center of region
    lables_data: Database of regions as json string
    '''
    x1, y1 = region['left'], region['top']
    x, y = x1 + region['width']/2, y1 + region['height']/2
    pyautogui.click(x=x, y=y, interval=0.25, duration=0.25)
    time.sleep(0.4)
    return "OK"

def type_in(region, text, press_enter=True):
    
    time.sleep(1)
    pyautogui.press("backspace", presses=20)
    # Type new value
    if text:
        for char in text:
            if char == "_":
                pyautogui.press('_', presses=1)
            else:
                pyautogui.write(char, interval=0.05)
    return "OK"

def mouse_scroll(region, wheel=1):
    '''
    scroll the mouse at the x, y coordinates
    '''
    print(f"mouse move{wheel}")
    x1, y1 = region['left'], region['top']
    x, y = x1 + region['width']/2, y1 + region['height']/2
    pyautogui.moveTo(x, y)
    time.sleep(0.2)
    pyautogui.scroll(wheel)
    time.sleep(0.2)
    return "OK"


def search_letter(image_path):
    image = cv2.imread(image_path)
    # Thực hiện nhận dạng
    results = reader.readtext(image)

    # Hiển thị kết quả
    for (bbox, text, confidence) in results:
        print(f"Detected: '{text}' (Confidence: {confidence:.2f})")
        # Vẽ khung quanh chữ
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left = tuple(map(int, top_left))
        bottom_right = tuple(map(int, bottom_right))
        cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(image, text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    # Hiển thị ảnh kết quả
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.title('Kết quả nhận dạng')
    plt.show()


def fix_hardcoded_ocr_errors(text):
    """
    Hardcoded fixes for specific OCR detection problems.
    """
    if not text:
        return text
    
    # Rule 1: If OCR detected 'ECCC', change to 'E00C'
    if text.upper() == 'LOWER_POWEP' or text.upper() == 'LOWER_POWEE':
        #print(f"Hardcoded fix: '{text}' → 'E00C'")
        return 'LOWER_POWER'
    
    if text == 'Reed':
        return 'Read'

    if text == 'Wrtte' or text == "Wriie":
        return 'Write'
    
    # Rule 2: If OCR detected text starts with 'generic_interrupt', fix character at position 16 to '1'
    if text.lower().startswith('int_status_inti') and len(text) > 15:
        fixed_text = text[:14] + '1' + text[15:]
        if fixed_text != text:
            #print(f"Hardcoded fix: '{text}' → '{fixed_text}'")
            pass
        return fixed_text
    
    # Add more hardcoded fixes as needed
    hardcoded_fixes = {
        'C000': '0000',
        'C00C': '000C', 
        'CC00': '0000',
        'CCCC': '0000',
        'EC00': 'E000',
        'ECC0': 'E000',
        'generic_interrupti_1': 'generic_interrupt1_1',
        'generic_interruptz_1': 'generic_interrupt2_1',
        'generic_interrupts_1': 'generic_interrupt3_1',
        'Reed': 'Read',
        'LOWER_POWEP': 'LOWER_POWER'
    }
    
    text_upper = text.upper()
    for wrong, correct in hardcoded_fixes.items():
        if text_upper == wrong.upper():
            #print(f"Hardcoded fix: '{text}' -> '{correct}'")
            return correct
    
    return text

def extract_letters(image, allowlist=None):
    # read the image with improved parameters for underscore and number detection
    if allowlist:
        results = reader.readtext(
            image,
            allowlist=allowlist,
            paragraph=False,
            min_size=5,
            text_threshold=0.6,
            low_text=0.3,
            link_threshold=0.3
        )
    else:
        results = reader.readtext(
            image,
            paragraph=False,
            min_size=5,
            text_threshold=0.6,
            low_text=0.3,
            link_threshold=0.3
        )
    Total_text = ""

    # Hiển thị kết quả
    for (bbox, text, confidence) in results:
        print(f"Detected: '{text}' (Confidence: {confidence:.2f})")
        # Clean up text but preserve underscores
        text = text.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
        Total_text += text
        # Vẽ khung quanh chữ
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left = tuple(map(int, top_left))
        bottom_right = tuple(map(int, bottom_right))
        cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(image, text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    # show what read success
    # plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    # plt.axis('off')
    # plt.title('Kết quả nhận dạng')
    # plt.show()
    
    # Apply hardcoded fixes for known OCR errors
    Total_text = fix_hardcoded_ocr_errors(Total_text)
    
    return Total_text


def get_region_letters(click_val, region, allowlist=None):
    ''''
    capture and find the text region in the image
    click_val: the text value to find
    region: the region to capture
    allowlist: the list of characters to recognize
    '''
    print("Start searching for text region...")
    x1, y1 = region['left'], region['top']
    x2, y2 = x1 + region['width'], y1 + region['height']
    pic_w = region['width']
    pic_h = region['height']
    # Capture the region of interest
    scale_ratio = 1.0
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    if pic_w < 150 or pic_h < 150:
        scale_ratio = 3
    else:
        scale_ratio = 2
    img = img.resize((img.width * scale_ratio, img.height * scale_ratio))
    
    # Enhanced processing for blue background (selected items)
    # Step 1: Check if image has blue background (selected item)
    img_rgb = np.array(img)
    blue_channel = img_rgb[:, :, 2]  # Extract blue channel
    avg_blue = np.mean(blue_channel)
    
    # If high blue content, it's likely a selected item with blue background
    if avg_blue > 150:  # Blue background detected
        print("Blue background detected - applying enhanced processing for selected item")
        # For blue backgrounds, enhance contrast more aggressively
        enhancer = ImageEnhance.Contrast(img)
        img_contrast = enhancer.enhance(5)  # Higher contrast for blue backgrounds
        img1 = img_contrast.convert("L")
        img1 = ImageEnhance.Contrast(img1).enhance(3.0)  # Even more contrast
    else:
        # Normal processing for white backgrounds
        enhancer = ImageEnhance.Contrast(img)
        img_contrast = enhancer.enhance(4)
        img1 = img_contrast.convert("L")
        img1 = ImageEnhance.Contrast(img1).enhance(2.0)
    
    # Use adaptive threshold with proper handling for inverted colors
    img_np = np.array(img1)
    
    if avg_blue > 150:  # Blue background with white text
        print("Blue background with WHITE text detected")
        # For white text on blue background, we need to INVERT the threshold
        _, img_thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:  # White background with black text
        # Normal threshold for black text on white background
        _, img_thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Additional processing to enhance underscores specifically for blue backgrounds
    if avg_blue > 150:  # Blue background detected
        # Create different kernels for better character enhancement
        # Horizontal kernel to enhance underscores
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
        # Vertical kernel to enhance letters
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
        
        # Apply morphological operations
        enhanced_horizontal = cv2.morphologyEx(img_thresh, cv2.MORPH_CLOSE, horizontal_kernel)
        enhanced_vertical = cv2.morphologyEx(img_thresh, cv2.MORPH_CLOSE, vertical_kernel)
        
        # Combine all enhancements
        img_thresh = cv2.bitwise_or(img_thresh, enhanced_horizontal)
        img_thresh = cv2.bitwise_or(img_thresh, enhanced_vertical)
    
    image = img_thresh
    # read the image
    # results = reader.readtext(image, allowlist='ABCDEF0123456789')
    if allowlist:
        results = reader.readtext(image, allowlist=allowlist, width_ths=0.8, height_ths=0.8)
    else:
        results = reader.readtext(image, width_ths=0.8, height_ths=0.8)

    for (bbox, text, confidence) in results:
        detected_text = fix_hardcoded_ocr_errors(text)

        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left = tuple(map(int, top_left))
        bottom_right = tuple(map(int, bottom_right))
        left, top = top_left
        right, bottom = bottom_right
        width = right - left
        height = bottom - top
        region = None
        print(f"Detected: '{detected_text}' (Confidence: {confidence:.2f})")
        if detected_text.upper() == click_val.upper():
            region = {
                'top': top/scale_ratio,
                'left': left/scale_ratio,
                'width': width/scale_ratio,
                'height': height/scale_ratio,
            }
            break
        # to debug, uncommend bellow code
        # cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
        # cv2.putText(image, text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        # plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        # plt.axis('off')
        # plt.title('Kết quả nhận dạng')
        # plt.show()
    print("end searching for text region...")
    return region


def get_text_lable(**kwargs):
    lables_data_name = kwargs.get("lables_data_name", "home_default")
    region_lable = kwargs.get("region_lable", "HOME")
    allowlist = kwargs.get("allowlist", None)
    lables_data_name = lables_data_name + '.json'
    lables_data_name = os.path.join(lable_folder, lables_data_name)
    labels = []
    if os.path.exists(lables_data_name):
        with open(lables_data_name, "r", encoding='utf-8') as f:
            labels = json.load(f)
        for region in labels:
            lable = region.get("label")
            if lable is None:
                continue
            elif lable == region_lable:
                return get_text(region, allowlist=allowlist)


def enhance_for_underscore(img_np):
    """
    Special preprocessing to enhance underscore detection without blurring.
    Gently strengthens horizontal lines (underscores) while preserving clarity.
    """
    # Gentler morphological operations - smaller kernels, fewer iterations
    # Small horizontal kernel to connect nearby underscore pixels without blurring
    kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
    img_enhanced = cv2.morphologyEx(img_np, cv2.MORPH_CLOSE, kernel_horizontal, iterations=1)
    
    # Very light dilation to slightly thicken underscores without making them blurry
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2))
    img_enhanced = cv2.dilate(img_enhanced, kernel_dilate, iterations=1)
    
    return img_enhanced



def get_text(region, allowlist=None):
    mode = region.get("mode")
    if mode == "click":
        return
    # print(region['label'])
    x1, y1 = region['left'], region['top']
    x2, y2 = x1 + region['width'], y1 + region['height']
    # screen short at the region
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    
    # Use higher resolution for better clarity
    img = img.resize((img.width * 4, img.height * 4), resample=Image.LANCZOS)
    
    # Sharpen the image before processing to improve clarity
    from PIL import ImageFilter
    img = img.filter(ImageFilter.SHARPEN)
    
    # More moderate contrast enhancement
    enhancer = ImageEnhance.Contrast(img)
    img_contrast = enhancer.enhance(3.0)  # Reduced from 4
    img1 = img_contrast.convert("L")
    img1 = ImageEnhance.Contrast(img1).enhance(1.5)  # Reduced from 2.0
    
    # Use adaptive threshold instead of fixed threshold for different backgrounds
    img_np = np.array(img1)
    # Apply OTSU threshold which automatically finds the best threshold value
    _, img_thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Gentle enhancement for underscore detection (less blurring)
    img_thresh = enhance_for_underscore(img_thresh)

    img_np = img_thresh
    
    # Always include underscore in allowlist if allowlist is provided
    if allowlist and '_' not in allowlist:
        allowlist += '_'
    
    # start read character from image
    text_val = extract_letters(img_np, allowlist=allowlist)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"img_{timestamp}.png"
    path = os.path.join(image_log_dir, filename)
    # Save the processed image for debugging
    cv2.imwrite(path, img_thresh)
    return text_val


def click_to_text(click_val, region, allowlist=None):
    mode = region.get("mode")
    # Detect the text region inside the captured region
    scroll_point_down = region['height'] * -1

    region1 = get_region_letters(click_val, region, allowlist=allowlist)
    if region1 is None:
        mouse_scroll(region, wheel=3000)
        time.sleep(1)
        for wscroll in range(10, 1000, 10):
            region1 = get_region_letters(click_val, region, allowlist=allowlist)
            if region1 is None:
                mouse_scroll(region, wheel=scroll_point_down)
                time.sleep(1)
            else:
                break
    if region1 is None:
        print("Text not found.")
        return "FAIL"

    # Calculate absolute coordinates on the screen
    abs_left = region['left'] + region1['left']
    abs_top = region['top'] + region1['top']
    abs_right = abs_left + region1['width']
    abs_bottom = abs_top + region1['height']

    # Optionally, save the detected region image for debugging
    # img = ImageGrab.grab(bbox=(abs_left, abs_top, abs_right, abs_bottom))
    # img = img.resize((img.width * 3, img.height * 3))
    # enhancer = ImageEnhance.Contrast(img)
    # img_contrast = enhancer.enhance(4)
    # img1 = img_contrast.convert("L")
    # img1 = ImageEnhance.Contrast(img1).enhance(2.0)
    # img1 = img1.point(lambda x: 255 if x > 150 else 0)

    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # filename = f"img_{timestamp}.png"
    # path = os.path.join(image_log_dir, filename)
    # img1.save(path)

    # Return the absolute coordinates for clicking
    click_region = {
        'left': abs_left,
        'top': abs_top,
        'width': region1['width'],
        'height': region1['height'],
        'right': abs_right,
        'bottom': abs_bottom
    }
    mouse_click_region(click_region)
    return "OK"


def select_combobox(**kwargs):
    lables_data_name = kwargs.get("lables_data_name", "home_default")
    region_lable = kwargs.get("region_lable", "HOME")
    allowlist = kwargs.get("allowlist", None)
    select_combobox_value = kwargs.get("cb_value", None)

    #Apply hardcoded fixes
    if select_combobox_value:
        select_combobox_value = fix_hardcoded_ocr_errors(select_combobox_value)

    lables_data_name = lables_data_name + '.json'
    lables_data_name = os.path.join(lable_folder, lables_data_name)
    labels = []
    if os.path.exists(lables_data_name):
        with open(lables_data_name, "r", encoding='utf-8') as f:
            labels = json.load(f)
        for region in labels:
            lable = region.get("label")
            if lable is None:
                continue
            elif lable == region_lable:
                return click_to_text(select_combobox_value, region, allowlist=allowlist)

def copy_and_rename_csv(**kwargs):
    """
    Copy a CSV file from src_csv_path, rename it to new_filename, and save it to the 'save_log' folder.
    The 'save_log' folder will be created in the same directory as the source CSV file.
    """
    src_csv_path = kwargs.get("src_csv_path", "src_csv_path")
    new_filename = kwargs.get("new_filename", "new_filename")

    # Check if source file exists
    if not os.path.exists(src_csv_path):
        print(f"Error: Source file does not exist: {src_csv_path}")
        return "FAIL"

    # Get the directory containing the source file
    src_dir = os.path.dirname(src_csv_path)
    save_log_dir = os.path.join(src_dir, "save_log")

    os.makedirs(save_log_dir, exist_ok=True)
    dst_csv_path = os.path.join(save_log_dir, new_filename)
    shutil.copy2(src_csv_path, dst_csv_path)
    print(f"File copied to: {dst_csv_path}")
    return "OK"


if __name__ == '__main__':
    # Initialize Development Desktop automation
    dev_desktop = DevDesktopAutomation()
    # Initialize automation controller for pause/resume
    automation_controller = AutomationController()
    
    try:
        # Start the Development Desktop application
        print("Starting Development Desktop application...")
        if not dev_desktop.connect():
            print("Failed to start Development Desktop application. Exiting.")
            exit(1)
        
        print("Development Desktop application started successfully!")
        time.sleep(2)  # Give the application time to fully load  

        ################################################################
        logger = TestLogger(loglevel='INFO', savelog='True', display = 'True')
        logger.info('Development Desktop application started - Beginning test automation')
        logger.info('This is an info')
        logger.warning('This is a warning')
        logger.error('This is an error')
        logger.critical('This is critical')
        logger.debug('This is debug')
        ################################################################
        
        loadSequenceObj = LoadSequence(ExcellPath="test_case/TN2.xlsx", sheetName="f6e_dl_bft_0822",logger=logger)
        __testSequence = loadSequenceObj.LoadTestSequence()
        __testSequence.TestSequence[0].logger.info('This is an info =================================================================')
        act = MouseKeysControl(logger)
        
        # Execute test sequence
        for testStep in __testSequence.TestSequence:
            # Check if automation is paused
            automation_controller.wait_if_paused()
            
            if testStep.ignore == 'x':
                testStep.testResult = False
                continue
            #resVal = executePyCommand(testStep)
            pyCmd = "resVal = " + testStep.pythonMethod + "(" + str(testStep.methodArg1) + ")"
            # print(pyCmd)

            # local_vars = locals()

            # try:
            #     exec(pyCmd, globals(), local_vars)

            #     resVal = local_vars.get('resVal', "FAIL")

            # except Exception as e:
            #     print(f"Error when execute command '{pyCmd}': {e}")
            #     resVal = "FAIL"

            exec(pyCmd)
            if testStep.equalValues in str(resVal):
                testStep.testResult = True
                logger.info(f"Test case: {testStep.testCaseName}, Step: {testStep.test_itemName} PASS")
            else:
                confirm = input(f"Actual: {resVal}, Expect: {testStep.equalValues}. Type p to pass and f to fail")
                if confirm.lower() == 'p':
                    testStep.testResult = True
                    logger.info(f"Test case: {testStep.testCaseName}, Step: {testStep.test_itemName} PASS")
                else:
                    testStep.testResult = False
                    logger.error(f"Test case: {testStep.testCaseName}, Step: {testStep.test_itemName} FAIL")
            if testStep.ignore == 'sa':
                print("Copy and save new data")
        
        # save the test result
        loadSequenceObj.save_to_excel_file(__testSequence, "test_sequence/ddf_test_sequence_test_2.xlsx")
        logger.info('Test automation completed successfully')
        
    except Exception as e:
        print(f"Error during test execution: {e}")
        if 'logger' in locals():
            logger.error(f"Test automation failed with error: {e}")
    
    finally:
        # Clean up automation controller
        automation_controller.cleanup()
        
        # Always close the Development Desktop application when done
        print("Closing Development Desktop application...")
        dev_desktop.close()
        print("Development Desktop application closed. Test automation finished.")
        
        # if testStep.equalValues:
        #     if resVal in testStep.equalValues or testStep.equalValues in resVal:
        #         print(testStep.test_step_name + "\r\n=========================PASS===================->\r\n Actual Value:\r\n" + resVal + " ^^^^^^^^^^^^^^\r\nExpected: \r\n" + testStep.equalValues + "\r\n")
        #     else:
        #         print(testStep.test_step_name + "\r\n=========================FAIL===================->\r\n Actual Value:\r\n" + resVal + " ^^^^^^^^^^^^^^\r\nExpected: \r\n" + testStep.equalValues + "\r\n")
        # elif testStep.lowValue and testStep.highValue:
        #     print("lowValue: " + str(testStep.lowValue))
        #     print("highValue: " + str(testStep.highValue))
        #     print("resVal: " + str(resVal))
        #     low = float(testStep.lowValue)
        #     high = float(testStep.highValue)
        #     actual = float(0)
        #     if actual >= low and actual <= high:
        #         print("Pass: low: " + str(low) + " actual: " + str(actual) + " high: " + str(high))
        #     else :
        #         print("Fail: low: " + str(low) + " actual: " + str(actual) + " high: " + str(high))

    # load_labels()
