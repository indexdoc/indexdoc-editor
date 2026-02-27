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
A lightweight Markdown editor specifically designed for technical writing, **supporting both desktop (Windows) and web versions** simultaneously. It features real-time preview to precisely meet technical documentation creation needs; supports exporting content to Word, PDF, and Markdown formats, allows one-click copying of Markdown text, and is compatible with importing files in multiple formats
（**.docx、.xlsx、.xls、.ods、.csv、.tsv、.html、.mhtml、.htm、.pptx、.md** ）.

[![Python Version](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)  [![GitHub Stars](https://img.shields.io/github/stars/indexdoc/indexdoc-editor?style=social)](https://github.com/indexdoc/indexdoc-editor.git) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Core Features
- 🔍 **Real-time Preview & Editing**: Lightweight Markdown editing core with side-by-side editing and rendering, enabling instant formatting verification for technical writing
- 💻 **Cross-platform Support**: Offers both **desktop (Windows)** and **web versions**, covering both offline local use and online collaboration scenarios
- 📤 **Multi-format Export**: One-click export of content to Word, PDF, and Markdown files to meet diverse output requirements
- 📋 **Quick Copy**: One-click copying of Markdown text in its original format for easy cross-platform pasting
- 📥 **Full-featured Import**: Compatible with importing files in .docx, .xlsx, .xls, .ods, .csv, .tsv, .html, .mhtml, .htm, .pptx, .md formats for efficient content migration

## 🚀 Quick Start

### Environment Preparation
- Python 3.10+, Tornado 6.0+
- Browser: Chrome, Firefox, Edge, or other mainstream browsers

```bash
# Clone repository
https://github.com/indexdoc/indexdoc-editor.git
```
```bash
# Install dependencies quickly
pip install -r requirements.txt

# Using Alibaba PyPI mirror (faster in China)
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### Install pandoc (Windows) for Word Export
1. Open the official pandoc download page: https://github.com/jgm/pandoc/releases/latest
2. Download the installer named pandoc-x.x.x-windows-x86_64.msi (ensure to configure environment variables after installation);

### Install wkhtmltopdf (Windows) for PDF Export
Official unified download address: https://github.com/wkhtmltopdf/packaging/releases (Official GitHub Releases)

1. Select and download the installer
   Open the official Releases page, find the version for Windows, and choose according to your system:
   For 64-bit systems: Download the file named wkhtmltox-x.x.x_msvc2015-win64.exe;

2. Install the .exe file and configure environment variables automatically

3. Verify installation
```bash
  wkhtmltopdf --version
```

### Configuration
##### Web Version Service Configuration (config.py)
| Configuration Item | Type | Default Value | Description |
|--------------------|------|---------------|-------------|
| `port` | int | `50003` | Backend service access port |
| Path Configuration | string | - | Includes `html_path` (frontend page path), `tmp_path` (temporary file path), `rpt_path` (report path), `user_file_path` (user uploaded file path), `log_path` (log file path). Non-existent directories are created automatically when the program starts |

##### Desktop Version Service Configuration (client_config.py)
| Configuration Item | Type | Default Value | Description |
|--------------------|------|---------------|-------------|
| `port` | int | `50001` | Backend service access port |
| `base_path` | string | Dynamically obtained by `frozen_support.get_base_path()` | Project base root path, all path configurations are concatenated based on this path |
| `html_path` | string | `base_path + '/html'` | Root path for frontend HTML files |
| `template_path` | string | `base_path + '/template'` | Storage path for template files |
| `tmp_path` | string | `base_path + '/tmp'` | Storage path for temporary files |
| `log_path` | string | `base_path + '/log'` | Storage path for log files, created automatically if non-existent |

**Note**: The configuration and operation of the web version and desktop version are independent of each other. Incorrect configuration of the web version does not affect the operation of the desktop version, and vice versa.

### Start the Service
##### Start Web Version
```bash
cd src  # Replace with the actual folder path where server.py is located
python.exe server.py
```

##### Start Desktop Version
```bash
cd src_client  # Replace with the actual folder path where client_start.py is located
python.exe client_start.py

# Debug mode is enabled by default in client_start.py
webview.start(debug=True) # Set to debug=False to disable debug mode
```

**Access Address**
- Web Version (local access): `http://127.0.0.1:50003/public/cherry_markdown/markdown.html`
- Desktop Version: Simply run client_start.py

## 📝 Usage Examples
### Web Version Usage Examples
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/mainPage.png)
#### Text Operations
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/wordProcessing.png)
#### Chart Operations
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/chartActions.png)
#### File Import
**Compatible with importing files in .docx, .xlsx, .xls, .ods, .csv, .tsv, .html, .mhtml, .htm, .pptx, .md formats**
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/importFile.png)

### Desktop Version Usage Examples
![Main Page 1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/clientMainPage.png)

## 📞 Contact Information
- Author: Hangzhou Zhiyu Shu Information Technology Co., Ltd.
- Email: indexdoc@qq.com

---
