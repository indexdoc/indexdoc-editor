import base64
import io
from pathlib import Path
from typing import Union, Optional
from PIL import Image
import olefile #部分图像格式用到，必须保留


class OutputFormat:
    """定义输出格式枚举"""
    MARKDOWN_ALT = 'MARKDOWN_ALT'  # ![文件名](data:...)
    MARKDOWN_NO_ALT = 'MARKDOWN_NO_ALT'  # ![](data:...)
    RAW_BASE64 = 'RAW_BASE64'  # 纯 Base64 字符串
    MIME_BASE64 = 'MIME_BASE64'  # data:image/xxx;base64,...


class Image2Base64:
    """
    智能图像转 Base64 工具类
    特性：支持 HEIC/PSD/SVG、智能缩放、二分法压缩、透明度自动合成
    """
    _SUPPORTED_EXTS = {
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp',
        '.bmp', '.tiff', '.tif', '.ico', '.psd', '.heic', '.heif'
    }
    _NEED_CONVERSION = {'.bmp', '.tiff', '.tif', '.ico', '.psd', '.heic', '.heif'}
    _MIME_MAP = {
        '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp',
    }

    @classmethod
    def convert_file(
            cls,
            image_path: Union[str, Path],
            max_dim: int = 1200,  # 限制长边像素
            max_kb: int = 200,  # 目标最大体积 (KB)
            force_webp: bool = True,  # 强制转为 WebP (推荐)
            out_format: str = OutputFormat.MARKDOWN_ALT,
            quality: int = 80  # 初始压缩质量
    ) -> str:
        # 0. 前置校验
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

        ext = path.suffix.lower()
        if ext not in cls._SUPPORTED_EXTS:
            supported_list = ", ".join(sorted(cls._SUPPORTED_EXTS))
            raise ValueError(f"Unsupported extension '{ext}'. Supported: {supported_list}")

        final_data: bytes = b""
        mime_type: str = ""

        # 1. 矢量图处理 (SVG) - 保持矢量特性，不走 Pillow
        if ext == '.svg':
            with open(path, 'rb') as f:
                final_data = f.read()
            mime_type = "image/svg+xml"

        # 2. 位图处理流程
        else:
            # HEIC 特殊加载支持
            if ext in ['.heic', '.heif']:
                try:
                    from pillow_heif import register_heif_opener
                    register_heif_opener()
                except ImportError:
                    raise ImportError("Please install 'pillow-heif' to support HEIC files.")

            with Image.open(path) as img:
                # 确定目标格式与 MIME
                final_data, mime_type = cls.convert_image(img, max_dim,max_kb,force_webp,quality )
        # 3. 输出格式化
        b64_str = base64.b64encode(final_data).decode('utf-8')

        if out_format == OutputFormat.RAW_BASE64:
            return b64_str

        data_uri = f"data:{mime_type};base64,{b64_str}"

        if out_format == OutputFormat.MIME_BASE64:
            return data_uri
        elif out_format == OutputFormat.MARKDOWN_NO_ALT:
            return f"![]({data_uri})"
        else:  # 默认 MARKDOWN_ALT
            return f"![{path.stem}]({data_uri})"

    @classmethod
    def convert_image(
            cls,
            img: Image.Image,
            max_dim: int = 1200,
            max_kb: int = 200,
            force_webp: bool = True,
            quality: int = 80
    ) -> tuple[bytes, str]:
        """
        核心处理逻辑：接收 Pillow Image 对象，返回压缩后的字节流和 MIME 类型
        """
        # 1. 确定格式
        if force_webp:
            target_format, mime_type = "WEBP", "image/webp"
        else:
            # 默认转 PNG 保证兼容性
            target_format, mime_type = "PNG", "image/png"

        # 2. 透明度处理
        if target_format in ["JPEG", "WEBP"] or img.mode not in ["RGB", "RGBA", "L"]:
            if img.mode in ["RGBA", "LA", "P"]:
                background = Image.new('RGB', img.size, (255, 255, 255))
                temp_rgba = img.convert('RGBA')
                background.paste(temp_rgba, mask=temp_rgba.split()[-1])
                img = background
            else:
                img = img.convert('RGB')

        # 3. 等比缩放
        if max(img.width, img.height) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        # 4. 二分法压缩
        raw_target_size = (max_kb * 1024) * 0.75
        if target_format == "PNG":
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue(), mime_type
        else:
            low, high = 30, quality
            best_data = None
            for _ in range(3):
                mid = (low + high) // 2
                buf = io.BytesIO()
                img.save(buf, format=target_format, quality=mid, optimize=True)
                data = buf.getvalue()
                if len(data) <= raw_target_size:
                    best_data, low = data, mid + 5
                else:
                    high = mid - 5
            return (best_data if best_data else buf.getvalue()), mime_type

    @classmethod
    def batch_convert(
            cls,
            input_dir: Union[str, Path],
            output_md: Optional[Union[str, Path]] = None,
            max_dim: int = 1200,
            max_kb: int = 200,
            force_webp: bool = True,
            out_format: str = OutputFormat.MARKDOWN_ALT,
            quality: int = 80
    ) -> dict:
        """
        批量转换目录下所有支持的图片文件
        :param input_dir: 输入目录路径
        :param output_md: 可选，将结果保存到的 Markdown 文件路径
        :return: 包含 {文件名: Base64结果} 的字典
        """
        input_path = Path(input_dir)
        if not input_path.is_dir():
            raise ValueError(f"'{input_dir}' is not a valid directory.")

        results = {}
        # 获取所有支持的文件并排序
        files = sorted([f for f in input_path.iterdir() if f.suffix.lower() in cls._SUPPORTED_EXTS])

        if not files:
            print(f"No supported images found in {input_dir}")
            return results

        print(f"Starting batch conversion of {len(files)} images...")

        for file_path in files:
            try:
                # 调用单文件转换方法
                res = cls.convert_file(
                    image_path=file_path,
                    max_dim=max_dim,
                    max_kb=max_kb,
                    force_webp=force_webp,
                    out_format=out_format,
                    quality=quality
                )
                results[file_path.name] = res
                print(f"✓ Converted: {file_path.name}")
            except Exception as e:
                print(f"✗ Failed: {file_path.name} | Error: {e}")

        # 如果指定了输出文件，则写入 Markdown
        if output_md:
            cls._save_to_markdown(results, output_md)

        return results

    @staticmethod
    def _save_to_markdown(results: dict, output_path: Union[str, Path]):
        """内部辅助：将结果写入文件"""
        output_path = Path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Image Conversion Report\n\n")
            f.write(f"Total processed: {len(results)}\n\n---\n\n")
            for name, content in results.items():
                f.write(f"### {name}\n\n")
                # 如果内容本身不是 markdown 格式，则包裹一下
                if not content.startswith('!['):
                    f.write(f"```text\n{content}\n```\n\n")
                else:
                    f.write(f"{content}\n\n")
        print(f"\n★ All results saved to: {output_path.absolute()}")

if __name__ == '__main__':
    Image2Base64.batch_convert(
        input_dir= r"D:\测试目录_全面\img",
        output_md="gallery.md",
        max_kb=150,  # 每个图片限制在 150KB 以内
        force_webp=True,
        out_format=OutputFormat.MARKDOWN_ALT
    )
