import os
import cv2
import matplotlib.pyplot as plt
import json
from PIL import ImageGrab, ImageEnhance, ImageDraw
import numpy as np
import ast  
import base64

from control import TestLogger
from control import TestSequence_t
from control import TestSequenceItem_t
from control import LoadSequence
from control import MouseKeysControl
from html_paser.parser1 import GetRegisterInfo
from datetime import datetime
import pyautogui
import time
import shutil
import logging
import easyocr


from paddleocr import PaddleOCR

LAST_INTERACTED_REGION = None

LABEL_FILE = r"region\GS_Config_Dropdown.json"
lable_folder = "region"
image_log_dir = 'image_log'

os.makedirs(image_log_dir, exist_ok=True)

# Khởi tạo PaddleOCR 
reader_paddle = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=False)
reader_easy = easyocr.Reader(['en'], gpu=False)


def mouse_click_region(region):
    global LAST_INTERACTED_REGION
    LAST_INTERACTED_REGION = region
    x1, y1 = region['left'], region['top']
    x, y = x1 + region['width']/2, y1 + region['height']/2
    pyautogui.click(x=x, y=y, interval=0.25, duration=0.25)
    time.sleep(0.4)
    return "OK"

def type_in(region, text, press_enter=True):
    global LAST_INTERACTED_REGION
    LAST_INTERACTED_REGION = region
    time.sleep(1)
    pyautogui.press("backspace", presses=20)
    if text:
        for char in text:
            if char == "_":
                pyautogui.press('_', presses=1)
            else:
                pyautogui.write(char, interval=0.05)
    return "OK"

def mouse_scroll(region, wheel=1):
    print(f"mouse move{wheel}")
    x1, y1 = region['left'], region['top']
    x, y = x1 + region['width']/2, y1 + region['height']/2
    pyautogui.moveTo(x, y)
    time.sleep(0.2)
    pyautogui.scroll(wheel)
    time.sleep(0.2)
    return "OK"

def filter_allowlist(text, allowlist):
    if not allowlist: return text
    return ''.join([c for c in text if c in allowlist])

