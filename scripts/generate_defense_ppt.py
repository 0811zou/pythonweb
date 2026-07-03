#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毕业设计答辩 PPT 生成器
——基于 Django 与大模型的农产品溯源与智能助农平台

生成内容：
  1. matplotlib 绘制 ER 图、架构图、程序结构图、流程图 → PNG
  2. python-pptx 组装 18 页精美答辩 PPT，嵌入图表

用法：python scripts/generate_defense_ppt.py
输出：docs/智农溯源_毕设答辩PPT.pptx
"""

import os, sys, io, textwrap
from pathlib import Path

# ── 配置 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "ppt_diagrams"
PPT_PATH = PROJECT_ROOT / "docs" / "智农溯源_毕设答辩PPT_v2.pptx"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SLIDE_W, SLIDE_H = 1280, 720  # pptx 内部单位（英寸×914400 的关系，这里用像素风格值）
# 实际 pptx 使用 EMU，1 inch = 914400 EMU。用 Inches() 更方便

# ── 颜色方案（农业+科技主题）──
C = {
    "navy":        "#1B3A5C",
    "green":       "#27AE60",
    "accent":      "#E67E22",  # 暖橙
    "accent2":     "#2980B9",  # 蓝
    "dark":        "#2C3E50",
    "text":        "#2C3E50",
    "muted":       "#7F8C8D",
    "light_bg":    "#F5F7FA",
    "light_green": "#E8F8F5",
    "light_orange":"#FEF5E7",
    "white":       "#FFFFFF",
    "black":       "#000000",
    "red":         "#E74C3C",
}

FONT = "Microsoft YaHei"
FONT_BOLD = "Microsoft YaHei"

# ═══════════════════════════════════════════════════════════
#  Part 1: matplotlib 图表生成
# ═══════════════════════════════════════════════════════════

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Arc
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "KaiTi"]
plt.rcParams["axes.unicode_minus"] = False

DPI = 150


def fig_to_bytes(fig, dpi=DPI):
    """将 matplotlib figure 转为 PNG bytes"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    buf.seek(0)
    plt.close(fig)
    return buf


def draw_rounded_box(ax, x, y, w, h, text, color="#2C3E50", bg="#F5F7FA",
                     fontsize=11, bold=True, text_color=None, edge_color=None):
    """绘制圆角矩形文本框"""
    if text_color is None:
        text_color = color
    if edge_color is None:
        edge_color = color
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=bg, edgecolor=edge_color, linewidth=1.5, zorder=3)
    ax.add_patch(box)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        ly = y + h / 2 + (len(lines) - 1) * fontsize * 0.35 - i * fontsize * 1.25
        ax.text(x + w / 2, ly, line, ha="center", va="center",
                fontsize=fontsize, fontweight="bold" if bold else "normal",
                color=text_color, zorder=4)


def draw_arrow(ax, x1, y1, x2, y2, color="#7F8C8D", lw=1.2, style="->"):
    """绘制箭头"""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle="arc3,rad=0"))


def draw_line(ax, x1, y1, x2, y2, color="#7F8C8D", lw=1.2):
    """绘制直线"""
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, zorder=1)


# ── 图 1: 系统总体架构图 ──
def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(11, 6.5), facecolor="white")
    ax.set_xlim(0, 11); ax.set_ylim(0, 6.5)
    ax.axis("off")
    ax.set_facecolor("white")

    # 左侧：浏览器
    draw_rounded_box(ax, 0.3, 2.8, 1.6, 1.0, "浏览器\n消费者 · 农户 · 管理员",
                     color=C["navy"], bg=C["light_bg"], fontsize=10)

    # 路由层
    draw_rounded_box(ax, 2.5, 2.8, 1.5, 1.0, "路由层\nconfig.urls\n+ app urls",
                     color=C["accent2"], bg="#EBF5FB", fontsize=9.5)

    # 业务层
    draw_rounded_box(ax, 4.6, 2.8, 1.7, 1.0, "业务控制层\nDjango Views\n+ DRF ViewSets",
                     color=C["green"], bg=C["light_green"], fontsize=9.5)

    # 模型层
    draw_rounded_box(ax, 6.9, 2.8, 1.5, 1.0, "模型层\nDjango ORM\nModels",
                     color=C["dark"], bg=C["light_bg"], fontsize=9.5)

    # 数据库
    draw_rounded_box(ax, 6.9, 1.2, 1.5, 0.9, "数据库\nSQLite\nPostgreSQL",
                     color=C["dark"], bg=C["light_bg"], fontsize=9.5)

    # 下方四个辅助能力
    sub_items = [
        ("二维码服务\nqrcode库", C["green"]),
        ("智能分析\nOllama/规则降级", C["accent"]),
        ("API 文档\nSwagger UI", C["accent2"]),
        ("模板/静态资源\ntemplates/static", C["navy"]),
    ]
    for i, (label, clr) in enumerate(sub_items):
        bg = C["light_green"] if clr == C["green"] else C["light_orange"] if clr == C["accent"] else "#EBF5FB" if clr == C["accent2"] else C["light_bg"]
        draw_rounded_box(ax, 0.5 + i * 2.5, 1.2, 1.8, 0.85, label,
                         color=clr, bg=bg, fontsize=9)

    # 水平箭头
    for (x1, x2) in [(1.9, 2.5), (4.0, 4.6), (6.3, 6.9)]:
        draw_arrow(ax, x1, 3.3, x2, 3.3, C["muted"])

    # 垂直箭头: 业务层 → 下方辅助
    for i in range(4):
        draw_line(ax, 4.2 + i * 0.4, 2.8, 1.4 + i * 2.5, 2.05, C["muted"], 0.8)

    # 模型层 → 数据库
    draw_arrow(ax, 7.65, 2.8, 7.65, 2.1, C["muted"])

    ax.set_title("系统总体架构图", fontsize=15, fontweight="bold", color=C["navy"], pad=10)
    return fig_to_bytes(fig)


