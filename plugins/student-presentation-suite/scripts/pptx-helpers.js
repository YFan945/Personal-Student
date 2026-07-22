/**
 * 共享 pptxgenjs 布局辅助函数。
 *
 * 生成的 deck.js 通过以下方式引入：
 *   const H = require("pptx-helpers");
 *
 * run_with_pptxgenjs.js 会自动将 scripts/ 目录加入 NODE_PATH。
 */

// ── 单位常量 ──────────────────────────────────────────────

const EMU_PER_CM = 360000;
const CM_PER_INCH = 2.54;

// 16:9 幻灯片默认尺寸（英寸）
const SLIDE_W_IN = 10;
const SLIDE_H_IN = 5.625;

// pptxgenjs 实例工厂 — 顶层 require 不会导致循环依赖
const _pptxgen = require("pptxgenjs");

// ── Token 辅助 ────────────────────────────────────────────

/**
 * 从 tokens 中取指定角色的颜色（带 # 前缀）。
 * @param {object} tokens - resolve_design_tokens() 的输出
 * @param {string} role - "canvas" | "surface" | "primary_text" | "secondary_text" | "primary_accent" | "secondary_accent"
 * @returns {string}
 */
function color(tokens, role) {
  const hex = (tokens.palette && tokens.palette[role]) || "000000";
  return "#" + hex;
}

/**
 * 根据语言选择字号。
 * @param {object} tokens
 * @param {string} lang - "chinese" | "english" | "bilingual"
 * @returns {{ title: number, body: number }}
 */
function fontSizeScale(tokens, lang) {
  const t = tokens.typography || {};
  const isCJK = lang === "chinese" || lang === "bilingual";
  return {
    title: t.title_min_pt || 24,
    body: isCJK ? (t.body_cjk_min_pt || 22) : (t.body_latin_min_pt || 20),
  };
}

/**
 * 选中风格的字体族（带通用 fallback）。
 * @param {object} tokens
 * @returns {{ title: string, body: string }}
 */
function fontFamily(tokens) {
  const t = tokens.typography || {};
  return {
    title: t.title_font || "Aptos Display",
    body: t.body_font || "Aptos",
  };
}

// ── 几何计算 ──────────────────────────────────────────────

/**
 * 安全绘图区 (inches)。自动扣除 safe margin、标题区和页脚区。
 * @param {number} slideW - 幻灯片宽度 (inches)
 * @param {number} slideH - 幻灯片高度 (inches)
 * @param {object} tokens
 * @param {{ reserveTitle?: boolean }} opts
 * @returns {{ x: number, y: number, w: number, h: number }}
 */
function safeArea(slideW, slideH, tokens, opts) {
  const g = tokens.geometry || {};
  const marginPct = (g.safe_margin_pct || 6) / 100;
  const marginX = slideW * marginPct;
  const marginY = slideH * marginPct;
  const titleZone = (opts && opts.reserveTitle !== false)
    ? slideH * (g.title_zone_pct || 16) / 100
    : marginY;
  const footerZone = slideH * (g.footer_zone_pct || 5) / 100;

  return {
    x: marginX,
    y: titleZone,
    w: slideW - marginX * 2,
    h: slideH - titleZone - footerZone,
  };
}

/**
 * 将 tokens spacing scale 转为 inches。
 * @param {object} tokens
 * @param {number} step - 间距档位 (1-6)
 * @returns {number} inches
 */
function spacing(tokens, step) {
  const scale = (tokens.geometry && tokens.geometry.spacing_scale_pt) || [6, 12, 18, 24, 36, 48];
  const pt = scale[Math.min(step - 1, scale.length - 1)] || 12;
  return pt / 72; // pt → inches
}

/**
 * 圆角半径 (inches)。
 * @param {object} tokens
 * @returns {number}
 */
function cornerRadius(tokens) {
  const pt = (tokens.geometry && tokens.geometry.corner_radius_pt) || 8;
  return pt / 72;
}

