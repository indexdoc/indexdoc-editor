# -*- coding: utf-8 -*-
"""
str2docx 和 file2docx
使用 Pandoc 将 Markdown 字符串或文件转换为 .docx
Pandoc 路径从环境变量获取，支持跨平台
"""

import subprocess
import os
import sys
import tempfile
from pathlib import Path
import platform
import logging
# 图片 DPI
DEFAULT_DPI = int(os.getenv("PANDOC_DPI", "150"))
# -------------------------------
# 配置：从环境变量获取 Pandoc 路径
# -------------------------------

def _find_pandoc_path():
    """查找 Pandoc 可执行文件路径"""
    # 1. 优先从环境变量读取
    # env_path = os.getenv("PANDOC_EXECUTABLE")
    # if env_path and os.path.exists(env_path):
    #     return env_path

    # 2. 根据操作系统推断默认名称
    # current_path = Path(__file__)
    exe_name = "pandoc.exe" if platform.system() == "Windows" else "pandoc"

    # 3. 检查当前目录的 bin/ 子目录
    local_path = Path(__file__).parent / "pandoc-bin" / exe_name
    if local_path.exists():
        return str(local_path)

    # 4. 检查系统 PATH 环境变量（全局安装的 pandoc）
    if shutil.which(exe_name):
        return exe_name

    # 5. 都找不到
    logging.error("无法找到pandoc.exe文件")
    return None


# 尝试导入 shutil（用于 which）
import shutil

# 全局变量：Pandoc 路径
PANDOC_PATH = _find_pandoc_path()
# 当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.join(BASE_DIR, "docx_template", "Normal-zh.docx")
# PDF_ENGINE_PATH = os.path.join(BASE_DIR, "wkhtmltox-bin", "wkhtmltopdf.exe")
PDF_ENGINE_PATH = os.path.join(BASE_DIR, "weasyprint-bin", "weasyprint.exe")


def _run_pandoc(cmd_args, input_data=None):
    """
    内部函数：执行 pandoc 命令
    """
    # 新增：设置隐藏窗口的参数（仅Windows系统）
    kwargs = {}
    if platform.system() == "Windows":
        # 隐藏子进程的控制台窗口
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    if PANDOC_PATH is None:
        logging.error('没有可用的pandoc.exe文件')
        return False
    cmd = [PANDOC_PATH] + cmd_args

    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            **kwargs  # 传入隐藏窗口参数
        )

        if result.returncode == 0:
            return True
        else:
            error = result.stderr.decode('utf-8', errors='replace')
            logging.debug(f"❌ Pandoc 错误 (返回码 {result.returncode}):")
            logging.debug(error)
            return False

    except Exception as e:
        logging.error(f"❌ 执行 Pandoc 时出错: {str(e)}")
        return False


def _run_weasyprint(html_content: str, output_pdf: str):
    """
    使用 weasyprint.exe 将 HTML 字符串转换为 PDF 文件
    html_content: HTML 字符串内容
    output_pdf: 输出 PDF 文件路径
    """
    if not os.path.exists(PDF_ENGINE_PATH):
        logging.error("❌ 找不到 weasyprint.exe 文件，请检查路径是否正确")
        return False

    # 创建临时 HTML 文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_html:
        tmp_html.write(html_content)
        tmp_html_path = tmp_html.name

    cmd = [PDF_ENGINE_PATH, tmp_html_path, output_pdf]

    # 隐藏命令窗口（仅限 Windows）
    kwargs = {}
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            **kwargs
        )

        # 删除临时文件
        os.remove(tmp_html_path)

        if result.returncode == 0:
            logging.info(f"✅ PDF 生成成功：{output_pdf}")
            return True
        else:
            error = result.stderr.decode("utf-8", errors="replace")
            logging.error(f"❌ WeasyPrint 错误（返回码 {result.returncode}）:")
            logging.error(error)
            return False

    except Exception as e:
        logging.error(f"❌ 执行 WeasyPrint 时出错: {str(e)}")
        return False

def str2docx(
        markdown_str,
        output_docx,
        template=DEFAULT_TEMPLATE,
        dpi=DEFAULT_DPI,
        extract_media=None
):
    """
    将 Markdown 字符串转换为 .docx 文件

    :param markdown_str: Markdown 格式的字符串
    :param output_docx: 输出的 .docx 文件路径
    :param template: Word 模板路径（.docx），用于控制样式
    :param dpi: 图片 DPI
    :param extract_media: 媒体文件输出目录（可选）
    :return: bool 是否成功
    """
    if not isinstance(markdown_str, str):
        logging.error("markdown_str 必须是字符串")
        return False

    # 确保输出目录存在
    Path(output_docx).parent.mkdir(parents=True, exist_ok=True)

    # 构建命令
    cmd = [
        '-', '--to', 'docx', '--output', output_docx,
        '--standalone', f'--dpi={dpi}',
        '--wrap=preserve',
        '--highlight-style=pygments'
    ]

    # 添加模板（如果存在）
    if template and os.path.exists(template):
        cmd.extend(['--reference-doc', template])
    elif template:
        logging.warning(f"模板文件不存在{template}: ")
        if DEFAULT_TEMPLATE and os.path.exists(DEFAULT_TEMPLATE):
            logging.warning(f"使用默认模板文件：{DEFAULT_TEMPLATE} ")

    # 添加媒体提取
    if extract_media:
        Path(extract_media).mkdir(parents=True, exist_ok=True)
        cmd.extend(['--extract-media', extract_media])

    logging.debug(f"正在将字符串转换为: {output_docx}")
    success = _run_pandoc(cmd, input_data=markdown_str.encode('utf-8'))

    if success:
        logging.info(f"成功生成: {output_docx}")
    return success


def file2docx(
        md_file_path,
        output_docx,
        template=DEFAULT_TEMPLATE,
        dpi=DEFAULT_DPI,
        extract_media=None
):
    """
    将 Markdown 文件转换为 .docx（内部调用 str2docx）
    """
    # 1. 检查文件是否存在
    if not os.path.exists(md_file_path):
        logging.error(f"找不到 Markdown 文件: {md_file_path}")
        return False

    # 2. 读取文件内容（UTF-8 编码）
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            markdown_str = f.read()
    except Exception as e:
        logging.error(f"读取文件失败: {md_file_path} - {str(e)}")
        return False

    # 3. 复用 str2docx 的核心逻辑
    return str2docx(
        markdown_str=markdown_str,
        output_docx=output_docx,
        template=template,
        dpi=dpi,
        extract_media=extract_media
    )


# wkhtmltopdf
def html2pdf(
        html_str,
        output_pdf,
):
    """
    将 HTML 字符串转换为 PDF 文件

    :param html_str: HTML 内容（字符串）
    :param output_pdf: 输出 PDF 文件路径
    :param pdf_engine: PDF 引擎（默认 wkhtmltopdf）
    :param margin: 页面边距
    :param dpi: 输出分辨率
    :return: bool 是否成功
    """
    if not isinstance(html_str, str):
        logging.error("html_str 必须是字符串")
        return False

    Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)

    # ==== 动态设置 PDF 引擎 ====
    pdf_engine = PDF_ENGINE_PATH if PDF_ENGINE_PATH else "wkhtmltopdf"

    cmd = [
        "-",
        "--from", "html",
        "--to", "pdf",
        "--output", output_pdf,
        "--standalone",
        "--pdf-engine", pdf_engine
    ]

    logging.info(f"📄 使用 PDF 引擎: {pdf_engine}")
    success = _run_pandoc(cmd, input_data=html_str.encode("utf-8"))

    if success:
        logging.info(f"✅ 成功生成 PDF: {output_pdf}")
    return success


