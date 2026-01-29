<div align="center">
  <strong>English</strong> | <a href="README.md">简体中文</a>
</div>

---
# Markdown Editor
A lightweight Markdown editor tailored for technical writing, featuring real-time preview, formating optimization capabilities that precisely meet the needs of technical document creation. It supports exporting content to Word, PDF, and Markdown formats, one-click copying of Markdown text, and is compatible with importing files in multiple formats (.docx, .xlsx, .xls, .ods, .csv, .tsv, .html, .mhtml, .htm, .pptx, .md).

[![Python Version](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)  [![GitHub Stars](https://img.shields.io/github/stars/indexdoc/indexdoc-editor?style=social)](https://github.com/indexdoc/indexdoc-editor.git)

## ✨ Core Features
- 🔍 **Real-time Preview & Editing**: Lightweight core Markdown editing with side-by-side rendering previews for instant typesetting verification during technical writing
- 📤 **Multi-format Export**: One-click export of content to Word, PDF and Markdown files to meet diverse output requirements
- 📋 **One-click Copy**: Instant copying of raw Markdown text for cross-platform pasting and usage
- 📥 **Multi-type Import**: Compatible with importing files in .docx, .xlsx, .xls, .ods, .csv, .tsv, .html, .mhtml, .htm, .pptx and .md formats for efficient content migration

## 🚀 Quick Start

### Environment Preparation
- Python 3.10+, Tornado 6.0+
- Browsers: Chrome, Firefox, Edge and other mainstream browsers

```bash
# Clone the repository
https://github.com/indexdoc/indexdoc-editor.git
```
```bash
# Install dependencies quickly
pip install -r requirements.txt

# Use Alibaba Cloud PyPI mirror (faster installation)
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### Install pandoc (Windows) - Required for Word Export
1. Visit the official pandoc download page: https://github.com/jgm/pandoc/releases/latest
2. Locate the installer named `pandoc-x.x.x-windows-x86_64.msi` (x.x.x refers to the latest version number) and click to download
3. Double-click the downloaded MSI file and follow the **Next** prompts; it is recommended to check **Add pandoc to the system PATH for all users** (automatically configures environment variables, manual configuration required if unchecked)

### Install wkhtmltopdf (Windows) - Required for PDF Export
Official unified download address: https://github.com/wkhtmltopdf/packaging/releases (Official GitHub Releases)

1. Select and download the installer
   Open the official Releases page, find the Windows version and select according to your system:
   - 64-bit systems (most computers): Download the file named `wkhtmltox-x.x.x_msvc2015-win64.exe` (x.x.x is the latest version number)
   - 32-bit systems (older computers): Download `wkhtmltox-x.x.x_msvc2015-win32.exe`

2. Install and configure environment variables automatically
   Double-click the downloaded EXE installer and follow the **Next** prompts
   **Critical step**: Check the option for **Add to PATH** (or **Add application directory to your system PATH**) during installation (usually checked by default, just confirm)
   Select the installation path (default C drive is recommended, no modification needed) and click **Install** to complete the installation

3. Verify the installation
```bash
wkhtmltopdf --version
```

### Configuration (config.py)

| Configuration Item | Type | Default Value | Description |
|--------------------|------|---------------|-------------|
| `port` | int | `50003` | Backend service access port |
| Path Configuration | string | - | Includes `html_path` (frontend page path), `tmp_path` (temporary file path), `rpt_path` (report path), `user_file_path` (user uploaded file path), `log_path` (log file path). The program automatically creates non-existent directories on startup |

### Start the Service
```bash
cd src  # Replace with the actual folder path where server.py is located
python.exe server.py
```
**Access Address**
Local access: `http://127.0.0.1:50003/public/cherry_markdown/markdown.html`

## 📝 Usage Examples
![Main Page](https://github.com/indexdoc/indexdoc-editor/raw/main/mainPage.png)
#### Text Operations
![Text Operations](https://github.com/indexdoc/indexdoc-editor/raw/main/wordProcessing.png)
#### Chart Operations
![Chart Operations](https://github.com/indexdoc/indexdoc-editor/raw/main/chartActions.png)
#### File Import
**Compatible with importing .docx, .xlsx, .xls, .ods, .csv, .tsv, .html, .mhtml, .htm, .pptx and .md files**
![File Import](https://github.com/indexdoc/indexdoc-editor/raw/main/importFile.png)

## 📞 Contact Us
- Author: Hangzhou Zhiyu Shu Information Technology Co., Ltd.
- Email: indexdoc@qq.com