# ── 图 2: 程序结构图 ──
def generate_program_structure():
    fig, ax = plt.subplots(figsize=(11, 7), facecolor="white")
    ax.set_xlim(0, 11); ax.set_ylim(0, 7)
    ax.axis("off"); ax.set_facecolor("white")

    # 根节点
    draw_rounded_box(ax, 3.9, 5.6, 3.2, 0.7, "pythonweb 项目根目录",
                     color=C["navy"], bg=C["light_bg"], fontsize=12)

    # 第二层 - 核心App (上面一排)
    apps_top = [
        ("config\n项目配置/路由", C["navy"]),
        ("accounts\n账号与农户档案", C["accent2"]),
        ("products\n产品/批次/评价", C["green"]),
        ("traceability\n溯源事件", C["dark"]),
        ("trade\n购物车/订单/物流", C["accent"]),
    ]
    for i, (label, clr) in enumerate(apps_top):
        bg = C["light_green"] if clr == C["green"] else C["light_orange"] if clr == C["accent"] else "#EBF5FB" if clr == C["accent2"] else C["light_bg"]
        draw_rounded_box(ax, 0.3 + i * 2.1, 4.0, 1.8, 1.0, label,
                         color=clr, bg=bg, fontsize=9.5)

    # 第三层 - 扩展App和支撑
    apps_bottom = [
        ("marketplace\n供需对接", C["green"]),
        ("knowledge\n农技知识库", C["accent2"]),
        ("preorder\n预售认养", C["dark"]),
        ("analysis\n市场分析/AI", C["accent"]),
        ("admin_panel\n后台审核管理", C["navy"]),
        ("core\n首页/通知/通用API", C["navy"]),
    ]
    for i, (label, clr) in enumerate(apps_bottom):
        bg = C["light_green"] if clr == C["green"] else C["light_orange"] if clr == C["accent"] else "#EBF5FB" if clr == C["accent2"] else C["light_bg"]
        draw_rounded_box(ax, 0.3 + i * 1.8, 2.4, 1.55, 1.0, label,
                         color=clr, bg=bg, fontsize=9)

    # 支撑层
    support = ["templates\n页面模板", "core/static\nCSS/JS静态资源", "media\n上传图片二维码", "deploy/\nDocker部署脚本"]
    for i, label in enumerate(support):
        draw_rounded_box(ax, 0.5 + i * 2.7, 0.8, 2.0, 0.9, label,
                         color=C["muted"], bg=C["light_bg"], fontsize=9.5,
                         edge_color=C["muted"])

    # 连接线：根 → 各App
    for i in range(5):
        draw_line(ax, 5.5, 5.6, 1.2 + i * 2.1, 5.0, C["muted"], 0.8)
    for i in range(6):
        draw_line(ax, 5.5, 5.6, 1.05 + i * 1.8, 3.4, C["muted"], 0.8)
    # App → 支撑
    for i in range(4):
        draw_line(ax, 1.5 + i * 2.7, 2.4, 1.5 + i * 2.7, 1.7, C["muted"], 0.8)

    ax.set_title("程序结构图（按 Django App 拆分）", fontsize=15, fontweight="bold", color=C["navy"], pad=10)
    return fig_to_bytes(fig)


# ── 图 3: 功能模块结构图 ──
def generate_function_modules():
    fig, ax = plt.subplots(figsize=(10, 7), facecolor="white")
    ax.set_xlim(0, 10); ax.set_ylim(0, 7)
    ax.axis("off"); ax.set_facecolor("white")

    # 中心节点
    cx, cy = 5, 3.5
    circle = mpatches.Ellipse((cx, cy), 2.8, 1.3, facecolor=C["navy"], edgecolor="none", zorder=3)
    ax.add_patch(circle)
    ax.text(cx, cy, "农产品溯源与\n智能助农平台", ha="center", va="center",
            fontsize=12, fontweight="bold", color="white", zorder=4)

    modules = [
        ("用户与权限", 0.7, 5.5, C["navy"]),
        ("产品管理", 2.2, 5.5, C["green"]),
        ("批次溯源", 3.7, 5.5, C["accent"]),
        ("交易订单", 5.2, 5.5, C["accent2"]),
        ("后台审核", 6.7, 5.5, C["dark"]),
        ("供需对接", 0.7, 1.5, C["green"]),
        ("预售认养", 2.2, 1.5, C["accent2"]),
        ("农技知识", 3.7, 1.5, C["navy"]),
        ("市场分析", 5.2, 1.5, C["accent"]),
        ("补贴/通知", 6.7, 1.5, C["dark"]),
    ]
    for label, x, y, clr in modules:
        bg = C["light_green"] if clr==C["green"] else C["light_orange"] if clr==C["accent"] else "#EBF5FB" if clr==C["accent2"] else C["light_bg"]
        draw_rounded_box(ax, x, y, 1.5, 0.9, label, color=clr, bg=bg, fontsize=10)
        draw_line(ax, cx, cy, x + 0.75, y + 0.45, C["muted"], 0.7)

    ax.set_title("功能模块结构图", fontsize=15, fontweight="bold", color=C["navy"], pad=10)
    return fig_to_bytes(fig)


# ── 图 4: 数据库 E-R 图 ──
def generate_er_diagram():
    fig, ax = plt.subplots(figsize=(12, 7.5), facecolor="white")
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.5)
    ax.axis("off"); ax.set_facecolor("white")

    entities = {
        "User\n用户":           (0.5, 5.3, C["navy"]),
        "FarmerProfile\n农户档案": (2.2, 5.3, C["accent2"]),
        "Product\n农产品":       (4.2, 5.3, C["green"]),
        "ProductBatch\n产品批次":  (6.3, 5.3, C["dark"]),
        "TraceEvent\n溯源事件":    (8.6, 5.3, C["accent"]),
        "Order\n订单":           (2.2, 2.6, C["navy"]),
        "OrderItem\n订单项":      (4.6, 2.6, C["green"]),
        "Review\n评价":          (7.2, 2.6, C["accent"]),
        "Cart/CartItem\n购物车":  (0.5, 2.6, C["dark"]),
        "Cart\n(含CartItem)":    (0.5, 2.0, C["dark"]),
        "SupplyDemandPost\n供需帖子": (8.6, 2.6, C["accent2"]),
        "DemandResponse\n需求响应":  (9.0, 1.4, C["accent"]),
        "PreOrder\n预售记录":     (0.5, 0.6, C["navy"]),
        "Notification\n站内通知":  (3.5, 0.6, C["accent2"]),
    }

    for label, (x, y, clr) in entities.items():
        bg = C["light_green"] if clr==C["green"] else C["light_orange"] if clr==C["accent"] else "#EBF5FB" if clr==C["accent2"] else C["light_bg"]
        draw_rounded_box(ax, x, y, 2.0, 0.95, label, color=clr, bg=bg, fontsize=8.5)

    # 关系连线
    relations = [
        (0.5+1.0, 5.3,    2.2+1.0, 5.3,    "1 : 1"),
        (2.2+1.0, 5.3,    4.2+1.0, 5.3,    "1 : N"),
        (4.2+1.0, 5.3,    6.3+1.0, 5.3,    "1 : N"),
        (6.3+1.0, 5.3,    8.6+1.0, 5.3,    "1 : N"),
        (0.5+1.0, 5.3,    0.5+1.0, 3.55,   "1 : N"),  # User → Cart
        (0.5+1.0, 5.3,    2.2+1.0, 3.55,   "1 : N"),  # User → Order
        (2.2+1.0, 5.3,    2.2+1.0, 3.55,   "1 : N"),  # Farmer → Order?
        (4.2+1.0, 5.3,    4.6+1.0, 3.55,   "1 : N"),  # Product → OrderItem
        (6.3+1.0, 5.3,    4.6+1.0, 3.55,   "1 : N"),  # Batch → OrderItem
        (2.2+1.0, 3.55,   4.6+1.0, 3.55,   "1 : N"),  # Order → OrderItem
        (2.2+1.0, 3.55,   7.2+1.0, 3.55,   "1 : N"),  # Order → Review
        (0.5+1.0, 5.3,    8.6+1.0, 3.55,   "1 : N"),  # User → SupplyDemandPost
        (8.6+1.0, 3.55,   9.0+1.0, 2.35,   "1 : N"),  # SupplyDemandPost → DemandResponse
        (2.2+1.0, 5.3,    9.0+1.0, 2.35,   "1 : N"),  # Farmer → DemandResponse
    ]

    for x1, y1, x2, y2, label in relations:
        if abs(y1 - y2) < 0.5:  # 水平线
            mid = (x1 + x2) / 2
            draw_arrow(ax, x1, y1, x2, y2, C["muted"], 1.0, "-")
            ax.text(mid, y1 + 0.18, label, ha="center", fontsize=7,
                    color=C["accent"], fontweight="bold", zorder=5)
        else:  # 垂直线
            mid_y = (y1 + y2) / 2
            draw_arrow(ax, x1, y1 - 0.01, x2, y2 + 0.01, C["muted"], 1.0, "-")
            ax.text(x1 + 0.2, mid_y, label, ha="left", va="center", fontsize=7,
                    color=C["accent"], fontweight="bold", zorder=5)

    ax.set_title("数据库 E-R 图（核心实体关系）", fontsize=15, fontweight="bold", color=C["navy"], pad=8)
    return fig_to_bytes(fig)