DEFAULT_MD_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "md_template", "template.md")
def str2md(
        markdown_str,
        output_md,
        template=DEFAULT_MD_TEMPLATE
):
    """
    将 Markdown 字符串保存为 .md 文件

    :param markdown_str: Markdown 格式的字符串
    :param output_md: 输出的 .md 文件路径
    :param template: 模板路径（.md），用于附加到最终文件（可选）
    :return: bool 是否成功
    """
    if not isinstance(markdown_str, str):
        logging.error("markdown_str 必须是字符串")
        return False

    # 确保输出目录存在
    Path(output_md).parent.mkdir(parents=True, exist_ok=True)

    # 如果有模板文件，将模板内容加入
    if template and os.path.exists(template):
        try:
            with open(template, 'r', encoding='utf-8') as tmpl_file:
                template_content = tmpl_file.read()
                # 在原始 Markdown 内容前加上模板内容
                markdown_str = template_content + "\n\n" + markdown_str
        except Exception as e:
            logging.error(f"读取模板文件失败: {str(e)}")
            return False

    try:
        # 将 markdown_str 保存到 output_md 文件
        with open(output_md, 'w', encoding='utf-8') as md_file:
            md_file.write(markdown_str)
        logging.info(f"成功生成 Markdown 文件: {output_md}")
        return True
    except Exception as e:
        logging.error(f"写入文件失败: {str(e)}")
        return False


# ======================================
# 使用示例
# ======================================

