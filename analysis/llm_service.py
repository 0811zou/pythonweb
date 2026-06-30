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


# ===== 农业智能问答（通用 Q&A）=====

FARMING_SYSTEM_PROMPT = """你是一位经验丰富的农业技术专家，名叫"小智"，专门为农民朋友提供免费咨询。
你的知识涵盖：种植技术、病虫害防治、施肥管理、土壤改良、灌溉技术、农产品储存、有机农业、温室大棚、农机使用、农产品销售等。

回答要求：
1. 用通俗易懂的中文，避免太专业的术语，像一位老农技员在田边聊天
2. 回答简洁实用，控制在200字以内，给具体可操作的建议
3. 如果不确定，诚实说"这个问题我需要查一下资料"，不要编造
4. 结合中国农业实际情况，考虑不同地区的气候和土壤特点
5. 适当使用emoji让回答更亲切（🌱🌾🍎💧等）
6. 对于非农业问题，礼貌引导回农业话题"""


def chat_with_farmer(question: str, conversation_history: list[dict] | None = None) -> dict:
    """
    农业智能问答
    - 调用 Ollama 大模型以农业专家身份回答
    - 模型不可用时回退到规则回答
    - 返回 {'answer': str, 'model': str}
    """
    # 构建对话消息
    messages = [{"role": "system", "content": FARMING_SYSTEM_PROMPT}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": question})

    # 构建完整 prompt（Ollama generate API 用单个 prompt）
    prompt_parts = [f"系统指令：{FARMING_SYSTEM_PROMPT}"]
    if conversation_history:
        for msg in conversation_history[-6:]:  # 只保留最近6条，控制上下文长度
            prompt_parts.append(f"{'用户' if msg['role'] == 'user' else '专家'}: {msg['content']}")
    prompt_parts.append(f"用户: {question}\n专家（简洁回答，200字以内）:")

    full_prompt = "\n".join(prompt_parts)

    llm_response = _call_ollama(full_prompt)

    if llm_response:
        return {"answer": llm_response.strip(), "model": f"Ollama ({OLLAMA_MODEL})"}

    # 回退：基于规则的简单回答
    fallback_answer = _rule_based_farming_answer(question)
    return {"answer": fallback_answer, "model": ""}


def _rule_based_farming_answer(question: str) -> str:
    """Ollama 不可用时的规则匹配回答"""
    q = question.strip().lower()

    if any(w in q for w in ['病虫', '虫害', '害虫', '长虫', '生虫']):
        return """🌿 病虫害防治建议：
1. 物理防治优先：使用黄板诱杀、防虫网、灯光诱捕
2. 生物防治：释放赤眼蜂、瓢虫等天敌
3. 化学防治：选用低毒低残留农药，严格遵守安全间隔期
4. 预防为主：合理轮作、清理病残体、保持田间通风
💡 建议拍照后在农技知识库搜索对应作物的病虫害图谱进行精准识别。"""

    if any(w in q for w in ['施肥', '肥料', '肥', '营养']):
        return """🌱 施肥管理建议：
1. 基肥为主、追肥为辅，有机肥与化肥配合使用
2. 测土配方施肥——先了解土壤缺什么再补什么
3. 不同作物需肥规律不同：叶菜类多施氮肥，果菜类增施磷钾肥
4. 避免过量施肥，会导致土壤板结和环境污染
💡 建议参考平台农技知识库中对应作物的施肥指南。"""

    if any(w in q for w in ['灌溉', '浇水', '干旱', '水']) and not any(w in q for w in ['水果', '水产']):
        return """💧 灌溉管理建议：
1. 采用滴灌或喷灌等节水技术，比漫灌节水50%以上
2. 根据土壤墒情和作物需水规律确定灌溉时间和水量
3. 夏季高温时早晚灌溉，避免中午浇水伤根
4. 有条件可建设水肥一体化系统，省水省肥省人工
🌾 缺水地区可考虑种植耐旱作物品种或覆盖地膜保墒。"""

    if any(w in q for w in ['储存', '贮藏', '保鲜', '保存', '冷藏']):
        return """📦 农产品储存建议：
1. 常温储存：保持通风干燥，避免阳光直射，定期检查
2. 冷藏保鲜：根据不同产品设定适宜温度（一般0-8℃）
3. 气调储藏：控制氧气和二氧化碳浓度延长保鲜期
4. 加工转化：对不易储存的产品可考虑烘干、腌制等加工方式
⚠️ 储存前务必剔除损伤和病虫害个体，防止交叉感染。"""

    if any(w in q for w in ['土壤', '土质', '土地', '改良']):
        return """🌍 土壤改良建议：
1. 增施有机肥和秸秆还田，提高土壤有机质含量
2. 合理轮作，豆科作物可固氮改良土壤
3. 酸性土壤施石灰，碱性土壤施石膏或硫磺
4. 深耕与免耕结合，改善土壤结构
🔬 建议先做土壤检测，了解pH值、有机质、氮磷钾含量后再制定改良方案。"""

    # 默认回答
    return """🌾 您好！我是农业智能助手"小智"。
关于您的问题，建议：
1. 在平台的【农技知识库】搜索相关文章和指南
2. 查看【培训课程】中是否有对应的系统教学
3. 在【供需对接】中与其他农户交流经验
4. 如果问题比较具体，可以补充更多细节，我会尽力帮您解答 💪
⚠️ 当前AI模型未连接，以上为离线知识库回答。"""
