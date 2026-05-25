import json
import os
import sys
from pathlib import Path
from openai import OpenAI

# 配置
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
if not API_KEY:
    print("[错误] 请设置环境变量 DEEPSEEK_API_KEY")
    sys.exit(1)

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
OUTPUT = Path("frontend/concepts.json")

prompt = """请生成以下 JSON，不要包含任何其他文字：
{
  "ai_concepts": [
    {"name": "xxx", "explanation": "一句话解释"}
  ],
  "programming_concepts": [
    {"name": "xxx", "explanation": "一句话解释"}
  ],
  "finance_concepts": [
    {"name": "xxx", "explanation": "一句话解释"}
  ]
}
要求：
- ai_concepts、programming_concepts、finance_concepts 各 3 个
- name 用中文概念名称
- explanation 用中文，不超过 50 字
- 选最有代表性的核心概念"""

try:
    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
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

except Exception as e:
    print(f"[失败] {e}")
    sys.exit(1)