def search_letter(image_path):
    image = cv2.imread(image_path)
    results = reader_paddle.ocr(image_path, cls=True)
    if results[0] is not None:
        for res in results[0]:
            box = res[0]
            text = res[1][0].replace(',', '1')
            confidence = res[1][1]
            print(f"Detected: '{text}' (Confidence: {confidence:.2f})")
            top_left = (int(min([point[0] for point in box])), int(min([point[1] for point in box])))
            bottom_right = (int(max([point[0] for point in box])), int(max([point[1] for point in box])))
            cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
            cv2.putText(image, text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.title('Kết quả nhận dạng')
    plt.show()

def extract_letters(image, allowlist=None):
    if len(image.shape) == 2:
        img_paddle = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        img_paddle = image
    total_text = ""
    results_p = reader_paddle.ocr(img_paddle, cls=True)
    if results_p[0]:
        for res in results_p[0]:
            text = res[1][0].replace(',', '1').strip()
            total_text += filter_allowlist(text, allowlist)
    if not total_text:
        results_e = reader_easy.readtext(image)
        for (bbox, text, confidence) in results_e:
            text = text.replace(',', '1').strip()
            total_text += filter_allowlist(text, allowlist)
    return total_text

def get_region_letters(click_val, region, allowlist=None):
    print(f"Hybrid searching for: '{click_val}'...")
    x1, y1 = int(region['left']), int(region['top'])
    pic_w, pic_h = int(region['width']), int(region['height'])
    img_pil = ImageGrab.grab(bbox=(x1, y1, x1 + pic_w, y1 + pic_h))
    scale_ratio = 2
    img_resized = img_pil.resize((img_pil.width * scale_ratio, img_pil.height * scale_ratio))
    
    print("Trying PaddleOCR...")
    img_np = np.array(img_resized)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    results_p = reader_paddle.ocr(img_bgr, cls=False)
    if results_p[0]:
        for res in results_p[0]:
            text = res[1][0].upper().replace(',', '1').strip()
            target = click_val.upper().strip()
            if target == text or target in text:
                print(f"Match found by PaddleOCR: '{text}'")
                box = res[0]
                return {'left': min([p[0] for p in box]) / scale_ratio, 'top': min([p[1] for p in box]) / scale_ratio,
                        'width': (max([p[0] for p in box]) - min([p[0] for p in box])) / scale_ratio, 'height': (max([p[1] for p in box]) - min([p[1] for p in box])) / scale_ratio}

    print("PaddleOCR failed. Preparing image for EasyOCR...")
    img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    blue_ch = img_np[:, :, 2]
    avg_blue = np.mean(blue_ch)
    if avg_blue > 150:
        _, img_thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        _, img_thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    img_processed = cv2.morphologyEx(img_thresh, cv2.MORPH_CLOSE, kernel)
    
    print("Trying EasyOCR...")
    results_e = reader_easy.readtext(img_processed)
    for (bbox, text, confidence) in results_e:
        text = text.upper().replace(',', '1').strip()
        target = click_val.upper().strip()
        if target == text or target in text:
            print(f"Match found by EasyOCR: '{text}' (Confidence: {confidence:.2f})")
            top_left = bbox[0]
            bottom_right = bbox[2]
            return {'left': top_left[0] / scale_ratio, 'top': top_left[1] / scale_ratio,
                    'width': (bottom_right[0] - top_left[0]) / scale_ratio, 'height': (bottom_right[1] - top_left[1]) / scale_ratio}
    print("Both OCR engines failed to find match.")
    return None

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
            if lable is None: continue
            elif lable == region_lable:
                return get_text(region, allowlist=allowlist)

def get_text(region, allowlist=None):
    global LAST_INTERACTED_REGION
    LAST_INTERACTED_REGION = region
    mode = region.get("mode")
    if mode == "click": return
    x1, y1 = region['left'], region['top']
    x2, y2 = x1 + region['width'], y1 + region['height']
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    img = img.resize((img.width * 3, img.height * 3))
    enhancer = ImageEnhance.Contrast(img)
    img_contrast = enhancer.enhance(4)
    img1 = img_contrast.convert("L")
    img1 = ImageEnhance.Contrast(img1).enhance(2.0)
    img_np = np.array(img1)
    _, img_thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    img_np = img_thresh
    text_val = extract_letters(img_np, allowlist=allowlist)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"img_{timestamp}.png"
    path = os.path.join(image_log_dir, filename)
    cv2.imwrite(path, img_thresh)
    return text_val

def click_to_text(click_val, region, allowlist=None):
    global LAST_INTERACTED_REGION
    mode = region.get("mode")
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
            else: break
    if region1 is None:
        print("Text not found.")
        return "FAIL"
    abs_left = region['left'] + region1['left']
    abs_top = region['top'] + region1['top']
    abs_right = abs_left + region1['width']
    abs_bottom = abs_top + region1['height']
    click_region = {'left': abs_left, 'top': abs_top, 'width': region1['width'], 'height': region1['height'], 'right': abs_right, 'bottom': abs_bottom}
    LAST_INTERACTED_REGION = click_region
    mouse_click_region(click_region)
    return "OK"

def select_combobox(**kwargs):
    lables_data_name = kwargs.get("lables_data_name", "home_default")
    region_lable = kwargs.get("region_lable", "HOME")
    allowlist = kwargs.get("allowlist", None)
    select_combobox_value = kwargs.get("cb_value", None)
    lables_data_name = lables_data_name + '.json'
    lables_data_name = os.path.join(lable_folder, lables_data_name)
    labels = []
    if os.path.exists(lables_data_name):
        with open(lables_data_name, "r", encoding='utf-8') as f:
            labels = json.load(f)
        for region in labels:
            lable = region.get("label")
            if lable is None: continue
            elif lable == region_lable:
                return click_to_text(select_combobox_value, region, allowlist=allowlist)

def html_parser(**kwargs):
    register_address = kwargs.get("register_address", "")
    path_html = r'C:\Users\MTA8HC\Documents\BMI420ipxact\content\extended_register_map_memmap.html'
    ocr_text = get_text_lable(**kwargs).lower()
    if not ocr_text: ocr_text = '0000'
    parser = GetRegisterInfo()
    reg_info = parser.get_register_by_address(path_html, register_address.replace(register_address[3], register_address[3].upper()))
    if not reg_info:
        print(f"html_parser: No register info found for address {register_address}")
        return "FAIL"
    expected_address = reg_info.get('Address', '').lower()
    expected_name = reg_info.get('Name', '').lower()
    expected_reset = (reg_info.get('Reset', '').lower()).replace('0x', '')
    if ocr_text.startswith('0x') and len(ocr_text) == 3: ocr_text = ocr_text.replace('0x', '0x0')
    if ocr_text == '0': ocr_text = '0000'
    print(f"html_parser: OCR='{ocr_text}', expected_address='{expected_address}', expected_name='{expected_name}', expected_reset='{expected_reset}'")
    if ocr_text == expected_address or ocr_text == expected_name or ocr_text == expected_reset: return "OK"
    else: return "FAIL"
    
def copy_and_rename_csv(**kwargs):
    src_csv_path = kwargs.get("src_csv_path", "src_csv_path")
    new_filename = kwargs.get("new_filename", "new_filename")
    if not os.path.exists(src_csv_path):
        print(f"Error: Source file does not exist: {src_csv_path}")
        return "FAIL"
    src_dir = os.path.dirname(src_csv_path)
    save_log_dir = os.path.join(src_dir, "save_log")
    os.makedirs(save_log_dir, exist_ok=True)
    dst_csv_path = os.path.join(save_log_dir, new_filename)
    shutil.copy2(src_csv_path, dst_csv_path)
    print(f"File copied to: {dst_csv_path}")
    return "OK"

def capture_error_screenshot(test_step, error_type="FAIL"):
    global LAST_INTERACTED_REGION  # <-- Kéo biến toàn cục vào
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img = ImageGrab.grab()
    draw = ImageDraw.Draw(img)

  
    try:
        if LAST_INTERACTED_REGION and isinstance(LAST_INTERACTED_REGION, dict):
            left = LAST_INTERACTED_REGION.get('left', 0)
            top = LAST_INTERACTED_REGION.get('top', 0)
            width = LAST_INTERACTED_REGION.get('width', 0)
            height = LAST_INTERACTED_REGION.get('height', 0)
            
            # Vẽ khung đỏ viền dày 4px
            if width > 0 and height > 0:
                draw.rectangle([left, top, left + width, top + height], outline="red", width=4)
    except Exception as e:
        print(f"Lỗi khi vẽ khung: {e}")


    ERROR_DIR = "Error_Screenshots"
    os.makedirs(ERROR_DIR, exist_ok=True)
    clean_name = str(test_step.testCaseName).replace(" ", "_").replace("/", "")
    file_path = f"{ERROR_DIR}/{error_type}_Step_{clean_name}_{timestamp}.png"
    img.save(file_path)

    # Chuyển ảnh sang Base64
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    return f"data:image/png;base64,{encoded_string}"


def generate_html_report(test_sequence, start_time, end_time, report_filename="Test_Report.html"):
    total = len([s for s in test_sequence.TestSequence if s.ignore != 'x'])
    passed = len([s for s in test_sequence.TestSequence if s.ignore != 'x' and getattr(s, 'testResult', False) == True])
    skipped = len([s for s in test_sequence.TestSequence if s.ignore == 'x'])
    executed = len([s for s in test_sequence.TestSequence if hasattr(s, 'actualValue') and s.ignore != 'x'])
    unexecuted = total - executed
    skipped += unexecuted
    failed = total - passed - skipped
    
    duration = round(end_time - start_time, 2)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Automation Test Report</title>
        <style>
            /* CSS gốc của bạn giữ nguyên */
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f8f9fa; }}
            h1 {{ color: #343a40; text-align: center; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }}
            .summary-container {{ display: flex; justify-content: space-around; margin-bottom: 20px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .stat-box {{ text-align: center; padding: 10px 20px; border-radius: 5px; color: white; font-weight: bold; min-width: 120px; }}
            .bg-total {{ background-color: #007bff; }}
            .bg-pass {{ background-color: #28a745; }}
            .bg-fail {{ background-color: #dc3545; }}
            .bg-skip {{ background-color: #6c757d; }}
            .bg-error {{ background-color: #fd7e14; }}
            table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-size: 14px; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; vertical-align: top; }}
            th {{ background-color: #343a40; color: white; position: sticky; top: 0; }}
            tr:hover {{ background-color: #f1f3f5; }}
            .row-pass {{ border-left: 5px solid #28a745; }}
            .row-fail {{ border-left: 5px solid #dc3545; background-color: #fff3f3; }}
            .row-error {{ border-left: 5px solid #fd7e14; background-color: #fff8f3; }}
            .row-skip {{ border-left: 5px solid #6c757d; color: #a0a0a0; }}
            .badge {{ padding: 5px 10px; border-radius: 20px; color: white; font-size: 12px; font-weight: bold; display: inline-block; text-align: center; min-width: 50px; }}
            .code-block {{ background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 8px; border-radius: 4px; font-family: monospace; font-size: 13px; color: #d63384; white-space: pre-wrap; word-wrap: break-word; max-width: 300px; display: block; }}
            
            /* CSS MỚI CHO POPUP ẢNH VÀ NÚT BẤM */
            .img-btn {{ background-color: white; color: #dc3545; font-weight: bold; padding: 5px 10px; border: 1px solid #dc3545; border-radius: 4px; cursor: pointer; transition: 0.2s; }}
            .img-btn:hover {{ background-color: #dc3545; color: white; }}
            .modal {{ display: none; position: fixed; z-index: 1000; padding-top: 40px; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.8); }}
            .modal-content {{ margin: auto; display: block; max-width: 95%; max-height: 90vh; border: 2px solid white; }}
            .close {{ position: absolute; top: 10px; right: 25px; color: white; font-size: 35px; font-weight: bold; cursor: pointer; }}
        </style>
    </head>
    <body>
        <h1>📊 Automation Test Report</h1>
        
        <div class="summary-container">
            <div><strong>Date:</strong> {now_str}</div>
            <div><strong>Duration:</strong> {duration} seconds</div>
        </div>

        <div class="summary-container">
            <div class="stat-box bg-total">Total<br><span style="font-size: 24px;">{total}</span></div>
            <div class="stat-box bg-pass">Pass<br><span style="font-size: 24px;">{passed}</span></div>
            <div class="stat-box bg-fail">Fail<br><span style="font-size: 24px;">{failed}</span></div>
            <div class="stat-box bg-skip">Skipped<br><span style="font-size: 24px;">{skipped}</span></div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Test Case</th>
                    <th>Action</th>
                    <th>Arguments</th>
                    <th>Expected</th>
                    <th>Actual / Error</th>
                    <th>Result</th>
                    <th>Evidence</th>
                </tr>
            </thead>
            <tbody>
    """

    for i, step in enumerate(test_sequence.TestSequence, 1):
        if step.ignore == 'x' or not hasattr(step, 'actualValue'):
            html += f"<tr class='row-skip'><td>{i}</td><td>{step.testCaseName}</td><td>{step.pythonMethod}</td><td>{getattr(step, 'inputArgs', '-')}</td><td>{step.equalValues}</td><td>-</td><td><span class='badge bg-skip'>SKIP</span></td><td>-</td></tr>"
            continue
            
        actual_val = getattr(step, 'actualValue', 'N/A')
        is_pass = getattr(step, 'testResult', False)
        is_sys_error = "System Error" in str(actual_val)
        
        if is_pass:
            row_class, badge_class, status_text = "row-pass", "bg-pass", "PASS"
            actual_display = actual_val
        elif is_sys_error:
            row_class, badge_class, status_text = "row-error", "bg-error", "ERROR"
            actual_display = f"<span class='code-block'>{actual_val}</span>" 
        else:
            row_class, badge_class, status_text = "row-fail", "bg-fail", "FAIL"
            actual_display = f"<span class='code-block' style='color:#dc3545;'>{actual_val}</span>"

        # LẤY ẢNH BASE64 VÀ GẮN VÀO NÚT BẤM
        error_img_b64 = getattr(step, 'error_screenshot_b64', '')
        if error_img_b64:
            evidence_html = f"<button class='img-btn' onclick='openModal(\"{error_img_b64}\")'>📷 View</button>"
        else:
            evidence_html = "-"

        input_args = getattr(step, 'inputArgs', '-')
        if input_args != '-': input_args = f"<span class='code-block' style='color:#0d6efd; border:none; background:transparent; padding:0;'>{input_args}</span>"

        html += f"""
            <tr class='{row_class}'>
                <td>{i}</td>
                <td>{step.testCaseName}</td>
                <td><strong>{step.pythonMethod}</strong></td>
                <td>{input_args}</td>
                <td>{step.equalValues}</td>
                <td>{actual_display}</td>
                <td><span class='badge {badge_class}'>{status_text}</span></td>
                <td>{evidence_html}</td>
            </tr>
        """
        

    html += """
            </tbody>
        </table>
        
        <div id="imageModal" class="modal">
            <span class="close" onclick="closeModal()">&times;</span>
            <img class="modal-content" id="modalImg">
        </div>

        <script>
            function openModal(base64Src) {
                document.getElementById('imageModal').style.display = "block";
                document.getElementById('modalImg').src = base64Src;
            }
            function closeModal() {
                document.getElementById('imageModal').style.display = "none";
            }
        </script>
    </body>
    </html>
    """
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(html)



if __name__ == '__main__':
    logger = TestLogger(loglevel='INFO', savelog='True', display = 'True')
    logger.info('This is an info')
    logger.warning('This is a warning')
    logger.error('This is an error')
    
    # loadSequenceObj = LoadSequence(ExcellPath="test_case/TN2.xlsx", sheetName="f6e_dl_bft_0822_1",logger=logger)
    loadSequenceObj = LoadSequence(ExcellPath="test_case/TN2.xlsx", sheetName="sgod",logger=logger)
    # loadSequenceObj = LoadSequence(ExcellPath="test_case/TN2.xlsx", sheetName="sbad",logger=logger)
    __testSequence = loadSequenceObj.LoadTestSequence()
    __testSequence.TestSequence[0].logger.info('This is an info =================================================================')
    act = MouseKeysControl(logger)
    
    ERROR_DIR = "Error_Screenshots"
    os.makedirs(ERROR_DIR, exist_ok=True)
    start_time = time.time()
    
    try:
        for testStep in __testSequence.TestSequence:
            if testStep.ignore == 'x':
                testStep.testResult = False
                continue
                
            resVal = None

            testStep.inputArgs = str(testStep.methodArg1).strip()
            

            try:
                arg_str = testStep.inputArgs.replace('\\', '\\\\')
                
     
                if not arg_str or arg_str.lower() in ['nan', 'none', '']:
                    pyCmd = "resVal = " + testStep.pythonMethod + "()"
                else:
                    pyCmd = "resVal = " + testStep.pythonMethod + "(" + arg_str + ")"
                

                exec(pyCmd)

            except Exception as e:
     
                error_msg = f"System Error: {type(e).__name__} - {str(e)}"
                logger.error(f"Execution Error: {error_msg}")
                b64_img = capture_error_screenshot(testStep, error_type="SYS_ERROR")
                testStep.error_screenshot_b64 = b64_img
                testStep.actualValue = error_msg
                testStep.testResult = False
                print(f"\n🛑 PHÁT HIỆN LỖI HỆ THỐNG: {error_msg}")
                break # <--- Lệnh này ngắt vòng lặp For
                

            testStep.actualValue = str(resVal)
            if testStep.equalValues in str(resVal):
                testStep.testResult = True
                logger.info(f"Test case: {testStep.testCaseName}, Step: {testStep.test_itemName} PASS")
            else:

                logger.error(f"Test case: {testStep.testCaseName}, Step: {testStep.test_itemName} FAIL (Actual: {resVal})")

                b64_img = capture_error_screenshot(testStep, error_type="FAIL")
                testStep.error_screenshot_b64 = b64_img
            
                print(f"\n🛑 TEST CASE '{testStep.testCaseName}' FAILED. (Thực tế: {resVal})")
                print("🛑 ĐANG DỪNG CHƯƠNG TRÌNH NGAY LẬP TỨC...")
                break 

   
            if testStep.ignore == 'sa':
                print("Copy and save new data")
                
    except KeyboardInterrupt:
        print("\n⚠️ Bạn đã chủ động dừng chương trình (Ctrl+C). Đang xuất báo cáo...")

    finally:
        end_time = time.time()
       
        loadSequenceObj.save_to_excel_file(__testSequence, "test_sequence/ddf_test_sequence3.xlsx")
        
     
        report_name = f"Test_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        generate_html_report(__testSequence, start_time, end_time, report_filename=report_name)
        
        print(f"\n✅ File HTML Report đã được tạo: {report_name}")
        print("--- KẾT THÚC CHƯƠNG TRÌNH ---")