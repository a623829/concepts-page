# -*- coding: utf-8 -*-
"""
DeepSeek API 数据更新器
=======================
由 GitHub Actions 定时调用，从环境变量 DEEPSEEK_API_KEY 读取 Key，
生成 10 个人工智能核心概念和 10 个编程核心概念，
输出为 frontend/concepts.json。

依赖：openai（在 CI workflow 中通过 pip install 安装）
"""

import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

# ---- 配置 ----
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-v4-flash"
OUTPUT_DIR = "frontend"
OUTPUT_FILE = "frontend/concepts.json"
CONCEPT_COUNT_PER_FIELD = 10


def get_api_key() -> str:
    """从环境变量读取 API Key。CI 中通过 GitHub Secrets 注入。"""
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("[错误] 环境变量 DEEPSEEK_API_KEY 未设置或为空")
        sys.exit(1)
    return key


def build_prompt() -> str:
    """构造提示词，要求模型返回严格 JSON。"""
    return f"""你是一个计算机科学教育专家。请帮我生成两组核心概念。

要求：
1. 第一组：{CONCEPT_COUNT_PER_FIELD} 个人工智能（AI）领域的核心概念
2. 第二组：{CONCEPT_COUNT_PER_FIELD} 个编程（Programming）领域的核心概念
3. 每个概念必须包含两个字段：
   - "name": 概念名称（简洁准确，中英文均可，优先使用中文）
   - "explanation": 一句话解释（用中文，通俗易懂，不超过 50 字）
4. 两组概念不能有重复，选最有代表性、最基础的核心概念

请严格按照以下 JSON 格式返回（不要添加任何额外说明文字）：

{{
  "ai_concepts": [
    {{"name": "机器学习", "explanation": "让计算机从数据中自动学习规律和模式的技术。"}},
    ...
  ],
  "programming_concepts": [
    {{"name": "变量", "explanation": "用于存储数据值的命名容器，是程序的基本组成单元。"}},
    ...
  ]
}}"""


def call_deepseek_api(client: OpenAI) -> dict:
    """调用 DeepSeek API，双模式自动降级。"""
    print(f"正在调用 DeepSeek API（模型: {MODEL_NAME}）...")
    print(f"每个领域生成 {CONCEPT_COUNT_PER_FIELD} 个概念，共 {CONCEPT_COUNT_PER_FIELD * 2} 个")

    for use_json_format in [True, False]:
        mode_label = "模式1: response_format=json_object" if use_json_format else "模式2: 纯 prompt 约束（降级）"
        print(f"\n--- {mode_label} ---")
        raw_content = ""

        for attempt in range(1, 3):
            try:
                system_prompt = (
                    "你是一个严格遵循指令的助手。"
                    "你必须只输出有效的 JSON，不要添加任何解释、说明或 markdown 代码块标记。"
                    "你的整个回复必须是一个可以被 json.loads() 直接解析的 JSON 对象。"
                )
                kwargs = {
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": build_prompt()},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4096,
                }
                if use_json_format:
                    kwargs["response_format"] = {"type": "json_object"}

                response = client.chat.completions.create(**kwargs)
                raw_content = response.choices[0].message.content
                if not raw_content:
                    raise ValueError("API 返回了空的 content")
                raw_content = raw_content.strip()
                print(f"   [尝试 {attempt}] API 调用成功")

                data = json.loads(raw_content)
                print(f"   [成功] JSON 解析成功")
                return data

            except json.JSONDecodeError as e:
                print(f"   [尝试 {attempt}] JSON 解析失败: {e}")
                if raw_content:
                    print(f"   返回内容预览: {raw_content[:200]}")
                if attempt < 2:
                    time.sleep(2)

            except Exception as e:
                print(f"   [尝试 {attempt}] {type(e).__name__}: {e}")
                if attempt < 2:
                    time.sleep(3)

        if use_json_format:
            print("   response_format 模式失败，自动降级为纯 prompt 约束模式...")
            time.sleep(1)

    raise RuntimeError(f"所有调用模式均失败。模型: {MODEL_NAME}")


def validate_result(data: dict) -> None:
    """校验返回数据结构。"""
    print("\n[校验] 检查数据...")
    for key in ["ai_concepts", "programming_concepts"]:
        if key not in data:
            raise ValueError(f"返回数据缺少顶层键: {key}")
    for field_name, key in [("人工智能", "ai_concepts"), ("编程", "programming_concepts")]:
        concepts = data[key]
        if not isinstance(concepts, list):
            raise ValueError(f"{key} 不是列表类型")
        if len(concepts) != CONCEPT_COUNT_PER_FIELD:
            print(f"   [注意] {field_name}领域概念数量: {len(concepts)}（期望 {CONCEPT_COUNT_PER_FIELD}）")
        for i, c in enumerate(concepts):
            if "name" not in c:
                raise ValueError(f"{key}[{i}] 缺少 'name' 字段")
            if "explanation" not in c:
                raise ValueError(f"{key}[{i}] 缺少 'explanation' 字段")
    print("   [成功] 数据校验通过")


def save_output(data: dict) -> None:
    """保存为 JSON 文件。"""
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[文件] 结果已保存到: {output_path.absolute()}")


def main() -> None:
    api_key = get_api_key()
    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    try:
        data = call_deepseek_api(client)
    except Exception as e:
        print(f"\n[失败] {e}")
        sys.exit(1)

    try:
        validate_result(data)
    except (ValueError, KeyError) as e:
        print(f"\n[失败] 数据校验失败: {e}")
        sys.exit(1)

    save_output(data)
    print("\n[完成] 数据更新成功")


if __name__ == "__main__":
    main()
