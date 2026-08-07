/**
 * Editable visual components for generated decks.
 *
 * Every component consumes one preallocated safe-area box. Components never
 * mutate the deck theme and never place content outside the supplied box.
 */

const pptxgen = require('pptxgenjs');
const H = require('pptx-helpers');
const S = require('pptx-shapes');
const SVG = require('pptx-svg-library');
const { imageSize } = require('image-size');

const SHAPE = new pptxgen().ShapeType;
const CHART = new pptxgen().ChartType;

function items(value) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function textOf(value, fallback) {
  if (typeof value === 'string') return value;
  if (value && typeof value === 'object') {
    return String(value.label || value.title || value.name || fallback || '');
  }
  return String(fallback || '');
}

function palette(tokens) {
  return {
    canvas: H.color(tokens, 'canvas'),
    surface: H.color(tokens, 'surface'),
    text: H.color(tokens, 'primary_text'),
    muted: H.color(tokens, 'secondary_text'),
    accent: H.color(tokens, 'primary_accent'),
    accent2: H.color(tokens, 'secondary_accent'),
  };
}

function containImage(path, box) {
  const size = imageSize(path);
  if (!size.width || !size.height) throw new RangeError(`Cannot determine image size: ${path}`);
  const scale = Math.min(box.w / size.width, box.h / size.height);
  const w = size.width * scale;
  const h = size.height * scale;
  return {
    x: box.x + (box.w - w) / 2,
    y: box.y + (box.h - h) / 2,
    w,
    h,
  };
}

function addPanel(slide, box, tokens, options) {
  const p = palette(tokens);
  const shape = options?.shape || 'roundRect';
  return S.addStyledContainer(slide, shape, box, tokens, {
    fill: options?.fill || p.surface,
    line: options?.line || p.accent,
    lineWidth: options?.lineWidth || 1.25,
    fillTransparency: options?.fillTransparency,
  });
}

function addLabel(slide, text, box, tokens, lang, options) {
  const role = options?.role || (options?.align === 'left' ? 'body' : 'label');
  const inset = options?.shape ? S.safeInsetForShape(options.shape, box) : { x: 0, y: 0 };
  const safeBox = {
    x: box.x + inset.x,
    y: box.y + inset.y,
    w: Math.max(0.1, box.w - inset.x * 2),
    h: Math.max(0.1, box.h - inset.y * 2),
  };
  const fittedOptions = {
    // Compact component labels often occupy sub-zones under one inch high.
    // A 16pt inset on every edge can consume the entire box; keep a readable
    // default while allowing callers to request larger editorial padding.
    margin: options?.margin ?? 6,
    bold: Boolean(options && options.bold),
    label: (options && options.label) || '视觉组件文本',
  };
  for (const key of ['align', 'valign', 'color', 'fontSize', 'fontFace', 'min', 'max']) {
    if (options?.[key] !== undefined) fittedOptions[key] = options[key];
  }
  return H.addFittedText(slide, text, safeBox, tokens, lang, role, fittedOptions);
}

function addNumberMarker(slide, box, tokens) {
  const p = palette(tokens);
  slide.addShape(SHAPE.ellipse, {
    ...box,
    fill: { color: p.accent },
    line: { color: p.accent, transparency: 100 },
  });
}

function addSectionHero(slide, data, area, tokens, lang) {
  const p = palette(tokens);
  // 官方规范：禁止装饰性竖向 accent 色条；标题从内容区左缘开始。
  const titleBox = {
    x: area.x,
    y: area.y + area.h * 0.05,
    w: area.w * 0.72,
    h: area.h * 0.42,
  };
  addLabel(slide, data.title || data.claim, titleBox, tokens, lang, {
    bold: true,
    align: 'left',
    fontSize: H.fontSizeScale(tokens, lang).title,
    fontFace: H.fontFamily(tokens).title,
    label: 'Hero 标题',
  });
  if (data.subtitle || data.takeaway) {
    addLabel(
      slide,
      data.subtitle || data.takeaway,
      {
        x: titleBox.x,
        y: titleBox.y + titleBox.h + H.spacing(tokens, 3),
        w: area.w * 0.58,
        h: area.h * 0.46,
      },
      tokens,
      lang,
      { align: 'left', color: p.muted, label: 'Hero 副标题' },
    );
  }
  slide.addShape(SHAPE.ellipse, {
    x: area.x + area.w * 0.8,
    y: area.y + area.h * 0.08,
    w: area.h * 0.42,
    h: area.h * 0.42,
    fill: { color: p.accent2, transparency: 12 },
    line: { transparency: 100 },
  });
}

