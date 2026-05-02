# app/prompts/__init__.py
"""
这个模块负责加载prompts目录下的YAML文件，并将其内容作为Python变量导出。
这使得其他模块可以通过标准的import语句来使用这些提示词。
"""
import yaml
from pathlib import Path

# --- 加载提示词 ---
try:
    # 获取当前文件所在的目录
    _PROMPTS_DIR = Path(__file__).parent

    # 构建qa_prompts.yaml文件的完整路径
    _PROMPTS_FILE_PATH = _PROMPTS_DIR / "qa_prompts.yaml"

    # 读取并解析YAML文件
    with open(_PROMPTS_FILE_PATH, "r", encoding="utf-8") as f:
        _prompts_data = yaml.safe_load(f)

    # 将YAML文件中的键值对，转换为当前模块的全局变量
    QUERY_ANALYZER_SYSTEM_PROMPT: str = _prompts_data.get("query_analyzer_system_prompt", "")
    SYNTHESIS_SYSTEM_PROMPT: str = _prompts_data.get("synthesis_system_prompt", "")

except FileNotFoundError:
    print(f"错误: 提示词文件 {_PROMPTS_FILE_PATH} 未找到。")
    QUERY_ANALYZER_SYSTEM_PROMPT = ""
    SYNTHESIS_SYSTEM_PROMPT = ""
except Exception as e:
    print(f"加载提示词时发生错误: {e}")
    QUERY_ANALYZER_SYSTEM_PROMPT = ""
    SYNTHESIS_SYSTEM_PROMPT = ""

