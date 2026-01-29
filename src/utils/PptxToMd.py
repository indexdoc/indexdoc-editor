import pptx2md
from pathlib import Path
import os
import tempfile
import shutil  # 新增：用于清理临时目录


# 导入你的IDUtil工具类
from utils import IDUtil
from utils.ImgToBase64Utils import OutputFormat
from utils.ImgToBase64Utils import Image2Base64

def replace_img_with_base64(md_file: Path, img_dir: Path, del_temp_img: bool = True):
    """
    终极修复版：解决URL编码(%5C)、Windows反斜杠、相对/绝对路径等所有匹配问题
    :param md_file: 生成的MD文件路径
    :param img_dir: pptx2md导出的临时图片目录
    :param del_temp_img: 是否删除临时图片/目录（推荐True）
    """
    import urllib.parse  # 内置库，无需额外安装，处理URL编码/解码

    if not md_file.exists() or not img_dir.is_dir():
        print(f"⚠ 跳过Base64替换：MD文件或图片目录不存在")
        return

    # 1. 读取MD内容，保留原始编码格式
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    img_path_2_b64 = {}
    # 2. 遍历临时图片，生成所有需要匹配的路径格式 + Base64映射
    for img_file in img_dir.glob("*.*"):
        if not img_file.is_file():
            continue
        try:
            # 调用你的Base64工具类生成MD格式的Base64（参数可按需求调整）
            b64_md_str = Image2Base64.convert_file(
                image_path=img_file,
                max_dim=1200,
                max_kb=200,
                force_webp=True,
                out_format=OutputFormat.MARKDOWN_ALT,
                quality=80
            )

            # 关键：生成5种需要替换的路径格式，覆盖pptx2md所有生成情况
            img_dir_name = img_dir.name  # 临时目录名（如4fb6cc7bfcbb11f0aefebc2411ecbf31_pptx_imgs）
            img_name = img_file.name     # 图片名（如测试文件_0.jpg）
            # 格式1：绝对路径（C:\Temp\xxx_imgs\测试文件_0.jpg）
            img_path_2_b64[str(img_file)] = b64_md_str
            # 格式2：纯文件名（测试文件_0.jpg）
            img_path_2_b64[img_name] = b64_md_str
            # 格式3：Windows原始反斜杠相对路径（xxx_imgs\测试文件_0.jpg）
            win_relative_path = f"{img_dir_name}\\{img_name}"
            img_path_2_b64[win_relative_path] = b64_md_str
            # 格式4：URL编码后的相对路径（xxx_imgs%5C测试文件_0.jpg）【核心修复项】
            url_encoded_path = urllib.parse.quote(win_relative_path, safe='')
            img_path_2_b64[url_encoded_path] = b64_md_str
            # 格式5：正斜杠相对路径（xxx_imgs/测试文件_0.jpg）【兼容兜底】
            slash_relative_path = f"{img_dir_name}/{img_name}"
            img_path_2_b64[slash_relative_path] = b64_md_str

        except Exception as e:
            print(f"⚠ 单张图片转Base64失败: {img_file.name} | 错误: {e}")
            continue

    # 3. 批量替换：按「长路径优先」替换，避免短路径匹配冲突
    # 排序：路径越长越先替换，防止纯文件名先匹配导致长路径替换失败
    for raw_img_path in sorted(img_path_2_b64.keys(), key=len, reverse=True):
        md_content = md_content.replace('![]('+raw_img_path+')', img_path_2_b64[raw_img_path])

    # 4. 重写MD文件，写入Base64内嵌内容
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 5. 清理临时图片目录，避免冗余
    if del_temp_img:
        try:
            import shutil
            shutil.rmtree(img_dir)
            print(f"✅ 清理临时图片目录完成: {img_dir.name}")
        except Exception as e:
            print(f"⚠ 临时图片目录清理失败: {e}")