if __name__ == "__main__":
    logging.debug(f"使用的 Pandoc 路径: {PANDOC_PATH}")
    if not PANDOC_PATH:
        sys.exit(1)

    # # 示例 1: 字符串转 docx
    # md_content = """
    #     # 项目报告
    #     这是一个测试文档。
    # """
    #
    # str2docx(
    #     markdown_str=md_content,
    #     output_docx="output/from_string2.docx"
    # )

    # 示例 2: 文件转 docx
    # file2docx(
    #     md_file_path="Mermaid.md",
    #     output_docx="output/from_file.docx",
    #     template = "docx_template/Normal-zh-编号.docx"
    # )

    # # 示例 3: html转 pdf
    # html = "<h1>测试标题</h1><p>这是 HTML 转 PDF 示例。</p>"
    # html2pdf(html, "output/test.pdf")
    #
    # 示例 3: html转 pdf
    html = '<svg xmlns="http://www.w3.org/2000/svg" id="tempMermaid_1761640976942mlp0rhob6f" width="100%" class="flowchart" style="overflow: visible;" viewBox="0 0 710.4296875 180.4375" role="graphics-document document" aria-roledescription="flowchart-v2"><style>#tempMermaid_1761640976942mlp0rhob6f{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#333;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#tempMermaid_1761640976942mlp0rhob6f .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#tempMermaid_1761640976942mlp0rhob6f .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#tempMermaid_1761640976942mlp0rhob6f .error-icon{fill:#552222;}#tempMermaid_1761640976942mlp0rhob6f .error-text{fill:#552222;stroke:#552222;}#tempMermaid_1761640976942mlp0rhob6f .edge-thickness-normal{stroke-width:1px;}#tempMermaid_1761640976942mlp0rhob6f .edge-thickness-thick{stroke-width:3.5px;}#tempMermaid_1761640976942mlp0rhob6f .edge-pattern-solid{stroke-dasharray:0;}#tempMermaid_1761640976942mlp0rhob6f .edge-thickness-invisible{stroke-width:0;fill:none;}#tempMermaid_1761640976942mlp0rhob6f .edge-pattern-dashed{stroke-dasharray:3;}#tempMermaid_1761640976942mlp0rhob6f .edge-pattern-dotted{stroke-dasharray:2;}#tempMermaid_1761640976942mlp0rhob6f .marker{fill:#333333;stroke:#333333;}#tempMermaid_1761640976942mlp0rhob6f .marker.cross{stroke:#333333;}#tempMermaid_1761640976942mlp0rhob6f svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#tempMermaid_1761640976942mlp0rhob6f p{margin:0;}#tempMermaid_1761640976942mlp0rhob6f .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#333;}#tempMermaid_1761640976942mlp0rhob6f .cluster-label text{fill:#333;}#tempMermaid_1761640976942mlp0rhob6f .cluster-label span{color:#333;}#tempMermaid_1761640976942mlp0rhob6f .cluster-label span p{background-color:transparent;}#tempMermaid_1761640976942mlp0rhob6f .label text,#tempMermaid_1761640976942mlp0rhob6f span{fill:#333;color:#333;}#tempMermaid_1761640976942mlp0rhob6f .node rect,#tempMermaid_1761640976942mlp0rhob6f .node circle,#tempMermaid_1761640976942mlp0rhob6f .node ellipse,#tempMermaid_1761640976942mlp0rhob6f .node polygon,#tempMermaid_1761640976942mlp0rhob6f .node path{fill:#ECECFF;stroke:#9370DB;stroke-width:1px;}#tempMermaid_1761640976942mlp0rhob6f .rough-node .label text,#tempMermaid_1761640976942mlp0rhob6f .node .label text,#tempMermaid_1761640976942mlp0rhob6f .image-shape .label,#tempMermaid_1761640976942mlp0rhob6f .icon-shape .label{text-anchor:middle;}#tempMermaid_1761640976942mlp0rhob6f .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#tempMermaid_1761640976942mlp0rhob6f .rough-node .label,#tempMermaid_1761640976942mlp0rhob6f .node .label,#tempMermaid_1761640976942mlp0rhob6f .image-shape .label,#tempMermaid_1761640976942mlp0rhob6f .icon-shape .label{text-align:center;}#tempMermaid_1761640976942mlp0rhob6f .node.clickable{cursor:pointer;}#tempMermaid_1761640976942mlp0rhob6f .root .anchor path{fill:#333333!important;stroke-width:0;stroke:#333333;}#tempMermaid_1761640976942mlp0rhob6f .arrowheadPath{fill:#333333;}#tempMermaid_1761640976942mlp0rhob6f .edgePath .path{stroke:#333333;stroke-width:2.0px;}#tempMermaid_1761640976942mlp0rhob6f .flowchart-link{stroke:#333333;fill:none;}#tempMermaid_1761640976942mlp0rhob6f .edgeLabel{background-color:rgba(232,232,232, 0.8);text-align:center;}#tempMermaid_1761640976942mlp0rhob6f .edgeLabel p{background-color:rgba(232,232,232, 0.8);}#tempMermaid_1761640976942mlp0rhob6f .edgeLabel rect{opacity:0.5;background-color:rgba(232,232,232, 0.8);fill:rgba(232,232,232, 0.8);}#tempMermaid_1761640976942mlp0rhob6f .labelBkg{background-color:rgba(232, 232, 232, 0.5);}#tempMermaid_1761640976942mlp0rhob6f .cluster rect{fill:#ffffde;stroke:#aaaa33;stroke-width:1px;}#tempMermaid_1761640976942mlp0rhob6f .cluster text{fill:#333;}#tempMermaid_1761640976942mlp0rhob6f .cluster span{color:#333;}#tempMermaid_1761640976942mlp0rhob6f div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(80, 100%, 96.2745098039%);border:1px solid #aaaa33;border-radius:2px;pointer-events:none;z-index:100;}#tempMermaid_1761640976942mlp0rhob6f .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#333;}#tempMermaid_1761640976942mlp0rhob6f rect.text{fill:none;stroke-width:0;}#tempMermaid_1761640976942mlp0rhob6f .icon-shape,#tempMermaid_1761640976942mlp0rhob6f .image-shape{background-color:rgba(232,232,232, 0.8);text-align:center;}#tempMermaid_1761640976942mlp0rhob6f .icon-shape p,#tempMermaid_1761640976942mlp0rhob6f .image-shape p{background-color:rgba(232,232,232, 0.8);padding:2px;}#tempMermaid_1761640976942mlp0rhob6f .icon-shape rect,#tempMermaid_1761640976942mlp0rhob6f .image-shape rect{opacity:0.5;background-color:rgba(232,232,232, 0.8);fill:rgba(232,232,232, 0.8);}#tempMermaid_1761640976942mlp0rhob6f .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#tempMermaid_1761640976942mlp0rhob6f .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#tempMermaid_1761640976942mlp0rhob6f :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}</style><g><marker id="tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-pointEnd" class="marker flowchart-v2" viewBox="0 0 10 10" refX="5" refY="5" markerUnits="userSpaceOnUse" markerWidth="8" markerHeight="8" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" class="arrowMarkerPath" style="stroke-width: 1; stroke-dasharray: 1, 0;"/></marker><marker id="tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-pointStart" class="marker flowchart-v2" viewBox="0 0 10 10" refX="4.5" refY="5" markerUnits="userSpaceOnUse" markerWidth="8" markerHeight="8" orient="auto"><path d="M 0 5 L 10 10 L 10 0 z" class="arrowMarkerPath" style="stroke-width: 1; stroke-dasharray: 1, 0;"/></marker><marker id="tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-circleEnd" class="marker flowchart-v2" viewBox="0 0 10 10" refX="11" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto"><circle cx="5" cy="5" r="5" class="arrowMarkerPath" style="stroke-width: 1; stroke-dasharray: 1, 0;"/></marker><marker id="tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-circleStart" class="marker flowchart-v2" viewBox="0 0 10 10" refX="-1" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto"><circle cx="5" cy="5" r="5" class="arrowMarkerPath" style="stroke-width: 1; stroke-dasharray: 1, 0;"/></marker><marker id="tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-crossEnd" class="marker cross flowchart-v2" viewBox="0 0 11 11" refX="12" refY="5.2" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto"><path d="M 1,1 l 9,9 M 10,1 l -9,9" class="arrowMarkerPath" style="stroke-width: 2; stroke-dasharray: 1, 0;"/></marker><marker id="tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-crossStart" class="marker cross flowchart-v2" viewBox="0 0 11 11" refX="-1" refY="5.2" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto"><path d="M 1,1 l 9,9 M 10,1 l -9,9" class="arrowMarkerPath" style="stroke-width: 2; stroke-dasharray: 1, 0;"/></marker><g class="root"><g class="clusters"/><g class="edgePaths"><path d="M100,90.219L107.652,90.219C115.303,90.219,130.607,90.219,145.327,90.295C160.047,90.371,174.184,90.523,181.252,90.6L188.321,90.676" id="L_A_B_0" class="edge-thickness-normal edge-pattern-solid edge-thickness-normal edge-pattern-solid flowchart-link" style=";" data-edge="true" data-et="edge" data-id="L_A_B_0" data-points="W3sieCI6MTAwLCJ5Ijo5MC4yMTg3NX0seyJ4IjoxNDUuOTEwMTU2MjUsInkiOjkwLjIxODc1fSx7IngiOjE5Mi4zMjAzMTI1LCJ5Ijo5MC43MTg3NX1d" marker-end="url(#tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-pointEnd)"/><path d="M270.32,90.719L274.404,90.635C278.487,90.552,286.654,90.385,294.237,90.302C301.82,90.219,308.82,90.219,312.32,90.219L315.82,90.219" id="L_B_C_0" class="edge-thickness-normal edge-pattern-solid edge-thickness-normal edge-pattern-solid flowchart-link" style=";" data-edge="true" data-et="edge" data-id="L_B_C_0" data-points="W3sieCI6MjcwLjMyMDMxMjUsInkiOjkwLjcxODc1fSx7IngiOjI5NC44MjAzMTI1LCJ5Ijo5MC4yMTg3NX0seyJ4IjozMTkuODIwMzEyNSwieSI6OTAuMjE4NzV9XQ==" marker-end="url(#tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-pointEnd)"/><path d="M459.588,65.549L470.214,60.994C480.84,56.439,502.092,47.329,518.565,42.774C535.039,38.219,546.734,38.219,552.582,38.219L558.43,38.219" id="L_C_D_0" class="edge-thickness-normal edge-pattern-solid edge-thickness-normal edge-pattern-solid flowchart-link" style=";" data-edge="true" data-et="edge" data-id="L_C_D_0" data-points="W3sieCI6NDU5LjU4ODExMDQ3NTkyNzUsInkiOjY1LjU0OTA0Nzk3NTkyNzUxfSx7IngiOjUyMy4zNDM3NSwieSI6MzguMjE4NzV9LHsieCI6NTYyLjQyOTY4NzUsInkiOjM4LjIxODc1fV0=" marker-end="url(#tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-pointEnd)"/><path d="M459.588,114.888L470.214,119.444C480.84,123.999,502.092,133.109,518.565,137.664C535.039,142.219,546.734,142.219,552.582,142.219L558.43,142.219" id="L_C_E_0" class="edge-thickness-normal edge-pattern-solid edge-thickness-normal edge-pattern-solid flowchart-link" style=";" data-edge="true" data-et="edge" data-id="L_C_E_0" data-points="W3sieCI6NDU5LjU4ODExMDQ3NTkyNzUsInkiOjExNC44ODg0NTIwMjQwNzI0OX0seyJ4Ijo1MjMuMzQzNzUsInkiOjE0Mi4yMTg3NX0seyJ4Ijo1NjIuNDI5Njg3NSwieSI6MTQyLjIxODc1fV0=" marker-end="url(#tempMermaid_1761640976942mlp0rhob6f_flowchart-v2-pointEnd)"/></g><g class="edgeLabels"><g><rect class="background" style="stroke: none"/></g><g class="edgeLabel" transform="translate(145.91015625, 90.21875)"><g class="label" data-id="L_A_B_0" transform="translate(-20.91015625, -11.5)"><g><rect class="background" style="" x="-2" y="-1" width="41.8203125" height="23"/><text y="-10.1" style=""><tspan class="text-outer-tspan" x="0" y="-0.1em" dy="1.1em"><tspan font-style="normal" class="text-inner-tspan" font-weight="normal">下</tspan><tspan font-style="normal" class="text-inner-tspan" font-weight="normal"> 班</tspan></tspan></text></g></g></g><g class="edgeLabel"><g class="label" data-id="L_B_C_0" transform="translate(0, 0)"><text y="-10.1"><tspan class="text-outer-tspan" x="0" y="-0.1em" dy="1.1em"/></text></g></g><g class="edgeLabel" transform="translate(523.34375, 38.21875)"><g class="label" data-id="L_C_D_0" transform="translate(-14.0859375, -11.5)"><g><rect class="background" style="" x="-3" y="-1" width="28.171875" height="23"/><text y="-10.1" style=""><tspan class="text-outer-tspan" x="0" y="-0.1em" dy="1.1em"><tspan font-style="normal" class="text-inner-tspan" font-weight="normal">Yes</tspan></tspan></text></g></g></g><g class="edgeLabel" transform="translate(523.34375, 142.21875)"><g class="label" data-id="L_C_E_0" transform="translate(-11.60546875, -11.5)"><g><rect class="background" style="" x="-2" y="-1" width="23.2109375" height="23"/><text y="-10.1" style=""><tspan class="text-outer-tspan" x="0" y="-0.1em" dy="1.1em"><tspan font-style="normal" class="text-inner-tspan" font-weight="normal">No</tspan></tspan></text></g></g></g></g><g class="nodes"><g class="node default" id="flowchart-A-0" transform="translate(54, 90.21875)"><rect class="basic label-container" style="" x="-46" y="-27" width="92" height="54"/><g class="label" style="" transform="translate(-16, -12)"><rect/><foreignObject width="32" height="24"><div xmlns="http://www.w3.org/1999/xhtml" style="display: table-cell; white-space: nowrap; line-height: 1.5; max-width: 200px; text-align: center;"><span class="nodeLabel"><p>公司</p></span></div></foreignObject></g></g><g class="node default" id="flowchart-B-1" transform="translate(230.8203125, 90.21875)"><g class="basic label-container outer-path"><path d="M-34 -27 C-7.386957318558512 -27, 19.226085362882976 -27, 34 -27 C34 -27, 34 -27, 34 -27 C34.13698447866772 -26.994334280052826, 34.27396895733544 -26.988668560105648, 34.41289672736166 -26.982922465033347 C34.56119594600085 -26.964436986707856, 34.70949516464004 -26.945951508382365, 34.82297295140367 -26.931806517013612 C34.939296305163836 -26.907416074608125, 35.055619658924 -26.88302563220264, 35.227427435703994 -26.847001329696653 C35.32557386018987 -26.817781873140042, 35.423720284675746 -26.788562416583435, 35.62349734602342 -26.729086208503173 C35.70349547229708 -26.69787084276639, 35.783493598570736 -26.66665547702961, 36.008477123264846 -26.578866633275286 C36.14167224635282 -26.513751505351646, 36.27486736944079 -26.448636377428002, 36.379736965185366 -26.397368756032446 C36.49807750469654 -26.326853100329078, 36.616418044207705 -26.256337444625707, 36.734740790612136 -26.185832391312644 C36.85156187030957 -26.102423743584986, 36.96838295000699 -26.019015095857323, 37.07106356344834 -25.94570254698197 C37.18753478849687 -25.847056451330705, 37.30400601354539 -25.748410355679443, 37.386407858128706 -25.678619553365657 C37.499955087621984 -25.56507232387238, 37.61350231711526 -25.451525094379104, 37.67861955336566 -25.386407858128706 C37.784733348837506 -25.261119536563022, 37.89084714430935 -25.135831214997342, 37.94570254698197 -25.07106356344834 C38.025746851428984 -24.958954539697448, 38.105791155876 -24.846845515946555, 38.185832391312644 -24.734740790612136 C38.269169841911854 -24.594882502874132, 38.35250729251106 -24.455024215136127, 38.39736875603245 -24.37973696518537 C38.46659545644436 -24.238131486145978, 38.53582215685627 -24.096526007106583, 38.57886663327529 -24.008477123264846 C38.6329763796045 -23.869805728030187, 38.68708612593371 -23.731134332795524, 38.729086208503176 -23.623497346023417 C38.75787776058639 -23.52678822732741, 38.786669312669595 -23.430079108631404, 38.84700132969665 -23.227427435703994 C38.87137731232562 -23.111173043780255, 38.89575329495458 -22.994918651856516, 38.93180651701361 -22.82297295140367 C38.94662896846043 -22.704060260632282, 38.96145141990725 -22.585147569860897, 38.98292246503335 -22.412896727361662 C38.986445841280315 -22.327709343791497, 38.98996921752728 -22.24252196022133, 39 -22 C39 -22, 39 -22, 39 -22 C39 -11.364587225054494, 39 -0.7291744501089887, 39 22 C39 22, 39 22, 39 22 C38.995064583731235 22.119327363669292, 38.99012916746247 22.23865472733858, 38.98292246503335 22.412896727361662 C38.97118369426103 22.507070678539243, 38.95944492348871 22.601244629716827, 38.93180651701361 22.82297295140367 C38.91135087533778 22.92053037998534, 38.89089523366196 23.018087808567014, 38.84700132969665 23.227427435703994 C38.817901013621885 23.32517367436568, 38.788800697547124 23.422919913027364, 38.729086208503176 23.623497346023417 C38.671854692430365 23.77016915144875, 38.61462317635755 23.916840956874083, 38.57886663327529 24.008477123264846 C38.52668955368663 24.11520704547789, 38.47451247409796 24.221936967690937, 38.39736875603245 24.379736965185366 C38.35384146348312 24.452785187347782, 38.310314170933786 24.525833409510202, 38.185832391312644 24.734740790612133 C38.12133875357319 24.82506975049335, 38.05684511583373 24.91539871037456, 37.94570254698197 25.07106356344834 C37.86668553833834 25.16435876926094, 37.787668529694706 25.257653975073534, 37.67861955336566 25.386407858128706 C37.592889936224765 25.4721374752696, 37.507160319083866 25.557867092410497, 37.386407858128706 25.678619553365657 C37.26191044619925 25.784063482545683, 37.137413034269805 25.889507411725706, 37.07106356344834 25.94570254698197 C36.94978875594972 26.03229109523963, 36.828513948451096 26.118879643497284, 36.734740790612136 26.185832391312644 C36.6605866927903 26.230018642724023, 36.586432594968464 26.274204894135398, 36.379736965185366 26.397368756032446 C36.25817972218139 26.45679447106423, 36.13662247917741 26.516220186096014, 36.008477123264846 26.578866633275286 C35.8809640241415 26.628622398950966, 35.75345092501816 26.678378164626647, 35.62349734602342 26.729086208503173 C35.49210600659168 26.768203105064117, 35.36071466715995 26.807320001625058, 35.227427435703994 26.847001329696653 C35.145905230397844 26.86409473862112, 35.064383025091686 26.881188147545586, 34.82297295140367 26.931806517013612 C34.680004178556636 26.949627555964035, 34.5370354057096 26.967448594914455, 34.41289672736166 26.982922465033347 C34.301434213728626 26.987532588698414, 34.18997170009558 26.992142712363485, 34 27 C34 27, 34 27, 34 27 C7.772540299162607 27, -18.454919401674786 27, -34 27 C-34 27, -34 27, -34 27 C-34.11708112248992 26.995157488953637, -34.234162244979835 26.99031497790727, -34.41289672736166 26.982922465033347 C-34.54709182296498 26.966195063810837, -34.6812869185683 26.94946766258833, -34.82297295140367 26.931806517013612 C-34.92391478903917 26.910641239383903, -35.024856626674676 26.889475961754197, -35.227427435703994 26.847001329696653 C-35.35426657280905 26.809239682487057, -35.481105709914104 26.771478035277458, -35.62349734602342 26.729086208503173 C-35.74684391710809 26.680956227113175, -35.870190488192755 26.63282624572318, -36.008477123264846 26.578866633275286 C-36.117484216624725 26.525576312547667, -36.2264913099846 26.472285991820044, -36.379736965185366 26.397368756032446 C-36.481498976114416 26.336731759141976, -36.58326098704347 26.276094762251507, -36.734740790612136 26.185832391312644 C-36.86422208359204 26.093384525041806, -36.99370337657194 26.000936658770968, -37.07106356344834 25.94570254698197 C-37.1385613138378 25.888534868541313, -37.206059064227254 25.831367190100657, -37.386407858128706 25.67861955336566 C-37.501463381630344 25.563564029864022, -37.61651890513198 25.44850850636238, -37.67861955336566 25.386407858128706 C-37.76494179135222 25.284487384329427, -37.85126402933879 25.182566910530145, -37.94570254698197 25.07106356344834 C-37.99905216641497 24.996342772338537, -38.05240178584797 24.92162198122873, -38.185832391312644 24.734740790612133 C-38.263343243684 24.604660796373942, -38.340854096055345 24.47458080213575, -38.39736875603244 24.37973696518537 C-38.45678354453869 24.258202072746617, -38.51619833304493 24.136667180307867, -38.57886663327528 24.00847712326485 C-38.63003183228298 23.87735195607798, -38.68119703129068 23.74622678889111, -38.729086208503176 23.623497346023417 C-38.76047385174349 23.51806811084558, -38.79186149498381 23.41263887566774, -38.84700132969665 23.227427435703994 C-38.86813438734415 23.126639262209828, -38.889267444991646 23.025851088715665, -38.93180651701361 22.82297295140367 C-38.94381414446023 22.72664210528282, -38.95582177190684 22.630311259161974, -38.98292246503335 22.412896727361662 C-38.98793729211056 22.291649387361492, -38.99295211918778 22.17040204736132, -39 22 C-39 22, -39 22, -39 22 C-39 12.243933453312302, -39 2.4878669066246033, -39 -22 C-39 -22, -39 -22, -39 -22 C-38.9940052054638 -22.144940768678527, -38.98801041092761 -22.289881537357058, -38.98292246503335 -22.41289672736166 C-38.963628426725954 -22.567682595219647, -38.944334388418554 -22.722468463077636, -38.93180651701361 -22.82297295140367 C-38.90356447305863 -22.95766543525737, -38.87532242910365 -23.092357919111066, -38.84700132969665 -23.227427435703994 C-38.801395764783905 -23.380613827934557, -38.75579019987116 -23.533800220165116, -38.729086208503176 -23.623497346023417 C-38.67541323200192 -23.761049396120683, -38.62174025550067 -23.898601446217953, -38.57886663327529 -24.008477123264846 C-38.53285421603681 -24.102597027088752, -38.48684179879833 -24.196716930912654, -38.39736875603245 -24.379736965185366 C-38.345469428946984 -24.466835274153755, -38.29357010186151 -24.55393358312215, -38.185832391312644 -24.734740790612133 C-38.0916539577468 -24.866645893897076, -37.997475524180956 -24.998550997182022, -37.94570254698197 -25.07106356344834 C-37.87240554354612 -25.157605171873872, -37.799108540110275 -25.244146780299403, -37.67861955336566 -25.386407858128706 C-37.57549914141775 -25.48952827007661, -37.472378729469845 -25.59264868202452, -37.386407858128706 -25.678619553365657 C-37.28232721325409 -25.766771362926075, -37.17824656837948 -25.854923172486494, -37.07106356344834 -25.945702546981966 C-36.979057674691134 -26.011393488925805, -36.88705178593392 -26.077084430869643, -36.734740790612136 -26.185832391312644 C-36.65822352615095 -26.231426784395495, -36.58170626168975 -26.277021177478346, -36.379736965185366 -26.397368756032446 C-36.29997229139343 -26.436363328936736, -36.22020761760149 -26.475357901841022, -36.008477123264846 -26.578866633275286 C-35.89695876586493 -26.622381231363438, -35.78544040846502 -26.66589582945159, -35.62349734602342 -26.729086208503173 C-35.50372895293297 -26.764742804014354, -35.383960559842514 -26.800399399525535, -35.227427435703994 -26.847001329696653 C-35.07150200247917 -26.879695454957705, -34.91557656925435 -26.912389580218758, -34.82297295140367 -26.931806517013612 C-34.67953450548438 -26.949686100651437, -34.5360960595651 -26.96756568428926, -34.41289672736166 -26.982922465033347 C-34.25485368576896 -26.989459173585825, -34.09681064417626 -26.995995882138306, -34 -27 C-34 -27, -34 -27, -34 -27" stroke="none" stroke-width="0" fill="#ECECFF" style=""/><path d="M-34 -27 C-15.414417464568501 -27, 3.1711650708629975 -27, 34 -27 M-34 -27 C-9.299165394337471 -27, 15.401669211325057 -27, 34 -27 M34 -27 C34 -27, 34 -27, 34 -27 M34 -27 C34 -27, 34 -27, 34 -27 M34 -27 C34.09625541773922 -26.996018846473607, 34.192510835478444 -26.992037692947218, 34.41289672736166 -26.982922465033347 M34 -27 C34.158834140943505 -26.99343057133634, 34.317668281887 -26.98686114267268, 34.41289672736166 -26.982922465033347 M34.41289672736166 -26.982922465033347 C34.557006607578465 -26.96495918719762, 34.70111648779526 -26.946995909361895, 34.82297295140367 -26.931806517013612 M34.41289672736166 -26.982922465033347 C34.49790512886379 -26.972326178836617, 34.58291353036592 -26.961729892639887, 34.82297295140367 -26.931806517013612 M34.82297295140367 -26.931806517013612 C34.92810275996488 -26.909763114223672, 35.03323256852609 -26.887719711433732, 35.227427435703994 -26.847001329696653 M34.82297295140367 -26.931806517013612 C34.94919611971756 -26.9053403017827, 35.07541928803145 -26.87887408655179, 35.227427435703994 -26.847001329696653 M35.227427435703994 -26.847001329696653 C35.37775542763102 -26.802246747424668, 35.52808341955805 -26.757492165152687, 35.62349734602342 -26.729086208503173 M35.227427435703994 -26.847001329696653 C35.34896567932771 -26.81081782685248, 35.47050392295143 -26.77463432400831, 35.62349734602342 -26.729086208503173 M35.62349734602342 -26.729086208503173 C35.75797358850445 -26.676613415858082, 35.89244983098548 -26.624140623212995, 36.008477123264846 -26.578866633275286 M35.62349734602342 -26.729086208503173 C35.75254257313465 -26.678732604631463, 35.88158780024587 -26.62837900075975, 36.008477123264846 -26.578866633275286 M36.008477123264846 -26.578866633275286 C36.09249275906095 -26.53779389167921, 36.17650839485706 -26.49672115008314, 36.379736965185366 -26.397368756032446 M36.008477123264846 -26.578866633275286 C36.08803408039628 -26.53997360685864, 36.16759103752771 -26.501080580441993, 36.379736965185366 -26.397368756032446 M36.379736965185366 -26.397368756032446 C36.47435504767025 -26.340988616518317, 36.56897313015514 -26.284608477004184, 36.734740790612136 -26.185832391312644 M36.379736965185366 -26.397368756032446 C36.47248280026308 -26.342104233821576, 36.56522863534079 -26.286839711610707, 36.734740790612136 -26.185832391312644 M36.734740790612136 -26.185832391312644 C36.83699761696382 -26.112822420603532, 36.9392544433155 -26.039812449894423, 37.07106356344834 -25.94570254698197 M36.734740790612136 -26.185832391312644 C36.85163732146172 -26.102369872497786, 36.9685338523113 -26.01890735368293, 37.07106356344834 -25.94570254698197 M37.07106356344834 -25.94570254698197 C37.19264785459505 -25.84272590524791, 37.314232145741755 -25.739749263513847, 37.386407858128706 -25.678619553365657 M37.07106356344834 -25.94570254698197 C37.175592741678784 -25.857170849047375, 37.28012191990923 -25.76863915111278, 37.386407858128706 -25.678619553365657 M37.386407858128706 -25.678619553365657 C37.49001032254839 -25.57501708894597, 37.59361278696808 -25.471414624526286, 37.67861955336566 -25.386407858128706 M37.386407858128706 -25.678619553365657 C37.46630517599135 -25.598722235503015, 37.54620249385399 -25.518824917640373, 37.67861955336566 -25.386407858128706 M37.67861955336566 -25.386407858128706 C37.750294043261135 -25.30178194782034, 37.82196853315661 -25.217156037511973, 37.94570254698197 -25.07106356344834 M37.67861955336566 -25.386407858128706 C37.775825260214575 -25.271637296925498, 37.873030967063485 -25.156866735722286, 37.94570254698197 -25.07106356344834 M37.94570254698197 -25.07106356344834 C38.03304934700836 -24.948726758270595, 38.12039614703474 -24.826389953092853, 38.185832391312644 -24.734740790612136 M37.94570254698197 -25.07106356344834 C38.01446889670985 -24.974750298086555, 38.083235246437724 -24.878437032724772, 38.185832391312644 -24.734740790612136 M38.185832391312644 -24.734740790612136 C38.26767156425748 -24.597396937210547, 38.34951073720233 -24.460053083808962, 38.39736875603245 -24.37973696518537 M38.185832391312644 -24.734740790612136 C38.25835365689349 -24.61303440343804, 38.33087492247433 -24.49132801626394, 38.39736875603245 -24.37973696518537 M38.39736875603245 -24.37973696518537 C38.45139474185137 -24.26922504482888, 38.50542072767029 -24.15871312447239, 38.57886663327529 -24.008477123264846 M38.39736875603245 -24.37973696518537 C38.457336515207054 -24.25707095316528, 38.51730427438165 -24.134404941145192, 38.57886663327529 -24.008477123264846 M38.57886663327529 -24.008477123264846 C38.62559959643598 -23.888710803062292, 38.67233255959667 -23.76894448285974, 38.729086208503176 -23.623497346023417 M38.57886663327529 -24.008477123264846 C38.61861719219868 -23.90660517151466, 38.65836775112207 -23.804733219764476, 38.729086208503176 -23.623497346023417 M38.729086208503176 -23.623497346023417 C38.773373992910386 -23.474737300485003, 38.817661777317596 -23.325977254946586, 38.84700132969665 -23.227427435703994 M38.729086208503176 -23.623497346023417 C38.766044259438985 -23.499357441220965, 38.8030023103748 -23.375217536418514, 38.84700132969665 -23.227427435703994 M38.84700132969665 -23.227427435703994 C38.87538822366123 -23.092044130477387, 38.90377511762581 -22.956660825250776, 38.93180651701361 -22.82297295140367 M38.84700132969665 -23.227427435703994 C38.873925308141665 -23.099021094514157, 38.90084928658667 -22.97061475332432, 38.93180651701361 -22.82297295140367 M38.93180651701361 -22.82297295140367 C38.9496790540274 -22.679591036823183, 38.96755159104119 -22.5362091222427, 38.98292246503335 -22.412896727361662 M38.93180651701361 -22.82297295140367 C38.94753981911805 -22.69675298740713, 38.963273121222485 -22.570533023410594, 38.98292246503335 -22.412896727361662 M38.98292246503335 -22.412896727361662 C38.989621427928256 -22.250930737455825, 38.996320390823165 -22.088964747549984, 39 -22 M38.98292246503335 -22.412896727361662 C38.98964608218842 -22.250334652402714, 38.9963696993435 -22.08777257744376, 39 -22 M39 -22 C39 -22, 39 -22, 39 -22 M39 -22 C39 -22, 39 -22, 39 -22 M39 -22 C39 -11.901885168403231, 39 -1.803770336806462, 39 22 M39 -22 C39 -4.409961140261938, 39 13.180077719476124, 39 22 M39 22 C39 22, 39 22, 39 22 M39 22 C39 22, 39 22, 39 22 M39 22 C38.99629113268764 22.089672144046773, 38.992582265375276 22.179344288093546, 38.98292246503335 22.412896727361662 M39 22 C38.996315936745326 22.089072437223475, 38.99263187349065 22.17814487444695, 38.98292246503335 22.412896727361662 M38.98292246503335 22.412896727361662 C38.96890729772749 22.525333004311555, 38.954892130421634 22.637769281261452, 38.93180651701361 22.82297295140367 M38.98292246503335 22.412896727361662 C38.97255588430818 22.49606232331938, 38.962189303583 22.579227919277095, 38.93180651701361 22.82297295140367 M38.93180651701361 22.82297295140367 C38.90327702914745 22.95903631813067, 38.874747541281295 23.095099684857672, 38.84700132969665 23.227427435703994 M38.93180651701361 22.82297295140367 C38.91003010193942 22.926829437161146, 38.88825368686522 23.03068592291862, 38.84700132969665 23.227427435703994 M38.84700132969665 23.227427435703994 C38.8128484775958 23.342144843716, 38.77869562549495 23.456862251728, 38.729086208503176 23.623497346023417 M38.84700132969665 23.227427435703994 C38.808648404765904 23.35625263966477, 38.770295479835156 23.485077843625543, 38.729086208503176 23.623497346023417 M38.729086208503176 23.623497346023417 C38.679043091025264 23.75174686470224, 38.62899997354735 23.879996383381066, 38.57886663327529 24.008477123264846 M38.729086208503176 23.623497346023417 C38.6756761384008 23.76037562476484, 38.62226606829843 23.897253903506265, 38.57886663327529 24.008477123264846 M38.57886663327529 24.008477123264846 C38.51873478419339 24.13147878655517, 38.4586029351115 24.2544804498455, 38.39736875603245 24.379736965185366 M38.57886663327529 24.008477123264846 C38.52018369236578 24.128514997516934, 38.46150075145626 24.248552871769025, 38.39736875603245 24.379736965185366 M38.39736875603245 24.379736965185366 C38.346981143266575 24.464298290183564, 38.296593530500694 24.54885961518176, 38.185832391312644 24.734740790612133 M38.39736875603245 24.379736965185366 C38.34870673408364 24.461402375138448, 38.300044712134834 24.54306778509153, 38.185832391312644 24.734740790612133 M38.185832391312644 24.734740790612133 C38.09910272548713 24.856213245562078, 38.01237305966161 24.977685700512023, 37.94570254698197 25.07106356344834 M38.185832391312644 24.734740790612133 C38.10994391338463 24.841029217168227, 38.03405543545663 24.947317643724322, 37.94570254698197 25.07106356344834 M37.94570254698197 25.07106356344834 C37.85549448832525 25.17757201704331, 37.76528642966853 25.28408047063828, 37.67861955336566 25.386407858128706 M37.94570254698197 25.07106356344834 C37.851165620239335 25.182683101934316, 37.7566286934967 25.294302640420295, 37.67861955336566 25.386407858128706 M37.67861955336566 25.386407858128706 C37.60992346258609 25.45510394890827, 37.54122737180653 25.52380003968784, 37.386407858128706 25.678619553365657 M37.67861955336566 25.386407858128706 C37.59698029054255 25.468047120951816, 37.51534102771944 25.549686383774922, 37.386407858128706 25.678619553365657 M37.386407858128706 25.678619553365657 C37.26374418091264 25.782510388467205, 37.14108050369657 25.886401223568758, 37.07106356344834 25.94570254698197 M37.386407858128706 25.678619553365657 C37.31994716187537 25.734908891757392, 37.253486465622025 25.791198230149128, 37.07106356344834 25.94570254698197 M37.07106356344834 25.94570254698197 C36.9910240835759 26.002849637201276, 36.910984603703454 26.059996727420582, 36.734740790612136 26.185832391312644 M37.07106356344834 25.94570254698197 C36.9381941478407 26.040569486312627, 36.80532473223306 26.135436425643285, 36.734740790612136 26.185832391312644 M36.734740790612136 26.185832391312644 C36.6166094604845 26.256223385282002, 36.498478130356865 26.32661437925136, 36.379736965185366 26.397368756032446 M36.734740790612136 26.185832391312644 C36.63645161771877 26.244400025901324, 36.5381624448254 26.302967660490005, 36.379736965185366 26.397368756032446 M36.379736965185366 26.397368756032446 C36.272886229369824 26.449604897792447, 36.16603549355429 26.50184103955245, 36.008477123264846 26.578866633275286 M36.379736965185366 26.397368756032446 C36.269712254484475 26.45115655956425, 36.159687543783576 26.504944363096055, 36.008477123264846 26.578866633275286 M36.008477123264846 26.578866633275286 C35.91194614332701 26.616533138530446, 35.81541516338916 26.654199643785606, 35.62349734602342 26.729086208503173 M36.008477123264846 26.578866633275286 C35.89597442312958 26.622765323090654, 35.783471722994314 26.66666401290602, 35.62349734602342 26.729086208503173 M35.62349734602342 26.729086208503173 C35.50852187817797 26.763315888345144, 35.393546410332526 26.797545568187118, 35.227427435703994 26.847001329696653 M35.62349734602342 26.729086208503173 C35.503058591019546 26.764942379402953, 35.382619836015664 26.800798550302734, 35.227427435703994 26.847001329696653 M35.227427435703994 26.847001329696653 C35.12404499679613 26.868678347599005, 35.02066255788827 26.89035536550136, 34.82297295140367 26.931806517013612 M35.227427435703994 26.847001329696653 C35.10553263980183 26.872559980671504, 34.983637843899665 26.89811863164636, 34.82297295140367 26.931806517013612 M34.82297295140367 26.931806517013612 C34.72031357143696 26.944602995381445, 34.61765419147026 26.95739947374928, 34.41289672736166 26.982922465033347 M34.82297295140367 26.931806517013612 C34.695132181722215 26.94774185233598, 34.56729141204077 26.963677187658348, 34.41289672736166 26.982922465033347 M34.41289672736166 26.982922465033347 C34.304035224950496 26.987425010078518, 34.19517372253932 26.991927555123688, 34 27 M34.41289672736166 26.982922465033347 C34.291302039172784 26.987951658537916, 34.169707350983906 26.992980852042482, 34 27 M34 27 C34 27, 34 27, 34 27 M34 27 C34 27, 34 27, 34 27 M34 27 C9.279625626620088 27, -15.440748746759823 27, -34 27 M34 27 C19.831650155312037 27, 5.663300310624074 27, -34 27 M-34 27 C-34 27, -34 27, -34 27 M-34 27 C-34 27, -34 27, -34 27 M-34 27 C-34.10715001559729 26.99556824257307, -34.21430003119458 26.99113648514614, -34.41289672736166 26.982922465033347 M-34 27 C-34.160617811934344 26.99335679815846, -34.32123562386868 26.986713596316914, -34.41289672736166 26.982922465033347 M-34.41289672736166 26.982922465033347 C-34.563830481479826 26.964108592202873, -34.71476423559798 26.9452947193724, -34.82297295140367 26.931806517013612 M-34.41289672736166 26.982922465033347 C-34.52149030161666 26.969386290118884, -34.63008387587166 26.95585011520442, -34.82297295140367 26.931806517013612 M-34.82297295140367 26.931806517013612 C-34.92386465923605 26.91065175049828, -35.024756367068434 26.889496983982944, -35.227427435703994 26.847001329696653 M-34.82297295140367 26.931806517013612 C-34.9128853648197 26.91295386644885, -35.002797778235724 26.89410121588408, -35.227427435703994 26.847001329696653 M-35.227427435703994 26.847001329696653 C-35.321933826697055 26.818865558063514, -35.41644021769012 26.790729786430372, -35.62349734602342 26.729086208503173 M-35.227427435703994 26.847001329696653 C-35.349290961228114 26.810720986234934, -35.47115448675223 26.77444064277321, -35.62349734602342 26.729086208503173 M-35.62349734602342 26.729086208503173 C-35.771625791501364 26.671286309718074, -35.919754236979315 26.613486410932975, -36.008477123264846 26.578866633275286 M-35.62349734602342 26.729086208503173 C-35.77417774465985 26.670290534505632, -35.92485814329628 26.61149486050809, -36.008477123264846 26.578866633275286 M-36.008477123264846 26.578866633275286 C-36.08738983210421 26.5402885606571, -36.166302540943576 26.50171048803891, -36.379736965185366 26.397368756032446 M-36.008477123264846 26.578866633275286 C-36.1461671632797 26.51155407436533, -36.283857203294545 26.444241515455367, -36.379736965185366 26.397368756032446 M-36.379736965185366 26.397368756032446 C-36.48195501557692 26.33646001860523, -36.584173065968486 26.275551281178018, -36.734740790612136 26.185832391312644 M-36.379736965185366 26.397368756032446 C-36.46709665437835 26.345313680139334, -36.55445634357133 26.293258604246223, -36.734740790612136 26.185832391312644 M-36.734740790612136 26.185832391312644 C-36.819713839828815 26.12516280028664, -36.9046868890455 26.064493209260636, -37.07106356344834 25.94570254698197 M-36.734740790612136 26.185832391312644 C-36.856100901105776 26.099182937887186, -36.977461011599424 26.012533484461727, -37.07106356344834 25.94570254698197 M-37.07106356344834 25.94570254698197 C-37.1789736475249 25.854307367862692, -37.286883731601456 25.762912188743414, -37.386407858128706 25.67861955336566 M-37.07106356344834 25.94570254698197 C-37.15814021872918 25.87195238197558, -37.24521687401001 25.798202216969184, -37.386407858128706 25.67861955336566 M-37.386407858128706 25.67861955336566 C-37.47417872583091 25.59084868566346, -37.56194959353311 25.503077817961255, -37.67861955336566 25.386407858128706 M-37.386407858128706 25.67861955336566 C-37.46721742756044 25.597809983933924, -37.54802699699218 25.51700041450219, -37.67861955336566 25.386407858128706 M-37.67861955336566 25.386407858128706 C-37.740500657917856 25.31334497604536, -37.80238176247006 25.240282093962012, -37.94570254698197 25.07106356344834 M-37.67861955336566 25.386407858128706 C-37.776303580575146 25.27107254514294, -37.873987607784635 25.15573723215717, -37.94570254698197 25.07106356344834 M-37.94570254698197 25.07106356344834 C-37.99409705698361 25.00328283490471, -38.042491566985255 24.93550210636108, -38.185832391312644 24.734740790612133 M-37.94570254698197 25.07106356344834 C-37.99774993927062 24.99816665493535, -38.04979733155926 24.925269746422362, -38.185832391312644 24.734740790612133 M-38.185832391312644 24.734740790612133 C-38.25636908641748 24.616364942429502, -38.326905781522306 24.497989094246872, -38.39736875603244 24.37973696518537 M-38.185832391312644 24.734740790612133 C-38.263747733486795 24.60398197489788, -38.341663075660946 24.473223159183625, -38.39736875603244 24.37973696518537 M-38.39736875603244 24.37973696518537 C-38.46387089837712 24.243704658751145, -38.53037304072179 24.107672352316918, -38.57886663327528 24.00847712326485 M-38.39736875603244 24.37973696518537 C-38.46296891523922 24.24554969474978, -38.528569074446004 24.111362424314187, -38.57886663327528 24.00847712326485 M-38.57886663327528 24.00847712326485 C-38.63299696902085 23.86975296187831, -38.68712730476641 23.731028800491764, -38.729086208503176 23.623497346023417 M-38.57886663327528 24.00847712326485 C-38.636963357397214 23.85958797964301, -38.695060081519145 23.710698836021166, -38.729086208503176 23.623497346023417 M-38.729086208503176 23.623497346023417 C-38.77590791019872 23.46622602234707, -38.82272961189425 23.30895469867072, -38.84700132969665 23.227427435703994 M-38.729086208503176 23.623497346023417 C-38.75549423664661 23.534794343112356, -38.78190226479005 23.4460913402013, -38.84700132969665 23.227427435703994 M-38.84700132969665 23.227427435703994 C-38.87156375074695 23.11028387817685, -38.89612617179724 22.993140320649704, -38.93180651701361 22.82297295140367 M-38.84700132969665 23.227427435703994 C-38.86520813271899 23.140595210457732, -38.88341493574133 23.053762985211474, -38.93180651701361 22.82297295140367 M-38.93180651701361 22.82297295140367 C-38.94784967938319 22.69426714233467, -38.96389284175277 22.56556133326567, -38.98292246503335 22.412896727361662 M-38.93180651701361 22.82297295140367 C-38.951423006993785 22.66560022426729, -38.97103949697396 22.508227497130907, -38.98292246503335 22.412896727361662 M-38.98292246503335 22.412896727361662 C-38.9866144208203 22.323633466301157, -38.99030637660726 22.23437020524065, -39 22 M-38.98292246503335 22.412896727361662 C-38.98895341326134 22.26708184300699, -38.99498436148933 22.121266958652324, -39 22 M-39 22 C-39 22, -39 22, -39 22 M-39 22 C-39 22, -39 22, -39 22 M-39 22 C-39 10.789412207650178, -39 -0.4211755846996432, -39 -22 M-39 22 C-39 8.218375604171268, -39 -5.563248791657465, -39 -22 M-39 -22 C-39 -22, -39 -22, -39 -22 M-39 -22 C-39 -22, -39 -22, -39 -22 M-39 -22 C-38.99404657931997 -22.143940441064366, -38.988093158639934 -22.28788088212873, -38.98292246503335 -22.41289672736166 M-39 -22 C-38.9954008797732 -22.11119647502394, -38.99080175954639 -22.222392950047883, -38.98292246503335 -22.41289672736166 M-38.98292246503335 -22.41289672736166 C-38.96621494555117 -22.54693232227451, -38.94950742606899 -22.680967917187363, -38.93180651701361 -22.82297295140367 M-38.98292246503335 -22.41289672736166 C-38.96257720273733 -22.576116009458808, -38.9422319404413 -22.73933529155596, -38.93180651701361 -22.82297295140367 M-38.93180651701361 -22.82297295140367 C-38.912602418111085 -22.914561498800477, -38.89339831920856 -23.00615004619728, -38.84700132969665 -23.227427435703994 M-38.93180651701361 -22.82297295140367 C-38.90987773687774 -22.927556099460876, -38.88794895674187 -23.032139247518085, -38.84700132969665 -23.227427435703994 M-38.84700132969665 -23.227427435703994 C-38.80062019792142 -23.383218911104237, -38.754239066146184 -23.539010386504483, -38.729086208503176 -23.623497346023417 M-38.84700132969665 -23.227427435703994 C-38.80572557792482 -23.36607024196302, -38.76444982615298 -23.504713048222047, -38.729086208503176 -23.623497346023417 M-38.729086208503176 -23.623497346023417 C-38.69355468346554 -23.714556840588518, -38.65802315842791 -23.805616335153623, -38.57886663327529 -24.008477123264846 M-38.729086208503176 -23.623497346023417 C-38.67056909562461 -23.773463853694796, -38.61205198274603 -23.923430361366176, -38.57886663327529 -24.008477123264846 M-38.57886663327529 -24.008477123264846 C-38.51120982705964 -24.14687133239856, -38.44355302084398 -24.285265541532276, -38.39736875603245 -24.379736965185366 M-38.57886663327529 -24.008477123264846 C-38.51863456125992 -24.131683795842353, -38.458402489244556 -24.254890468419855, -38.39736875603245 -24.379736965185366 M-38.39736875603245 -24.379736965185366 C-38.32295968207314 -24.504611503598685, -38.24855060811384 -24.629486042012005, -38.185832391312644 -24.734740790612133 M-38.39736875603245 -24.379736965185366 C-38.32441632020235 -24.502166949401975, -38.251463884372264 -24.62459693361858, -38.185832391312644 -24.734740790612133 M-38.185832391312644 -24.734740790612133 C-38.09491133133811 -24.862083658322213, -38.00399027136357 -24.989426526032293, -37.94570254698197 -25.07106356344834 M-38.185832391312644 -24.734740790612133 C-38.1351960504364 -24.80566139865753, -38.08455970956015 -24.876582006702932, -37.94570254698197 -25.07106356344834 M-37.94570254698197 -25.07106356344834 C-37.840247041157085 -25.195574643896556, -37.73479153533219 -25.320085724344768, -37.67861955336566 -25.386407858128706 M-37.94570254698197 -25.07106356344834 C-37.861172662252336 -25.170867809756032, -37.77664277752271 -25.27067205606372, -37.67861955336566 -25.386407858128706 M-37.67861955336566 -25.386407858128706 C-37.60594835411482 -25.45907905737954, -37.53327715486399 -25.531750256630374, -37.386407858128706 -25.678619553365657 M-37.67861955336566 -25.386407858128706 C-37.57526884051551 -25.48975857097885, -37.47191812766537 -25.593109283828998, -37.386407858128706 -25.678619553365657 M-37.386407858128706 -25.678619553365657 C-37.28989925911492 -25.760358167220854, -37.19339066010113 -25.842096781076055, -37.07106356344834 -25.945702546981966 M-37.386407858128706 -25.678619553365657 C-37.284496031840156 -25.764934467284238, -37.182584205551606 -25.85124938120282, -37.07106356344834 -25.945702546981966 M-37.07106356344834 -25.945702546981966 C-36.95107783673741 -26.031370709247717, -36.831092110026475 -26.11703887151347, -36.734740790612136 -26.185832391312644 M-37.07106356344834 -25.945702546981966 C-36.951923302436214 -26.030767058341393, -36.832783041424086 -26.115831569700816, -36.734740790612136 -26.185832391312644 M-36.734740790612136 -26.185832391312644 C-36.63010744701611 -26.24818033110223, -36.52547410342008 -26.31052827089182, -36.379736965185366 -26.397368756032446 M-36.734740790612136 -26.185832391312644 C-36.60431874592311 -26.263547061512817, -36.473896701234075 -26.34126173171299, -36.379736965185366 -26.397368756032446 M-36.379736965185366 -26.397368756032446 C-36.27792434452197 -26.447141913375148, -36.17611172385857 -26.496915070717854, -36.008477123264846 -26.578866633275286 M-36.379736965185366 -26.397368756032446 C-36.23504142070071 -26.468106097390482, -36.090345876216055 -26.538843438748515, -36.008477123264846 -26.578866633275286 M-36.008477123264846 -26.578866633275286 C-35.88489729835717 -26.627087630589454, -35.761317473449495 -26.675308627903622, -35.62349734602342 -26.729086208503173 M-36.008477123264846 -26.578866633275286 C-35.928966700498684 -26.609891696512914, -35.84945627773252 -26.64091675975054, -35.62349734602342 -26.729086208503173 M-35.62349734602342 -26.729086208503173 C-35.53850458651319 -26.754389649327887, -35.453511827002956 -26.779693090152602, -35.227427435703994 -26.847001329696653 M-35.62349734602342 -26.729086208503173 C-35.523973359816885 -26.75871578295314, -35.42444937361036 -26.78834535740311, -35.227427435703994 -26.847001329696653 M-35.227427435703994 -26.847001329696653 C-35.09885242904093 -26.873960673572398, -34.97027742237787 -26.900920017448147, -34.82297295140367 -26.931806517013612 M-35.227427435703994 -26.847001329696653 C-35.12917432983355 -26.867602839560565, -35.03092122396311 -26.888204349424473, -34.82297295140367 -26.931806517013612 M-34.82297295140367 -26.931806517013612 C-34.71892504538668 -26.944776074973113, -34.614877139369696 -26.957745632932617, -34.41289672736166 -26.982922465033347 M-34.82297295140367 -26.931806517013612 C-34.70457782752737 -26.946564453814236, -34.58618270365107 -26.961322390614864, -34.41289672736166 -26.982922465033347 M-34.41289672736166 -26.982922465033347 C-34.30082607501053 -26.987557741501853, -34.18875542265938 -26.992193017970358, -34 -27 M-34.41289672736166 -26.982922465033347 C-34.285628403417526 -26.988186321848563, -34.15836007947339 -26.99345017866378, -34 -27 M-34 -27 C-34 -27, -34 -27, -34 -27 M-34 -27 C-34 -27, -34 -27, -34 -27" stroke="#9370DB" stroke-width="1.3" fill="none" stroke-dasharray="0 0" style=""/></g><g class="label" style="" transform="translate(-24, -12)"><rect/><foreignObject width="48" height="24"><div xmlns="http://www.w3.org/1999/xhtml" style="display: table-cell; white-space: nowrap; line-height: 1.5; max-width: 200px; text-align: center;"><span class="nodeLabel"><p>菜市场</p></span></div></foreignObject></g></g><g class="node default" id="flowchart-C-3" transform="translate(402.0390625, 90.21875)"><polygon points="82.21875,0 164.4375,-82.21875 82.21875,-164.4375 0,-82.21875" class="label-container" transform="translate(-81.71875, 82.21875)"/><g class="label" style="" transform="translate(-55.21875, -12)"><rect/><foreignObject width="110.4375" height="24"><div xmlns="http://www.w3.org/1999/xhtml" style="display: table-cell; white-space: nowrap; line-height: 1.5; max-width: 200px; text-align: center;"><span class="nodeLabel"><p>看见\\n卖西瓜的</p></span></div></foreignObject></g></g><g class="node default" id="flowchart-D-5" transform="translate(632.4296875, 38.21875)"><rect class="basic label-container" style="" x="-70" y="-27" width="140" height="54"/><g class="label" style="" transform="translate(-40, -12)"><rect/><foreignObject width="80" height="24"><div xmlns="http://www.w3.org/1999/xhtml" style="display: table-cell; white-space: nowrap; line-height: 1.5; max-width: 200px; text-align: center;"><span class="nodeLabel"><p>买一个包子</p></span></div></foreignObject></g></g><g class="node default" id="flowchart-E-7" transform="translate(632.4296875, 142.21875)"><rect class="basic label-container" style="" x="-70" y="-27" width="140" height="54"/><g class="label" style="" transform="translate(-40, -12)"><rect/><foreignObject width="80" height="24"><div xmlns="http://www.w3.org/1999/xhtml" style="display: table-cell; white-space: nowrap; line-height: 1.5; max-width: 200px; text-align: center;"><span class="nodeLabel"><p>买一斤包子</p></span></div></foreignObject></g></g></g></g></g></svg>'
    _run_weasyprint(html, "output/test.pdf")
