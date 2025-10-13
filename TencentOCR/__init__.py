# __init__.py
from . import tencent_ocr
from . import tencent_ocr_config

# 插件信息
PluginInfo = {
    "group": "ocr",  # 固定值
    "global_options": tencent_ocr_config.globalOptions,
    "local_options": tencent_ocr_config.localOptions,
    "api_class": tencent_ocr.Api,
}