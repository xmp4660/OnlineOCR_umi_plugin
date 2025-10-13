# baidu_ocr_config.py
from plugin_i18n import Translator

tr = Translator(__file__, "i18n.csv")

# 全局配置
# baidu_ocr_config.py
globalOptions = {
    "title": tr("百度 OCR"),
    "type": "group",
    "api_key": {           # ✅ 必须是小写
        "title": tr("API Key"),
        "default": "",
        "toolTip": tr("百度智能云 OCR 的 API Key。"),
    },
    "secret_key": {        # ✅ 必须是小写
        "title": tr("Secret Key"),
        "default": "",
        "toolTip": tr("百度智能云 OCR 的 Secret Key。"),
    },
    "timeout": {
        "title": tr("超时时间"),
        "type": "number",
        "default": 10,
        "min": 5,
        "max": 60,
        "unit": tr("秒"),
    }
}

# 局部配置
localOptions = {
    "title": tr("文字识别（百度 OCR）"),
    "type": "group",
    "api_type": { 
        "title": tr("OCR 接口"),
        "type": "enum",
        "optionsList": [
            ["general_basic", tr("通用文字识别（标准版）")],
            ["general", tr("通用文字识别（标准含位置版）")],
            ["accurate_basic", tr("通用文字识别（高精度版）")],
            ["accurate", tr("通用文字识别（高精度含位置版）")],
            ["webimage", tr("网络图片文字识别")],
            ["table", tr("表格文字识别V2")],
            ["numbers", tr("数字识别")],
            ["handwriting", tr("手写文字识别")],
            ["formula", tr("数学公式识别")], 
        ],
        "default": "general",
        "toolTip": tr("选择要调用的百度 OCR 接口。含位置版可将识别结果精准贴合原图。"),
    },
    "language_type": {
        "title": tr("语言类型"),
        "type": "enum",
        "optionsList": [
            ["CHN_ENG", "简体中文 + 英文"],
            ["ENG", "英文"],
            ["JAP", "日文"],
            ["KOR", "韩文"],
            ["FRE", "法文"],
            ["SPA", "西班牙文"],
            ["RUS", "俄文"],
            ["GER", "德文"],
            ["POR", "葡萄牙文"],
            ["ITL", "意大利文"],
            ["SWE", "瑞典文"],
            ["NOR", "挪威文"],
        ],
        "toolTip": tr("指定要识别的语言类型。"),
    },
    "detect_direction": {
        "title": tr("自动旋转"),
        "type": "boolean",
        "default": False,
        "toolTip": tr("是否自动检测图像方向，自动旋转纠正。"),
    },
    "paragraph": {
        "title": tr("段落划分"),
        "type": "boolean",
        "default": False,
        "toolTip": tr("是否输出段落信息。"),
    },
}