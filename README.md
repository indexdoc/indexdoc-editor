# Markdown编辑器
一款专为技术写作打造的轻量化Markdown编辑器，支持实时预览，内置AI语法检查与格式优化能力，精准匹配技术文档创作需求；支持内容导出为Word、PDF、Markdown格式，可一键复制Markdown文本，同时兼容多格式文件导入（.docx、.xlsx、.xls、.ods、.csv、.tsv、.html、.mhtml、.htm、.pptx、.md）。

[![Python Version](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)  [![GitHub Stars](https://img.shields.io/github/stars/indexdoc/indexdoc-editor?style=social)](https://github.com/indexdoc/indexdoc-editor.git)

## ✨ 核心功能
- 🔍 **实时预览编辑**：轻量化Markdown编辑核心，边写边看渲染效果，技术写作即时校验排版
- 📤 **多格式导出**：支持将内容一键导出为Word、PDF、Markdown格式文件，满足多样输出需求
- 📋 **快捷复制**：支持一键复制Markdown原格式文本，方便跨平台粘贴使用
- 📥 **全类型导入**：兼容.docx、.xlsx、.xls、.ods、.csv、.tsv、.html、.mhtml、.htm、.pptx、.md多格式文件导入，内容迁移更高效

##  🚀快速开始

### 环境准备
- Python 3.10+、Tornado 6.0+、
- 浏览器：Chrome、Firefox、Edge等主流浏览器。

```bash
#克隆地址
https://github.com/indexdoc/indexdoc-editor.git
```
```bash
#快速安装依赖库
pip install -r requirements.txt

# 阿里镜像源
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 配置
### 后端核心配置（config.py）
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `port` | int | `50003` | 后端服务访问端口 |
| 路径配置 | string | - | 包含`html_path`（前端页面路径）、`tmp_path`（临时文件路径）、`rpt_path`（报表路径）、`user_file_path`（用户上传文件路径）、`log_path`（日志文件路径），程序启动时自动创建不存在的目录 |
### 启动服务
```bash
cd src  # 替换为server.py实际所在的文件夹路径
python.exe server.py
```
**访问地址**
 本地访问：`http://127.0.0.1:50003/public/cherry_markdown/markdown.html`



## 📝 使用示例
![主页1](https://github.com/indexdoc/indexdoc-editor/raw/main/mainPage.png)
#### 文字操作
![主页1](https://github.com/indexdoc/indexdoc-editor/raw/main/wordProcessing.png)
#### 图表操作
![主页1](https://github.com/indexdoc/indexdoc-editor/raw/main/chartActions.png)
#### 导出操作

#### 导入文件
**兼容.docx、.xlsx、.xls、.ods、.csv、.tsv、.html、.mhtml、.htm、.pptx、.md多格式文件导入**
![主页1](https://github.com/indexdoc/indexdoc-editor/raw/main/importFile.png)

## 📞 联系方式

- 作者：杭州智予数信息技术有限公司

- 邮箱：indexdoc@qq.com