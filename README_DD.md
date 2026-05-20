# Bosch Development Desktop App - Automated Testing Guide

Comprehensive automation testing solution specifically designed for the **Bosch Development Desktop Application** using computer vision and OCR technology.

## 📁 DD Test Region Files (JSON)

The following JSON region files have been created for Bosch Development Desktop (DD) Test automation:

### Core Interface Regions
- **`Landing_page.json`** - Main landing page UI elements
- **`home.json`** - Home screen navigation and controls
- **`ocr_Home.json`** - OCR-optimized home screen regions

### General Settings (GS) Modules
- **`GS.json`** - General Settings main interface
- **`GS_Config.json`** - General Settings Configuration panel
- **`GS_Dropdown.json`** - General Settings dropdown menus
- **`ddf_GS_Register.json`** - General Settings Register Access

### Application Features
- **`ddf_AS.json`** - App Settings interface
- **`ocr_AS.json`** - OCR-optimized App Settings
- **`ddf_EX.json`** - Export file functionality
- **`ddf_IF_Selection.json`** - Interface Selection controls
- **`ddf_Memo_map.json`** - Memory Map Interface
- **`ocr_Memo_map.json`** - OCR Memory Map regions

### Debug & Validation
- **`fail_OCR.json`** - Regions for OCR failure test cases

## � Project Structure

### Test Sequences
**Location**: `test_sequence/` folder
- Contains automation execution sequences
- Step-by-step test workflows
- Parameter configuration scripts

### Test Cases  
**Location**: `test_case/` folder
- Test scripts and scenarios
- Validation procedures
- Expected result definitions

## 🚀 Quick Start

1. **Select appropriate JSON regions** from the DD Test collection above
2. **Identify specific test sequences** from the `test_sequence/` folder for targeted actions
3. **Compile comprehensive test cases** by selecting and integrating multiple action sequences from `test_sequence/` into consolidated test scripts within the `test_case/` folder
4. **Execute automation** using `Auto_test_ddf.py`

## 🎯 Testing Coverage

The DD Test automation covers:
- **Interface Navigation** - All major UI sections
- **Settings Management** - Configuration and parameter control
- **Data Export** - File export and validation
- **Memory Operations** - Memory map access and verification
- **OCR Validation** - Text recognition across different UI contexts

---

**Streamlined automation testing for Bosch Development Desktop App!** 🚀