def pptx_to_md(pptx_file):
    """单文件PPT转MD：图片自动转为Base64内嵌"""
    # 生成唯一的MD文件名和专属图片临时目录（避免多文件冲突）
    uuid_str = IDUtil.get_uuid()
    md_file_path = Path(tempfile.gettempdir()) / f"{uuid_str}.md"
    temp_img_dir = Path(tempfile.gettempdir()) / f"{uuid_str}_pptx_imgs"
    temp_img_dir.mkdir(parents=True, exist_ok=True)  # 创建专属图片目录

    # 配置pptx2md转换参数
    config = pptx2md.ConversionConfig(
        pptx_path=pptx_file,
        output_path=md_file_path,
        image_dir=temp_img_dir,  # 图片导出到「专属临时目录」，而非全局临时目录
        disable_notes=True       # 根据需求调整：是否禁用PPT备注页转换
    )
    # 执行PPT转MD（此时MD中是图片路径，图片在临时目录）
    pptx2md.convert(config)
    # 核心步骤：调用替换函数，将MD中的图片路径改为Base64内嵌
    replace_img_with_base64(md_file_path, temp_img_dir)

    return md_file_path


def batch_pptx_to_md(input_dir: str, output_dir: str = None, image_dir: str = None):
    """
    批量PPT转MD：图片自动转为Base64内嵌（原image_dir参数失效，无需传值）
    Args:
        input_dir (str): 包含 PPTX 文件的文件夹路径
        output_dir (str, optional): 输出 Markdown 文件的文件夹。若为 None，则输出到与 PPTX 相同位置
        image_dir (str, optional): 兼容原参数，实际已失效（图片不再导出到该目录，直接内嵌Base64）
    """
    input_path = Path(input_dir)
    if not input_path.exists() or not input_path.is_dir():
        raise ValueError(f"输入目录不存在或不是文件夹: {input_dir}")

    # 处理输出目录
    if output_dir is None:
        output_path = input_path
    else:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    # 筛选所有pptx文件
    pptx_files = list(input_path.glob("*.pptx"))
    if not pptx_files:
        print(f"在 {input_dir} 中未找到 .pptx 文件")
        return

    print(f"发现 {len(pptx_files)} 个 PPTX 文件，开始转换（图片自动Base64内嵌）...\n")

    # 批量转换
    for pptx_file in pptx_files:
        try:
            md_file = output_path / f"{pptx_file.stem}.md"
            # 为当前PPT创建专属临时图片目录（避免多PPT图片冲突）
            uuid_str = IDUtil.get_uuid()
            temp_img_dir = Path(tempfile.gettempdir()) / f"{uuid_str}_{pptx_file.stem}_imgs"
            temp_img_dir.mkdir(parents=True, exist_ok=True)

            # 配置pptx2md
            config = pptx2md.ConversionConfig(
                pptx_path=pptx_file,
                output_path=md_file,
                image_dir=temp_img_dir,  # 图片导出到专属临时目录
                disable_notes=True
            )

            print(f"正在转换: {pptx_file.name}")
            pptx2md.convert(config)
            # 核心：替换图片路径为Base64
            replace_img_with_base64(md_file, temp_img_dir)
            print(f"✅ 转换成功: {md_file.name}\n")

        except Exception as e:
            print(f"❌ 转换失败: {pptx_file.name} | 错误: {e}\n")
            continue

    print("📌 批量转换完成！所有MD文件均为图片Base64内嵌格式")


if __name__ == "__main__":
    # 配置你的路径（image_folder无需传值，已失效）
    input_folder = r'D:\测试目录_全面\ppt'  # 你的PPT文件夹路径
    output_folder = './markdown_out'       # MD输出路径，设为None则输出到PPT同目录
    # image_folder = None  # 无需设置，图片直接Base64内嵌，该参数失效

    # 执行批量转换
    batch_pptx_to_md(
        input_dir=input_folder,
        output_dir=output_folder,
        # image_dir无需传值，保留原参数仅为兼容
    )