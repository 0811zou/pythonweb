"""
Ollama 本地大模型服务

用法：
  1. 安装 Ollama：https://ollama.com/download
  2. 拉取模型：ollama pull qwen2.5:7b
  3. 启动服务：ollama serve（通常会自动启动）
  4. Django 会自动调用本地模型，不可用时回退到规则摘要

完全免费，本地运行，无需联网，无需 API Key。
"""

import json
import urllib.request
import urllib.error
import logging

logger = logging.getLogger(__name__)

# Ollama 默认地址（本地服务）
OLLAMA_BASE_URL = "http://localhost:11434"
# 使用的模型（7B 模型效果不错，资源占用中等）
OLLAMA_MODEL = "qwen2.5:7b"
# 请求超时（秒）
OLLAMA_TIMEOUT = 30


def _call_ollama(prompt: str) -> str | None:
    """调用 Ollama API 生成文本"""
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "max_tokens": 600}
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            result = json.loads(resp.read().decode())
            return result.get("response", "").strip()
    except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError,
            TimeoutError, json.JSONDecodeError) as e:
        logger.warning("Ollama 调用失败，使用规则摘要: %s", e)
        return None


def _build_prompt(data: dict) -> str:
    """构建发给大模型的提示词"""
    sd = data.get("product_supply_demand", [])
    rd = data.get("regional_demand_top", [])
    rs = data.get("region_stats", [])

    products_text = "\n".join(
        f"- {d['product']}: 已售 {d['sold']}, 可用 {d['available']}"
        for d in sd
    ) or "暂无数据"

    region_text = "\n".join(
        f"- {r.get('region', '未知')}: {r.get('orders', 0)} 单, "
        f"总额 ¥{float(r.get('total', 0)):.0f}"
        for r in rs
    ) or "暂无数据"

    hot_product = rd[0]["product"] if rd else "暂无"
    shortage = [d for d in sd if d.get("shortage", 0) > 0]
    shortage_text = "、".join(d["product"] for d in shortage[:5]) or "无"

    return f"""
你是一位专业的农业市场分析专家。请根据以下平台订单数据，生成一段简洁的农产品市场简报（150字以内）。

当前最热门产品：{hot_product}
供不应求产品：{shortage_text}

各产品供需详情：
{products_text}

订单地区分布：
{region_text}

要求：1) 一句话概括市场整体状况 2) 指出最热产品和供应缺口 3) 给农户一条具体建议。
直接输出分析结果，不要输出"根据数据"、"基于以上"等前缀。
"""


def _build_fallback_summary(data: dict) -> dict:
    """Ollama 不可用时的规则摘要"""
    rd = data.get("regional_demand_top", [])
    sd = data.get("product_supply_demand", [])
    rs = data.get("region_stats", [])

    total_products = len(sd)
    hot_product = rd[0]["product"] if rd else "暂无"
    shortage = [d for d in sd if d.get("shortage", 0) > 0]
    shortage_count = len(shortage)
    shortage_names = [d["product"] for d in shortage[:5]]

    text = f"当前平台共分析 {total_products} 种农产品。"
    text += f"其中「{hot_product}」销量最高，是当前最热门产品。"
    if shortage_count > 0:
        text += f" ⚠️ 有 {shortage_count} 种产品供不应求：{'、'.join(shortage_names)}。建议相关农户增加产量。"
    else:
        text += " 目前供需基本平衡。"
    if rs:
        text += " 订单来源地区分布广泛，市场需求良好。"

    return {
        "summary_text": text,
        "total_products_analyzed": total_products,
        "hot_product": hot_product,
        "shortage_products_count": shortage_count,
        "shortage_products": shortage_names,
        "ai_model": "",
    }


def generate_analysis(data: dict) -> dict:
    """
    生成市场分析简报
    - 优先调用本地 Ollama 大模型
    - 模型不可用时回退到规则引擎
    """
    # 先构造规则摘要作为保底
    fallback = _build_fallback_summary(data)

    prompt = _build_prompt(data)
    llm_response = _call_ollama(prompt)

    if llm_response:
        sd = data.get("product_supply_demand", [])
        rd = data.get("regional_demand_top", [])
        shortage = [d for d in sd if d.get("shortage", 0) > 0]

        return {
            "summary_text": llm_response,
            "total_products_analyzed": len(sd),
            "hot_product": rd[0]["product"] if rd else "暂无",
            "shortage_products_count": len(shortage),
            "shortage_products": [d["product"] for d in shortage[:5]],
            "regional_orders": data.get("region_stats", []),
            "ai_model": f"Ollama ({OLLAMA_MODEL})",
        }

    # 保底：规则引擎（不暴露技术细节）
    fallback["ai_model"] = ""
    return fallback