function addProcessFlow(slide, data, area, tokens, lang) {
  const steps = items(data.steps || data.items);
  if (steps.length < 2 || steps.length > 5) {
    throw new RangeError('addProcessFlow requires 2-5 steps.');
  }
  const gap = H.spacing(tokens, 3);
  const cardW = (area.w - gap * (steps.length - 1)) / steps.length;
  const cardH = area.h * 0.72;
  const y = area.y + (area.h - cardH) / 2;
  steps.forEach((step, index) => {
    const x = area.x + index * (cardW + gap);
    const shape = 'roundRect';
    const card = { x, y, w: cardW, h: cardH };
    const inset = S.safeInsetForShape(shape, card);
    addPanel(slide, card, tokens, { shape, variant: index });
    addLabel(
      slide,
      data.numbered === false
        ? textOf(step, `Step ${index + 1}`)
        : `${index + 1}. ${textOf(step, `Step ${index + 1}`)}`,
      { x: x + inset.x, y: y + inset.y, w: cardW - inset.x * 2, h: cardH - inset.y * 2 },
      tokens,
      lang,
      { bold: true, role: 'node', label: `流程步骤 ${index + 1}` },
    );
    if (index < steps.length - 1) {
      slide.addShape(SHAPE.line, {
        x: x + cardW,
        y: y + cardH * 0.5,
        w: gap,
        h: 0,
        line: {
          color: palette(tokens).accent2,
          width: 2,
          endArrowType: 'triangle',
        },
      });
    }
  });
}

function addTimeline(slide, data, area, tokens, lang) {
  const stages = items(data.stages || data.items);
  if (stages.length < 3 || stages.length > 6) {
    throw new RangeError('addTimeline requires 3-6 stages.');
  }
  const p = palette(tokens);
  const axisY = area.y + area.h * 0.52;
  const stepW = area.w / stages.length;
  slide.addShape(SHAPE.line, {
    x: area.x + stepW * 0.5,
    y: axisY,
    w: area.w - stepW,
    h: 0,
    line: { color: p.accent, width: 2.5 },
  });
  stages.forEach((stage, index) => {
    const centerX = area.x + stepW * (index + 0.5);
    addNumberMarker(slide, { x: centerX - 0.2, y: axisY - 0.2, w: 0.4, h: 0.4 }, tokens);
    const above = index % 2 === 0;
    addLabel(
      slide,
      textOf(stage),
      {
        x: centerX - stepW * 0.5,
        y: above ? area.y : axisY + 0.45,
        w: stepW,
        h: area.h * 0.36,
      },
      tokens,
      lang,
      { bold: true, label: `时间线阶段 ${index + 1}` },
    );
  });
}

function addComparison(slide, data, area, tokens, lang) {
  const entries = items(data.items);
  if (entries.length < 2 || entries.length > 3) {
    throw new RangeError('addComparison requires 2-3 items.');
  }
  const gap = H.spacing(tokens, 3);
  const cells = H.gridLayout(area, entries.length, 1, { columnGap: gap });
  const p = palette(tokens);
  entries.forEach((entry, index) => {
    const shape = 'roundRect';
    addPanel(slide, cells[index], tokens, {
      shape,
      line: index === Number(data.highlight || 0) ? p.accent2 : p.accent,
      lineWidth: index === Number(data.highlight || 0) ? 2.5 : 1.25,
    });
    const label = textOf(entry);
    const detail =
      entry && typeof entry === 'object'
        ? items(entry.points || entry.details)
            .map(textOf)
            .join('\n')
        : '';
    addLabel(
      slide,
      label,
      {
        x: cells[index].x + cells[index].w * 0.08,
        y: cells[index].y + cells[index].h * 0.06,
        w: cells[index].w * 0.84,
        h: cells[index].h * 0.32,
      },
      tokens,
      lang,
      { bold: true, label: `对比标题 ${index + 1}` },
    );
    if (detail) {
      addLabel(
        slide,
        detail,
        {
          x: cells[index].x + cells[index].w * 0.08,
          y: cells[index].y + cells[index].h * 0.42,
          w: cells[index].w * 0.84,
          h: cells[index].h * 0.5,
        },
        tokens,
        lang,
        { align: 'left', color: p.muted, label: `对比内容 ${index + 1}` },
      );
    }
  });
}

