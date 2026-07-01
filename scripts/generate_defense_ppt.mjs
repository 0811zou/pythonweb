import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SLIDE_W = 1280;
const SLIDE_H = 720;

const COLORS = {
  ink: "#000000",
  text: "#202124",
  muted: "#555555",
  faint: "#7A7A7A",
  panel: "#EDEDED",
  panel2: "#F6F6F6",
  rule: "#B8BCC4",
  accent: "#FF6B35",
  white: "#FFFFFF",
};

const FONT = "Microsoft YaHei";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const item = argv[i];
    if (!item.startsWith("--")) continue;
    const key = item.slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) {
      args[key] = next;
      i += 1;
    } else {
      args[key] = true;
    }
  }
  return args;
}

function defaultProjectRoot() {
  return path.resolve(__dirname, "..");
}

function ensureDirFor(filePath) {
  return fs.mkdir(path.dirname(filePath), { recursive: true });
}

function addShape(slide, {
  name,
  geometry = "rect",
  left,
  top,
  width,
  height,
  fill = COLORS.panel,
  line = { style: "solid", fill: "none", width: 0 },
}) {
  return slide.shapes.add({
    name,
    geometry,
    position: { left, top, width, height },
    fill,
    line,
  });
}

function addText(slide, text, {
  name,
  left,
  top,
  width,
  height,
  fontSize = 20,
  bold = false,
  color = COLORS.text,
  alignment = "left",
  verticalAlignment = "top",
  lineSpacing,
  fill = "none",
  line = { style: "solid", fill: "none", width: 0 },
}) {
  const shape = slide.shapes.add({
    name,
    geometry: "textbox",
    position: { left, top, width, height },
    fill,
    line,
  });
  shape.text = text;
  shape.text.style = {
    fontSize,
    bold,
    color,
    alignment,
    verticalAlignment,
    typeface: FONT,
    ...(lineSpacing ? { lineSpacing } : {}),
  };
  return shape;
}

function addFooter(slide, n, label = "智农溯源 毕设答辩") {
  addText(slide, label, {
    name: "footer-label",
    left: 42,
    top: 660,
    width: 520,
    height: 28,
    fontSize: 14,
    color: COLORS.faint,
  });
  addText(slide, String(n).padStart(2, "0"), {
    name: "footer-number",
    left: 1184,
    top: 660,
    width: 54,
    height: 28,
    fontSize: 14,
    color: COLORS.faint,
    alignment: "right",
  });
}

function addTitle(slide, n, title, subtitle = "") {
  addText(slide, title, {
    name: "slide-title",
    left: 42,
    top: 36,
    width: 1120,
    height: 60,
    fontSize: 40,
    bold: true,
    color: COLORS.ink,
  });
  if (subtitle) {
    addText(slide, subtitle, {
      name: "slide-subtitle",
      left: 42,
      top: 102,
      width: 980,
      height: 44,
      fontSize: 21,
      color: COLORS.muted,
    });
  }
  addFooter(slide, n);
}

function addPanel(slide, left, top, width, height, fill = COLORS.panel) {
  return addShape(slide, {
    name: "panel",
    geometry: "roundRect",
    left,
    top,
    width,
    height,
    fill,
    line: { style: "solid", fill: COLORS.panel, width: 1 },
  });
}

function addCard(slide, { left, top, width, height, heading, body, accent = false }) {
  addPanel(slide, left, top, width, height, COLORS.panel);
  addShape(slide, {
    name: "card-mark",
    left: left + 22,
    top: top + 26,
    width: 16,
    height: 16,
    fill: accent ? COLORS.accent : COLORS.ink,
    line: { style: "solid", fill: "none", width: 0 },
  });
  addText(slide, heading, {
    name: "card-heading",
    left: left + 54,
    top: top + 20,
    width: width - 76,
    height: 34,
    fontSize: 24,
    bold: true,
    color: COLORS.ink,
  });
  addText(slide, body, {
    name: "card-body",
    left: left + 54,
    top: top + 62,
    width: width - 76,
    height: height - 76,
    fontSize: 18,
    color: COLORS.text,
    lineSpacing: 1.15,
  });
}

function addBulletList(slide, items, { left, top, width, height, fontSize = 22 }) {
  const text = items.map((item) => `• ${item}`).join("\n");
  return addText(slide, text, {
    name: "bullet-list",
    left,
    top,
    width,
    height,
    fontSize,
    color: COLORS.text,
    lineSpacing: 1.22,
  });
}

function addNode(slide, label, x, y, w, h, { fill = COLORS.panel, fontSize = 20, bold = true } = {}) {
  const node = addShape(slide, {
    name: `node-${label}`,
    geometry: "roundRect",
    left: x,
    top: y,
    width: w,
    height: h,
    fill,
    line: { style: "solid", fill: COLORS.rule, width: 1 },
  });
  node.text = label;
  node.text.style = {
    fontSize,
    bold,
    color: COLORS.ink,
    alignment: "center",
    verticalAlignment: "middle",
    typeface: FONT,
  };
  return node;
}

