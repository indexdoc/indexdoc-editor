import os
import logging
import subprocess
from pathlib import Path

from config import base_path

DEFAULT_TEMPLATE =  os.path.join(base_path + '/src/utils/docxTemplate/', "Normal-zh.docx")  # 可自定义默认模板
DEFAULT_MD_TEMPLATE =  os.path.join(base_path + '/src/utils/mdTemplate/', "template.md")  # 可自定义默认模板
DEFAULT_DPI = 150


def _run_pandoc(cmd, input_data=None):
    """
    运行 pandoc 命令的辅助函数
    """
    try:
        process = subprocess.run(
            ['pandoc'] + cmd,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            )
        if process.returncode != 0:
            logging.error(f"Pandoc 转换失败: {process.stderr.decode('utf-8')}")
            return False
        return True
    except FileNotFoundError:
        logging.error("Pandoc 未安装，请先运行: sudo apt install pandoc")
        return False


def str2docx(
        markdown_str,
        output_docx,
        template=DEFAULT_TEMPLATE,
        dpi=DEFAULT_DPI,
        extract_media=None
):
    """
    将 Markdown 字符串转换为 .docx 文件（Linux 版本）
    """
    if not isinstance(markdown_str, str):
        logging.error("markdown_str 必须是字符串")
        return False

    # 确保输出目录存在
    Path(output_docx).parent.mkdir(parents=True, exist_ok=True)

    # 构建 pandoc 命令参数
    cmd = [
        '-', '--to', 'docx', '--output', output_docx,
        '--standalone', f'--dpi={dpi}',
        '--wrap=preserve',
        '--highlight-style=pygments'
    ]

    # 如果模板存在则添加
    if template and os.path.exists(template):
        cmd.extend(['--reference-doc', template])
    elif template:
        logging.warning(f"模板文件不存在: {template}")

    # 添加媒体提取目录
    if extract_media:
        Path(extract_media).mkdir(parents=True, exist_ok=True)
        cmd.extend(['--extract-media', extract_media])

    logging.debug(f"执行命令: pandoc {' '.join(cmd)}")

    success = _run_pandoc(cmd, input_data=markdown_str.encode('utf-8'))

    if success:
        logging.info(f"✅ 成功生成 Word 文件: {output_docx}")
    else:
        logging.error("❌ 生成失败")
    return success

PDF_ENGINE_PATH = None
def html2pdf(
        html_str: str,
        output_pdf: str,
) -> bool:
    """
    Linux: HTML 字符串 → PDF 文件

    :param html_str: HTML 内容字符串
    :param output_pdf: 输出 PDF 文件路径
    :return: bool 是否成功
    """
    if not isinstance(html_str, str):
        logging.error("html_str 必须是字符串")
        return False

    # 创建输出目录
    Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)

    # PDF 引擎
    pdf_engine = PDF_ENGINE_PATH if PDF_ENGINE_PATH and Path(PDF_ENGINE_PATH).exists() else "wkhtmltopdf"
    logging.info(f"📄 使用 PDF 引擎: {pdf_engine}")

    # Pandoc 命令
    cmd = [
        "-",                  # 从 stdin 读取 HTML
        "--from", "html",
        "--to", "pdf",
        "--output", output_pdf,
        "--standalone",
        "--pdf-engine", pdf_engine
    ]

    # 调用 Pandoc
    success = _run_pandoc(cmd, input_data=html_str.encode("utf-8"))

    if success:
        logging.info(f"✅ 成功生成 PDF: {output_pdf}")
    return success

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

if __name__ == "__main__":
    pass