function addMetricDashboard(slide, data, area, tokens, lang) {
  const metrics = items(data.metrics || data.items);
  if (metrics.length < 2 || metrics.length > 4) {
    throw new RangeError('addMetricDashboard requires 2-4 metrics.');
  }
  const cells = H.gridLayout(area, metrics.length, 1, {
    columnGap: H.spacing(tokens, 3),
  });
  const p = palette(tokens);
  metrics.forEach((metric, index) => {
    const shape = 'roundRect';
    addPanel(slide, cells[index], tokens, { shape, variant: index });
    const value = metric && typeof metric === 'object' ? metric.value : metric;
    const label = metric && typeof metric === 'object' ? metric.label : '';
    addLabel(
      slide,
      value,
      {
        x: cells[index].x,
        y: cells[index].y + cells[index].h * 0.18,
        w: cells[index].w,
        h: cells[index].h * 0.3,
      },
      tokens,
      lang,
      { bold: true, role: 'kpi', shape, color: p.accent, label: `指标值 ${index + 1}` },
    );
    addLabel(
      slide,
      label,
      {
        x: cells[index].x,
        y: cells[index].y + cells[index].h * 0.48,
        w: cells[index].w,
        h: cells[index].h * 0.42,
      },
      tokens,
      lang,
      { role: 'label', shape, color: p.muted, label: `指标标签 ${index + 1}` },
    );
  });
}

function addChartWithTakeaway(slide, data, area, tokens, lang) {
  const p = palette(tokens);
  const colors = [p.accent, p.accent2, p.muted];
  const rawSeries = items(data.series);
  const chartColors = rawSeries.map((entry, index) => entry.color || colors[index % colors.length]);
  const series = rawSeries.map((entry) => {
    const normalized = { ...entry };
    delete normalized.color;
    return normalized;
  });
  if (!series.length) {
    throw new RangeError('addChartWithTakeaway requires editable chart series.');
  }
  const chartBox = { x: area.x, y: area.y, w: area.w * 0.64, h: area.h };
  // 官方规范：stacked 图数据标签只能用 ctr/inEnd/inBase，outEnd 会损坏文件；
  // 非 stacked 用 outEnd 合法。
  const stacked = data.stacked === true;
  slide.addChart(CHART.bar, series, {
    ...chartBox,
    showTitle: true,
    title: data.title || data.measure || 'Key result',
    titleFontFace: H.fontFamily(tokens).title,
    titleFontSize: Math.max(20, H.fontSizeScale(tokens, lang).body),
    // PptxGenJS ignores a `color` property on series data. Supplying one color per
    // series through chartColors writes c:ser/c:spPr and keeps style tokens visible.
    chartColors,
    catAxisLabelFontFace: H.fontFamily(tokens).body,
    valAxisLabelFontFace: H.fontFamily(tokens).body,
    catAxisLabelFontSize: 18,
    valAxisLabelFontSize: 18,
    catAxisLabelColor: p.muted,
    valAxisLabelColor: p.muted,
    catGridLine: { style: 'none' },
    valGridLine: { color: p.muted, size: 1 },
    dataLabelColor: p.text,
    dataLabelPosition: stacked ? 'inEnd' : 'outEnd',
    dataLabelFormatCode: '#,##0.##',
    dataLabelFontFace: H.fontFamily(tokens).body,
    dataLabelFontSize: 18,
    showValue: true,
    showLegend: series.length > 1,
    legendFontFace: H.fontFamily(tokens).body,
    legendFontSize: 18,
    showCatName: false,
    showSerName: false,
    altText: data.alt_text || data.altText || data.takeaway || 'Editable data chart',
  });
  const takeawayBox = {
    x: area.x + area.w * 0.69,
    y: area.y + area.h * 0.08,
    w: area.w * 0.31,
    h: area.h * 0.84,
  };
  addPanel(slide, takeawayBox, tokens, { line: p.accent2 });
  addLabel(
    slide,
    data.takeaway || 'State the conclusion supported by this chart.',
    takeawayBox,
    tokens,
    lang,
    { bold: true, label: '图表结论' },
  );
}