# ── 图 5: 批次溯源流程图 ──
def generate_traceability_flow():
    fig, ax = plt.subplots(figsize=(11, 5), facecolor="white")
    ax.set_xlim(0, 11); ax.set_ylim(0, 5)
    ax.axis("off"); ax.set_facecolor("white")

    steps = [
        ("① 农户\n发布产品", C["green"]),
        ("② 管理员\n审核产品", C["navy"]),
        ("③ 创建\n产品批次", C["accent2"]),
        ("④ 批次质检\n审核通过", C["dark"]),
        ("⑤ 生成批次码\n+ 二维码", C["accent"]),
        ("⑥ 农户下载\n贴到包装", C["green"]),
        ("⑦ 消费者\n扫码溯源", C["accent"]),
    ]
    for i, (label, clr) in enumerate(steps):
        x = 0.3 + i * 1.55
        bg = C["light_green"] if clr==C["green"] else C["light_orange"] if clr==C["accent"] else "#EBF5FB" if clr==C["accent2"] else C["light_bg"]
        draw_rounded_box(ax, x, 1.8, 1.35, 1.4, label, color=clr, bg=bg, fontsize=9.5)
        if i < len(steps) - 1:
            draw_arrow(ax, x + 1.35, 2.5, x + 1.55, 2.5, C["muted"])

    # 下方补充说明
    ax.text(5.5, 0.8,
            "实现要点：批次审核通过自动生成 B-日期-随机串 编码；qrcode 生成二维码指向 /trace/<batch_code>/；溯源事件基于链式结构记录机制",
            ha="center", fontsize=10, color=C["muted"], style="italic",
            bbox=dict(boxstyle="round,pad=0.5", facecolor=C["light_bg"], edgecolor="none"))

    ax.set_title("核心流程：产品批次溯源", fontsize=15, fontweight="bold", color=C["navy"], pad=10)
    return fig_to_bytes(fig)


# ── 图 6: 订单交易流程图 ──
def generate_order_flow():
    fig, ax = plt.subplots(figsize=(11, 6.2), facecolor="white")
    ax.set_xlim(0, 11); ax.set_ylim(0, 6.2)
    ax.axis("off"); ax.set_facecolor("white")

    top_steps = [
        ("① 浏览\n产品", C["navy"]),
        ("② 加入\n购物车", C["accent2"]),
        ("③ 填写\n收货信息", C["green"]),
        ("④ 生成订单\n+ 订单项", C["accent"]),
        ("⑤ 线下支付\n上传凭证", C["dark"]),
    ]
    bottom_steps = [
        ("⑨ 评价\n反馈", C["accent"]),
        ("⑧ 确认\n收货", C["green"]),
        ("⑦ 填写物流\n单号发货", C["accent2"]),
        ("⑥ 农户\n确认订单", C["navy"]),
    ]
    # 顶行
    for i, (label, clr) in enumerate(top_steps):
        x = 0.3 + i * 2.1
        bg = C["light_green"] if clr==C["green"] else C["light_orange"] if clr==C["accent"] else "#EBF5FB" if clr==C["accent2"] else C["light_bg"]
        draw_rounded_box(ax, x, 3.5, 1.8, 1.1, label, color=clr, bg=bg, fontsize=10)
        if i < len(top_steps) - 1:
            draw_arrow(ax, x + 1.8, 4.05, x + 2.1, 4.05, C["muted"])
    # 下行（反向）
    for i, (label, clr) in enumerate(bottom_steps):
        x = 0.3 + i * 2.1
        bg = C["light_green"] if clr==C["green"] else C["light_orange"] if clr==C["accent"] else "#EBF5FB" if clr==C["accent2"] else C["light_bg"]
        draw_rounded_box(ax, x, 1.5, 1.8, 1.1, label, color=clr, bg=bg, fontsize=10)
        if i < len(bottom_steps) - 1:
            draw_arrow(ax, x + 1.8, 2.05, x + 2.1, 2.05, C["muted"])
    # 转弯：⑤ → ⑥
    draw_arrow(ax, 9.2, 3.5, 9.2, 2.6, C["muted"])
    # 向下：⑨ ← 已连接完成, 用弯曲表示流程连续
    ax.annotate("", xy=(0.3 + 3 * 2.1, 2.6), xytext=(0.3 + 3 * 2.1 + 0.9, 1.5),
                arrowprops=dict(arrowstyle="->", color=C["muted"], lw=1.0,
                                connectionstyle="arc3,rad=0.3"))

    ax.text(5.5, 0.5,
            "设计亮点：OrderItem 关联 ProductBatch，交易记录能够追溯到具体产品批次来源",
            ha="center", fontsize=10.5, color=C["muted"], style="italic",
            bbox=dict(boxstyle="round,pad=0.5", facecolor=C["light_bg"], edgecolor="none"))

    ax.set_title("核心流程：订单交易闭环", fontsize=15, fontweight="bold", color=C["navy"], pad=10)
    return fig_to_bytes(fig)


# ── 图 7: AI 智能分析 ──
def generate_ai_analysis():
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    ax.set_xlim(0, 10); ax.set_ylim(0, 5.5)
    ax.axis("off"); ax.set_facecolor("white")

    # 左侧：数据来源
    draw_rounded_box(ax, 0.4, 1.5, 2.6, 2.8,
                     "数据来源\n─────────\n• 产品销量与库存\n• 订单地区分布\n• 供需缺口统计\n• 热销产品排行",
                     color=C["navy"], bg=C["light_bg"], fontsize=10, bold=False)

    # 中间：处理流程
    draw_rounded_box(ax, 3.6, 3.5, 2.0, 0.75, "Django ORM\n聚合统计", color=C["accent2"], bg="#EBF5FB", fontsize=10)
    draw_rounded_box(ax, 3.6, 2.0, 2.0, 1.1, "本地大模型\nOllama\n→ 生成简报", color=C["accent"], bg=C["light_orange"], fontsize=9.5)
    draw_arrow(ax, 3.0, 2.9, 3.6, 4.0, C["muted"])
    draw_arrow(ax, 5.6, 3.85, 6.2, 3.0, C["muted"])
    draw_rounded_box(ax, 3.6, 1.0, 2.0, 0.55, "模型不可用 → 规则降级", color=C["red"], bg="#FDEDEC", fontsize=9)

    # 右侧：输出能力
    draw_rounded_box(ax, 6.8, 1.5, 2.8, 2.8,
                     "输出能力\n─────────\n• 市场整体状况概括\n• 当前热门农产品\n• 供不应求品类提示\n• 农户销售建议",
                     color=C["green"], bg=C["light_green"], fontsize=10, bold=False)

    # 箭头：左→中→右
    draw_arrow(ax, 3.0, 2.9, 3.6, 2.55, C["muted"])

    ax.text(1.7, 0.3, "数据采集", ha="center", fontsize=11, fontweight="bold", color=C["navy"])
    ax.text(5.6, 0.3, "智能分析", ha="center", fontsize=11, fontweight="bold", color=C["accent"])
    ax.text(8.2, 0.3, "助农输出", ha="center", fontsize=11, fontweight="bold", color=C["green"])

    ax.set_title("智能助农分析架构", fontsize=15, fontweight="bold", color=C["navy"], pad=10)
    return fig_to_bytes(fig)


