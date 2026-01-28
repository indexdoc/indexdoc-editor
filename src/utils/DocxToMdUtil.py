import mammoth
import markdownify
from PIL import Image
import io
import base64

def convert_docx_to_md(docx_path ,need_compress_img=True):
    with open(docx_path, "rb") as docx_file:
        # 使用 mammoth 转换为 HTML
        # mammoth 的 HTML 转换比直接转 MD 更稳定，结构更清晰
        if need_compress_img:
            result = mammoth.convert_to_html(docx_file,convert_image=mammoth.images.img_element(image_handler))
        else:
            result = mammoth.convert_to_html(docx_file)
        html = result.value
        # 将 HTML 转换为标准的 Markdown
        markdown_content = markdownify.markdownify(html, heading_style="ATX")
        return markdown_content

def image_handler(image):
    """
    mammoth 自定义图片处理器
    它会拦截 Word 中的图片，并进行压缩处理
    """
    with image.open() as image_bytes:
        # 1. 将原始二进制流载入 Pillow
        img = Image.open(image_bytes)

        # 2. 执行压缩逻辑 (参考之前的核心逻辑)
        # 比如：限制长边 1000px，转为 WebP
        max_dim = 1000
        if max(img.width, img.height) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        output = io.BytesIO()
        # 转换为性价比最高的 WEBP 格式
        img.save(output, format="WEBP", quality=75, optimize=True)
        optimized_data = output.getvalue()

        # 3. 返回 HTML 属性，mammoth 会将其放入 <img> 标签的 src
        encoded_data = base64.b64encode(optimized_data).decode("utf-8")
        return {
            "src": f"data:image/webp;base64,{encoded_data}"
        }

if __name__ == "__main__":
    import time
    start = time.time()
    md_text= convert_docx_to_md(r"D:\测试目录_全面\docx\xxxx省烟草公司xx市公司微xx服务软件开发服务平台投标文件-终稿（共666页）.docx")
    print(time.time()-start)
    start = time.time()
    md_text= convert_docx_to_md(r"D:\测试目录_全面\docx\xxxx省烟草公司xx市公司微xx服务软件开发服务平台投标文件-终稿（共666页）.docx",False)
    print(time.time()-start)

    with open('./test.md','w',encoding='utf-8') as f:
        f.write(md_text)


