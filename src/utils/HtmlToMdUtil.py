import base64
import email
import io
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, unquote, urlparse

import requests
from PIL import Image
from readability import Document
import html2text
from utils.imgToBase64Utils import Image2Base64


# ============ 图片下载和处理类 ============
class ImageDownloader:
    """下载和处理图片的类"""

    def __init__(self, session: requests.Session = None, timeout: int = 15):
        self.session = session or requests.Session()
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def download_image(self, img_url: str, base_url: str) -> Optional[bytes]:
        """下载图片"""
        try:
            # 处理相对URL
            if not img_url.startswith(('http://', 'https://', 'data:')):
                img_url = urljoin(base_url, img_url)

            # 跳过data URL
            if img_url.startswith('data:'):
                return None

            response = self.session.get(
                img_url,
                headers=self.headers,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            # 检查是否为图片
            content_type = response.headers.get('Content-Type', '').lower()
            if not any(x in content_type for x in ['image/', 'octet-stream']):
                return None

            return response.content

        except Exception as e:
            print(f"下载图片失败 {img_url}: {e}")
            return None

    def convert_to_base64(self, image_data: bytes, image_url: str = "") -> str:
        """将图片数据转换为Base64 Markdown格式"""
        try:
            # 将字节数据转换为PIL Image对象
            img = Image.open(io.BytesIO(image_data))

            # 使用ImageFile2Base64转换为Base64
            final_data, mime_type = Image2Base64.convert_image(
                img=img,
                max_dim=1200,
                max_kb=200,
                force_webp=True,
                quality=80
            )

            # 生成Base64字符串
            b64_str = base64.b64encode(final_data).decode('utf-8')
            data_uri = f"data:{mime_type};base64,{b64_str}"

            # 从URL提取文件名作为alt文本
            if image_url:
                filename = Path(unquote(urlparse(image_url).path)).stem
                return f"![{filename}]({data_uri})"
            else:
                return f"![]({data_uri})"

        except Exception as e:
            print(f"转换图片为Base64失败: {e}")
            # 返回原始URL作为备选
            if image_url:
                return f"![图片]({image_url})"
            return "![图片加载失败]"

class HtmlToMd:
    @staticmethod
    def _save_markdown(markdown_text: str, output_path: Path):
        """辅助函数：保存 Markdown 到文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
    @staticmethod
    def _html_to_md_core(html: str, base_url: str = "", local_image: bool = False) -> str:
        """核心 HTML 转 Markdown 逻辑，支持图片本地化"""
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0
        h.single_line_break = True
        h.use_automatic_links = False
        h.wrap_links = False
        h.wrap_list_items = False
        h.emphasis_mark = '*'

        # 先转换为基本Markdown
        markdown = h.handle(html).strip()

        # 如果需要本地化图片
        if local_image and base_url:
            markdown = HtmlToMd._process_images_in_markdown(markdown, base_url)

        return markdown

    @staticmethod
    def _process_images_in_markdown(markdown: str, base_url: str) -> str:
        """处理Markdown中的图片链接，转换为Base64"""
        import re

        # 创建图片下载器
        downloader = ImageDownloader()

        # 正则匹配Markdown图片格式：![alt](url)
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'

        def replace_image(match):
            alt_text = match.group(1)
            img_url = match.group(2)

            # 如果已经是data URI，跳过
            if img_url.startswith('data:'):
                return match.group(0)

            # 下载图片
            img_data = downloader.download_image(img_url, base_url)
            if img_data:
                # 转换为Base64格式
                base64_markdown = downloader.convert_to_base64(img_data, img_url)
                return base64_markdown
            else:
                # 下载失败，保留原链接
                return match.group(0)

        # 替换所有图片链接
        return re.sub(img_pattern, replace_image, markdown)

    @staticmethod
    def mhtml_to_markdown(mhtml_path, output_md_path=None, article_mode=False, local_image=False):
        """
        将 MHTML 文件转换为 Markdown。

        :param mhtml_path: 输入的 .mhtml 文件路径
        :param output_md_path: 输出的 .md 文件路径（可选，默认为同名 .md）
        :param article_mode: 是否使用 readability 提取正文
        :param local_image: 是否将图片转换为Base64嵌入
        :return: Markdown 文本字符串
        """
        mhtml_path = Path(mhtml_path)
        if output_md_path is None:
            output_md_path = mhtml_path.with_suffix('.md')
        else:
            output_md_path = Path(output_md_path)

        # 读取 MHTML
        with open(mhtml_path, 'rb') as f:
            msg = email.message_from_binary_file(f)

        html_content = None
        base_url = ""

        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                try:
                    html_content = payload.decode(charset)
                except (UnicodeDecodeError, LookupError):
                    html_content = payload.decode('utf-8', errors='replace')

                # 尝试从MHTML中提取基础URL
                content_location = part.get('Content-Location', '')
                if content_location:
                    base_url = content_location
                break

        if html_content is None:
            raise ValueError("未在 MHTML 文件中找到 HTML 部分")

        # 可选：用 readability 提取正文
        if article_mode:
            doc = Document(html_content)
            title = doc.title()
            html_content = doc.summary()
            markdown_text = f"# {title}\n\n" + HtmlToMd._html_to_md_core(
                html_content, base_url, local_image
            )
        else:
            markdown_text = HtmlToMd._html_to_md_core(html_content, base_url, local_image)

        HtmlToMd._save_markdown(markdown_text, output_md_path)
        return markdown_text

    @staticmethod
    def html_to_md(html: str, output_md_path=None, article_mode=False, local_image=False, base_url: str = "") -> str:
        """
        将 HTML 字符串转换为 Markdown。

        :param html: HTML 源码字符串
        :param output_md_path: 输出文件路径（可选）
        :param article_mode: 是否提取正文
        :param local_image: 是否将图片转换为Base64嵌入
        :param base_url: 基础URL，用于解析相对图片路径
        :return: Markdown 字符串
        """
        if article_mode:
            doc = Document(html)
            title = doc.title()
            clean_html = doc.summary()
            markdown_text = f"# {title}\n\n" + HtmlToMd._html_to_md_core(
                clean_html, base_url, local_image
            )
        else:
            markdown_text = HtmlToMd._html_to_md_core(html, base_url, local_image)

        if output_md_path:
            HtmlToMd._save_markdown(markdown_text, Path(output_md_path))

        return markdown_text
    @staticmethod
    def url_to_markdown(url: str, output_md_path=None, article_mode=True, local_image=False) -> str:
        """
        从 URL 抓取网页并转为 Markdown。

        :param url: 网页 URL
        :param output_md_path: 输出文件路径（可选）
        :param article_mode: 是否提取正文（默认 True）
        :param local_image: 是否将图片转换为Base64嵌入
        :return: Markdown 字符串
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            session = requests.Session()
            res = session.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            html_bytes = res.content  # 👈 原始字节，不要用 res.text！
            # 1. 尝试从 HTML 中提取 charset
            encoding = HtmlToMd._extract_charset_from_html(html_bytes)

            # 2. 如果没找到，再考虑 apparent_encoding，但要过滤明显错误的猜测
            if not encoding:
                ae = res.apparent_encoding
                # 如果是中文网站，Windows-1254 / ISO-8859-1 基本可判定为误判
                if ae and ae.lower() not in ('windows-1254', 'iso-8859-1', 'ascii'):
                    encoding = ae
                else:
                    encoding = 'utf-8'  # 默认对现代网站更安全

            # 3. 安全解码
            try:
                html = html_bytes.decode(encoding, errors='strict')
            except (UnicodeDecodeError, LookupError):
                # fallback 到 utf-8 with replace
                html = html_bytes.decode('utf-8', errors='replace')

            base_url = url
        except Exception as e:
            raise RuntimeError(f"无法获取网页 {url}: {e}")

        if article_mode:
            doc = Document(html)
            title = doc.title()
            clean_html = doc.summary()
            markdown_text = f"# {title}\n\n" + HtmlToMd._html_to_md_core(
                clean_html, base_url, local_image
            )
        else:
            markdown_text = HtmlToMd._html_to_md_core(html, base_url, local_image)

        if output_md_path:
            HtmlToMd._save_markdown(markdown_text, Path(output_md_path))

        return markdown_text

    @staticmethod
    def _extract_charset_from_html(html_bytes: bytes) -> str | None:
        """从 HTML 前 2KB 中提取 <meta charset> 声明"""
        # 用 latin1 安全解码前段（不会报错）
        import re
        sample = html_bytes[:2048].decode('latin1', errors='ignore')

        # 匹配 <meta charset="xxx"> 或 <meta http-equiv="Content-Type" content="...charset=xxx...">
        match = re.search(
            r'<meta[^>]+charset\s*=\s*[\'"]?([a-zA-Z0-9\-_]+)',
            sample,
            re.IGNORECASE
        )
        if match:
            return match.group(1).strip().lower()

        # 兼容旧式写法
        match2 = re.search(
            r'<meta[^>]+http-equiv\s*=\s*[\'"]?content-type[\'"]?[^>]*content\s*=\s*[\'"][^\'"]*charset\s*=\s*([a-zA-Z0-9\-_]+)',
            sample,
            re.IGNORECASE
        )
        if match2:
            return match2.group(1).strip().lower()

        return None

def convert_to_md(html: str | Path |bytes, output_md_path=None, article_mode=False, local_image=True):
    """
    智能转换：根据输入自动判断是 URL、HTML/MHTML 文件 或 HTML 字符串，并转为 Markdown。

    :param html: 可以是：
                 - URL 字符串（如 "https://example.com"）
                 - 本地文件路径（.html, .htm, .mhtml）
                 - 纯 HTML 字符串（不包含换行开头的典型文件路径特征）
                 - bytes类型
    :param output_md_path: 输出 Markdown 路径（可选）
    :param article_mode: 是否提取正文（对网页有效）
    :param local_image: 是否嵌入图片为 Base64
    :return: Markdown 字符串
    """
    # ====== 处理 bytes 输入 ======
    if isinstance(html, bytes):
        # 尝试解码：优先 UTF-8，其次 GB18030，最后 replace
        for encoding in ['utf-8', 'gb18030']:
            try:
                html_str = html.decode(encoding)
                return HtmlToMd.html_to_md(
                    html=html_str,
                    output_md_path=output_md_path,
                    article_mode=article_mode,
                    local_image=local_image,
                )
            except UnicodeDecodeError:
                continue
        # fallback
        html_str = html.decode('utf-8', errors='replace')
        return HtmlToMd.html_to_md(
            html=html_str,
            output_md_path=output_md_path,
            article_mode=article_mode,
            local_image=local_image,
        )

    # 统一转为 Path 对象（如果是字符串路径）
    if isinstance(html, str):
        # 判断是否为 URL
        parsed = urlparse(html)
        if parsed.scheme in ('http', 'https') and parsed.netloc:
            # 是 URL
            return HtmlToMd.url_to_markdown(
                url=html,
                output_md_path=output_md_path,
                article_mode=article_mode,
                local_image=local_image
            )

        # 判断是否为本地文件路径（存在且扩展名匹配）
        path = Path(html)
        if path.exists() and path.is_file():
            suffix = path.suffix.lower()
            if suffix in ('.html', '.htm', '.mhtml'):
                if suffix == '.mhtml':
                    return HtmlToMd.mhtml_to_markdown(
                        mhtml_path=path,
                        output_md_path=output_md_path,
                        article_mode=article_mode,
                        local_image=local_image
                    )
                else:
                    # .html / .htm
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        html_content = f.read()
                    return HtmlToMd.html_to_md(
                        html=html_content,
                        output_md_path=output_md_path,
                        article_mode=article_mode,
                        local_image=local_image,
                        base_url=path.as_uri()  # 用于相对资源解析
                    )

        # 否则视为纯 HTML 字符串
        return HtmlToMd.html_to_md(
            html=html,
            output_md_path=output_md_path,
            article_mode=article_mode,
            local_image=local_image,
            base_url=""  # 无 base_url，图片可能无法下载
        )

    elif isinstance(html, Path):
        # 明确是 Path 对象
        if not html.exists() or not html.is_file():
            raise FileNotFoundError(f"文件不存在: {html}")

        suffix = html.suffix.lower()
        if suffix == '.mhtml':
            return HtmlToMd.mhtml_to_markdown(
                mhtml_path=html,
                output_md_path=output_md_path,
                article_mode=article_mode,
                local_image=local_image
            )
        elif suffix in ('.html', '.htm'):
            with open(html, 'r', encoding='utf-8', errors='replace') as f:
                html_content = f.read()
            return HtmlToMd.html_to_md(
                html=html_content,
                output_md_path=output_md_path,
                article_mode=article_mode,
                local_image=local_image,
                base_url=html.as_uri()
            )
        else:
            # 假设是纯文本 HTML 内容？不太合理，但可读取内容
            with open(html, 'r', encoding='utf-8', errors='replace') as f:
                html_content = f.read()
            return HtmlToMd.html_to_md(
                html=html_content,
                output_md_path=output_md_path,
                article_mode=article_mode,
                local_image=local_image,
                base_url=""
            )

    else:
        raise TypeError("参数 'html' 必须是 str 、 bytes 或 pathlib.Path 类型")


if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    html = "https://news.qq.com/rain/a/20260114A01NI000"
    html = "https://www.aituple.com"
    # html = "https://www.indexdoc.com"
    html = r"D:\测试目录_全面\mhtml\IndexDoc.com - 专业的AI文档服务平台.mhtml"
    # html = "https://www.indexdoc.com/contact.html"
    md = convert_to_md(html,'./IndexDoc.com - 专业的AI文档服务平台.md')
    # md = mhtml_to_markdown(mhtml)
    print(md)