// ── 文字适配估算 ──────────────────────────────────────────

/**
 * 估算文本在给定盒子里需要的行数。
 * 中文 ≈ 字号×0.035cm/字，英文 ≈ 字号×0.021cm/字
 * @param {string} text - 文本内容
 * @param {number} boxW - 盒子宽度 (inches)
 * @param {number} fontSize - 字号 (pt)
 * @param {boolean} isCJK - 是否 CJK 为主
 * @returns {{ lines: number, fillRatio: number, overflow: boolean }}
 */
function estimateTextFit(text, boxW, boxH, fontSize, isCJK) {
  // 零尺寸盒子无法计算填充率
  if (boxW <= 0 || boxH <= 0) {
    return { lines: 0, fillRatio: 0, overflow: false };
  }
  const boxWCm = boxW * CM_PER_INCH;
  const boxHCm = boxH * CM_PER_INCH;
  const charWidthCm = fontSize * (isCJK ? 0.035 : 0.021);
  const charsPerLine = Math.max(1, Math.floor(boxWCm / charWidthCm));

  const paragraphs = text.split("\n");
  let totalLines = 0;
  for (const p of paragraphs) {
    totalLines += Math.max(1, Math.ceil(p.length / charsPerLine));
  }
  const lineHeightCm = fontSize * 1.4 / 72 * CM_PER_INCH;
  const textHeightCm = totalLines * lineHeightCm;
  const fillRatio = textHeightCm / boxHCm;

  return {
    lines: totalLines,
    fillRatio: Math.round(fillRatio * 100) / 100,
    overflow: fillRatio > 0.85,
  };
}

// ── Box 创建辅助 ─────────────────────────────────────────

/**
 * 在安全区域内添加标题文本框。
 * @param {object} slide - pptxgen slide 对象
 * @param {string} text
 * @param {{ x: number, y: number, w: number, h: number }} area - safeArea() 返回
 * @param {object} tokens
 * @param {string} lang
 * @returns {object} 创建的 text 对象
 */
function addTitle(slide, text, area, tokens, lang) {
  const sizes = fontSizeScale(tokens, lang);
  const fonts = fontFamily(tokens);
  const g = tokens.geometry || {};
  const marginPct = (g.safe_margin_pct || 6) / 100;
  // 标题放在安全边距和内容区之间
  const titleTop = SLIDE_H_IN * marginPct + spacing(tokens, 1);
  const titleH = area.y - titleTop - spacing(tokens, 1);
  return slide.addText(text, {
    x: area.x,
    y: titleTop,
    w: area.w,
    h: Math.max(titleH, 0.6),
    fontSize: sizes.title,
    fontFace: fonts.title,
    color: color(tokens, "primary_text"),
    bold: true,
    align: "left",
    valign: "bottom",
  });
}

/**
 * 在安全区域内添加正文文本框。
 * @param {object} slide
 * @param {string|string[]} text
 * @param {{ x: number, y: number, w: number, h: number }} area
 * @param {object} tokens
 * @param {string} lang
 * @param {{ bullet?: boolean, spacing?: number }} opts
 * @returns {object}
 */
function addBody(slide, text, area, tokens, lang, opts) {
  const sizes = fontSizeScale(tokens, lang);
  const fonts = fontFamily(tokens);
  const isCJK = lang === "chinese" || lang === "bilingual";
  const textStr = Array.isArray(text) ? text.join("\n") : text;

  // 溢出预估
  const fit = estimateTextFit(textStr, area.w, area.h, sizes.body, isCJK);
  if (fit.overflow) {
    // eslint-disable-next-line no-console
    console.warn(
      `[pptx-helpers] 文字溢出风险：${fit.lines} 行，填充率 ${fit.fillRatio}。建议拆分幻灯片或精简内容。`
    );
  }

  const options = {
    x: area.x,
    y: area.y,
    w: area.w,
    h: area.h,
    fontSize: sizes.body,
    fontFace: fonts.body,
    color: color(tokens, "primary_text"),
    align: "left",
    valign: "top",
    lineSpacingMultiple: 1.3,
    paraSpaceAfter: ((opts && opts.spacing) ? spacing(tokens, opts.spacing) : spacing(tokens, 1)) * 72,
  };

  if (opts && opts.bullet !== false) {
    options.bullet = true;
  }

  return slide.addText(textStr, options);
}

