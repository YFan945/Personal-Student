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
const _pptxgen = require('pptxgenjs');
const _shapeType = new _pptxgen().ShapeType;

// ── Token 辅助 ────────────────────────────────────────────

/**
 * 从 tokens 中取指定角色的 6 位十六进制颜色（pptxgenjs 不接受 # 前缀）。
 * @param {object} tokens - resolve_design_tokens() 的输出
 * @param {string} role - "canvas" | "surface" | "primary_text" | "secondary_text" | "primary_accent" | "secondary_accent"
 * @returns {string}
 */
function color(tokens, role) {
  const hex = (tokens.palette && tokens.palette[role]) || '000000';
  return String(hex).replace(/^#/, '').slice(0, 6).toUpperCase();
}

/**
 * 根据语言选择字号。
 * @param {object} tokens
 * @param {string} lang - "chinese" | "english" | "bilingual"
 * @returns {{ title: number, body: number }}
 */
function fontSizeScale(tokens, lang) {
  const t = tokens.typography || {};
  const isCJK = lang === 'chinese' || lang === 'bilingual';
  return {
    title: t.title_min_pt || 24,
    body: isCJK ? t.body_cjk_min_pt || 22 : t.body_latin_min_pt || 20,
  };
}

// 官方 pptx skill 安全字体白名单：这些字体在 LibreOffice QA 与 Office 中
// 宽度一致，可信任 text-fit 检查。绝不默认 Aptos。
const SAFE_TITLE_FONTS = [
  'Cambria',
  'Bookman Old Style',
  'Century Schoolbook',
  'Times New Roman',
  'Arial',
  'Calibri',
  'Courier New',
];
const SAFE_BODY_FONTS = ['Calibri', 'Arial', 'Times New Roman', 'Cambria', 'Courier New'];

/**
 * 选中风格的字体族，强制落到官方安全字体。
 * @param {object} tokens
 * @returns {{ title: string, body: string }}
 */
function fontFamily(tokens) {
  const t = tokens.typography || {};
  const pick = (value, candidates, fallback) =>
    candidates.includes(String(value || '')) ? String(value) : fallback;
  return {
    title: pick(t.title_font, SAFE_TITLE_FONTS, 'Cambria'),
    body: pick(t.body_font, SAFE_BODY_FONTS, 'Calibri'),
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
  const gap = spacing(tokens, 3);
  const reserveTitle = !opts || opts.reserveTitle !== false;
  const titleZone = (slideH * (g.title_zone_pct || 16)) / 100;
  const footerZone = Math.max(marginY, (slideH * (g.footer_zone_pct || 5)) / 100);
  const titleHeight = reserveTitle ? Math.max(0.6, titleZone - gap * 2) : 0;
  const contentY = reserveTitle ? marginY + titleHeight + gap : marginY;
  const contentHeight = slideH - contentY - footerZone;
  if (slideW - marginX * 2 <= 0 || contentHeight <= 0) {
    throw new RangeError('Design tokens leave no usable slide safe area.');
  }

  return {
    x: marginX,
    y: contentY,
    w: slideW - marginX * 2,
    h: contentHeight,
    slideW,
    slideH,
    titleBox: reserveTitle
      ? { x: marginX, y: marginY, w: slideW - marginX * 2, h: titleHeight }
      : null,
  };
}

/**
 * 页脚文本框安全区 (inches)。返回值始终位于幻灯片边界内。
 * @param {number} slideW
 * @param {number} slideH
 * @param {object} tokens
 * @returns {{ x: number, y: number, w: number, h: number }}
 */
function footerArea(slideW, slideH, tokens) {
  const g = tokens.geometry || {};
  const marginPct = (g.safe_margin_pct || 6) / 100;
  const marginX = slideW * marginPct;
  const marginY = slideH * marginPct;
  const footerZone = Math.max(marginY, (slideH * (g.footer_zone_pct || 5)) / 100);
  const height = Math.min(0.28, footerZone);
  return {
    x: marginX,
    y: slideH - footerZone,
    w: slideW - marginX * 2,
    h: height,
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
    return {
      lines: text ? 1 : 0,
      fillRatio: text ? Number.POSITIVE_INFINITY : 0,
      overflow: Boolean(text),
    };
  }
  const boxWCm = boxW * CM_PER_INCH;
  const boxHCm = boxH * CM_PER_INCH;
  const charWidthCm = fontSize * (isCJK ? 0.035 : 0.021);
  const charsPerLine = Math.max(1, Math.floor(boxWCm / charWidthCm));

  const paragraphs = text.split('\n');
  let totalLines = 0;
  for (const p of paragraphs) {
    totalLines += Math.max(1, Math.ceil(p.length / charsPerLine));
  }
  const lineHeightCm = ((fontSize * 1.4) / 72) * CM_PER_INCH;
  const textHeightCm = totalLines * lineHeightCm;
  const fillRatio = textHeightCm / boxHCm;

  return {
    lines: totalLines,
    fillRatio: Math.round(fillRatio * 100) / 100,
    overflow: fillRatio > 0.85,
  };
}

/**
 * 在写入文本框前估算适配情况。溢出时仅警告并返回 fit（含 overflow），
 * 不再阻断生成——对齐官方方式：溢出靠 QA 阶段逐页视觉检查兜底。
 */
function assertTextFits(text, boxW, boxH, fontSize, isCJK, label) {
  const fit = estimateTextFit(String(text || ''), boxW, boxH, fontSize, isCJK);
  if (fit.overflow) {
    // eslint-disable-next-line no-console
    console.warn(
      `${label || '文本框'}存在溢出风险：${fit.lines} 行，填充率 ${fit.fillRatio}。` +
        '请在 QA 逐页检查中确认，必要时拆分幻灯片、精简内容或扩大文本框。',
    );
  }
  return fit;
}

function plainText(text) {
  if (!Array.isArray(text)) {
    return String(text || '');
  }
  return text
    .map((item) => (typeof item === 'string' ? item : String((item && item.text) || '')))
    .join('');
}

/**
 * 将安全区切成等宽等高网格，避免生成脚本重复手算坐标。
 */
function gridLayout(area, columns, rows, opts) {
  if (!Number.isInteger(columns) || columns < 1 || !Number.isInteger(rows) || rows < 1) {
    throw new RangeError('gridLayout columns/rows must be positive integers.');
  }
  const columnGap = (opts && opts.columnGap) || 0;
  const rowGap = (opts && opts.rowGap) || 0;
  const cellW = (area.w - columnGap * (columns - 1)) / columns;
  const cellH = (area.h - rowGap * (rows - 1)) / rows;
  if (cellW <= 0 || cellH <= 0) {
    throw new RangeError('Grid gaps leave no usable cell area.');
  }
  const cells = [];
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      cells.push({
        x: area.x + column * (cellW + columnGap),
        y: area.y + row * (cellH + rowGap),
        w: cellW,
        h: cellH,
        row,
        column,
      });
    }
  }
  return cells;
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
  const fallbackTop =
    (area.slideH || SLIDE_H_IN) * (((tokens.geometry || {}).safe_margin_pct || 6) / 100);
  const titleBox = area.titleBox || {
    x: area.x,
    y: fallbackTop,
    w: area.w,
    h: area.y - fallbackTop - spacing(tokens, 1),
  };
  assertTextFits(text, titleBox.w, titleBox.h, sizes.title, lang !== 'english', '标题');
  return slide.addText(text, {
    x: titleBox.x,
    y: titleBox.y,
    w: titleBox.w,
    h: titleBox.h,
    fontSize: sizes.title,
    fontFace: fonts.title,
    color: color(tokens, 'primary_text'),
    bold: true,
    align: 'left',
    valign: 'bottom',
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
  const isCJK = lang === 'chinese' || lang === 'bilingual';
  const textStr = Array.isArray(text) ? text.join('\n') : text;

  // 溢出预估
  assertTextFits(textStr, area.w, area.h, sizes.body, isCJK, '正文');

  const options = {
    x: area.x,
    y: area.y,
    w: area.w,
    h: area.h,
    fontSize: sizes.body,
    fontFace: fonts.body,
    color: color(tokens, 'primary_text'),
    align: 'left',
    valign: 'top',
    lineSpacingMultiple: 1.3,
    paraSpaceAfter:
      (opts && opts.spacing ? spacing(tokens, opts.spacing) : spacing(tokens, 1)) * 72,
  };

  if (opts && opts.bullet !== false) {
    options.bullet = true;
  }

  return slide.addText(textStr, options);
}

/**
 * 添加经过字号下限和溢出检查的通用文本框。
 */
function addTextBox(slide, text, box, tokens, lang, opts) {
  const sizes = fontSizeScale(tokens, lang);
  const fonts = fontFamily(tokens);
  const isCJK = lang === 'chinese' || lang === 'bilingual';
  const requestedSize = (opts && opts.fontSize) || sizes.body;
  const fontSize = Math.max(requestedSize, sizes.body);
  const margin = opts && opts.margin !== undefined ? opts.margin : 16;
  const margins = Array.isArray(margin) ? margin : [margin, margin, margin, margin];
  const usableW = box.w - ((margins[1] || 0) + (margins[3] || 0)) / 72;
  const usableH = box.h - ((margins[0] || 0) + (margins[2] || 0)) / 72;
  assertTextFits(
    plainText(text),
    usableW,
    usableH,
    fontSize,
    isCJK,
    (opts && opts.label) || '文本框',
  );
  return slide.addText(text, {
    ...(opts || {}),
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    fontSize,
    fontFace: (opts && opts.fontFace) || fonts.body,
    color: (opts && opts.color) || color(tokens, 'primary_text'),
    align: (opts && opts.align) || 'left',
    valign: (opts && opts.valign) || 'top',
    margin,
  });
}

/**
 * 添加始终位于画布内的页脚。页脚允许使用 10pt 以上辅助字号。
 */
function addFooter(slide, text, tokens, opts) {
  const slideW = (opts && opts.slideW) || SLIDE_W_IN;
  const slideH = (opts && opts.slideH) || SLIDE_H_IN;
  const box = footerArea(slideW, slideH, tokens);
  const fontSize = Math.max((opts && opts.fontSize) || 11, 10);
  assertTextFits(plainText(text), box.w, box.h, fontSize, false, '页脚');
  return slide.addText(text, {
    ...box,
    fontSize,
    fontFace: (opts && opts.fontFace) || fontFamily(tokens).body,
    color: (opts && opts.color) || color(tokens, 'secondary_text'),
    align: (opts && opts.align) || 'right',
    valign: 'mid',
    margin: 0,
  });
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
  const padding = spacing(tokens, 2);
  const textWidth = box.w - padding * 2;
  const textHeight = box.h - padding * 2;
  const isCJK = /[\u3400-\u9fff]/u.test(String(text || ''));
  const typography = tokens.typography || {};
  const fontSize = isCJK ? typography.body_cjk_min_pt || 22 : typography.body_latin_min_pt || 20;
  assertTextFits(text, textWidth, textHeight, fontSize, isCJK, '卡片文本');
  const shape = slide.addShape(_shapeType.roundRect, {
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    fill: { color: color(tokens, 'surface') },
    line: {
      color: color(tokens, 'primary_accent'),
      width: (tokens.lines && tokens.lines.standard_pt) || 1.25,
    },
    rectRadius: radius,
  });
  const textObj = slide.addText(text, {
    x: box.x + padding,
    y: box.y + padding,
    w: textWidth,
    h: textHeight,
    fontSize,
    fontFace: fontFamily(tokens).body,
    color: color(tokens, 'primary_text'),
    valign: 'middle',
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
  const linePt =
    (tokens.lines && tokens.lines[`${weight}_pt`]) ||
    (tokens.lines && tokens.lines.standard_pt) ||
    1.25;
  return slide.addShape(_shapeType.line, {
    x,
    y,
    w,
    h: 0,
    line: { color: color(tokens, 'secondary_text'), width: linePt },
  });
}

/**
 * 给 slide 设置背景色（canvas 角色落到背景）。
 * 官方设计规范：深色封面/总结页用 dark_palette.canvas，浅色内容页用 canvas，
 * 形成深/浅对比；生成脚本必须逐页调用。
 * @param {object} slide - pptxgen slide 对象
 * @param {object} tokens
 * @param {boolean} [dark] - true 用 dark_palette.canvas，false/缺省用 canvas
 * @returns {object} slide
 */
function addBackground(slide, tokens, dark) {
  if (dark && tokens.dark_palette && tokens.dark_palette.canvas) {
    slide.background = {
      color: String(tokens.dark_palette.canvas).replace(/^#/, '').slice(0, 6).toUpperCase(),
    };
  } else {
    slide.background = { color: color(tokens, 'canvas') };
  }
  return slide;
}

// ── 全局主题 ──────────────────────────────────────────────

/**
 * 将 design tokens 应用到 pptxgen 实例的全局默认值。
 * 背景不是全局属性：每页必须用 addBackground()（或 slide.background）显式设置，
 * 深色封面/浅色内容对比由调用处决定。
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
  pptx.defineLayout({ name: 'STUDENT_WIDE', width: slideW, height: slideH });
  pptx.layout = 'STUDENT_WIDE';

  // 默认文字样式
  pptx.theme = {
    fontFace: fonts.body,
    fontSize: sizes.body,
    color: color(tokens, 'primary_text'),
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
  footerArea,
  gridLayout,
  spacing,
  cornerRadius,

  // 文字适配
  estimateTextFit,
  assertTextFits,
  plainText,

  // Box 创建
  addTitle,
  addBody,
  addTextBox,
  addFooter,
  addAccentCard,
  addDivider,

  // 背景
  addBackground,

  // 全局
  applyTokens,
};
