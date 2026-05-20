# Auto Test GUI - Automated Desktop Application Testing

## 🎯 What Does This Do?

This tool automatically tests desktop applications by:
- **👀 Looking at your screen** and finding buttons, dropdowns, and text fields
- **📖 Reading text** from the application (even when it changes colors or backgrounds)  
- **🖱️ Clicking buttons** and selecting menu options automatically
- **⌨️ Typing text** into forms and input fields
- **📊 Comparing results** with expected values to verify everything works correctly
- **📋 Running test sequences** from Excel spreadsheets with hundreds of test steps

## 🚀 Perfect For

- **QA Teams**: Automate repetitive testing tasks
- **Software Developers**: Regression testing for desktop applications
- **System Administrators**: Automated configuration and validation
- **Anyone**: Who needs to repeatedly interact with desktop software

## ✨ Key Features

### 🎮 Human-like Interactions  
- **Clicks buttons** and menu items precisely
- **Selects dropdown options** by reading and choosing the right value
- **Types text** with proper timing and special character handling
- **Scrolls through long lists** to find specific items
- **Handles dynamic content** that changes position or appearance

### 📈 Excel-Driven Testing
- **Load test cases** from Excel spreadsheets
- **Run hundreds of test steps** automatically
- **Compare actual vs expected results**
- **Generate detailed reports** with pass/fail status
- **Save results** back to Excel for analysis

## 🎬 How It Works

### 1. **Define What to Test**
Begin by analyzing your manual test procedures to identify GUI elements requiring automation. The system supports various interaction types including click operations, scrolling, text selection, input validation, image comparison, and dropdown selection. 

Using the integrated `lable_image.py` utility, visually map and define screen regions by drawing precise boundaries around target elements. The tool captures coordinate data and generates structured JSON configuration files for each defined area. Save your region definitions using 'Ctrl+S' to preserve the mapping data.

Reference the `test_sequence/ddf_test_sequence_test.xlsx` template to understand how automation scripts correlate with your newly created JSON region files, ensuring proper integration between visual mapping and test execution workflows.

### 2. **Create Test Scenarios**
Leverage the JSON region definitions and `test_sequence/ddf_test_sequence_test.xlsx` template to construct comprehensive automation test scripts. Systematically arrange and sequence the test operations to create a complete end-to-end testing workflow.

The Excel template provides the structural framework for organizing test steps, while the JSON files supply the precise coordinate mappings for GUI element interactions. Customize the sequence order, add conditional logic, and integrate validation checkpoints to build robust automated test scenarios that mirror your manual testing procedures.

### 3. **Run and Relax**
Run `Auto_test_ddf.py` and the tool takes over:
- Opens your application
- Performs all the clicks, selections, and typing
- Reads the results from the screen  
- Reports what passed or failed in `test_sequence/ddf_test_sequence3.xlsx`

## 🚀 Getting Started

### What You Need
- Windows computer
- Python --version<3.10 installed
- Install all required tools and libraries from `requirement.txt`
- The desktop application you want to test
- 30 minutes to set up your first test

### Quick Setup
1. **Install the tool** (one-time setup)
2. **Take screenshots** of your application to define test areas
3. **Create an Excel file** with your test steps
4. **Run your first automated test**

### Example Test Sequence
```
Step 1: Click "Settings" button
Step 2: Select "Advanced" from dropdown  
Step 3: Type "CONFIG_123" in text field
Step 4: Click "Apply"
Step 5: Verify "Configuration Saved" message appears
```

## 📞 Support

- Check the `image_log/` folder to see what the tool detected
- Review `save_log/` folder for detailed test execution logs
- Update screen coordinates if your application layout changes

---

