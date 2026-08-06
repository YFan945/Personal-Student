'use strict';

const pptxgen = require('pptxgenjs');
const SHAPE = new pptxgen().ShapeType;

const SUPPORTED_SHAPES = Object.freeze([
  'rect',
  'roundRect',
  'ellipse',
  'pill',
  'hexagon',
  'chevron',
  'parallelogram',
  'arch',
  'bracket',
  'none',
]);

function normalizeShape(shape) {
  const value = String(shape || 'rect');
  if (!SUPPORTED_SHAPES.includes(value)) throw new RangeError(`Unsupported styled shape: ${value}`);
  return value;
}

function safeInsetForShape(shape, box) {
  const value = normalizeShape(shape);
  const unit = Math.min(Number(box.w), Number(box.h));
  const factors = {
    rect: [0.08, 0.08],
    roundRect: [0.09, 0.09],
    pill: [0.18, 0.12],
    ellipse: [0.2, 0.18],
    hexagon: [0.18, 0.08],
    chevron: [0.2, 0.08],
    parallelogram: [0.16, 0.1],
    arch: [0.16, 0.18],
    bracket: [0.12, 0.08],
    none: [0.04, 0.04],
  };
  const [xFactor, yFactor] = factors[value];
  return { x: unit * xFactor, y: unit * yFactor };
}

function addStyledContainer(slide, shape, box, tokens, options = {}) {
  const value = normalizeShape(shape);
  if (value === 'none') return null;
  const palette = tokens.palette || {};
  const fill = options.fill || palette.surface || 'FFFFFF';
  const line = options.line || palette.primary_accent || '2563EB';
  if (value === 'bracket') {
    const width = Math.max(1, Number(options.lineWidth || 1.5));
    const arm = Math.min(box.w * 0.14, 0.2);
    slide.addShape(SHAPE.line, {
      x: box.x,
      y: box.y,
      w: 0,
      h: box.h,
      line: { color: line, width },
    });
    slide.addShape(SHAPE.line, { x: box.x, y: box.y, w: arm, h: 0, line: { color: line, width } });
    slide.addShape(SHAPE.line, {
      x: box.x,
      y: box.y + box.h,
      w: arm,
      h: 0,
      line: { color: line, width },
    });
    return null;
  }
  const mapped = value === 'pill' ? SHAPE.roundRect : value === 'arch' ? SHAPE.arc : SHAPE[value];
  const shapeOptions = {
    ...box,
    fill: { color: fill, transparency: Number(options.fillTransparency || 0) },
    line: {
      color: line,
      width: Number(options.lineWidth || 1.25),
      transparency: Number(options.lineTransparency || 0),
    },
  };
  if (value === 'pill') shapeOptions.radius = Math.min(box.w, box.h) / 2;
  if (value === 'arch') shapeOptions.adjustPoint = 0.25;
  return slide.addShape(mapped, shapeOptions);
}

module.exports = { SUPPORTED_SHAPES, normalizeShape, safeInsetForShape, addStyledContainer };