/**
 * 添加强调色卡片（圆角矩形 + 文字）。
 * @param {object} slide
 * @param {string} text
 * @param {{ x: number, y: number, w: number, h: number }} box
 * @param {object} tokens
 * @returns {{ shape: object, text: object }}
 */
function addAccentCard(slide, text, box, tokens) {
  const radius = cornerRadius(tokens);
  const shape = slide.addShape(_pptxgen.ShapeType.roundRect, {
    x: box.x, y: box.y, w: box.w, h: box.h,
    fill: { color: color(tokens, "surface") },
    line: { color: color(tokens, "primary_accent"), width: (tokens.lines && tokens.lines.standard_pt) || 1.25 },
    rectRadius: radius,
  });
  const textObj = slide.addText(text, {
    x: box.x + spacing(tokens, 2), y: box.y + spacing(tokens, 2),
    w: box.w - spacing(tokens, 2) * 2, h: box.h - spacing(tokens, 2) * 2,
    fontSize: (tokens.typography && tokens.typography.body_latin_min_pt) || 20,
    fontFace: fontFamily(tokens).body,
    color: color(tokens, "primary_text"),
    valign: "middle",
  });
  return { shape, text: textObj };
}

/**
 * 添加分隔线。
 * @param {object} slide
 * @param {number} x
 * @param {number} y
 * @param {number} w
 * @param {object} tokens
 * @param {"hairline"|"standard"|"emphasis"|"section"} weight
 * @returns {object}
 */
function addDivider(slide, x, y, w, tokens, weight) {
  const linePt = (tokens.lines && tokens.lines[weight + "_pt"]) || (tokens.lines && tokens.lines.standard_pt) || 1.25;
  return slide.addShape(_pptxgen.ShapeType.line, {
    x, y, w, h: 0,
    line: { color: color(tokens, "secondary_text"), width: linePt },
  });
}

// ── 全局主题 ──────────────────────────────────────────────

/**
 * 将 design tokens 应用到 pptxgen 实例的全局默认值。
 * @param {object} pptx - new pptxgen() 实例
 * @param {object} tokens
 * @param {string} lang
 * @param {{ slideW?: number, slideH?: number }} [opts] - 可选幻灯片尺寸覆盖
 */
function applyTokens(pptx, tokens, lang, opts) {
  const sizes = fontSizeScale(tokens, lang);
  const fonts = fontFamily(tokens);
  const slideW = (opts && opts.slideW) || SLIDE_W_IN;
  const slideH = (opts && opts.slideH) || SLIDE_H_IN;

  // 设置幻灯片尺寸（默认 16:9）
  pptx.defineLayout({ name: "STUDENT_WIDE", width: slideW, height: slideH });
  pptx.layout = "STUDENT_WIDE";

  // 默认文字样式
  pptx.theme = {
    fontFace: fonts.body,
    fontSize: sizes.body,
    color: color(tokens, "primary_text"),
  };
}

// ── 导出 ──────────────────────────────────────────────────

module.exports = {
  // 常量
  EMU_PER_CM,
  SLIDE_W_IN,
  SLIDE_H_IN,

  // Token 辅助
  color,
  fontSizeScale,
  fontFamily,

  // 几何计算
  safeArea,
  spacing,
  cornerRadius,

  // 文字适配
  estimateTextFit,

  // Box 创建
  addTitle,
  addBody,
  addAccentCard,
  addDivider,

  // 全局
  applyTokens,
};
