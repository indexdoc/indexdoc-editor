<div align="center">
  <div style="font-size: 15px; line-height: 2; padding: 4px 0; letter-spacing: 0.5px;">
    <strong style="color: #24292f;">English</strong>
    | <a href="README.md" style="color: #0969da; text-decoration: none;">简体中文</a>
    | <a href="https://www.indexdoc.com/webapp/?tab=markdown&page=.%2Fcherry_markdown%2Fmarkdown.html" target="_blank" style="color: #165DFF; font-weight: 600; text-decoration: none;">✨ onlineDemo</a>
  </div>
</div>
  <div style="font-size: 14px; color: #57606a; padding: 2px 0; text-align: left;">
    <span style="background: #f6f8fa; padding: 2px 8px; border-radius: 4px; font-size: 13px;">Core Repos</span><br/>
    <a href="https://github.com/indexdoc/indexdoc-batch-generator" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-batch-generator（Batch Document Assistant）</a><br/>
    <a href="https://github.com/indexdoc/indexdoc-model-to-code" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-model-to-code（Code Generator / CodeAsst）</a><br/>
    <a href="https://github.com/indexdoc/indexdoc-ai-offline" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-ai-offline（Local Document AI Assistant）</a><br/>
    <a href="https://github.com/indexdoc/indexdoc-converter" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-converter（File Converter）</a><br/>
    <a href="https://github.com/indexdoc/indexdoc-vector" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-vector（Vector Database）</a><br/>
  </div>


---
# indexdoc-editor
A lightweight Markdown editor specifically designed for technical writing, **supporting both desktop (Windows) and web versions** with real-time preview to precisely meet the needs of technical documentation creation. It allows exporting content to Word, PDF, and Markdown formats, one-click copying of Markdown text, and supports importing files in multiple formats ( ** .docx、.xlsx、.xls、.ods、.csv、.tsv、.html、.mhtml、.htm、.pptx、.md ** ).

[![Python Version](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)  [![GitHub Stars](https://img.shields.io/github/stars/indexdoc/indexdoc-editor?style=social)](https://github.com/indexdoc/indexdoc-editor.git)  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Core Features
- 🔍 **Real-time Preview & Editing**: Lightweight Markdown editing core with side-by-side rendering preview, enabling instant format verification for technical writing
- 💻 **Multi-end Support**: Provides both **desktop (Windows)** and web versions, covering local offline and online collaboration scenarios
- 📤 **Multi-format Export**: One-click export of content to Word, PDF, and Markdown files to meet diverse output requirements
- 📋 **Quick Copy**: One-click copying of raw Markdown text for cross-platform pasting
- 📥 **Full-type Import**: Compatible with importing files in .docx、.xlsx、.xls、.ods、.csv、.tsv、.html、.mhtml、.htm、.pptx、.md formats for efficient content migration

##  🚀 Quick Start

### Environment Preparation
- Python 3.10+, Tornado 6.0+
- Browsers: Chrome, Firefox, Edge, and other mainstream browsers

```bash
# Clone repository
https://github.com/indexdoc/indexdoc-editor.git
```
```bash
# Install dependencies quickly
pip install -r requirements.txt

# Aliyun PyPI mirror
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### Install pandoc (Windows) for Word Export
1. Open the official pandoc download page: https://github.com/jgm/pandoc/releases/latest
2. Find the installer named pandoc-x.x.x-windows-x86_64.msi (x.x.x is the latest version number) and click to download
3. Double-click the downloaded msi file and click "Next" throughout the installation. It is recommended to check "Add pandoc to the system PATH for all users" (automatically configures environment variables; manual configuration is required if unchecked)

### Install wkhtmltopdf (Windows) for PDF Export
Official unified download address: https://github.com/wkhtmltopdf/packaging/releases (Official GitHub Releases)

1. Select and download the installer
Open the official Releases page, find the Windows version corresponding to your system:
- 64-bit systems (most computers): Download the file named wkhtmltox-x.x.x_msvc2015-win64.exe (x.x.x is the latest version number)
- 32-bit systems (older computers): Download the file named wkhtmltox-x.x.x_msvc2015-win32.exe

2. Install and configure environment variables automatically
Double-click the downloaded exe installer and click "Next" throughout;
Critical step: The installation interface will have an option "Add to PATH" (or "Add application directory to your system PATH") – **make sure to check it** (usually checked by default, just confirm);
Select the installation path (default C drive is recommended, no need to modify), then click "Install" to complete installation.

3. Verify installation
```bash
  wkhtmltopdf --version
```

### Configuration
##### Web Service Configuration (config.py)
| Configuration Item | Type | Default Value | Description |
|--------|------|--------|------|
| `port` | int | `50003` | Backend service access port |
| Path Configuration | string | - | Includes `html_path` (frontend page path), `tmp_path` (temporary file path), `rpt_path` (report path), `user_file_path` (user uploaded file path), `log_path` (log file path). Non-existent directories are automatically created on program startup |

##### Desktop Service Configuration (client_config.py)
| Configuration Item | Type | Default Value | Description |
|--------|------|--------|------|
| `port` | int | `50001` | Backend service access port |
| `base_path` | string | Dynamically obtained by `frozen_support.get_base_path()` | Project root path; all path configurations are concatenated based on this path |
| `html_path` | string | `base_path + '/html'` | Root path for frontend HTML files |
| `template_path` | string | `base_path + '/template'` | Storage path for template files |
| `tmp_path` | string | `base_path + '/tmp'` | Storage path for temporary files |
| `log_path` | string | `base_path + '/log'` | Storage path for log files; automatically created if the path does not exist |

** Note: The configuration and operation of the web version and desktop version are independent of each other. Incorrect configuration of the web version does not affect the operation of the desktop version, and vice versa. **

### Start Service
##### Start Web Version
```bash
cd src  # Replace with the actual folder path of server.py
python.exe server.py
```

##### Start Desktop Version
```bash
cd src_client  # Replace with the actual folder path of client_start.py
python.exe client_start.py

# In the client_start.py file, debug mode is enabled by default
webview.start(debug=True) #debug=False to disable debug mode
```

**Access Address**
- Web version local access: `http://127.0.0.1:50003/public/cherry_markdown/markdown.html`
- Desktop version: Simply run client_start.py

## 📝 Usage Examples
###  Web Version Usage Examples
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/mainPage.png)
#### Text Operations
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/wordProcessing.png)
#### Chart Operations
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/chartActions.png)
#### File Import
**Compatible with importing files in .docx、.xlsx、.xls、.ods、.csv、.tsv、.html、.mhtml、.htm、.pptx、.md formats**
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/importFile.png)

###  Desktop Version Usage Examples
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/clientMainPage.png)

## 📞 Contact Information
- Author: Hangzhou Zhiyushu Information Technology Co., Ltd.
- Email: indexdoc@qq.com