# ── 图 8: 用户角色与需求图 ──
def generate_user_roles():
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    ax.set_xlim(0, 10); ax.set_ylim(0, 5.5)
    ax.axis("off"); ax.set_facecolor("white")

    roles = [
        ("消费者", C["accent2"], [
            "浏览农产品", "扫码溯源查询", "加入购物车下单",
            "收藏产品", "评价反馈", "发布需求帖"
        ]),
        ("农户", C["green"], [
            "维护店铺档案", "发布产品创建批次",
            "下载溯源二维码", "处理订单填物流",
            "响应需求帖", "申请补贴看分析"
        ]),
        ("管理员", C["navy"], [
            "产品审核", "批次质检审核",
            "用户管理", "入驻申请审核",
            "补贴审批", "数据导出"
        ]),
    ]
    for i, (title, clr, items) in enumerate(roles):
        x = 0.3 + i * 3.3
        draw_rounded_box(ax, x, 2.6, 2.9, 0.6, title, color=clr, bg=clr, fontsize=11,
                         text_color="white", edge_color=clr)
        for j, item in enumerate(items):
            draw_rounded_box(ax, x, 1.0 + j * 0.38, 2.9, 0.32, f"  {item}",
                             color=clr, bg=C["light_bg"], fontsize=9, bold=False)

    ax.set_title("三类用户角色与核心需求", fontsize=15, fontweight="bold", color=C["navy"], pad=10)
    return fig_to_bytes(fig)


# ── 图 9: 部署架构图 ──
def generate_deployment():
    fig, ax = plt.subplots(figsize=(10, 5), facecolor="white")
    ax.set_xlim(0, 10); ax.set_ylim(0, 5)
    ax.axis("off"); ax.set_facecolor("white")

    # 用户
    draw_rounded_box(ax, 0.3, 2.0, 1.2, 1.0, "用户\n浏览器", color=C["navy"], bg=C["light_bg"], fontsize=10)
    # Nginx
    draw_rounded_box(ax, 2.1, 2.0, 1.5, 1.0, "Nginx\n反向代理", color=C["dark"], bg=C["light_bg"], fontsize=10)
    # Gunicorn+Django
    draw_rounded_box(ax, 4.3, 2.0, 2.0, 1.0, "Gunicorn\nDjango 应用", color=C["green"], bg=C["light_green"], fontsize=10)
    # 数据库
    draw_rounded_box(ax, 4.3, 0.5, 2.0, 0.8, "PostgreSQL\n数据持久化", color=C["navy"], bg=C["light_bg"], fontsize=9.5)
    # 静态文件
    draw_rounded_box(ax, 7.0, 2.0, 1.8, 1.0, "WhiteNoise\n静态文件服务", color=C["accent2"], bg="#EBF5FB", fontsize=10)
    # Ollama
    draw_rounded_box(ax, 7.0, 0.5, 1.8, 0.8, "Ollama\n本地模型服务", color=C["accent"], bg=C["light_orange"], fontsize=9.5)
    # Docker
    draw_rounded_box(ax, 0.3, 0.5, 1.2, 0.8, "Docker\n容器化", color=C["muted"], bg=C["light_bg"], fontsize=9.5,
                     edge_color=C["muted"])

    # 箭头
    draw_arrow(ax, 1.5, 2.5, 2.1, 2.5, C["muted"])
    draw_arrow(ax, 3.6, 2.5, 4.3, 2.5, C["muted"])
    draw_arrow(ax, 6.3, 2.5, 7.0, 2.5, C["muted"])
    draw_arrow(ax, 5.3, 2.0, 5.3, 1.3, C["muted"])

    ax.set_title("生产环境部署方案", fontsize=15, fontweight="bold", color=C["navy"], pad=10)
    return fig_to_bytes(fig)


# ── 批量生成所有图表 ──
def generate_all_diagrams():
    diagrams = {}
    print("🎨 生成图表中...")
    funcs = [
        ("architecture",   generate_architecture_diagram,   "系统总体架构图"),
        ("program_struct",  generate_program_structure,      "程序结构图"),
        ("function_modules",generate_function_modules,       "功能模块图"),
        ("er_diagram",      generate_er_diagram,             "数据库ER图"),
        ("trace_flow",      generate_traceability_flow,      "批次溯源流程图"),
        ("order_flow",      generate_order_flow,             "订单交易流程图"),
        ("ai_analysis",     generate_ai_analysis,            "AI智能分析图"),
        ("user_roles",      generate_user_roles,             "用户角色需求图"),
        ("deployment",      generate_deployment,             "部署架构图"),
    ]
    for name, func, desc in funcs:
        try:
            diagrams[name] = func()
            path = OUTPUT_DIR / f"{name}.png"
            with open(path, "wb") as f:
                f.write(diagrams[name].getvalue())
            print(f"  ✅ {desc} → {path.name}")
        except Exception as e:
            print(f"  ❌ {desc}: {e}")
    return diagrams


# ═══════════════════════════════════════════════════════════
#  Part 2: python-pptx PPT 构建
# ═══════════════════════════════════════════════════════════

from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import datetime


COLOR_NAMES = {
    "white": "#FFFFFF", "black": "#000000", "none": "#FFFFFF",
    "red": "#E74C3C", "grey": "#7F8C8D", "gray": "#7F8C8D",
}

