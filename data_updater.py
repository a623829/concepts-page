import json
import os
import sys
import random
from pathlib import Path
from openai import OpenAI

# 配置
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
if not API_KEY:
    print("[错误] 请设置环境变量 DEEPSEEK_API_KEY")
    sys.exit(1)

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
OUTPUT = Path("frontend/concepts.json")

# 用随机种子确保每次生成不同内容
seed = random.randint(1, 99999)

prompt = f"""你是一个知识卡片生成器。请生成以下 JSON，不要包含任何其他文字：

{{"ai_concepts": [
  {{"name": "概念名", "explanation": "一句话解释（20字以内）"}},
  ...
], "programming_concepts": [
  {{"name": "概念名", "explanation": "一句话解释（20字以内）"}},
  ...
], "finance_concepts": [
  {{"name": "概念名", "explanation": "一句话解释（20字以内）"}},
  ...
]}}

严格要求：
- 每个分类恰好 3 个概念，共 9 个
- 种子 ID: {seed}（根据此种子选择不同概念集合）
- 必须选择与之前不同的概念组合，不要重复常见的概念
- name 用中文，explanation 用中文且不超过 20 字
- 每个分类的概念要跨领域、有代表性
- ai: 选 AI 领域有深度的概念（如架构、理论、框架）
- programming: 选计算机核心原理（不要数据结构、算法等太基础的）
- finance: 选经济学/金融学核心概念"""

try:
    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.3,
    )
    content = resp.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("\n", 1)[0].rstrip("`").strip()
    data = json.loads(content)

    # 校验
    for key in ("ai_concepts", "programming_concepts", "finance_concepts"):
        assert len(data.get(key, [])) == 3, f"{key} 数量不对"
        for item in data[key]:
            assert "name" in item and "explanation" in item

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"生成完成: {OUTPUT}")
    # 打印摘要
    for key in data:
        names = [item["name"] for item in data[key]]
        print(f"  {key}: {', '.join(names)}")

except Exception as e:
    print(f"[失败] {e}")
    sys.exit(1)
