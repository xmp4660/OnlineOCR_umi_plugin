# __init__.py
from . import baidu_ocr
from . import baidu_ocr_config

# 插件信息
PluginInfo = {
    "group": "ocr",  # 固定值
    "global_options": baidu_ocr_config.globalOptions,
    "local_options": baidu_ocr_config.localOptions,
    "api_class": baidu_ocr.Api,
}