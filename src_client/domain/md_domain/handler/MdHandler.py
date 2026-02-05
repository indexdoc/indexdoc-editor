import base64
import json
import os
import re
import uuid

import config
import pyperclip as pyperclip
from util import FileUtil
import frozen_support
from domain.base_domain.BaseHandler import BaseApiHandler
from util.markdown import MarkDownUtil

from indexdoc_converter.pptx_to_md import pptx_to_md
from indexdoc_converter.docx_to_md import convert_docx_to_md
from indexdoc_converter.excel_to_md import TableToMarkdown
from indexdoc_converter.html_to_md import convert_to_md

class ApiMdWordHandler(BaseApiHandler):
    need_login = False

    def myget(self):
        pass

    def mypost(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        data = json.loads(self.request.body.decode("utf-8"))
        _md_content = data.get("md_content", "")
        # _md_content = _md_content.replace('\n','\n\n')
        tmp_path = frozen_support.get_tmp_path()
        output_path = f"{tmp_path}/{uuid.uuid4().hex}.docx"
        _status = MarkDownUtil.str2docx(markdown_str=_md_content, output_docx=output_path)
        if _status:
            with open(output_path, "rb") as f:
                file_bytes = f.read()
            encoded = base64.b64encode(file_bytes).decode("utf-8")
            self.write({"success": True, "msg": "导出成功", "file": encoded})
        else:
            self.write({"success": False, "msg": "导出失败"})

class ApiMdFileHandler(BaseApiHandler):
    need_login = False

    def myget(self):
        pass

    def mypost(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        data = json.loads(self.request.body.decode("utf-8"))
        _md_content = data.get("md_content", "")
        tmp_path = frozen_support.get_tmp_path()
        output_path = f"{tmp_path}/{uuid.uuid4().hex}.md"
        _status = MarkDownUtil.str2md(markdown_str=_md_content, output_md=output_path)
        if _status:
            with open(output_path, "rb") as f:
                file_bytes = f.read()
            encoded = base64.b64encode(file_bytes).decode("utf-8")
            self.write({"success": True, "msg": "导出成功", "file": encoded})
        else:
            self.write({"success": False, "msg": "导出失败"})


class ApiMdPasteHandler(BaseApiHandler):
    need_login = False

    # 实现标准的 get 方法（即使只处理 POST，也要实现空的 get 方法避免 405）
    def myget(self):
        # 可以直接返回 405 提示，更规范
        self.set_status(405)
        self.write({"success": False, "msg": "该接口仅支持 POST 方法"})

    def mypost(self):
        try:
            text = pyperclip.paste()  # 读取剪贴板内容
            text = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', text)
            self.write({"success": True, "data": text})
        except Exception as e:
            self.set_status(500)
            self.write({"success": False, "msg": f"读取剪贴板失败: {str(e)}"})


class ApiMdPdfHandler(BaseApiHandler):
    need_login = False

    def myget(self):
        pass

    def mypost(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        data = json.loads(self.request.body.decode("utf-8"))
        _html_content = data.get("html_content", "")
        tmp_path = frozen_support.get_tmp_path()
        output_path = f"{tmp_path}/{uuid.uuid4().hex}.docx"  # 注意：这里文件名是 docx 但实际是 pdf？建议修正
        _status = MarkDownUtil.html2pdf(_html_content, output_path)
        if _status:
            with open(output_path, "rb") as f:
                file_bytes = f.read()
            encoded = base64.b64encode(file_bytes).decode("utf-8")
            self.write({"success": True, "msg": "导出成功", "file": encoded})
        else:
            self.write({"success": False, "msg": "导出失败"})


class ApiImportFileHandler(BaseApiHandler):
    need_login = False

    def mypost(self):
        upload_path = config.user_file_path + '/upload/'  # 文件的暂存路径
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file_metas = self.request.files.get('file', None)

        if not file_metas or len(file_metas) == 0:
            _rtn = {'success': False, 'msg': '文件为空！', 'obj': None}
            self.write(_rtn)
            return

        file_meta = file_metas[0]
        # 获取文件后缀
        _file_suffix = FileUtil.get_file_suffix(file_meta['filename'])
        support_suffix = {'.docx', '.xlsx', '.xls', '.ods', '.csv', '.tsv', '.html', '.mhtml', '.htm', '.pptx', '.md'}
        support_suffix_word = {'.docx'}
        support_suffix_excel = {'.xlsx', '.xls', '.ods', '.csv', '.tsv'}
        support_suffix_html = {'.html', '.mhtml', '.htm'}
        support_suffix_pptx = {'.pptx'}

        # 校验文件后缀，不支持则直接返回提示
        if _file_suffix not in support_suffix:
            _rtn = {'success': False,
                    'msg': '您当前上传的文件格式不支持，当前支持的文件类型有：Word、Excel、PPT、网页文件（.html、.mhtml、.htm）、Markdown',
                    }
            self.write(_rtn)
            return

        # 后缀校验通过，执行文件保存
        _file_path = upload_path + file_meta['filename']
        with open(_file_path, 'wb') as tempfile:
            tempfile.write(file_meta['body'])

        md_text = ""
        try:
            if _file_suffix in support_suffix_word:
                md_text = convert_docx_to_md(_file_path)
            elif _file_suffix in support_suffix_excel:
                converter = TableToMarkdown()
                md_result = converter.convert(_file_path)
                md_text = md_result['fill']
            elif _file_suffix in support_suffix_html:
                md_text = convert_to_md(_file_path, local_image=True)
            elif _file_suffix in support_suffix_pptx:
                md_file_path = pptx_to_md(_file_path)
                with open(md_file_path, 'r', encoding='utf-8') as f:
                    md_text = f.read()
                # 清理临时md文件
                if os.path.exists(md_file_path):
                    os.remove(md_file_path)
            # md文件直接读取内容
            elif _file_suffix == '.md':
                with open(_file_path, 'r', encoding='utf-8') as f:
                    md_text = f.read()
        except Exception as e:
            _rtn = {'success': False,
                    'msg': f'文件解析失败：{str(e)}',
                    }
            self.write(_rtn)
            # 清理上传的临时文件（可选，根据项目需求）
            if os.path.exists(_file_path):
                os.remove(_file_path)
            return
        finally:
            # 最终清理上传的源文件
            if os.path.exists(_file_path):
                os.remove(_file_path)
            pass

        # 转换成功，返回md内容给前端
        _rtn = {'success': True,
                'msg': '文件导入成功！',
                'context': md_text,
                }
        self.write(_rtn)
        return


urls = [
    ('/api/md/mdWord', ApiMdWordHandler),
    ('/api/md/mdFile', ApiMdFileHandler),
    ('/api/md/mdPdf', ApiMdPdfHandler),
    ('/api/md/mdPaste', ApiMdPasteHandler),
    ('/api/md/importFile', ApiImportFileHandler),
]