function addArchitecture(slide, data, area, tokens, lang) {
  const nodes = items(data.nodes || data.items);
  if (nodes.length < 2 || nodes.length > 6) {
    throw new RangeError('addArchitecture requires 2-6 nodes.');
  }
  const columns = nodes.length > 3 ? 3 : nodes.length;
  const rows = Math.ceil(nodes.length / columns);
  const cells = H.gridLayout(area, columns, rows, {
    columnGap: H.spacing(tokens, 3),
    rowGap: H.spacing(tokens, 3),
  });
  nodes.forEach((node, index) => {
    const cell = cells[index];
    if (index > 0) {
      const previous = cells[index - 1];
      slide.addShape(SHAPE.line, {
        x: previous.x + previous.w,
        y: previous.y + previous.h / 2,
        w: Math.max(0.05, cell.x - previous.x - previous.w),
        h: cell.y + cell.h / 2 - previous.y - previous.h / 2,
        line: { color: palette(tokens).muted, width: 1.5, endArrowType: 'triangle' },
      });
    }
    const shape = 'roundRect';
    addPanel(slide, cell, tokens, { shape, variant: index });
    addLabel(slide, textOf(node), cell, tokens, lang, {
      bold: true,
      role: 'node',
      shape,
      label: `架构节点 ${index + 1}`,
    });
  });
}

function addMatrix(slide, data, area, tokens, _lang) {
  const entries = items(data.items);
  if (entries.length < 2 || entries.length > 4) {
    throw new RangeError('addMatrix requires 2-4 items.');
  }
  const p = palette(tokens);
  const plot = {
    x: area.x + area.w * 0.12,
    y: area.y + area.h * 0.02,
    w: area.w * 0.82,
    h: area.h * 0.47,
  };
  slide.addShape(SHAPE.line, {
    x: plot.x,
    y: plot.y + plot.h,
    w: plot.w,
    h: 0,
    line: { color: p.muted, width: 1.5, endArrowType: 'triangle' },
  });
  slide.addShape(SHAPE.line, {
    x: plot.x,
    y: plot.y,
    w: 0,
    h: plot.h,
    line: { color: p.muted, width: 1.5, beginArrowType: 'triangle' },
  });
  entries.forEach((entry, index) => {
    const xValue = Number((entry && entry.x) || (index + 1) / (entries.length + 1));
    const yValue = Number((entry && entry.y) || ((index % 3) + 1) / 4);
    const x = plot.x + Math.max(0.08, Math.min(0.92, xValue)) * plot.w;
    const y = plot.y + (1 - Math.max(0.08, Math.min(0.92, yValue))) * plot.h;
    slide.addShape(SHAPE.ellipse, {
      x: x - 0.16,
      y: y - 0.16,
      w: 0.32,
      h: 0.32,
      fill: { color: index % 2 ? p.accent2 : p.accent },
      line: { transparency: 100 },
    });
  });
  const legend = {
    x: area.x,
    y: area.y + area.h * 0.58,
    w: area.w,
    h: area.h * 0.42,
  };
  const legendCells = H.gridLayout(legend, entries.length, 1, {
    columnGap: H.spacing(tokens, 3),
  });
  entries.forEach((entry, index) => {
    addPanel(slide, legendCells[index], tokens, {
      line: index % 2 ? p.accent2 : p.accent,
    });
    addLabel(slide, textOf(entry), legendCells[index], tokens, _lang, {
      bold: true,
      label: `矩阵标签 ${index + 1}`,
    });
  });
}

function addAnnotatedVisual(slide, data, area, tokens, lang) {
  const p = palette(tokens);
  const imageBox = { x: area.x, y: area.y, w: area.w * 0.56, h: area.h };
  if (data.asset) {
    addPanel(slide, imageBox, tokens, { shape: 'rect', fill: p.surface, line: p.muted });
    slide.addImage({
      path: data.asset,
      ...containImage(data.asset, imageBox),
      altText: data.alt_text || data.altText || data.purpose || 'Presentation visual',
    });
  } else if (data.svg_reference) {
    addPanel(slide, imageBox, tokens, { shape: 'none', fill: p.canvas, line: p.muted });
    SVG.addCornerDecoration(
      slide,
      data.svg_reference,
      {
        x: imageBox.x + imageBox.w * 0.16,
        y: imageBox.y + imageBox.h * 0.12,
        w: imageBox.w * 0.68,
        h: imageBox.h * 0.68,
      },
      tokens,
    );
  } else {
    addPanel(slide, imageBox, tokens, { shape: 'ellipse', fill: p.surface, line: p.accent });
    addLabel(
      slide,
      data.title || data.purpose || textOf(items(data.annotations || data.items)[0], 'Overview'),
      imageBox,
      tokens,
      lang,
      { bold: true, label: '解释焦点' },
    );
  }
  const annotations = items(data.annotations || data.items).slice(0, 3);
  const annotationArea = {
    x: area.x + area.w * 0.6,
    y: area.y,
    w: area.w * 0.4,
    h: area.h,
  };
  const cells = H.gridLayout(annotationArea, 1, Math.max(1, annotations.length), {
    rowGap: H.spacing(tokens, 3),
  });
  annotations.forEach((annotation, index) => {
    addPanel(slide, cells[index], tokens);
    addLabel(slide, textOf(annotation), cells[index], tokens, lang, {
      align: 'left',
      fontSize: 18,
      margin: 16,
      label: `图像注释 ${index + 1}`,
    });
  });
}