def rgb(hex_str):
    """hex → RGBColor, handles named colors"""
    if hex_str in COLOR_NAMES:
        hex_str = COLOR_NAMES[hex_str]
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class PPTBuilder:
    def __init__(self, diagrams):
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        self.diagrams = diagrams
        self.slide_num = 0

    def add_slide(self, bg="white"):
        """添加空白幻灯片"""
        slide_layout = self.prs.slide_layouts[6]  # blank
        slide = self.prs.slides.add_slide(slide_layout)
        self.slide_num += 1
        # 背景
        bg_shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = rgb(C["white"] if bg == "white" else bg)
        bg_shape.line.fill.background()
        return slide

    def add_textbox(self, slide, left, top, width, height, text,
                    font_size=18, bold=False, color=C["text"], alignment="left",
                    font_name=FONT, line_spacing=1.15):
        """添加文本框"""
        txBox = slide.shapes.add_textbox(Inches(left), Inches(top),
                                          Inches(width), Inches(height))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.bold = bold
        p.font.color.rgb = rgb(color)
        p.font.name = font_name
        p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER,
                       "right": PP_ALIGN.RIGHT}[alignment]
        p.space_after = Pt(2)
        if line_spacing:
            p.line_spacing = Pt(font_size * line_spacing)
        return txBox

    def add_multiline_textbox(self, slide, left, top, width, height, lines,
                               font_size=18, color=C["text"], alignment="left",
                               line_spacing=1.25, first_bold=False):
        """添加多行文本框，lines 为 [(text, bold), ...]"""
        txBox = slide.shapes.add_textbox(Inches(left), Inches(top),
                                          Inches(width), Inches(height))
        tf = txBox.text_frame
        tf.word_wrap = True
        for i, item in enumerate(lines):
            if isinstance(item, str):
                text, is_bold = item, False
            else:
                text, is_bold = item
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            p.text = text
            p.font.size = Pt(font_size)
            p.font.bold = is_bold or (first_bold and i == 0)
            p.font.color.rgb = rgb(color)
            p.font.name = FONT
            p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER,
                           "right": PP_ALIGN.RIGHT}[alignment]
            p.space_after = Pt(2)
            if line_spacing:
                p.line_spacing = Pt(font_size * line_spacing)
        return txBox

    def add_rounded_rect(self, slide, left, top, width, height, fill_color=C["light_bg"],
                          border_color=None, border_width=Pt(1)):
        """添加圆角矩形"""
        shape = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill_color)
        shape.line.color.rgb = rgb(border_color or fill_color)
        shape.line.width = border_width
        return shape

    def add_rect(self, slide, left, top, width, height, fill_color):
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill_color)
        shape.line.fill.background()
        return shape

    def add_image(self, slide, diagram_key, left, top, width, height=None):
        """插入 matplotlib 生成的图表"""
        if diagram_key not in self.diagrams:
            self.add_textbox(slide, left, top, width, 0.5,
                             f"[图 {diagram_key} 生成失败]", font_size=12, color=C["red"])
            return
        buf = self.diagrams[diagram_key]
        if height is None:
            height = width * 0.6
        slide.shapes.add_picture(buf, Inches(left), Inches(top),
                                  Inches(width), Inches(height))

    def add_footer(self, slide):
        """统一页脚"""
        n = self.slide_num
        # 细线
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.6), Inches(7.0), Inches(12.1), Pt(1))
        line.fill.solid()
        line.fill.fore_color.rgb = rgb(C["muted"])
        line.line.fill.background()
        # 左侧标签
        self.add_textbox(slide, 0.6, 7.05, 5, 0.35,
                         "智农溯源 · 毕业设计答辩", font_size=9, color=C["muted"])
        # 右侧页码
        self.add_textbox(slide, 11.5, 7.05, 1.2, 0.35,
                         str(n).zfill(2), font_size=10, color=C["muted"],
                         alignment="right")

    def add_title_bar(self, slide, title, subtitle=""):
        """统一标题栏"""
        # 顶部分隔条
        bar = self.add_rect(slide, 0, 0, 13.333, 0.08, C["navy"])
        # 标题
        self.add_textbox(slide, 0.7, 0.35, 11.5, 0.65, title,
                         font_size=32, bold=True, color=C["navy"])
        if subtitle:
            self.add_textbox(slide, 0.7, 1.0, 11.5, 0.45, subtitle,
                             font_size=14, color=C["muted"])
        # 底部横线
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.7), Inches(1.5), Inches(2.0), Pt(3))
        line.fill.solid()
        line.fill.fore_color.rgb = rgb(C["accent"])
        line.line.fill.background()

    def add_card(self, slide, left, top, width, height, title, body,
                 accent_color=C["navy"]):
        """添加卡片"""
        # 卡片背景
        card = self.add_rounded_rect(slide, left, top, width, height,
                                      fill_color=C["white"],
                                      border_color="#D5D8DC", border_width=Pt(0.8))
        # 左侧色条
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(left), Inches(top + 0.2), Inches(0.06), Inches(height - 0.4))
        bar.fill.solid()
        bar.fill.fore_color.rgb = rgb(accent_color)
        bar.line.fill.background()
        # 标题
        self.add_textbox(slide, left + 0.25, top + 0.15, width - 0.5, 0.4, title,
                         font_size=16, bold=True, color=accent_color)
        # 内容
        self.add_textbox(slide, left + 0.25, top + 0.6, width - 0.5, height - 0.8, body,
                         font_size=11, color=C["text"])

    # ═══════════════════════════════════════
    #  各幻灯片页面
    # ═══════════════════════════════════════

    def slide_cover(self):
        """第 1 页：封面"""
        slide = self.add_slide()
        # 左侧白色区域
        # 顶部装饰条
        self.add_rect(slide, 0, 0, 13.333, 0.06, C["accent"])
        # 左侧竖条装饰
        self.add_rect(slide, 0.6, 1.2, 0.06, 1.8, C["accent"])
        # 主标题
        self.add_textbox(slide, 1.0, 1.0, 10, 0.7,
                         "基于 Django 与大模型的", font_size=26, color=C["muted"])
        self.add_textbox(slide, 1.0, 1.65, 11, 1.2,
                         "农产品溯源与智能助农平台", font_size=44, bold=True, color=C["navy"])
        self.add_textbox(slide, 1.0, 2.85, 12, 0.5,
                         "面向农户、消费者和平台管理员的农产品可信交易与助农服务平台",
                         font_size=15, color=C["muted"])

        # 栈标签
        stack_y = 3.8
        tags = ["Django 6", "DRF", "Bootstrap 5", "ECharts", "Ollama 本地大模型", "Docker"]
        for i, tag in enumerate(tags):
            x = 1.0 + i * 1.85
            tag_shape = self.add_rounded_rect(slide, x, stack_y, 1.65, 0.45,
                                               fill_color=C["light_bg"],
                                               border_color="#D5D8DC")
            tf = tag_shape.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = tag
            p.font.size = Pt(10)
            p.font.color.rgb = rgb(C["text"])
            p.font.name = FONT
            p.alignment = PP_ALIGN.CENTER

        # 右侧信息区背景
        self.add_rect(slide, 9.5, 4.8, 3.5, 2.4, C["navy"])
        self.add_textbox(slide, 9.8, 5.0, 3.0, 0.5, "毕业设计答辩",
                         font_size=22, bold=True, color="white")
        meta_lines = [
            "答辩人：______________",
            "指导教师：______________",
            f"日期：{datetime.date.today().strftime('%Y年%m月')}",
        ]
        self.add_multiline_textbox(slide, 9.8, 5.6, 3.0, 1.2, meta_lines,
                                    font_size=12, color="#BDC3C7", line_spacing=1.8)
        # 页脚
        self.add_footer(slide)

    def slide_agenda(self):
        """第 2 页：汇报提纲"""
        slide = self.add_slide()
        self.add_title_bar(slide, "汇报提纲", "按 [问题-设计-实现-验证-总结] 逻辑展开")
        self.add_footer(slide)

        # 左侧：答辩重点
        self.add_rounded_rect(slide, 0.7, 2.2, 3.8, 3.0, fill_color=C["light_bg"])
        self.add_textbox(slide, 1.1, 2.5, 3.2, 0.45, "📌 答辩重点",
                         font_size=18, bold=True, color=C["navy"])
        self.add_multiline_textbox(slide, 1.1, 3.2, 3.2, 1.6, [
            "系统真实可运行",
            "数据库关系清楚",
            "核心流程闭环",
            "技术实现有亮点",
        ], font_size=15, color=C["text"], line_spacing=1.8)

        # 右侧：提纲
        items = [
            "1. 研究背景与课题目标",
            "2. 需求分析与技术路线",
            "3. 系统架构与程序结构",
            "4. 数据库 E-R 设计",
            "5. 核心功能实现（溯源 + 交易 + AI）",
            "6. 系统测试与演示路线",
            "7. 创新点、总结与展望",
        ]
        self.add_multiline_textbox(slide, 5.2, 2.2, 6.5, 4.5, items,
                                    font_size=18, color=C["text"], line_spacing=2.0)

    def slide_background(self):
        """第 3 页：研究背景与问题"""
        slide = self.add_slide()
        self.add_title_bar(slide, "研究背景与问题",
                           "传统农产品流通链条中，信任、渠道和数据能力是主要痛点")
        self.add_footer(slide)

        cards = [
            ("来源信息不透明", "消费者难以获取产地、采收、质检和流转信息，影响购买信任和食品安全。",
             C["accent"]),
            ("农户渠道有限", "中小农户缺少稳定线上展示和交易渠道，销售依赖中间环节，利润被层层压缩。",
             C["navy"]),
            ("助农服务分散", "补贴申请、技术培训、供需对接和市场判断缺少统一入口，数字化程度不足。",
             C["green"]),
        ]
        for i, (title, body, clr) in enumerate(cards):
            self.add_card(slide, 0.7 + i * 4.1, 2.2, 3.8, 2.8, title, body, clr)

        # 课题定位
        self.add_rounded_rect(slide, 0.7, 5.5, 12.0, 0.9, fill_color=C["navy"])
        self.add_textbox(slide, 1.0, 5.65, 2.0, 0.45, "🎯 课题定位", font_size=16, bold=True,
                         color="white")
        self.add_textbox(slide, 3.0, 5.65, 9.0, 0.45,
                         "建设连接农户、消费者、管理员的「可信溯源 + 助农服务」平台，用低成本 Web 技术实现产品发布→交易→溯源→供需→智能分析闭环",
                         font_size=13, color="#D5D8DC")

    def slide_objectives(self):
        """第 4 页：系统目标与角色需求"""
        slide = self.add_slide()
        self.add_title_bar(slide, "系统目标与角色需求",
                           "围绕消费者、农户和管理员三类角色建立业务闭环")
        self.add_footer(slide)

        # 插入角色图
        self.add_image(slide, "user_roles", 0.3, 2.0, 12.7, 4.8)

    def slide_tech_stack(self):
        """第 5 页：技术路线"""
        slide = self.add_slide()
        self.add_title_bar(slide, "技术路线与开发环境",
                           "采用成熟 Python Web 技术栈，兼顾开发效率、扩展性和部署便利性")
        self.add_footer(slide)

        rows_data = [
            ("层次", "技术", "作用"),
            ("后端框架", "Django 6.0 + DRF", "业务处理、ORM、认证授权、模板渲染"),
            ("前端页面", "Django Templates + Bootstrap 5", "响应式页面、表单、列表和后台管理界面"),
            ("数据可视化", "ECharts", "首页数据看板、市场分析图表和地区统计"),
            ("数据库", "SQLite（开发）/ PostgreSQL（生产）", "数据持久化，ORM 管理数据模型"),
            ("批次溯源", "qrcode + 链式结构记录机制", "批次二维码生成、溯源记录防篡改设计"),
            ("智能分析", "本地大模型 Ollama（qwen2.5:7b）", "市场简报生成和农业智能问答"),
            ("API 文档", "drf-spectacular / Swagger", "自动生成 OpenAPI 文档"),
            ("部署", "Docker + Gunicorn + WhiteNoise", "容器化部署和静态资源服务"),
        ]

        table_shape = slide.shapes.add_table(
            len(rows_data), 3,
            Inches(0.8), Inches(2.1),
            Inches(11.5), Inches(4.4))
        table = table_shape.table
        table.columns[0].width = Inches(1.8)
        table.columns[1].width = Inches(3.5)
        table.columns[2].width = Inches(6.2)

        for r, row in enumerate(rows_data):
            for c, cell_text in enumerate(row):
                cell = table.cell(r, c)
                cell.text = cell_text
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(13 if r > 0 else 14)
                    p.font.name = FONT
                    p.font.bold = (r == 0)
                    p.font.color.rgb = rgb(C["white"] if r == 0 else C["text"])
                if r == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb(C["navy"])
                elif r % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb(C["light_bg"])
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE

        self.add_textbox(slide, 1.0, 6.7, 10, 0.35,
                         "💡 技术选型理由：Django 内置 ORM + 认证 + 后台管理，适合快速开发管理型 Web 平台；配合 DRF 方便后续扩展移动端",
                         font_size=11, color=C["muted"])

    def slide_architecture(self):
        """第 6 页：系统总体架构"""
        slide = self.add_slide()
        self.add_title_bar(slide, "系统总体架构",
                           "B/S 架构：浏览器访问 → 路由分发 → 业务处理 → 数据持久化 + 外部能力集成")
        self.add_footer(slide)
        self.add_image(slide, "architecture", 0.5, 1.9, 12.3, 5.0)

    def slide_program_structure(self):
        """第 7 页：程序结构"""
        slide = self.add_slide()
        self.add_title_bar(slide, "程序结构图",
                           "按 Django App 拆分业务模块，核心模块边界清晰、职责明确")
        self.add_footer(slide)
        self.add_image(slide, "program_struct", 0.5, 1.9, 12.3, 5.0)

    def slide_function_modules(self):
        """第 8 页：功能模块"""
        slide = self.add_slide()
        self.add_title_bar(slide, "功能模块结构",
                           "以「可信溯源 + 交易闭环 + 助农服务」为主线，覆盖 10+ 业务模块")
        self.add_footer(slide)
        self.add_image(slide, "function_modules", 0.7, 1.9, 11.5, 5.0)

    def slide_er(self):
        """第 9 页：数据库 E-R 图"""
        slide = self.add_slide()
        self.add_title_bar(slide, "数据库 E-R 图",
                           "核心关系链：用户 → 农户档案 → 产品 → 批次 → 溯源事件 | 用户 → 订单 → 订单项 → 批次")
        self.add_footer(slide)
        self.add_image(slide, "er_diagram", 0.3, 1.8, 12.7, 5.2)

    def slide_data_tables(self):
        """第 10 页：主要数据表"""
        slide = self.add_slide()
        self.add_title_bar(slide, "主要数据表设计",
                           "围绕溯源、交易和助农扩展建立数据模型（55+ 用户 / 109 产品 / 378 批次数据）")
        self.add_footer(slide)

        rows_data = [
            ("数据表", "模型", "核心字段"),
            ("core_farmerprofile", "FarmerProfile", "phone, address, farm_story, verified"),
            ("core_product", "Product", "name, category, price, status, review_note"),
            ("core_productbatch", "ProductBatch", "batch_code, harvest_date, quantity, qr_code, qc_report"),
            ("core_traceevent", "TraceEvent", "event_type, title, record_fingerprint（链式结构）"),
            ("core_order", "Order", "buyer, total_amount, payment_method, tracking_number"),
            ("core_orderitem", "OrderItem", "order, product_batch, quantity, price"),
            ("core_supplydemandpost", "SupplyDemandPost", "post_type, product_name, category, status"),
            ("core_demandresponse", "DemandResponse", "farmer, demand_post, product, message"),
            ("core_review", "Review", "order, buyer, product, rating, comment"),
            ("core_notification", "Notification", "recipient, type, title, is_read"),
        ]

        table_shape = slide.shapes.add_table(
            len(rows_data), 3,
            Inches(0.7), Inches(2.0),
            Inches(12.0), Inches(4.8))
        table = table_shape.table
        table.columns[0].width = Inches(3.2)
        table.columns[1].width = Inches(2.8)
        table.columns[2].width = Inches(6.0)

        for r, row in enumerate(rows_data):
            for c, cell_text in enumerate(row):
                cell = table.cell(r, c)
                cell.text = cell_text
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(12 if r > 0 else 13)
                    p.font.name = FONT
                    p.font.bold = (r == 0)
                    p.font.color.rgb = rgb(C["white"] if r == 0 else C["text"])
                if r == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb(C["navy"])
                elif r % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb(C["light_bg"])
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE

    def slide_trace_flow(self):
        """第 11 页：批次溯源流程"""
        slide = self.add_slide()
        self.add_title_bar(slide, "核心流程：产品批次溯源",
                           "每批产品生成独立批次编码和二维码，消费者扫码即可查看完整溯源信息")
        self.add_footer(slide)
        self.add_image(slide, "trace_flow", 0.5, 1.9, 12.3, 4.5)
        # 补充说明
        self.add_textbox(slide, 1.0, 6.5, 11, 0.4,
                         "技术实现：ProductBatch.save() 自动生成 B-日期-随机串 批次码；qrcode 库生成二维码；TraceEvent 链式记录防篡改",
                         font_size=11, color=C["muted"])

    def slide_order_flow(self):
        """第 12 页：订单交易流程"""
        slide = self.add_slide()
        self.add_title_bar(slide, "核心流程：订单交易闭环",
                           "从购物车到评价反馈，OrderItem 绑定具体批次，保证交易记录可追溯来源")
        self.add_footer(slide)
        self.add_image(slide, "order_flow", 0.5, 1.9, 12.3, 4.5)
        self.add_textbox(slide, 1.0, 6.5, 11, 0.4,
                         "库存控制：购物车结算使用 select_for_update() 行级锁 + transaction.atomic() 防超卖",
                         font_size=11, color=C["muted"])

    def slide_ai(self):
        """第 13 页：智能助农分析"""
        slide = self.add_slide()
        self.add_title_bar(slide, "智能助农分析",
                           "订单与供需数据聚合后生成市场简报，大模型不可用时自动降级")
        self.add_footer(slide)
        self.add_image(slide, "ai_analysis", 0.5, 1.9, 12.0, 4.5)
        self.add_textbox(slide, 1.0, 6.5, 11, 0.4,
                         "降级策略：llm_service.py 中实现 Ollama 优先 + 规则引擎兜底，分析页面在离线状态下仍可正常访问",
                         font_size=11, color=C["muted"])

    def slide_admin(self):
        """第 14 页：后台管理与权限"""
        slide = self.add_slide()
        self.add_title_bar(slide, "后台管理与权限控制",
                           "通过角色识别、装饰器权限和审核流程保证数据质量和系统安全")
        self.add_footer(slide)

        cards = [
            ("🔐 权限控制", "• Django 内置认证体系\n• 农户功能需 FarmerProfile + verified\n• 管理员功能需 staff 权限\n• DRF API 层保留权限控制\n• @farmer_required 装饰器拦截",
             C["navy"]),
            ("✅ 审核流程", "• 产品审核（通过/拒绝+模态框填原因）\n• 批次质检审核（通过/拒绝）\n• 农户入驻审核（通过/拒绝）\n• 补贴申请审核\n• 已上架产品编辑需重新审核",
             C["green"]),
            ("📊 运营能力", "• 用户管理（55+注册用户）\n• 订单与产品数据导出\n• 站内通知（订单/供需/审核）\n• 后台数据看板\n• 供需对接审核",
             C["accent"]),
        ]
        for i, (title, body, clr) in enumerate(cards):
            self.add_card(slide, 0.7 + i * 4.1, 2.2, 3.8, 3.5, title, body, clr)

    def slide_testing(self):
        """第 15 页：系统测试"""
        slide = self.add_slide()
        self.add_title_bar(slide, "系统测试",
                           "围绕核心主流程、接口权限和页面可用性进行完整验证")
        self.add_footer(slide)

        rows_data = [
            ("测试项", "操作", "预期结果", "结论"),
            ("用户登录", "输入正确账号密码", "登录成功并按角色跳转首页", "✅ 通过"),
            ("产品审核", "管理员点击通过/拒绝", "产品状态变更 + 通知农户", "✅ 通过"),
            ("批次溯源", "输入有效批次码或扫码", "展示产品/农户/质检/溯源事件", "✅ 通过"),
            ("订单提交", "填写收货信息 → 提交", "生成订单 + 扣减库存 + 关联批次", "✅ 通过"),
            ("供需响应", "农户用产品响应需求帖", "创建 DemandResponse + 通知买家", "✅ 通过"),
            ("AI 分析", "访问市场分析页", "展示统计图表和 AI/规则简报", "✅ 通过"),
            ("权限校验", "未审核农户访问收款方式", "拦截并提示审核中", "✅ 通过"),
        ]

        table_shape = slide.shapes.add_table(
            len(rows_data), 4,
            Inches(0.6), Inches(2.0),
            Inches(12.0), Inches(4.5))
        table = table_shape.table
        table.columns[0].width = Inches(2.0)
        table.columns[1].width = Inches(3.5)
        table.columns[2].width = Inches(4.5)
        table.columns[3].width = Inches(2.0)

        for r, row in enumerate(rows_data):
            for c, cell_text in enumerate(row):
                cell = table.cell(r, c)
                cell.text = cell_text
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(12 if r > 0 else 13)
                    p.font.name = FONT
                    p.font.bold = (r == 0)
                    p.font.color.rgb = rgb(C["white"] if r == 0 else C["text"])
                if r == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb(C["navy"])
                elif r % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb(C["light_bg"])
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE

    def slide_demo(self):
        """第 16 页：系统演示路线"""
        slide = self.add_slide()
        self.add_title_bar(slide, "系统演示路线",
                           "答辩现场按一条闭环路线演示，控制在 2-3 分钟")
        self.add_footer(slide)

        # 模拟演示流程节点
        demo_steps = [
            ("首页\n看板", C["navy"]),
            ("产品\n列表", C["accent2"]),
            ("产品\n详情", C["green"]),
            ("下单\n支付", C["accent"]),
            ("农户\n后台", C["navy"]),
            ("批次管\n理+二维码", C["dark"]),
            ("溯源\n查询", C["accent"]),
            ("市场\n分析", C["green"]),
            ("管理\n审核", C["navy"]),
        ]
        positions = [
            (0.5, 3.0), (1.8, 3.0), (3.1, 3.0), (4.4, 3.0),
            (5.7, 3.0),  # 第一行
            (5.7, 5.0), (4.4, 5.0), (3.1, 5.0), (0.5, 5.0),  # 第二行（反向）
        ]
        for i, ((label, clr), (x, y)) in enumerate(zip(demo_steps, positions)):
            shape = self.add_rounded_rect(slide, x, y, 1.1, 0.9,
                                           fill_color=clr, border_color=clr)
            tf = shape.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = label
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = rgb("white")
            p.font.name = FONT
            p.alignment = PP_ALIGN.CENTER

        self.add_textbox(slide, 1.5, 6.3, 10, 0.6,
                         "演示原则：先消费者视角 → 农户/管理员后台 → 溯源+分析体现系统特色 | 重点页面提前打开，减少现场等待",
                         font_size=13, color=C["muted"], alignment="center")

    def slide_innovation(self):
        """第 17 页：创新点与特色"""
        slide = self.add_slide()
        self.add_title_bar(slide, "创新点与特色",
                           "从业务闭环、可信溯源和智能助农三个层面体现项目价值")
        self.add_footer(slide)

        innovations = [
            ("交易 + 溯源深度结合", "订单项关联具体产品批次，消费者购买后能追溯至源头；购物车结算实现行级锁库存控制。",
             C["accent"]),
            ("低成本二维码溯源方案", "批次码 + qrcode 自动生成，农户下载即用；TraceEvent 采用链式结构记录，具备防篡改设计基础。",
             C["green"]),
            ("本地大模型助农 + 降级", "Ollama 生成市场简报和农技问答；模型不可用时规则引擎兜底，保证系统在任何环境下可用。",
             C["accent2"]),
            ("农户主动供需交互", "需求帖由农户主动用产品响应，形成买方-农户双向互动；全程站内通知，增强平台活跃度。",
             C["navy"]),
        ]
        for i, (title, desc, clr) in enumerate(innovations):
            y = 2.1 + i * 1.3
            self.add_card(slide, 0.7, y, 12.0, 1.1, title, desc, clr)

    def slide_summary(self):
        """第 18 页：总结与展望"""
        slide = self.add_slide()
        self.add_title_bar(slide, "总结与展望",
                           "系统完成从需求分析、设计、实现到测试的完整闭环")
        self.add_footer(slide)

        # 数据指标
        metrics = [
            ("3", "类核心角色"),
            ("11", "个业务模块"),
            ("10+", "个数据模型"),
            ("55+", "注册用户"),
            ("378", "条批次数据"),
        ]
        for i, (num, label) in enumerate(metrics):
            x = 0.8 + i * 2.5
            self.add_rounded_rect(slide, x, 2.1, 2.2, 1.8, fill_color=C["light_bg"])
            self.add_textbox(slide, x + 0.3, 2.3, 1.6, 0.8, num,
                             font_size=42, bold=True, color=C["navy"], alignment="center")
            self.add_textbox(slide, x + 0.3, 3.2, 1.6, 0.4, label,
                             font_size=14, color=C["muted"], alignment="center")

        # 展望
        self.add_rounded_rect(slide, 0.7, 4.3, 12.0, 1.0, fill_color=C["navy"])
        self.add_textbox(slide, 1.0, 4.45, 2.5, 0.4,
                         "🔮 后续可扩展：", font_size=14, bold=True, color="white")
        outlook = "微信小程序 · 真实在线支付 · 物联网数据采集 · 可信存证平台接入 · 个性化推荐与价格预测"
        self.add_textbox(slide, 3.3, 4.45, 9.0, 0.4, outlook,
                         font_size=13, color="#BDC3C7")

        # 感谢
        self.add_textbox(slide, 3.5, 5.8, 7, 0.7,
                         "感谢各位老师，请批评指正！",
                         font_size=30, bold=True, color=C["accent"], alignment="center")

    def slide_qa(self):
        """第 19 页：Q&A 准备（备注页，演讲时不展示）"""
        slide = self.add_slide()
        self.add_title_bar(slide, "Q&A 常见问题准备",
                           "答辩常见问题及回答要点，供准备时参考")
        self.add_footer(slide)

        qa_items = [
            ("Q1: 和普通电商平台有什么区别？",
             "本系统不仅做交易，更强调「可信溯源」：批次二维码、链式结构记录、质检审核。同时加入农技知识、补贴申请、供需对接和 AI 市场分析，是面向农业场景的综合平台。"),
            ("Q2: 溯源信息如何保证可信？",
             "每批次生成唯一编码和二维码，溯源事件采用链式结构记录机制，后一条记录包含前一条的指纹，具备防篡改设计基础，后续可接入可信存证平台。"),
            ("Q3: 为什么选择 Django？",
             "Django 内置 ORM、用户认证、后台管理和安全防护，适合快速开发管理型 Web 平台。配合 DRF 生成 RESTful API，方便后续扩展移动端或小程序。"),
            ("Q4: 大模型不可用怎么办？",
             "llm_service.py 实现了降级设计：Ollama 优先调用，超时或连接失败时使用规则引擎生成摘要，保证分析页面在任何情况下都能正常展示。"),
            ("Q5: 核心数据库关系？",
             "两条主线：① 用户→农户档案→产品→批次→溯源事件（支撑溯源）；② 用户→订单→订单项→批次（支撑交易）。订单项直接关联批次，保证可追溯。"),
        ]
        for i, (q, a) in enumerate(qa_items):
            y = 2.1 + i * 1.05
            self.add_textbox(slide, 0.7, y, 2.5, 0.35, q,
                             font_size=12, bold=True, color=C["navy"])
            self.add_textbox(slide, 3.3, y, 9.5, 0.85, a,
                             font_size=11, color=C["text"])

    def build(self):
        """构建所有幻灯片"""
        print("📄 构建 PPT 幻灯片...")
        pages = [
            ("封面", self.slide_cover),
            ("汇报提纲", self.slide_agenda),
            ("研究背景与问题", self.slide_background),
            ("系统目标与角色需求", self.slide_objectives),
            ("技术路线", self.slide_tech_stack),
            ("系统总体架构", self.slide_architecture),
            ("程序结构图", self.slide_program_structure),
            ("功能模块结构", self.slide_function_modules),
            ("数据库E-R图", self.slide_er),
            ("主要数据表设计", self.slide_data_tables),
            ("批次溯源流程", self.slide_trace_flow),
            ("订单交易流程", self.slide_order_flow),
            ("智能助农分析", self.slide_ai),
            ("后台管理与权限", self.slide_admin),
            ("系统测试", self.slide_testing),
            ("系统演示路线", self.slide_demo),
            ("创新点与特色", self.slide_innovation),
            ("总结与展望", self.slide_summary),
            ("Q&A准备（备注）", self.slide_qa),
        ]
        for name, func in pages:
            func()
            print(f"  ✅ 第{self.slide_num}页: {name}")


# ═══════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  毕业设计答辩 PPT 生成器")
    print("  基于 Django 与大模型的农产品溯源与智能助农平台")
    print("=" * 60)

    # Step 1: 生成图表
    diagrams = generate_all_diagrams()

    # Step 2: 构建 PPT
    builder = PPTBuilder(diagrams)
    builder.build()

    # Step 3: 保存
    builder.prs.save(str(PPT_PATH))
    print(f"\n🎉 PPT 已生成：{PPT_PATH}")
    print(f"   共 {builder.slide_num} 页幻灯片")
    print(f"   图表缓存：{OUTPUT_DIR}")
    print("\n💡 提示：")
    print("   - 封面页请手动填写答辩人姓名、学号、指导教师")
    print("   - 建议提前打开系统页面，现场演示时减少加载等待")
    print("   - 演讲时间控制在 10 分钟内，重点讲溯源流程和 AI 分析")


if __name__ == "__main__":
    main()
