# baidu_ocr.py
import base64
import json
from urllib import request, parse
from urllib.error import URLError, HTTPError
import ssl

# 忽略 SSL 验证（可选）
ssl._create_default_https_context = ssl._create_unverified_context


class Api:
    def __init__(self, global_argd):
        self.api_key = global_argd.get("api_key", "").strip()
        self.secret_key = global_argd.get("secret_key", "").strip()
        self.timeout = global_argd.get("timeout", 10)

        self.access_token = None
        # URL 映射将在 _ocr_request 中动态构建，此处无需预设

    def _get_access_token(self):
        url = 'https://aip.baidubce.com/oauth/2.0/token'
        params = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.secret_key
        }
        data = parse.urlencode(params).encode('utf-8')
        
        try:
            req = request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            with request.urlopen(req, timeout=self.timeout) as f:
                result = json.loads(f.read().decode('utf-8'))
                if 'access_token' in result:
                    return result['access_token']
                else:
                    print(f"[Error] 获取access_token失败: {result}")
                    return None
        except Exception as e:
            print(f"[Error] 获取access_token异常: {str(e)}")
            return None

    def start(self, argd):
        new_api_key = argd.get("api_key", "").strip()
        new_secret_key = argd.get("secret_key", "").strip()

        if new_api_key:
            self.api_key = new_api_key
        if new_secret_key:
            self.secret_key = new_secret_key

        self.timeout = argd.get("timeout", self.timeout)

        if not self.api_key:
            return "[Error] API Key 不能为空，请在插件设置中填写。"
        if not self.secret_key:
            return "[Error] Secret Key 不能为空，请在插件设置中填写。"

        self.access_token = self._get_access_token()
        if not self.access_token:
            return "[Error] 无法获取 access_token，请检查密钥是否正确或网络连接。"

        # 局部配置（表格识别不需要 language_type 等）
        self.api_type = argd.get("api_type", "general")
        self.language_type = argd.get("language_type", "CHN_ENG")
        self.detect_direction = argd.get("detect_direction", False)
        self.paragraph = argd.get("paragraph", False)
        # 表格识别专属参数（可选）
        self.return_excel = argd.get("return_excel", False)
        self.cell_contents = argd.get("cell_contents", False)

        return ""

    def stop(self):
        self.access_token = None

    def _ocr_request(self, image_base64):
        if not self.access_token:
            return {"code": 102, "data": "[Error] access_token 未获取"}

        # 所有支持的接口 URL
        urls = {
            "general_basic": "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic",
            "general": "https://aip.baidubce.com/rest/2.0/ocr/v1/general",
            "accurate_basic": "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic",
            "accurate": "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate",
            "webimage": "https://aip.baidubce.com/rest/2.0/ocr/v1/webimage",
            "numbers": "https://aip.baidubce.com/rest/2.0/ocr/v1/numbers",
            "handwriting": "https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting",
            "formula": "https://aip.baidubce.com/rest/2.0/ocr/v1/formula",
            "table": "https://aip.baidubce.com/rest/2.0/ocr/v1/table",  
        }

        if self.api_type not in urls:
            return {"code": 102, "data": f"[Error] 不支持的接口: {self.api_type}"}

        url = f"{urls[self.api_type]}?access_token={self.access_token}"

        payload = {"image": image_base64}

        # 通用文本识别参数
        if self.api_type in ["general_basic", "general", "accurate_basic", "accurate", "webimage"]:
            payload["language_type"] = self.language_type
            payload["detect_direction"] = "true" if self.detect_direction else "false"
            payload["paragraph"] = "true" if self.paragraph else "false"

        # 表格识别专属参数
        elif self.api_type == "table":
            if self.return_excel:
                payload["return_excel"] = "true"
            if self.cell_contents:
                payload["cell_contents"] = "true"

        data = parse.urlencode(payload).encode('utf-8')

        try:
            req = request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            with request.urlopen(req, timeout=self.timeout) as f:
                result = json.loads(f.read().decode('utf-8'))
        except Exception as e:
            return {"code": 102, "data": f"[Error] 请求失败: {str(e)}"}

        return self._parse_result(result)

    def runPath(self, img_path: str):
        try:
            with open(img_path, "rb") as f:
                image_bytes = f.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        except Exception as e:
            return {"code": 102, "data": f"[Error] 读取图片失败: {str(e)}"}
        return self._ocr_request(image_base64)

    def runBytes(self, image_bytes):
        try:
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        except Exception as e:
            return {"code": 102, "data": f"[Error] 图片编码失败: {str(e)}"}
        return self._ocr_request(image_base64)

    def runBase64(self, image_base64: str):
        return self._ocr_request(image_base64)
    
    def _parse_result(self, result):
        if "error_code" in result:
            msg = result.get("error_msg", "未知错误")
            return {"code": 102, "data": f"[Error] {msg}"}

        data = []
        api = self.api_type

        # === 原有文本识别接口 ===
        if api in ["general", "accurate", "numbers", "handwriting", "formula"]:
            items = result.get("words_result", [])
            for item in items:
                text = item.get("words", "")
                loc = item.get("location")
                if not loc:
                    continue
                left, top, width, height = loc["left"], loc["top"], loc["width"], loc["height"]
                box = [
                    [left, top],
                    [left + width, top],
                    [left + width, top + height],
                    [left, top + height]
                ]
                data.append({"text": text, "box": box, "score": 1.0})

        elif api in ["general_basic", "accurate_basic", "webimage"]:
            for i, item in enumerate(result.get("words_result", [])):
                text = item.get("words", "")
                h = 40
                y = i * h
                box = [[0, y], [200, y], [200, y + h], [0, y + h]]
                data.append({"text": text, "box": box, "score": 1.0})
        elif api == "table":
            tables = result.get("tables_result", [])
            if not tables:
                return {"code": 101, "data": []}

            # 构建所有表格的文本表示（支持多表格）
            all_table_texts = []
            all_cells_for_render = []  # 用于渲染框（可选）

            for table in tables:
                rows = {}
                max_row = -1
                max_col = -1

                # 提取 body（表格主体）
                for cell in table.get("body", []):
                    text = str(cell.get("words", "")).replace("\n", " ").replace("\t", " ")  # 清理内部换行/制表符
                    row_start = cell.get("row_start", 0)
                    row_end = cell.get("row_end", row_start)
                    col_start = cell.get("col_start", 0)
                    col_end = cell.get("col_end", col_start)

                    max_row = max(max_row, row_end)
                    max_col = max(max_col, col_end)

                    # 合并单元格：只填左上角，其余留空（或填相同内容，这里简化为填左上）
                    for r in range(row_start, row_end + 1):
                        for c in range(col_start, col_end + 1):
                            if r not in rows:
                                rows[r] = {}
                            # 只在左上角写内容，其余为空（更符合 Excel 行为）
                            if r == row_start and c == col_start:
                                rows[r][c] = text
                            else:
                                rows[r][c] = ""  # 或者填 text（重复内容）

                # 构建二维网格
                grid = []
                for r in range(0, max_row + 1):
                    row = []
                    for c in range(0, max_col + 1):
                        row.append(rows.get(r, {}).get(c, ""))
                    grid.append(row)

                # 转为制表符分隔文本
                table_text = "\n".join("\t".join(cell for cell in row) for row in grid)
                all_table_texts.append(table_text)

                # （可选）收集单元格用于绘制识别框
                for part in ["header", "body", "footer"]:
                    for item in table.get(part, []):
                        text = item.get("words", "")
                        loc = item.get("location") if part in ["header", "footer"] else item.get("cell_location")
                        if loc and isinstance(loc, list) and len(loc) == 4:
                            try:
                                box = [[p["x"], p["y"]] for p in loc]
                                all_cells_for_render.append({"text": text, "box": box})
                            except (KeyError, TypeError):
                                continue

            # 合并多个表格（用两个换行分隔）
            full_text = "\n\n".join(all_table_texts)

            # 返回一个包含完整表格文本的 OCR 结果项（兼容上层）
            fake_box = [[0, 0], [100, 0], [100, 100], [0, 100]]

            return {
                "code": 100,
                "data": [
                    {
                        "text": full_text,
                        "box": fake_box,
                        "score": 1.0
                    }
                ]
            }

        else:
            return {"code": 102, "data": f"[Error] 不支持的结果解析: {api}"}

        if not data:
            return {"code": 101, "data": ""}

        return {"code": 100, "data": data}