function addQuotePanel(slide, data, area, tokens, lang) {
  const p = palette(tokens);
  // 官方规范：禁止装饰性竖条；引文仅用底面色块 + 文本层级区分。
  addPanel(slide, area, tokens, { fill: p.surface, line: p.surface });
  addLabel(
    slide,
    data.quote || data.text,
    {
      x: area.x + area.w * 0.08,
      y: area.y + area.h * 0.16,
      w: area.w * 0.84,
      h: area.h * 0.38,
    },
    tokens,
    lang,
    { bold: true, align: 'left', label: '引文' },
  );
  if (data.source) {
    addLabel(
      slide,
      data.source,
      {
        x: area.x + area.w * 0.48,
        y: area.y + area.h * 0.65,
        w: area.w * 0.4,
        h: area.h * 0.31,
      },
      tokens,
      lang,
      { align: 'right', color: p.muted, label: '引文来源' },
    );
  }
}

function addSummary(slide, data, area, tokens, lang) {
  const takeaways = items(data.items || data.takeaways).slice(0, 4);
  if (!takeaways.length) throw new RangeError('addSummary requires 1-4 takeaways.');
  if (takeaways.length === 1) {
    addPanel(slide, area, tokens, { line: palette(tokens).accent2 });
    return addLabel(slide, textOf(takeaways[0]), area, tokens, lang, {
      bold: true,
      label: '总结结论',
    });
  }
  return addProcessFlow(slide, { steps: takeaways, numbered: false }, area, tokens, lang);
}

function addReferenceList(slide, data, area, tokens, lang) {
  const references = items(data.items || data.references);
  if (!references.length) throw new RangeError('addReferenceList requires at least one reference.');
  addPanel(slide, area, tokens, { line: palette(tokens).muted });
  return addLabel(
    slide,
    references.map(textOf).join('\n'),
    {
      x: area.x + area.w * 0.06,
      y: area.y + area.h * 0.08,
      w: area.w * 0.88,
      h: area.h * 0.84,
    },
    tokens,
    lang,
    { align: 'left', role: 'reference', label: '参考资料' },
  );
}

const COMPONENTS = {
  hero: addSectionHero,
  'visual-dominant': addAnnotatedVisual,
  'process-path': addProcessFlow,
  timeline: addTimeline,
  comparison: addComparison,
  dashboard: addMetricDashboard,
  architecture: addArchitecture,
  matrix: addMatrix,
  quote: addQuotePanel,
  summary: addSummary,
  reference: addReferenceList,
};

function renderVisual(slide, family, data, area, tokens, lang) {
  const component =
    family === 'dashboard' && items((data || {}).series).length
      ? addChartWithTakeaway
      : COMPONENTS[family];
  if (!component) throw new RangeError(`Unknown visual layout family: ${family}`);
  return component(slide, data || {}, area, tokens, lang);
}

function renderVisualSpec(slide, visual, family, area, tokens, lang) {
  const normalized = visual && typeof visual === 'object' ? visual : {};
  const data = {
    ...(normalized.details && typeof normalized.details === 'object' ? normalized.details : {}),
    ...Object.fromEntries(
      ['asset', 'alt_text', 'purpose', 'type']
        .filter((key) => normalized[key] !== undefined)
        .map((key) => [key, normalized[key]]),
    ),
  };
  return renderVisual(slide, family, data, area, tokens, lang);
}

module.exports = {
  addAnnotatedVisual,
  addArchitecture,
  addChartWithTakeaway,
  addComparison,
  addMatrix,
  addMetricDashboard,
  addProcessFlow,
  addQuotePanel,
  addReferenceList,
  addSectionHero,
  addSummary,
  addTimeline,
  renderVisual,
  renderVisualSpec,
};
