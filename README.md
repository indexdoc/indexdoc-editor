<div align="center">
  <div style="font-size: 15px; line-height: 2; padding: 4px 0; letter-spacing: 0.5px;">
    <strong style="color: #24292f;">简体中文</strong> 
    | <a href="README_EN.md" style="color: #0969da; text-decoration: none;">English</a>
    | <a href="https://www.indexdoc.com/webapp/?tab=markdown&page=.%2Fcherry_markdown%2Fmarkdown.html" target="_blank" style="color: #165DFF; font-weight: 600; text-decoration: none;">✨ 在线Demo</a>
  </div>
</div>
  <div style="font-size: 14px; color: #57606a; padding: 2px 0; text-align: left;">
    <span style="background: #f6f8fa; padding: 2px 8px; border-radius: 4px; font-size: 13px;">核心仓库</span><br/>
    <a href="https://github.com/indexdoc/indexdoc-batch-generator" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-batch-generator（批量文档助手）</a><br/>
    <a href="https://github.com/indexdoc/indexdoc-model-to-code" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-model-to-code（代码生成器 / CodeAsst）</a><br/>
    <a href="https://github.com/indexdoc/indexdoc-ai-offline" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-ai-offline（本地文档AI助手）</a><br/>
    <a href="https://github.com/indexdoc/indexdoc-converter" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-converter（文档转换器）</a><br/>
    <a href="https://github.com/indexdoc/indexdoc-vector" target="_blank" style="color: #0969da; text-decoration: none; margin: 0 6px;">indexdoc-vector（向量数据库）</a><br/>
  </div>
---

# indexdoc-editor
一款专为技术写作打造的轻量化Markdown编辑器，**同时支持客户端(Windows)与网页端**，支持实时预览，精准匹配技术文档创作需求；支持内容导出为Word、PDF、Markdown格式，可一键复制Markdown文本，同时兼容多格式文件导入
（**.docx、.xlsx、.xls、.ods、.csv、.tsv、.html、.mhtml、.htm、.pptx、.md** ）。

[![Python Version](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)  [![GitHub Stars](https://img.shields.io/github/stars/indexdoc/indexdoc-editor?style=social)](https://github.com/indexdoc/indexdoc-editor.git) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 核心功能
- 🔍 **实时预览编辑**：轻量化Markdown编辑核心，边写边看渲染效果，技术写作即时校验排版
- 💻 **多端支持**：同时提供**客户端(Windows)**与**网页版**，本地离线与在线协作场景全覆盖
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

### 安装导出 Word文档所需要的工具 pandoc(Windows系统)
1、打开 pandoc 官方下载页：https://github.com/jgm/pandoc/releases/latest
2、找到以 pandoc-x.x.x-windows-x86_64.msi 命名的安装包下载（注意配置环境变量）；

### 安装导出 Pdf文档所需要的工具 wkhtmltopdf(Windows系统)
官方下载地址统一：https://github.com/wkhtmltopdf/packaging/releases 官方 GitHub Releases

1、选择并下载安装包
打开官方 Releases 页，找到Windows对应版本，根据自己的系统选择：
如：64 位系统：下载命名为 wkhtmltox-x.x.x_msvc2015-win64.exe 的文件；

2、安装.exe文件并自动配置环境变量

3、验证安装
```bash
  wkhtmltopdf --version
```

### 配置
##### 网页端服务配置（config.py）
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `port` | int | `50003` | 后端服务访问端口 |
| 路径配置 | string | - | 包含`html_path`（前端页面路径）、`tmp_path`（临时文件路径）、`rpt_path`（报表路径）、`user_file_path`（用户上传文件路径）、`log_path`（日志文件路径），程序启动时自动创建不存在的目录 |

##### 客户端服务配置（client_config.py）
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `port` | int | `50001` | 后端服务访问端口 |
| `base_path` | string | 由`frozen_support.get_base_path()`动态获取 | 项目基础根路径，所有路径配置均基于此路径拼接 |
| `html_path` | string | `base_path + '/html'` | 前端HTML文件根路径 |
| `template_path` | string | `base_path + '/template'` | 模板文件存储路径 |
| `tmp_path` | string | `base_path + '/tmp'` | 临时文件存储路径 |
| `log_path` | string | `base_path + '/log'` | 日志文件存储路径，若路径不存在会自动创建 |

 ** 注意：网页端和服端的配置和运行相互独立，如 网页端配置未正确不影响客户端运行，反之亦然。 **
### 启动服务
##### 网页端启动
```bash
cd src  # 替换为server.py实际所在的文件夹路径
python.exe server.py
```

##### 客户端启动
```bash
cd src_client  # 替换为client_start.py实际所在的文件夹路径
python.exe client_start.py

# 在client_start.py文件中，默认打开调试模式
webview.start(debug=True) #debug=False 关闭调试模式
```

**访问地址**
 网页端本地访问：`http://127.0.0.1:50003/public/cherry_markdown/markdown.html`
 客户端： 运行client_start.py 即可

## 📝 使用示例
###  网页端使用示例
![主页1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/mainPage.png)
#### 文字操作
![主页1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/wordProcessing.png)
#### 图表操作
![主页1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/chartActions.png)
#### 导入文件
**兼容.docx、.xlsx、.xls、.ods、.csv、.tsv、.html、.mhtml、.htm、.pptx、.md多格式文件导入**
![主页1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/importFile.png)

###  客户端使用示例
![主页1](https://github.com/indexdoc/indexdoc-editor/raw/main/README/clientMainPage.png)
## 📞 联系方式

- 作者：杭州智予数信息技术有限公司

- 邮箱：indexdoc@qq.com
