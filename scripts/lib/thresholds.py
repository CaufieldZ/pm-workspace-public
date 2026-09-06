"""阈值配置 Python 加载器。

用法：
    from lib.thresholds import T
    max_lines = T['checker']['max_lines']

或快捷常量（高频访问）：
    from lib.thresholds import CHECKER_MAX_LINES
"""
import pathlib

import yaml

_PATH = pathlib.Path(__file__).parent / "thresholds.yaml"
T: dict = yaml.safe_load(_PATH.read_text(encoding="utf-8"))

# 被代码真读的快捷常量。其余阈值在 thresholds.yaml，按需 T['section']['key'] 取
# （risky_op / write_tool / html_split / read_discipline 等由 hook 侧硬编码同步，
#  Python 侧无消费方，故不再镜像为常量）
CHECKER_MAX_LINES: int = T["checker"]["max_lines"]
VOICE_CHECK_HTML_MIN_LINES: int = T["voice_check"]["html_min_lines"]