function connect(slide, from, to, opts = {}) {
  const config = {
    kind: opts.kind || "straight",
    fromSide: opts.fromSide,
    toSide: opts.toSide,
    line: { style: opts.style || "solid", fill: opts.color || COLORS.rule, width: opts.width || 2 },
  };
  if (opts.head !== false) {
    config.tail = { type: "arrow", width: "sm", length: "sm" };
  }
  return slide.shapes.connect(from, to, config);
}

function addNotes(slide, notes) {
  slide.speakerNotes.textFrame.setText(Array.isArray(notes) ? notes : [notes]);
  slide.speakerNotes.setVisible(true);
}

function createTitleSlide(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addText(slide, "基于 Django 与大模型的", {
    name: "cover-eyebrow",
    left: 42,
    top: 58,
    width: 760,
    height: 44,
    fontSize: 30,
    color: COLORS.muted,
  });
  addText(slide, "农产品溯源与智能助农平台", {
    name: "cover-title",
    left: 42,
    top: 118,
    width: 980,
    height: 150,
    fontSize: 56,
    bold: true,
    color: COLORS.ink,
    lineSpacing: 0.95,
  });
  addShape(slide, {
    name: "cover-rule",
    left: 42,
    top: 304,
    width: 740,
    height: 3,
    fill: COLORS.accent,
  });
  addPanel(slide, 0, 390, 1280, 330, COLORS.panel);
  addText(slide, "毕业设计答辩", {
    name: "cover-type",
    left: 452,
    top: 456,
    width: 330,
    height: 44,
    fontSize: 28,
    bold: true,
    color: COLORS.ink,
  });
  addText(slide, "Django 5.2 / DRF / Bootstrap / ECharts / 本地大模型（Ollama）", {
    name: "cover-stack",
    left: 452,
    top: 515,
    width: 620,
    height: 36,
    fontSize: 20,
    color: COLORS.text,
  });
  addText(slide, "答辩人：__________    指导教师：__________    日期：__________", {
    name: "cover-meta",
    left: 452,
    top: 580,
    width: 690,
    height: 34,
    fontSize: 18,
    color: COLORS.muted,
  });
  addText(slide, "01", {
    name: "cover-page",
    left: 1184,
    top: 660,
    width: 54,
    height: 26,
    fontSize: 14,
    color: COLORS.faint,
    alignment: "right",
  });
  addNotes(slide, "开场说明：本课题针对农产品来源不透明、农户销售渠道有限和助农服务数字化不足的问题，设计并实现一个综合性 Web 平台。");
  return slide;
}

function createAgendaSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "汇报提纲", "按问题、设计、实现、验证、总结的答辩逻辑展开");
  addBulletList(slide, [
    "研究背景与课题目标",
    "需求分析与技术路线",
    "系统架构与程序结构",
    "数据库 ER 设计",
    "核心功能实现",
    "系统测试与演示路线",
    "创新点、总结与展望",
  ], { left: 620, top: 168, width: 560, height: 410, fontSize: 30 });
  addPanel(slide, 42, 176, 446, 300, COLORS.panel);
  addText(slide, "答辩重点", {
    left: 82,
    top: 220,
    width: 360,
    height: 40,
    fontSize: 28,
    bold: true,
    color: COLORS.ink,
  });
  addText(slide, "让老师看到：系统真实可运行、数据库关系清楚、核心流程闭环、技术实现有亮点。", {
    left: 82,
    top: 286,
    width: 344,
    height: 104,
    fontSize: 22,
    color: COLORS.text,
    lineSpacing: 1.18,
  });
  addNotes(slide, "这一页快速说明汇报结构，不展开细节，控制在 20 秒以内。");
}

function createBackgroundSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "研究背景与问题", "传统农产品流通链条中，信任、渠道和数据能力是主要痛点");
  addCard(slide, {
    left: 42,
    top: 205,
    width: 366,
    height: 190,
    heading: "来源信息不透明",
    body: "消费者难以获取产地、采收、质检和流转信息，影响购买信任。",
    accent: true,
  });
  addCard(slide, {
    left: 457,
    top: 205,
    width: 366,
    height: 190,
    heading: "农户渠道有限",
    body: "中小农户缺少稳定线上展示和交易渠道，销售依赖中间环节。",
  });
  addCard(slide, {
    left: 872,
    top: 205,
    width: 366,
    height: 190,
    heading: "助农服务分散",
    body: "补贴、培训、供需对接和市场判断缺少统一入口，数字化程度不足。",
  });
  addPanel(slide, 42, 450, 1196, 118, COLORS.panel2);
  addText(slide, "课题定位", {
    left: 76,
    top: 478,
    width: 150,
    height: 36,
    fontSize: 24,
    bold: true,
    color: COLORS.ink,
  });
  addText(slide, "建设一个连接农户、消费者和管理员的可信溯源与助农服务平台，用低成本 Web 技术完成产品发布、交易、溯源、供需和智能分析闭环。", {
    left: 230,
    top: 475,
    width: 940,
    height: 54,
    fontSize: 22,
    color: COLORS.text,
    lineSpacing: 1.15,
  });
  addNotes(slide, "强调课题不是普通电商，而是围绕农产品信任和助农服务展开。");
}

function createObjectivesSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "系统目标与角色需求", "围绕消费者、农户和管理员三类角色建立业务闭环");
  addCard(slide, {
    left: 42,
    top: 190,
    width: 360,
    height: 310,
    heading: "消费者",
    body: "浏览产品\n扫码溯源\n加入购物车\n下单支付\n评价反馈",
    accent: true,
  });
  addCard(slide, {
    left: 460,
    top: 190,
    width: 360,
    height: 310,
    heading: "农户",
    body: "维护店铺\n发布产品\n创建批次\n下载二维码\n处理订单和补贴",
  });
  addCard(slide, {
    left: 878,
    top: 190,
    width: 360,
    height: 310,
    heading: "管理员",
    body: "审核产品\n审核批次\n管理用户\n处理入驻申请\n导出业务数据",
  });
  addText(slide, "目标：让交易数据、批次数据和助农服务在一个平台内贯通。", {
    left: 84,
    top: 555,
    width: 1040,
    height: 42,
    fontSize: 26,
    bold: true,
    color: COLORS.ink,
  });
  addNotes(slide, "用三类角色解释需求，可以自然过渡到功能模块设计。");
}

function createTechStackSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "技术路线", "采用成熟 Python Web 技术栈，兼顾开发效率、扩展性和部署便利性");
  const rows = [
    ["层次", "技术", "作用"],
    ["后端", "Django 5.2 + DRF", "业务处理、ORM、认证、REST API"],
    ["前端", "Django Templates + Bootstrap", "响应式页面、表单和后台界面"],
    ["数据", "SQLite / PostgreSQL", "开发和生产环境数据持久化"],
    ["溯源", "qrcode + 链式结构记录机制", "批次二维码与防篡改设计"],
    ["智能", "本地大模型（Ollama）", "市场简报和农业问答"],
    ["部署", "Docker + Gunicorn + WhiteNoise", "容器化部署和静态资源服务"],
  ];
  const table = slide.tables.add({
    rows: rows.length,
    columns: 3,
    left: 76,
    top: 170,
    width: 1128,
    height: 385,
    columnTracks: [{ mode: "fixed", value: 150 }, { mode: "fixed", value: 360 }, { mode: "fr", value: 1 }],
    values: rows,
  });
  table.styleOptions = { headerRow: true, bandedRows: true };
  table.borders.assign({ style: "solid", fill: COLORS.rule, width: 1 });
  for (let c = 0; c < 3; c += 1) {
    table.getCell(0, c).fill = COLORS.ink;
    table.getCell(0, c).text.style = { color: COLORS.white, bold: true, fontSize: 18, typeface: FONT };
  }
  for (let r = 1; r < rows.length; r += 1) {
    for (let c = 0; c < 3; c += 1) {
      const cell = table.getCell(r, c);
      cell.text.style = { fontSize: 16, typeface: FONT, color: COLORS.text };
    }
  }
  addText(slide, "答辩建议：AI 只讲“本地大模型能力”，不要主动暴露具体模型版本。", {
    left: 76,
    top: 580,
    width: 980,
    height: 34,
    fontSize: 19,
    color: COLORS.muted,
  });
  addNotes(slide, "技术路线页重点说清为什么选 Django：自带 ORM、认证和后台，适合管理型 Web 系统。");
}

function createArchitectureSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "系统总体架构", "B/S 架构：页面访问、业务处理、数据持久化和外部能力集成");
  const user = addNode(slide, "浏览器\n消费者 / 农户 / 管理员", 70, 215, 230, 92, { fill: COLORS.panel2, fontSize: 19 });
  const route = addNode(slide, "路由层\nconfig.urls / app urls", 370, 215, 230, 92, { fontSize: 19 });
  const view = addNode(slide, "业务层\nViews / DRF ViewSets", 670, 215, 230, 92, { fontSize: 19 });
  const orm = addNode(slide, "模型层\nDjango ORM", 970, 215, 230, 92, { fill: COLORS.panel2, fontSize: 19 });
  connect(slide, user, route, { fromSide: "right", toSide: "left" });
  connect(slide, route, view, { fromSide: "right", toSide: "left" });
  connect(slide, view, orm, { fromSide: "right", toSide: "left" });

  const db = addNode(slide, "数据库\nSQLite / PostgreSQL", 970, 420, 230, 82, { fontSize: 18 });
  const media = addNode(slide, "媒体文件\n产品图 / 二维码", 670, 420, 230, 82, { fontSize: 18 });
  const ai = addNode(slide, "智能分析\n本地大模型 / 规则降级", 370, 420, 230, 82, { fontSize: 18 });
  const docs = addNode(slide, "API 文档\nSwagger / OpenAPI", 70, 420, 230, 82, { fontSize: 18 });
  connect(slide, orm, db, { fromSide: "bottom", toSide: "top", kind: "elbow" });
  connect(slide, view, media, { fromSide: "bottom", toSide: "top", kind: "elbow" });
  connect(slide, view, ai, { fromSide: "bottom", toSide: "top", kind: "elbow" });
  connect(slide, route, docs, { fromSide: "bottom", toSide: "top", kind: "elbow" });
  addNotes(slide, "说明架构从浏览器进入，经过路由和视图，最终通过 ORM 访问数据；二维码、AI 和 API 文档是增强能力。");
}

function createProgramStructureSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "程序结构图", "按 Django App 拆分业务，核心模块边界清晰");
  const root = addNode(slide, "pythonweb 项目根目录", 480, 156, 320, 58, { fill: COLORS.panel2, fontSize: 22 });
  const dirs = [
    ["config\n配置与总路由", 60, 275],
    ["accounts\n登录与农户档案", 300, 275],
    ["products\n产品/批次/评价", 540, 275],
    ["trade\n购物车/订单/物流", 780, 275],
    ["traceability\n溯源事件", 1020, 275],
    ["marketplace\n供需对接", 60, 430],
    ["knowledge\n农技知识库", 300, 430],
    ["preorder\n预售认养", 540, 430],
    ["analysis\n市场分析/AI", 780, 430],
    ["admin_panel\n后台审核管理", 1020, 430],
  ];
  const nodes = dirs.map(([label, x, y]) => addNode(slide, label, x, y, 200, 74, { fontSize: 18 }));
  nodes.forEach((node) => connect(slide, root, node, { fromSide: "bottom", toSide: "top", kind: "elbow", head: false, width: 1.4 }));
  addPanel(slide, 60, 575, 1160, 44, COLORS.panel2);
  addText(slide, "templates 负责页面模板，core/static 负责静态资源，deploy / scripts 负责部署与初始化脚本。", {
    left: 90,
    top: 586,
    width: 1060,
    height: 26,
    fontSize: 18,
    color: COLORS.muted,
  });
  addNotes(slide, "这一页对应代码目录，证明项目不是单文件堆叠，而是按业务拆分维护。");
}

function createFunctionModuleSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "功能模块结构", "平台以“可信溯源 + 交易闭环 + 助农服务”为主线");
  const center = addNode(slide, "农产品溯源与\n智能助农平台", 500, 292, 280, 96, { fill: COLORS.ink, fontSize: 23 });
  center.text.style = { fontSize: 23, bold: true, color: COLORS.white, alignment: "center", verticalAlignment: "middle", typeface: FONT };
  const modules = [
    ["用户与权限", 82, 185],
    ["产品管理", 360, 185],
    ["批次溯源", 838, 185],
    ["交易订单", 1110 - 210, 185],
    ["补贴申请", 82, 470],
    ["供需/预售", 360, 470],
    ["农技知识", 638, 470],
    ["数据分析", 916, 470],
  ];
  modules.forEach(([label, x, y], idx) => {
    const node = addNode(slide, label, x, y, 210, 72, { fill: idx === 2 ? COLORS.panel2 : COLORS.panel, fontSize: 21 });
    connect(slide, center, node, { kind: "elbow", head: false, width: 1.5 });
  });
  addText(slide, "核心演示：产品发布 → 批次审核 → 二维码溯源 → 下单交易 → 农户处理 → 评价反馈。", {
    left: 106,
    top: 610,
    width: 1040,
    height: 34,
    fontSize: 21,
    bold: true,
    color: COLORS.ink,
  });
  addNotes(slide, "功能模块页不要逐项解释，重点抓住主流程和助农扩展功能。");
}

function createERSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "数据库 E-R 图", "核心关系：用户、农户、产品、批次、溯源事件和订单");
  const nodes = {
    user: addNode(slide, "User\n用户", 70, 230, 145, 72, { fill: COLORS.panel2, fontSize: 18 }),
    farmer: addNode(slide, "FarmerProfile\n农户档案", 285, 230, 190, 72, { fontSize: 18 }),
    product: addNode(slide, "Product\n农产品", 545, 230, 170, 72, { fontSize: 18 }),
    batch: addNode(slide, "ProductBatch\n产品批次", 785, 230, 190, 72, { fill: COLORS.panel2, fontSize: 18 }),
    trace: addNode(slide, "TraceEvent\n溯源事件", 1040, 230, 170, 72, { fontSize: 18 }),
    order: addNode(slide, "Order\n订单", 320, 460, 145, 72, { fontSize: 18 }),
    item: addNode(slide, "OrderItem\n订单项", 575, 460, 170, 72, { fill: COLORS.panel2, fontSize: 18 }),
    review: addNode(slide, "Review\n评价", 830, 460, 145, 72, { fontSize: 18 }),
  };
  connect(slide, nodes.user, nodes.farmer, { fromSide: "right", toSide: "left", head: false });
  connect(slide, nodes.farmer, nodes.product, { fromSide: "right", toSide: "left", head: false });
  connect(slide, nodes.product, nodes.batch, { fromSide: "right", toSide: "left", head: false });
  connect(slide, nodes.batch, nodes.trace, { fromSide: "right", toSide: "left", head: false });
  connect(slide, nodes.user, nodes.order, { fromSide: "bottom", toSide: "top", kind: "elbow", head: false });
  connect(slide, nodes.order, nodes.item, { fromSide: "right", toSide: "left", head: false });
  connect(slide, nodes.item, nodes.batch, { fromSide: "top", toSide: "bottom", kind: "elbow", head: false });
  connect(slide, nodes.order, nodes.review, { fromSide: "right", toSide: "left", kind: "elbow", head: false });
  connect(slide, nodes.review, nodes.product, { fromSide: "top", toSide: "bottom", kind: "elbow", head: false });
  addText(slide, "1:1", { left: 230, top: 247, width: 58, height: 24, fontSize: 16, bold: true });
  addText(slide, "1:N", { left: 490, top: 247, width: 62, height: 24, fontSize: 16, bold: true });
  addText(slide, "1:N", { left: 730, top: 247, width: 62, height: 24, fontSize: 16, bold: true });
  addText(slide, "1:N", { left: 985, top: 247, width: 62, height: 24, fontSize: 16, bold: true });
  addText(slide, "订单项直接关联产品批次，因此消费者购买记录可以反查具体来源。", {
    left: 120,
    top: 600,
    width: 980,
    height: 34,
    fontSize: 22,
    bold: true,
    color: COLORS.ink,
    alignment: "center",
  });
  addNotes(slide, "答 ER 图时突出两条主链：用户-农户-产品-批次-溯源事件，以及用户-订单-订单项-批次。");
}

function createTablesSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "主要数据表设计", "围绕溯源、交易和助农扩展建立数据模型");
  const rows = [
    ["数据表", "模型", "作用"],
    ["core_farmerprofile", "FarmerProfile", "农户联系方式、地址、店铺简介和认证信息"],
    ["core_product", "Product", "农产品名称、分类、价格、单位和审核状态"],
    ["core_productbatch", "ProductBatch", "批次编码、采收日期、质检报告、二维码"],
    ["core_traceevent", "TraceEvent", "种植、施肥、采收、质检等链式溯源记录"],
    ["core_order / orderitem", "Order / OrderItem", "订单信息、收货信息和批次明细"],
    ["core_supplydemandpost", "SupplyDemandPost", "供应和需求信息发布"],
    ["core_preorder", "PreOrder", "预售活动和消费者预订记录"],
  ];
  const table = slide.tables.add({
    rows: rows.length,
    columns: 3,
    left: 54,
    top: 165,
    width: 1172,
    height: 415,
    columnTracks: [{ mode: "fixed", value: 245 }, { mode: "fixed", value: 245 }, { mode: "fr", value: 1 }],
    values: rows,
  });
  table.styleOptions = { headerRow: true, bandedRows: true };
  table.borders.assign({ style: "solid", fill: COLORS.rule, width: 1 });
  for (let c = 0; c < 3; c += 1) {
    table.getCell(0, c).fill = COLORS.ink;
    table.getCell(0, c).text.style = { color: COLORS.white, bold: true, fontSize: 17, typeface: FONT };
  }
  for (let r = 1; r < rows.length; r += 1) {
    for (let c = 0; c < 3; c += 1) {
      table.getCell(r, c).text.style = { fontSize: 15, typeface: FONT, color: COLORS.text };
    }
  }
  addNotes(slide, "表格页用于补充 ER 图，讲重点表即可，不需要逐字段展开。");
}

function createTraceFlowSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "核心流程：批次溯源", "每批产品生成独立批次编码和二维码，消费者可扫码查询");
  const steps = [
    ["农户发布产品", 52],
    ["管理员审核", 258],
    ["创建产品批次", 464],
    ["批次质检通过", 670],
    ["生成二维码", 876],
    ["消费者扫码溯源", 1082],
  ];
  const nodes = steps.map(([label, x], i) => addNode(slide, label, x, 260, 150, 78, {
    fill: i === 4 ? COLORS.panel2 : COLORS.panel,
    fontSize: 18,
  }));
  for (let i = 0; i < nodes.length - 1; i += 1) {
    connect(slide, nodes[i], nodes[i + 1], { fromSide: "right", toSide: "left" });
  }
  addPanel(slide, 96, 435, 1088, 108, COLORS.panel2);
  addText(slide, "实现要点", {
    left: 130,
    top: 462,
    width: 130,
    height: 34,
    fontSize: 24,
    bold: true,
  });
  addText(slide, "批次审核通过后自动生成可读批次码；二维码指向 /trace/<batch_code>/；溯源事件采用基于链式结构的记录机制，具备防篡改设计基础。", {
    left: 270,
    top: 458,
    width: 850,
    height: 58,
    fontSize: 20,
    color: COLORS.text,
    lineSpacing: 1.14,
  });
  addNotes(slide, "这里讲代码中的 ProductBatch 和 TraceEvent，不要说成已经上区块链，只说具备防篡改设计基础。");
}

function createOrderFlowSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "核心流程：订单交易", "从购物车到评价反馈，订单项绑定具体产品批次");
  const top = [
    ["浏览产品", 86, 220],
    ["加入购物车", 310, 220],
    ["填写收货信息", 534, 220],
    ["生成订单", 758, 220],
    ["线下支付凭证", 982, 220],
  ];
  const bottom = [
    ["农户确认", 982, 430],
    ["填写物流单号", 758, 430],
    ["确认收货", 534, 430],
    ["评价反馈", 310, 430],
  ];
  const nodes = [...top, ...bottom].map(([label, x, y], i) => addNode(slide, label, x, y, 160, 72, {
    fill: i === 3 ? COLORS.panel2 : COLORS.panel,
    fontSize: 18,
  }));
  for (let i = 0; i < top.length - 1; i += 1) connect(slide, nodes[i], nodes[i + 1], { fromSide: "right", toSide: "left" });
  connect(slide, nodes[4], nodes[5], { fromSide: "bottom", toSide: "top", kind: "elbow" });
  for (let i = 5; i < nodes.length - 1; i += 1) connect(slide, nodes[i], nodes[i + 1], { fromSide: "left", toSide: "right" });
  addText(slide, "设计亮点：OrderItem 关联 ProductBatch，保证交易记录能够追溯到具体批次。", {
    left: 135,
    top: 575,
    width: 1010,
    height: 34,
    fontSize: 22,
    bold: true,
    color: COLORS.ink,
    alignment: "center",
  });
  addNotes(slide, "订单流程页说明支付是线下凭证模拟，符合毕设实现范围；重点强调订单项绑定批次。");
}

function createAISlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "智能助农分析", "订单数据聚合后生成市场简报，模型不可用时自动降级");
  const left = addPanel(slide, 54, 166, 520, 420, COLORS.panel);
  const right = addPanel(slide, 706, 166, 520, 420, COLORS.panel2);
  void left;
  void right;
  addText(slide, "数据来源", { left: 94, top: 205, width: 230, height: 34, fontSize: 26, bold: true });
  addBulletList(slide, [
    "产品销量与库存",
    "订单地区分布",
    "供需缺口统计",
    "热销产品排序",
  ], { left: 94, top: 260, width: 360, height: 210, fontSize: 22 });
  const collect = addNode(slide, "Django ORM\n聚合统计", 472, 322, 160, 70, { fontSize: 18, fill: COLORS.white });
  const model = addNode(slide, "本地大模型\n生成简报", 646, 322, 160, 70, { fontSize: 18, fill: COLORS.white });
  connect(slide, collect, model, { fromSide: "right", toSide: "left" });
  addText(slide, "输出能力", { left: 850, top: 205, width: 230, height: 34, fontSize: 26, bold: true });
  addBulletList(slide, [
    "市场整体状况概括",
    "当前热门农产品",
    "供不应求品类提示",
    "给农户的销售建议",
  ], { left: 850, top: 260, width: 330, height: 210, fontSize: 22 });
  addText(slide, "降级策略：模型不可用时，规则引擎仍可生成摘要，保证功能页面可用。", {
    left: 180,
    top: 610,
    width: 930,
    height: 30,
    fontSize: 21,
    bold: true,
    alignment: "center",
  });
  addNotes(slide, "AI 模块只强调能力和降级设计，不主动说具体模型版本。");
}

function createAdminSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "后台管理与权限控制", "通过角色识别和审核流程保证数据质量");
  addCard(slide, {
    left: 60,
    top: 190,
    width: 350,
    height: 300,
    heading: "权限控制",
    body: "Django 登录认证\n农户功能需要 FarmerProfile\n管理员功能需要 staff 权限\n接口层保留 DRF 权限控制",
    accent: true,
  });
  addCard(slide, {
    left: 465,
    top: 190,
    width: 350,
    height: 300,
    heading: "审核流程",
    body: "产品审核\n批次质检审核\n农户入驻审核\n补贴申请审核",
  });
  addCard(slide, {
    left: 870,
    top: 190,
    width: 350,
    height: 300,
    heading: "运营能力",
    body: "用户管理\n订单与产品数据导出\n站内通知\n后台数据看板",
  });
  addNotes(slide, "后台管理页体现系统不是只有前台页面，还有审核和运营能力。");
}

function createTestingSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "系统测试", "围绕主流程、接口权限和页面可用性进行验证");
  const rows = [
    ["测试项", "操作", "预期结果", "结论"],
    ["用户登录", "输入正确账号密码", "登录成功并按角色跳转", "通过"],
    ["产品审核", "管理员点击通过", "产品状态变为已上架", "通过"],
    ["批次溯源", "输入有效批次码", "展示产品、质检和溯源事件", "通过"],
    ["订单提交", "填写收货信息并提交", "生成订单和订单项", "通过"],
    ["AI 分析", "访问市场分析页", "展示统计和简报", "通过"],
  ];
  const table = slide.tables.add({
    rows: rows.length,
    columns: 4,
    left: 64,
    top: 180,
    width: 1152,
    height: 320,
    columnTracks: [{ mode: "fixed", value: 180 }, { mode: "fixed", value: 300 }, { mode: "fr", value: 1 }, { mode: "fixed", value: 110 }],
    values: rows,
  });
  table.styleOptions = { headerRow: true, bandedRows: true };
  table.borders.assign({ style: "solid", fill: COLORS.rule, width: 1 });
  for (let c = 0; c < 4; c += 1) {
    table.getCell(0, c).fill = COLORS.ink;
    table.getCell(0, c).text.style = { color: COLORS.white, bold: true, fontSize: 17, typeface: FONT };
  }
  for (let r = 1; r < rows.length; r += 1) {
    for (let c = 0; c < 4; c += 1) {
      table.getCell(r, c).text.style = { fontSize: 15, typeface: FONT, color: COLORS.text };
    }
  }
  addText(slide, "覆盖范围：模型创建、API 权限、页面加载、表单提交、异常输入和核心业务闭环。", {
    left: 100,
    top: 558,
    width: 980,
    height: 34,
    fontSize: 21,
    bold: true,
    color: COLORS.ink,
    alignment: "center",
  });
  addNotes(slide, "测试页要说明不是只展示页面，也验证了后台状态变化和接口权限。");
}

function createDemoSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "系统演示路线", "答辩现场按一条闭环路线演示，避免跳转混乱");
  const steps = [
    ["首页看板", 80, 180],
    ["产品列表", 310, 180],
    ["产品详情", 540, 180],
    ["下单支付", 770, 180],
    ["农户后台", 1000, 180],
    ["批次二维码", 770, 410],
    ["溯源查询", 540, 410],
    ["市场分析", 310, 410],
    ["管理审核", 80, 410],
  ];
  const nodes = steps.map(([label, x, y], idx) => addNode(slide, label, x, y, 150, 70, {
    fill: idx === 6 ? COLORS.panel2 : COLORS.panel,
    fontSize: 18,
  }));
  for (let i = 0; i < 4; i += 1) connect(slide, nodes[i], nodes[i + 1], { fromSide: "right", toSide: "left" });
  connect(slide, nodes[4], nodes[5], { fromSide: "bottom", toSide: "top", kind: "elbow" });
  for (let i = 5; i < nodes.length - 1; i += 1) connect(slide, nodes[i], nodes[i + 1], { fromSide: "left", toSide: "right" });
  addText(slide, "演示原则：先展示消费者视角，再展示农户和管理员视角，最后用溯源与分析体现系统特色。", {
    left: 120,
    top: 602,
    width: 1040,
    height: 34,
    fontSize: 21,
    bold: true,
    alignment: "center",
  });
  addNotes(slide, "演示时控制在 2 到 3 分钟，重点页面提前打开，减少现场等待。");
}

function createInnovationSlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "创新点与特色", "从业务闭环、可信溯源和智能助农三个层面体现项目价值");
  const items = [
    ["交易 + 溯源结合", "订单项关联具体产品批次，交易后仍能追溯来源。"],
    ["低成本二维码方案", "批次码和二维码降低消费者查询门槛，便于农户落地。"],
    ["链式结构记录机制", "溯源事件具备防篡改设计基础，后续可接入可信存证平台。"],
    ["本地大模型助农", "订单数据生成市场简报，并提供离线规则降级策略。"],
  ];
  items.forEach(([heading, body], idx) => {
    const x = idx % 2 === 0 ? 70 : 670;
    const y = idx < 2 ? 190 : 410;
    addCard(slide, { left: x, top: y, width: 540, height: 150, heading, body, accent: idx === 0 });
  });
  addNotes(slide, "创新点不要夸大，重点说设计融合和落地能力。");
}

function createSummarySlide(presentation, n) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.white;
  addTitle(slide, n, "总结与展望", "系统完成了从需求、设计、实现到测试的完整过程");
  const metrics = [
    ["3", "类核心角色"],
    ["10+", "业务模块"],
    ["8+", "核心实体关系"],
    ["4", "主要创新点"],
  ];
  metrics.forEach(([stat, label], idx) => {
    const x = 58 + idx * 306;
    addPanel(slide, x, 205, 260, 190, idx === 0 ? COLORS.panel2 : COLORS.panel);
    addText(slide, stat, {
      left: x + 26,
      top: 238,
      width: 208,
      height: 78,
      fontSize: 58,
      bold: true,
      color: COLORS.ink,
      alignment: "center",
    });
    addText(slide, label, {
      left: x + 26,
      top: 326,
      width: 208,
      height: 34,
      fontSize: 22,
      color: COLORS.text,
      alignment: "center",
    });
  });
  addPanel(slide, 80, 470, 1120, 92, COLORS.panel2);
  addText(slide, "后续可扩展：微信小程序、真实在线支付、物联网数据采集、可信存证平台、个性化推荐与价格预测。", {
    left: 120,
    top: 500,
    width: 1040,
    height: 38,
    fontSize: 22,
    bold: true,
    color: COLORS.ink,
    alignment: "center",
  });
  addText(slide, "感谢各位老师，请批评指正。", {
    left: 410,
    top: 604,
    width: 460,
    height: 42,
    fontSize: 28,
    bold: true,
    color: COLORS.accent,
    alignment: "center",
  });
  addNotes(slide, "结尾先总结已完成内容，再说不足和展望，最后进入 Q&A。");
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function exportEvidence(presentation, previewDir, layoutDir, qaDir) {
  await fs.mkdir(previewDir, { recursive: true });
  await fs.mkdir(layoutDir, { recursive: true });
  await fs.mkdir(qaDir, { recursive: true });
  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    console.log(`render ${stem}`);
    await writeBlob(path.join(previewDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(layoutDir, `${stem}.layout.json`), await layout.text(), "utf8");
  }
  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await writeBlob(path.join(qaDir, "deck-montage.webp"), montage);
  const inspect = await presentation.inspect({
    kind: "slide,textbox,shape,table,chart,notes,layout",
    maxChars: 60000,
  });
  await fs.writeFile(path.join(qaDir, "inspect.ndjson"), inspect.ndjson, "utf8");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const projectRoot = path.resolve(args["project-root"] || defaultProjectRoot());
  const outPath = path.resolve(args.out || path.join(projectRoot, "docs", "智农溯源_毕设答辩PPT.pptx"));
  const previewDir = path.resolve(args["preview-dir"] || path.join(projectRoot, "outputs", "ppt-preview"));
  const layoutDir = path.resolve(args["layout-dir"] || path.join(projectRoot, "outputs", "ppt-layout"));
  const qaDir = path.resolve(args["qa-dir"] || path.join(projectRoot, "outputs", "ppt-qa"));

  await ensureDirFor(outPath);
  const presentation = Presentation.create({
    slideSize: { width: SLIDE_W, height: SLIDE_H },
  });

  createTitleSlide(presentation);
  createAgendaSlide(presentation, 2);
  createBackgroundSlide(presentation, 3);
  createObjectivesSlide(presentation, 4);
  createTechStackSlide(presentation, 5);
  createArchitectureSlide(presentation, 6);
  createProgramStructureSlide(presentation, 7);
  createFunctionModuleSlide(presentation, 8);
  createERSlide(presentation, 9);
  createTablesSlide(presentation, 10);
  createTraceFlowSlide(presentation, 11);
  createOrderFlowSlide(presentation, 12);
  createAISlide(presentation, 13);
  createAdminSlide(presentation, 14);
  createTestingSlide(presentation, 15);
  createDemoSlide(presentation, 16);
  createInnovationSlide(presentation, 17);
  createSummarySlide(presentation, 18);

  await exportEvidence(presentation, previewDir, layoutDir, qaDir);
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outPath);
  await fs.rm(`${outPath}.inspect.ndjson`, { force: true });
  console.log(JSON.stringify({
    pptx: outPath,
    slides: presentation.slides.items.length,
    previewDir,
    layoutDir,
    qaDir,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
