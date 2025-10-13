import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from urllib import request


class Api:
    def __init__(self, global_argd):
        self.secret_id = global_argd.get("secret_id", "").strip()
        self.secret_key = global_argd.get("secret_key", "").strip()
        self.timeout = global_argd.get("timeout", 10)
        self.host = None
        self.endpoint = None
        self.region = "ap-guangzhou"
        self.version = None

    def start(self, argd):
        self.pdf_page_number = 1  # 安全默认值，即使不用
        supported_apis = [
            "GeneralBasicOCR",
            "GeneralAccurateOCR",
            "GeneralHandwritingOCR",
            "GeneralEfficientOCR",
            "GeneralFastOCR",
            "FormulaOCR",
            "RecognizeTableOCR" ,
            "RecognizeTableAccurateOCR",
            "TableOCR",
            "EnglishOCR" ,
            "AdvertiseOCR"
        ]

        self.api_type = argd.get("api_type", "GeneralBasicOCR")
        if self.api_type not in supported_apis:
            return f"不支持的接口: {self.api_type}"

        # GeneralBasicOCR 特有参数
        if self.api_type == "GeneralBasicOCR":
            user_lang = argd.get("language_type", "auto").strip().lower()
            valid_language_types = {
                'auto': 'auto', 'zh': 'zh', 'chinese': 'zh', 'zh_rare': 'zh_rare',
                'mix': 'mix', 'jap': 'jap', 'japanese': 'jap', 'kor': 'kor',
                'korean': 'kor', 'spa': 'spa', 'spanish': 'spa', 'fre': 'fre',
                'french': 'fre', 'ger': 'ger', 'german': 'ger', 'por': 'por',
                'portuguese': 'por', 'vie': 'vie', 'vietnamese': 'vie', 'may': 'may',
                'malay': 'may', 'rus': 'rus', 'russian': 'rus', 'ita': 'ita',
                'italian': 'ita', 'hol': 'hol', 'dutch': 'hol', 'swe': 'swe',
                'swedish': 'swe', 'fin': 'fin', 'finnish': 'fin', 'dan': 'dan',
                'danish': 'dan', 'nor': 'nor', 'norwegian': 'nor', 'hun': 'hun',
                'hungarian': 'hun', 'tha': 'tha', 'thai': 'tha', 'hi': 'hi',
                'hindi': 'hi', 'ara': 'ara', 'arabic': 'ara'
            }
            self.language_type = valid_language_types.get(user_lang, 'auto')
        else:
            self.language_type = "auto"

        # RecognizeTableOCR 特有参数
        if self.api_type == "RecognizeTableOCR":
            self.is_pdf = argd.get("is_pdf", False)
            self.pdf_page_number = argd.get("pdf_page_number", 1)
            table_lang = argd.get("table_language", "zh").strip().lower()
            self.table_language = "jap" if table_lang in ("jap", "japanese") else "zh"

        # RecognizeTableAccurateOCR 特有参数
        if self.api_type == "RecognizeTableAccurateOCR":
            # 即使是图片，也设为默认值 1（安全，且符合 API 要求）
            self.pdf_page_number = argd.get("pdf_page_number", 1)
            
        # 在 RecognizeTableAccurateOCR 之后添加：
        if self.api_type == "TableOCR":
            # TableOCR 无特殊参数，仅需图片
            self.timeout = argd.get("timeout", 30)
        self.timeout = argd.get("timeout", 30)

        config = self._get_api_config()
        if not config:
            return f"不支持的接口: {self.api_type}"

        self.host = config["host"]
        self.endpoint = config["endpoint"]
        self.version = config["version"]

        return ""

    def stop(self):
        pass

    def _get_api_config(self):
        common_config = {
            "version": "2018-11-19",
            "endpoint": "https://ocr.tencentcloudapi.com",
            "host": "ocr.tencentcloudapi.com"
        }
        config_map = {
            "GeneralBasicOCR": common_config,
            "GeneralAccurateOCR": common_config,
            "GeneralHandwritingOCR": common_config,
            "GeneralEfficientOCR": common_config,
            "GeneralFastOCR": common_config,
            "FormulaOCR": common_config,
            "RecognizeTableOCR": common_config,
            "RecognizeTableAccurateOCR": common_config,
            "TableOCR": common_config,
            "EnglishOCR": common_config,
            "AdvertiseOCR":common_config,
        }
        return config_map.get(self.api_type)

    def _build_sign(self, params):
        version = self.version
        algorithm = "TC3-HMAC-SHA256"
        service = "ocr"
        timestamp = int(time.time())
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

        payload = {}
        if params.get("image_base64"):
            payload["ImageBase64"] = params["image_base64"]

        # GeneralBasicOCR 参数
        if self.api_type == "GeneralBasicOCR":
            payload["LanguageType"] = self.language_type
        # RecognizeTableOCR 参数
        elif self.api_type == "RecognizeTableOCR":
            payload["IsPdf"] = self.is_pdf
            if self.is_pdf:
                payload["PdfPageNumber"] = self.pdf_page_number
            payload["TableLanguage"] = self.table_language
        # RecognizeTableAccurateOCR 参数
        elif self.api_type == "RecognizeTableAccurateOCR":
            # 如果你确定只用图片，可以完全不传 PdfPageNumber
            # 腾讯云会自动识别为图片
            # payload["PdfPageNumber"] = self.pdf_page_number  # ← 注释掉这行
            pass
        # TableOCR：仅需 ImageBase64，无其他参数
        elif self.api_type == "TableOCR":
            # payload 已包含 ImageBase64，无需额外操作
            pass
        elif self.api_type == "EnglishOCR":
            payload["EnableCoordPoint"] = params.get("enable_coord_point", False)
            payload["EnableCandWord"] = params.get("enable_cand_word", False)
            payload["Preprocess"] = params.get("preprocess", True)

        body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        hashed_payload = hashlib.sha256(body.encode("utf-8")).hexdigest()

        canonical_uri = "/"
        canonical_querystring = ""
        canonical_headers = f"content-type:application/json; charset=utf-8\nhost:{self.host}\n"
        signed_headers = "content-type;host"
        canonical_request = (
            f"POST\n"
            f"{canonical_uri}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{hashed_payload}"
        )

        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical}"

        def sign(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = sign(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        auth_header = (
            f"{algorithm} "
            f"Credential={self.secret_id}/{date}/{service}/tc3_request, "
            f"SignedHeaders=content-type;host, "
            f"Signature={signature}"
        )

        return auth_header, body, timestamp, version

    def _ocr_request(self, image_base64):
        if not image_base64 or len(image_base64) < 10:
            return {"code": 102, "data": "[Error] 图像数据为空或无效"}

        try:
            params = {"image_base64": image_base64}
            auth_header, body, timestamp, version = self._build_sign(params)

            req = request.Request(self.endpoint, data=body.encode("utf-8"), method="POST")
            req.add_header("Authorization", auth_header)
            req.add_header("Content-Type", "application/json; charset=utf-8")
            req.add_header("Host", self.host)
            req.add_header("X-TC-Action", self.api_type)
            req.add_header("X-TC-Version", version)
            req.add_header("X-TC-Region", self.region)
            req.add_header("X-TC-Timestamp", str(timestamp))

            with request.urlopen(req, timeout=self.timeout) as f:
                response = json.loads(f.read().decode("utf-8"))

            resp = response.get("Response", {})
            if "Error" in resp:
                err = resp["Error"]
                return {"code": 102, "data": f"[Error] {err.get('Code')}: {err.get('Message')}"}

            return self._parse_result(resp)

        except Exception as e:
            return {"code": 102, "data": f"[Error] 请求失败: {str(e)}"}

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
        # 通用 OCR 接口（除 FormulaOCR 和 RecognizeTableOCR）
        if self.api_type in [
            "GeneralBasicOCR",
            "GeneralAccurateOCR",
            "GeneralHandwritingOCR",
            "GeneralEfficientOCR",
            "GeneralFastOCR",
            "EnglishOCR",
            "AdvertiseOCR"
        ]:
            data = []
            for item in result.get("TextDetections", []):
                text = item.get("DetectedText", "")
                box = [[pt.get("X", 0), pt.get("Y", 0)] for pt in item.get("Polygon", [])]
                score = item.get("Confidence", 1.0)
                data.append({"text": text, "box": box, "score": score})
            return {"code": 100, "data": data} if data else {"code": 101, "data": ""}

        elif self.api_type == "FormulaOCR":
            formula_list = result.get("FormulaInfos", [])
            request_id = result.get("RequestId", "")
            data = []

            for item in formula_list:
                text = item.get("DetectedText", "").strip()
                if not text:
                    continue
                confidence = item.get("Confidence", 1.0)
                x = item.get("X", 0)
                y = item.get("Y", 0)
                w = item.get("Width", 0)
                h = item.get("Height", 0)

                x1, y1 = x, y
                x2, y2 = x + max(w, 1), y + max(h, 1)
                box = [
                    [x1, y1],
                    [x2, y1],
                    [x2, y2],
                    [x1, y2]
                ]

                data.append({
                    "text": text,
                    "box": box,
                    "score": confidence,
                    "angle": result.get("Angle", 0)
                })

            if data:
                return {"code": 100, "data": data, "extra": {"request_id": request_id}}
            else:
                return {"code": 101, "data": "", "extra": {"request_id": request_id}}

        elif self.api_type in ["RecognizeTableOCR", "RecognizeTableAccurateOCR"]:
            tables = []
            raw_cells_list = []
            for table in result.get("TableDetections", []):
                cells = table.get("Cells", [])
                raw_cells_list.append(cells)
                if not cells:
                    tables.append([])
                    continue

                # 安全获取最大行列（RowBr/ColBr 表示结束边界，即实际行/列数）
                max_row = max(cell.get("RowBr", 0) for cell in cells)
                max_col = max(cell.get("ColBr", 0) for cell in cells)

                # 创建二维表格网格
                grid = [["" for _ in range(max_col)] for _ in range(max_row)]

                # 填充单元格内容（带边界检查！）
                for cell in cells:
                    row_tl = cell.get("RowTl", -1)
                    col_tl = cell.get("ColTl", -1)
                    text = cell.get("Text", "")

                    # 🔒 关键修复：防止 list index out of range
                    if 0 <= row_tl < max_row and 0 <= col_tl < max_col:
                        if grid[row_tl][col_tl] == "":
                            grid[row_tl][col_tl] = text
                    # 可选：记录异常单元格（调试用）
                    # else:
                    #     print(f"[WARN] Cell out of bounds: RowTl={row_tl}, ColTl={col_tl}, max_row={max_row}, max_col={max_col}")

                tables.append(grid)

            # 将表格转为纯文本（用于兼容上层 text/score 结构）
            table_texts = []
            for grid in tables:
                lines = []
                for row in grid:
                    line = "\t".join(str(cell) for cell in row if cell)
                    if line.strip():
                        lines.append(line)
                table_text = "\n".join(lines)
                table_texts.append(table_text)

            # 构造兼容格式：每个表格作为一个“文本块”
            data = []
            for i, text in enumerate(table_texts):
                if text.strip():
                    data.append({
                        "text": text,
                        "box": [],          # 表格无精确 box，可留空或估算
                        "score": 1.0,       # 表格无置信度，设为 1.0
                        "type": "table",    # 新增类型标记！
                        "table_data": tables[i]  # 保留结构化数据
                    })

            excel_b64 = result.get("Data", "")
            angle = result.get("Angle", 0)
            request_id = result.get("RequestId", "")

            return {
                "code": 100,
                "data": data,
                "extra": {
                    "excel_base64": excel_b64,
                    "angle": angle,
                    "request_id": request_id,
                    "raw_cells": raw_cells_list
                }
            }

        elif self.api_type == "TableOCR":
            # 旧版 TableOCR 解析
            cells = result.get("TextDetections", [])
            raw_cells_list = [cells]  # 为了和新版结构对齐，包装成列表

            if not cells:
                return {
                    "code": 101,
                    "data": "",
                    "extra": {
                        "excel_base64": "",
                        "request_id": result.get("RequestId", "")
                    }
                }

            # 过滤结构化单元格（RowTl/ColTl >= 0）
            structured_cells = [c for c in cells if c.get("RowTl", -1) >= 0 and c.get("ColTl", -1) >= 0]

            if not structured_cells:
                # 全是非结构化文本，按顺序拼接
                text = "\n".join(c.get("Text", "") for c in cells if c.get("Text", "").strip())
                return {
                    "code": 100,
                    "data": [{"text": text, "box": [], "score": 1.0, "type": "table"}],
                    "extra": {
                        "excel_base64": result.get("Data", ""),
                        "request_id": result.get("RequestId", "")
                    }
                }

            max_row = max(cell.get("RowBr", 0) for cell in structured_cells)
            max_col = max(cell.get("ColBr", 0) for cell in structured_cells)
            grid = [["" for _ in range(max_col)] for _ in range(max_row)]

            for cell in structured_cells:
                row_tl = cell.get("RowTl", -1)
                col_tl = cell.get("ColTl", -1)
                text = cell.get("Text", "")
                if 0 <= row_tl < max_row and 0 <= col_tl < max_col:
                    if grid[row_tl][col_tl] == "":
                        grid[row_tl][col_tl] = text

            # 转为文本
            lines = []
            for row in grid:
                line = "\t".join(str(cell) for cell in row if cell)
                if line.strip():
                    lines.append(line)
            table_text = "\n".join(lines)

            data = []
            if table_text.strip():
                data.append({
                    "text": table_text,
                    "box": [],
                    "score": 1.0,
                    "type": "table",
                    "table_data": grid
                })

            return {
                "code": 100,
                "data": data,
                "extra": {
                    "excel_base64": result.get("Data", ""),
                    "request_id": result.get("RequestId", ""),
                    "raw_cells": raw_cells_list
                }
            }

        else:
            return {"code": 102, "data": f"[Error] 不支持的接口: {self.api_type}"}