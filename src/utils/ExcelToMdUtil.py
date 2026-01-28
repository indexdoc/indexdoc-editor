import os
import sys
import time
import warnings
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd

from utils import FileUtil

pd.set_option('future.no_silent_downcasting', True)

# 忽略 Openpyxl 样式警告
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class TableToMarkdown:
    def __init__(self, file_title_level=1, single_row_value_as_title = True, max_rows=6000, max_cols=128):
        self.max_title_len = 20
        self.file_title_level = file_title_level
        self.max_rows = max_rows+1
        self.max_cols = max_cols+1
        self.file_title_start_char = '#'*file_title_level
        self.sheet_title_start_char = '#'*(file_title_level+1)
        if single_row_value_as_title:
            self.table_title_start_char = '#'*(file_title_level+2)
        else:
            self.table_title_start_char = ''

    def _safe_str(self, val) -> str:
        if pd.isna(val) or (isinstance(val, str) and not val.strip()):
            return ""
        s = str(val)
        replacements = {"|": "&#124;", "\n": "<br>", "\r": ""}
        for old, new in replacements.items():
            s = s.replace(old, new)
        return s.strip()

    def _get_merged_cells_by_read_xml(self, file_path):
        import zipfile
        from lxml import etree
        from openpyxl.utils import range_boundaries

        merges_by_name = {}
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                # 1. 建立 rId 到 XML 路径的映射 (修复路径匹配问题)
                rels_xml = z.read('xl/_rels/workbook.xml.rels')
                rels_root = etree.fromstring(rels_xml)
                rid_to_path = {
                    node.get('Id'): f"xl/{node.get('Target')}"
                    for node in rels_root.xpath('//*[local-name()="Relationship"]')
                }

                # 2. 获取 Sheet Name 对应的 rId
                wb_xml = z.read('xl/workbook.xml')
                wb_root = etree.fromstring(wb_xml)
                sheet_nodes = wb_root.xpath('//*[local-name()="sheet"]')

                for node in sheet_nodes:
                    name = node.get('name')
                    # 关键修复：处理带命名空间的属性获取
                    rid = node.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                    xml_path = rid_to_path.get(rid)

                    if not xml_path or xml_path not in z.namelist():
                        continue

                    # 3. 解析 mergeCells
                    m_rects = []
                    with z.open(xml_path) as f:
                        # 使用 local-name 过滤，增强兼容性
                        context = etree.iterparse(f, events=('end',),
                                                  tag='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}mergeCell')

                        found = False
                        for _, elem in context:
                            found = True
                            ref = elem.get('ref')
                            if ref:
                                min_col, min_row, max_col, max_row = range_boundaries(ref)
                                m_rects.append((min_row - 1, min_col - 1, max_row - 1, max_col - 1))
                            elem.clear()

                        # 如果没找到，尝试无命名空间解析
                        if not found:
                            f.seek(0)
                            context = etree.iterparse(f, events=('end',), tag='mergeCell')
                            for _, elem in context:
                                ref = elem.get('ref')
                                if ref:
                                    min_col, min_row, max_col, max_row = range_boundaries(ref)
                                    m_rects.append((min_row - 1, min_col - 1, max_row - 1, max_col - 1))
                                elem.clear()

                    merges_by_name[name] = m_rects
        except Exception as e:
            print(f"\n警告: 读取 XLSX 合并单元格失败: {e}")
        return merges_by_name

    def _get_data_and_merges(self, file_path: Path):
        ext = file_path.suffix.lower()
        result = {}
        if ext == '.xlsx':
            # 统一使用 dtype=str 避免 pandas 自动转换日期导致格式错乱
            all_dfs = pd.read_excel(file_path, sheet_name=None, header=None, dtype=str
                                    ,nrows = self.max_rows,usecols=lambda c: isinstance(c, int) and c < self.max_cols)
            merges_by_name = self._get_merged_cells_by_read_xml(file_path)
            for name, df in all_dfs.items():
                # 判断条件：1. DataFrame 本身没有行列 2. 或者剔除所有空值后依然没有数据
                if df.empty or df.dropna(how='all').dropna(axis=1, how='all').empty:
                    continue  # 跳过此 Sheet
                # 检查是否只有“仅包含空格”的单元格（更严格的过滤）
                if not df.stack().str.strip().any():
                    continue
                raw_merges = merges_by_name.get(name, [])
                result[name] = (df, self._clip_merges(df, raw_merges))
        elif ext == '.xls':
            import xlrd
            wb = xlrd.open_workbook(str(file_path), formatting_info=True)
            for sheet in wb.sheets():
                if sheet.nrows == 0 or sheet.ncols == 0:
                    continue
                actual_rows = min(sheet.nrows, self.max_rows)
                data = []
                for i in range(actual_rows):
                    row_values = []
                    # 获取该行所有单元格及其类型
                    cells = sheet.row(i)[:self.max_cols]
                    for cell in cells:
                        # xlrd 的 ctype: 2 代表数值 (XL_CELL_NUMBER)
                        if cell.ctype == 2:
                            # 检查是否为整数 (例如 123.0)
                            if cell.value == int(cell.value):
                                row_values.append(str(int(cell.value)))
                            else:
                                row_values.append(str(cell.value))
                        else:
                            row_values.append(cell.value)
                    data.append(row_values)
                df = pd.DataFrame(data)
                # 4. 深度内容检查：
                # 去除 DataFrame 中所有的 NaN，并检查剩余字符串是否全部为空白
                # .stack() 将二维转一维，.astype(str).str.strip() 处理空格，.any() 检查是否有任何真值
                if df.empty or not df.stack().astype(str).str.strip().replace('nan', '').any():
                    continue
                # 5. 处理合并单元格
                merges = [(r1, c1, r2 - 1, c2 - 1) for (r1, r2, c1, c2) in sheet.merged_cells]
                # 存储结果
                result[sheet.name] = (df, self._clip_merges(df, merges))
        elif ext == '.ods':
            # --- ODF 读取与空 Sheet 过滤 ---
            from odf import opendocument
            from odf.table import Table, TableRow
            from odf.teletype import extractText
            doc = opendocument.load(str(file_path))
            TABLE_NS = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
            for sheet in doc.spreadsheet.getElementsByType(Table):
                sheet_name = sheet.getAttribute("name")
                data, merged_rects = [], []
                rows = sheet.getElementsByType(TableRow)
                for r_idx, row in enumerate(rows):
                    if len(data) >= self.max_rows: break
                    row_data, col_idx = [], 0
                    for cell in row.childNodes:
                        if col_idx >= self.max_cols: break
                        tag = getattr(cell, 'tagName', '')
                        if 'table-cell' not in tag and 'covered-table-cell' not in tag: continue
                        attrs = cell.attributes
                        col_rep_val = attrs.get((TABLE_NS, 'number-columns-repeated'))
                        col_rep = min(int(col_rep_val or 1), self.max_cols - col_idx)
                        val = extractText(cell)
                        rs_val = attrs.get((TABLE_NS, 'number-rows-spanned'))
                        cs_val = attrs.get((TABLE_NS, 'number-columns-spanned'))
                        rs, cs = int(rs_val or 1), int(cs_val or 1)
                        for rep in range(col_rep):
                            row_data.append(val)
                            if (rs > 1 or cs > 1) and rep == 0:
                                merged_rects.append((len(data), col_idx,
                                                     len(data) + rs - 1,
                                                     col_idx + cs - 1))
                            col_idx += 1
                    data.append(row_data)
                # 1. 转换为 DataFrame
                df = pd.DataFrame(data)
                # 2. 核心：过滤空内容
                # 注意：ODS 提取的文字可能是空格，需要 strip() 之后检查
                if df.empty:
                    continue
                # 检查是否包含任何实质性内容（排除 NaN 和 仅空白字符）
                # 使用 numpy 优化性能：只要有一个单元格不为空且不是 NaN
                is_blank = not df.stack().astype(str).str.strip().replace(['nan', 'None', ''],
                                                                          [np.nan, np.nan, np.nan]).dropna().any()
                if is_blank:
                    continue
                # 3. 只有非空才保存
                result[sheet_name] = (df, self._clip_merges(df, merged_rects))
        else:  # CSV/TSV - 单sheet文件
            sep = '\t' if ext == '.tsv' else ','
            file_encoding = FileUtil.detect_encoding(str(file_path))
            table_col_cnt = pd.read_csv(file_path, nrows=1, header=None, encoding=file_encoding).shape[1]
            df = pd.read_csv(
                file_path,
                sep=sep,
                header=None,
                dtype=object,
                encoding=file_encoding,
                nrows=self.max_rows,
                usecols=range(min(table_col_cnt, self.max_cols)),  # 更精确的列选择
                engine='c',  # 指定引擎
                memory_map=True  # 大文件时使用内存映射
            )
            result['Sheet1'] = (df, [])
        return result

    def _clip_merges(self, df: pd.DataFrame, merges: list):
        """通用工具：确保合并单元格坐标不超出 DataFrame 实际边界"""
        h, w = df.shape
        clipped = []
        for r1, c1, r2, c2 in merges:
            if r1 >= h or c1 >= w: continue  # 完全在界外
            clipped.append((
                r1, c1,
                min(r2, h - 1),
                min(c2, w - 1)
            ))
        return clipped

    def _split_tables_to_indices(self, df: pd.DataFrame, merged_rects: list) -> List[Tuple[int, int, int, int]]:
        """关键方法：分析物理布局，返回各个表格块的(r_start, r_end, c_start, c_end)"""
        if df.empty: return []

        # 1. 创建探测掩码
        v_is_content = np.vectorize(lambda x: bool(str(x).strip()) if x is not None else False)
        mask = v_is_content(df.values)

        # 2. 涂抹掩码 (合并单元格必须视为一体)
        for r1, c1, r2, c2 in merged_rects:
            r_s, r_e = max(0, r1), min(mask.shape[0] - 1, r2)
            c_s, c_e = max(0, c1), min(mask.shape[1] - 1, c2)
            mask[r_s: r_e + 1, c_s: c_e + 1] = True

        def find_indices_recursive(curr_mask, r_off, c_off):
            if not curr_mask.any(): return []

            # 找到当前有内容区域的最小外接矩形
            rows_any = np.any(curr_mask, axis=1)
            cols_any = np.any(curr_mask, axis=0)
            r_idx, c_idx = np.where(rows_any)[0], np.where(cols_any)[0]
            if len(r_idx) == 0: return []

            rs, re, cs, ce = r_idx[0], r_idx[-1], c_idx[0], c_idx[-1]
            active_mask = curr_mask[rs:re + 1, cs:ce + 1]

            # 寻找空行切割
            empty_rows = np.where(~np.any(active_mask, axis=1))[0]
            if empty_rows.size > 0:
                cut = empty_rows[0]
                return (find_indices_recursive(curr_mask[:rs + cut, :], r_off, c_off) +
                        find_indices_recursive(curr_mask[rs + cut + 1:, :], r_off + rs + cut + 1, c_off))

            # 寻找空列切割
            empty_cols = np.where(~np.any(active_mask, axis=0))[0]
            if empty_cols.size > 0:
                cut = empty_cols[0]
                return (find_indices_recursive(curr_mask[:, :cs + cut], r_off, c_off) +
                        find_indices_recursive(curr_mask[:, cs + cut + 1:], r_off, c_off + cs + cut + 1))

            return [(r_off + rs, r_off + re + 1, c_off + cs, c_off + ce + 1)]

        return find_indices_recursive(mask, 0, 0)

    def _split_tables_to_indices2(self, df: pd.DataFrame, merged_rects: list):
        """迭代版本，避免递归深度和内存复制"""
        if df.empty:
            return []

        # 创建标记矩阵
        h, w = df.shape
        marked = np.zeros((h, w), dtype=bool)

        # 标记有内容的单元格
        for i in range(h):
            for j in range(w):
                if pd.notna(df.iloc[i, j]) and str(df.iloc[i, j]).strip():
                    marked[i, j] = True

        # 标记合并区域
        for r1, c1, r2, c2 in merged_rects:
            r2 = min(r2, h - 1)
            c2 = min(c2, w - 1)
            marked[r1:r2 + 1, c1:c2 + 1] = True

        # 使用BFS寻找连通区域
        indices = []
        visited = np.zeros((h, w), dtype=bool)

        for i in range(h):
            for j in range(w):
                if marked[i, j] and not visited[i, j]:
                    # BFS找到区域边界
                    min_r, max_r = i, i
                    min_c, max_c = j, j
                    stack = [(i, j)]

                    while stack:
                        r, c = stack.pop()
                        if r < 0 or r >= h or c < 0 or c >= w:
                            continue
                        if not marked[r, c] or visited[r, c]:
                            continue

                        visited[r, c] = True
                        min_r = min(min_r, r)
                        max_r = max(max_r, r)
                        min_c = min(min_c, c)
                        max_c = max(max_c, c)

                        # 四方向扩展
                        stack.extend([(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)])

                    indices.append((min_r, max_r + 1, min_c, max_c + 1))

        return indices

    def _split_tables_to_indices3(self, df: pd.DataFrame, merged_rects: list) -> List[Tuple[int, int, int, int]]:
        """优化版：使用原生 Numpy 向量化运算生成掩码"""
        if df.empty: return []

        # 1. 创建探测掩码 (高效率向量化)
        # 第一步：找出所有非空单元格 (not NaN)
        mask = pd.notna(df).values

        # 第二步：针对字符串类型的单元格，检查是否不是纯空白字符
        # 我们只在原有 mask 为 True 的地方进行检查，节省计算
        # 使用 numpy.char.strip 或 pandas 的全局字符串处理
        # 这里最快的方法是直接判断不等于空字符串
        str_mask = (df.values.astype(str) != "") & (df.values.astype(str) != "nan")

        # 最终探测掩码：既不是 NaN 也不是空字符串/nan字符串
        mask &= str_mask

        # 2. 涂抹掩码 (合并单元格必须视为一体)
        # 这部分涉及切片赋值，Numpy 的底层操作非常快
        h, w = mask.shape
        for r1, c1, r2, c2 in merged_rects:
            # 增加越界保护
            r_end = min(r2, h - 1)
            c_end = min(c2, w - 1)
            if r1 < h and c1 < w:
                mask[r1: r_end + 1, c1: c_end + 1] = True

        # 3. 递归寻找物理边界 (递归部分的逻辑保持不变，因为其核心已经是 np.any)
        def find_indices_recursive(curr_mask, r_off, c_off):
            # 这一步 np.any(axis=1) 是向量化操作的精髓，性能极高
            rows_any = np.any(curr_mask, axis=1)
            if not np.any(rows_any): return []

            cols_any = np.any(curr_mask, axis=0)
            r_idx = np.where(rows_any)[0]
            c_idx = np.where(cols_any)[0]

            rs, re, cs, ce = r_idx[0], r_idx[-1], c_idx[0], c_idx[-1]
            active_mask = curr_mask[rs:re + 1, cs:ce + 1]

            # 寻找全空行切割线 (投影法)
            empty_rows = np.where(~np.any(active_mask, axis=1))[0]
            if empty_rows.size > 0:
                cut = empty_rows[0]
                return (find_indices_recursive(curr_mask[:rs + cut, :], r_off, c_off) +
                        find_indices_recursive(curr_mask[rs + cut + 1:, :], r_off + rs + cut + 1, c_off))

            # 寻找全空列切割线
            empty_cols = np.where(~np.any(active_mask, axis=0))[0]
            if empty_cols.size > 0:
                cut = empty_cols[0]
                return (find_indices_recursive(curr_mask[:, :cs + cut], r_off, c_off) +
                        find_indices_recursive(curr_mask[:, cs + cut + 1:], r_off, c_off + cs + cut + 1))

            return [(r_off + rs, r_off + re + 1, c_off + cs, c_off + ce + 1)]

        return find_indices_recursive(mask, 0, 0)

    def _render_block_pair(self, df_blank: pd.DataFrame, df_fill: pd.DataFrame, block_merges: list) -> Tuple[str, str]:
        if df_blank.empty: return "", ""

        final_blank_parts, final_fill_parts = [], []
        pending_rows_blank, pending_rows_fill = [], []

        # 记录需要跳过的行号（用于处理多行垂直合并的标题）
        skip_until_row = -1

        def flush_table():
            if not pending_rows_blank: return
            sub_df_blank = pd.DataFrame(pending_rows_blank)
            sub_df_fill = pd.DataFrame(pending_rows_fill)
            final_blank_parts.append(self._generate_pure_table(sub_df_blank))
            final_fill_parts.append(self._generate_pure_table(sub_df_fill))
            pending_rows_blank.clear()
            pending_rows_fill.clear()

        last_title_str = ""
        for i in range(len(df_fill)):
            # 如果当前行属于上一个识别出的标题的合并范围，直接跳过
            if i <= skip_until_row:
                continue

            row_fill = df_fill.iloc[i]
            row_blank = df_blank.iloc[i]

            # 提取非空值
            valid_vals = row_fill.astype(str).str.strip().replace(['nan', 'None', ''],
                                                                  [np.nan, np.nan, np.nan]).dropna()

            if len(valid_vals) == 0:
                flush_table()
                continue

            # 识别只有一个有效值的行作为“标题行”
            is_title_row = len(set(valid_vals.values)) == 1 and len(df_fill.columns) > 1

            title_str = self._safe_str(valid_vals.iloc[0])
            if title_str.strip() == "合计3199":
                pass
            if is_title_row:
                flush_table()
                # --- 新增：精准判断垂直合并范围 ---
                current_val = valid_vals.iloc[0]
                # 在 block_merges 中查找是否有覆盖当前行（i）的合并单元格
                for r1, c1, r2, c2 in block_merges:
                    # 如果合并单元格从当前行开始，且跨越了多行，且不是第1行及第2行
                    if r1 == i and r2 > r1 and c1 > 2:
                       skip_until_row = r2  # 标记后续行需要跳过
                       break
                title_str = self._safe_str(current_val)
                # 增加一个逻辑：只有单行且不包含“注：”或“说明”字样的才设为标题
                is_hint = any(title_str.startswith(prefix) for prefix in ["注：", "说明", "备注", "合计", "小计", "总计", "金额"])

                if len(title_str) <= self.max_title_len and not is_hint:
                    # 渲染为层级标题
                    title_text = f"{self.table_title_start_char} {title_str}"
                else:
                    # 渲染为加粗或纯文本
                    title_text = f"**{title_str}**" if len(title_str) <= 60 else title_str
                if title_str != last_title_str:
                    final_blank_parts.append(title_text)
                    final_fill_parts.append(title_text)
                    last_title_str = title_str
            else:
                # 普通数据行
                pending_rows_blank.append(row_blank)
                pending_rows_fill.append(row_fill)

        flush_table()
        return "\n\n".join(final_blank_parts), "\n\n".join(final_fill_parts)

    def _generate_pure_table(self, df: pd.DataFrame) -> str:
        """
        表格生成逻辑：将 DataFrame 转换为 MD Table 字符串。
        1. 自动过滤全空行。
        2. 自动过滤与上一行完全重复的行（针对 Fill 模式去重）。
        3. 针对 Typora 补全空数据行。
        """
        if df.empty:
            return ""

        # 转换数据为清洗后的字符串二维列表
        data = [[self._safe_str(c) for c in row] for row in df.values]
        header = data[0]
        col_count = len(header)

        # 准备 Markdown 表格头部
        sep = ["---"] * col_count
        lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]

        last_row_str = "| " + " | ".join(header) + " |"  # 初始化为表头，用于去重比较
        valid_row_count = 0

        for row in data[1:]:
            # 补齐长度
            row_strs = list(row) + [""] * (col_count - len(row))
            row_strs = row_strs[:col_count]  # 截断多余列

            # 1. 检查是否为空行（所有单元格均为空字符串）
            if not any(s.strip() for s in row_strs):
                continue

            # 生成当前行的字符串表示（用于去重判断）
            current_row_str = "| " + " | ".join(row_strs) + " |"

            # 2. 检查是否与上一行内容完全一样
            if current_row_str == last_row_str:
                continue

            # 通过校验，插入行
            lines.append(current_row_str)
            last_row_str = current_row_str
            valid_row_count += 1

        # --- 兼容性补丁：针对 Typora ---
        # 如果除了表头之外没有有效数据行，手动补一行 &nbsp;
        # if valid_row_count == 0:
        #     empty_row = ["&nbsp;"] * col_count
        #     lines.append("| " + " | ".join(empty_row) + " |")

        return "\n".join(lines)

    def sheet_to_md(self, sheet_name: str, df: pd.DataFrame, merges: list) -> Tuple[str, str]:
        """
        同步生成两个模式的 Sheet 内容。
        """
        # 结果容器
        res_blank = [f"{self.sheet_title_start_char} {sheet_name}"]
        res_fill = [f"{self.sheet_title_start_char}  {sheet_name}"]

        # 1. 数据副本准备
        df_base = df.fillna("")
        if not merges:
            df_blank = df_filled = df_base
        else:
            df_blank, df_filled = df_base.copy(), df_base.copy()
            for r1, c1, r2, c2 in merges:
                val = self._safe_str(df.iloc[r1, c1])
                df_filled.iloc[r1:r2 + 1, c1:c2 + 1] = val
                df_blank.iloc[r1:r2 + 1, c1:c2 + 1] = ""
                df_blank.iloc[r1, c1] = val

        # 2. 物理块切分
        indices = self._split_tables_to_indices(df_filled, merges)
        if not indices:
            return "", ""

        # 3. 遍历每个物理块，同步渲染
        for (r_s, r_e, c_s, c_e) in indices:
            # 筛选并计算当前块的相对合并坐标
            current_merges = [
                (r1 - r_s, c1 - c_s, r2 - r_s, c2 - c_s)
                for r1, c1, r2, c2 in merges
                if r_s <= r1 < r_e and c_s <= c1 < c_e
            ]

            # 同步获取 MD
            md_blank, md_fill = self._render_block_pair(
                df_blank.iloc[r_s:r_e, c_s:c_e],
                df_filled.iloc[r_s:r_e, c_s:c_e],
                current_merges
            )

            res_blank.append(md_blank)
            res_fill.append(md_fill)

        return "\n\n".join(res_blank), "\n\n".join(res_fill)

    def convert(self, file_path: str) -> Dict[str, str]:
        path = Path(file_path)
        sheets_data = self._get_data_and_merges(path)
        if not sheets_data: return {'blank': '', 'fill': ''}

        title = self.file_title_start_char + " " + path.stem
        out_blank, out_fill = [title], [title]

        for sheet_name, (sheet_df, sheet_merges) in sheets_data.items():
            sheet_md_blank, sheet_md_filed = self.sheet_to_md(sheet_name, sheet_df, sheet_merges)
            out_blank.append(sheet_md_blank)
            out_fill.append(sheet_md_filed)

        return {'blank': "\n\n".join(out_blank), 'fill': "\n\n".join(out_fill)}

# --- 执行入口 ---
if __name__ == "__main__":
    input_dir = r"D:\测试目录\single_file"
    output_dir = r"D:\output_markdown"
    os.makedirs(output_dir, exist_ok=True)

    converter = TableToMarkdown()
    exts = {'.xlsx', '.xls', '.ods', '.csv', '.tsv'}

    files = [f for ext in exts for f in Path(input_dir).rglob(f"*{ext}")
             if f.is_file() and not f.name.startswith('~$')]

    print(f"🚀 扫描完成，共 {len(files)} 个文件。")
    for i, fp in enumerate(files, 1):
        start = time.time()
        print(f"[{i}/{len(files)}] {fp.name} ({os.path.getsize(fp)/1024/1024:.2f} MB) ...", end='',flush=True)
        res = converter.convert(str(fp))
        rel = fp.relative_to(input_dir)
        target_dir = Path(output_dir) / rel.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        if res['blank']:
            (target_dir / f"{fp.stem}_blank.md").write_text(res['blank'], encoding='utf-8')
        if res['fill']:
            (target_dir / f"{fp.stem}_fill.md").write_text(res['fill'], encoding='utf-8')
        print(f" (完成时间：{time.time() - start:.2f}s)")
