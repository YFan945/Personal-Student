'use strict';

const fs = require('node:fs');
const H = require('pptx-helpers');
const L = require('pptx-layouts');
const V = require('pptx-visuals');
const SVG = require('pptx-svg-library');

const FAMILY_BY_TYPE = Object.freeze({
  chart: 'dashboard',
  data: 'dashboard',
  process: 'process-path',
  timeline: 'timeline',
  comparison: 'comparison',
  architecture: 'architecture',
  system: 'architecture',
  matrix: 'matrix',
  quote: 'quote',
  image: 'visual-dominant',
  illustration: 'visual-dominant',
  summary: 'summary',
  references: 'reference',
  reference: 'reference',
});

function slideText(slideSpec) {
  const value =
    slideSpec.slide_copy ??
    slideSpec.supporting_points ??
    slideSpec.content ??
    slideSpec.claim ??
    '';
  if (Array.isArray(value)) return value.map(String);
  if (value && typeof value === 'object')
    return Object.values(value).filter((item) => typeof item === 'string');
  return String(value || '');
}

function bodyText(slideSpec) {
  if (slideSpec.visual)
    return String(
      slideSpec.claim || (typeof slideSpec.content === 'string' ? slideSpec.content : '') || '',
    );
  return slideText(slideSpec);
}

function bodyRole(slideSpec) {
  return ['cover', 'section-divider', 'closing'].includes(slideSpec.kind) ? 'label' : 'body';
}

function shouldRenderBody(slideSpec) {
  return visualFamily(slideSpec) !== 'summary';
}

function visualFamily(slideSpec) {
  return slideSpec.visual?.layout_family || FAMILY_BY_TYPE[slideSpec.visual?.type] || null;
}

function contextFor(slideSpec, context) {
  const content = slideText(slideSpec);
  const itemCount = Array.isArray(content) ? content.length : content ? 1 : 0;
  const asset = slideSpec.visual?.asset;
  return {
    slideId: slideSpec.id,
    title: slideSpec.title,
    titleChars: [...String(slideSpec.title || '')].length,
    slideKind: slideSpec.kind,
    role: slideSpec.role,
    layout: slideSpec.layout,
    layoutFamily: visualFamily(slideSpec),
    itemCount,
    hasAsset: Boolean(asset && fs.existsSync(asset)),
    hasData: Boolean(slideSpec.visual?.details?.series || slideSpec.visual?.details?.metrics),
    hasQuote: Boolean(slideSpec.visual?.details?.quote || slideSpec.visual?.type === 'quote'),
    seed: context.seed || `${context.topic || 'deck'}:${slideSpec.id}`,
  };
}

function chooseLayout(slideSpec, context) {
  const selected = L.selectLayouts(
    contextFor(slideSpec, context),
    context.tokens,
    context.history,
    1,
  );
  if (!selected.length) throw new RangeError(`No feasible layout for slide ${slideSpec.id}`);
  return selected[0];
}

function resolveSlideComposition(slideSpec, context) {
  const layout = chooseLayout(slideSpec, context);
  const area =
    context.safeArea ||
    H.safeArea(context.slideW || H.SLIDE_W_IN, context.slideH || H.SLIDE_H_IN, context.tokens, {
      reserveTitle: false,
    });
  return L.resolveLayout(layout.id, area, { mirror: Boolean(context.mirror) });
}

function preflightSlide(slideSpec, context) {
  const layout = resolveSlideComposition(slideSpec, context);
  const body = bodyText(slideSpec);
  const results = [
    H.preflightText(slideSpec.title, layout.zones.title, context.tokens, context.lang, 'title'),
  ];
  if (
    shouldRenderBody(slideSpec) &&
    ((Array.isArray(body) && body.length) || (!Array.isArray(body) && body))
  ) {
    results.push(
      H.preflightText(
        Array.isArray(body) ? body.join('\n') : body,
        layout.zones.body,
        context.tokens,
        context.lang,
        bodyRole(slideSpec),
      ),
    );
  }
  const missingAsset = Boolean(slideSpec.visual?.asset && !fs.existsSync(slideSpec.visual.asset));
  const errors = results
    .filter((result) => !result.ok)
    .map((result) => `${result.role}: ${result.resolution}`);
  if (missingAsset && context.imageStrategy !== 'hybrid-adaptive')
    errors.push('visual asset does not exist and no adaptive fallback is enabled');
  return {
    ok: errors.length === 0,
    slide_id: slideSpec.id,
    layout: layout.id,
    text: results,
    errors,
    missing_asset: missingAsset,
  };
}

function fallbackIllustration(slide, slideSpec, box, context) {
  const tokens = context.tokens;
  const corner = tokens.style_dna?.corner_svg_set || 'minimal-focus';
  slide.addImage({
    data: SVG.getCornerSvg(corner, {
      primary: tokens.palette?.primary_accent,
      secondary: tokens.palette?.secondary_accent,
    }),
    x: box.x + box.w * 0.18,
    y: box.y + box.h * 0.08,
    w: box.w * 0.64,
    h: box.h * 0.64,
    altText:
      slideSpec.visual?.alt_text ||
      slideSpec.visual?.purpose ||
      tokens.style_dna?.fallback_illustration ||
      'Explanatory diagram',
  });
  if (slideSpec.visual?.purpose) {
    H.addFittedText(
      slide,
      slideSpec.visual.purpose,
      { x: box.x + box.w * 0.08, y: box.y + box.h * 0.76, w: box.w * 0.84, h: box.h * 0.18 },
      tokens,
      context.lang,
      'caption',
      { align: 'center', label: '视觉用途说明' },
    );
  }
}

function renderSlide(slide, slideSpec, context) {
  const preflight = preflightSlide(slideSpec, context);
  if (!preflight.ok)
    throw new RangeError(`Slide ${slideSpec.id} preflight failed: ${preflight.errors.join('; ')}`);
  const layout = resolveSlideComposition(slideSpec, context);
  H.addBackground(slide, context.tokens, false);
  const cornerName = context.tokens.style_dna?.corner_svg_set;
  if (cornerName && ['cover', 'section-divider', 'closing'].includes(slideSpec.kind)) {
    H.addStyleMotif(slide, { x: 0.32, y: 0.24, w: 1.2, h: 0.86 }, context.tokens, 'restrained');
    SVG.addCornerDecoration(
      slide,
      cornerName,
      { x: (context.slideW || H.SLIDE_W_IN) - 1.18, y: 0.12, w: 0.9, h: 0.9 },
      context.tokens,
      { transparency: 8 },
    );
  }
  H.addFittedText(
    slide,
    slideSpec.title,
    layout.zones.title,
    context.tokens,
    context.lang,
    'title',
    {
      align:
        layout.text_policy === 'display' && layout.silhouette === 'center-focus'
          ? 'center'
          : 'left',
      bold: true,
      label: `幻灯片 ${slideSpec.id} 标题`,
    },
  );
  const body = bodyText(slideSpec);
  if (
    shouldRenderBody(slideSpec) &&
    ((Array.isArray(body) && body.length) || (!Array.isArray(body) && body))
  ) {
    H.addFittedText(
      slide,
      Array.isArray(body) ? body.join('\n') : body,
      layout.zones.body,
      context.tokens,
      context.lang,
      bodyRole(slideSpec),
      { bullet: Array.isArray(body), label: `幻灯片 ${slideSpec.id} 正文` },
    );
  }
  if (slideSpec.visual) {
    const family = visualFamily(slideSpec);
    const assetUsable = !slideSpec.visual.asset || fs.existsSync(slideSpec.visual.asset);
    if (family && assetUsable) {
      const visualBox = family === 'summary' ? layout.zones.body : layout.zones.visual;
      V.renderVisualSpec(slide, slideSpec.visual, family, visualBox, context.tokens, context.lang);
    } else fallbackIllustration(slide, slideSpec, layout.zones.visual, context);
  } else if (!['cover', 'section-divider', 'closing', 'references'].includes(slideSpec.kind)) {
    fallbackIllustration(
      slide,
      { ...slideSpec, visual: { purpose: slideSpec.claim || 'Organize the slide claim' } },
      layout.zones.visual,
      context,
    );
  }
  if (slideSpec.speaker_notes && typeof slide.addNotes === 'function')
    slide.addNotes(slideSpec.speaker_notes);
  context.history.push({ layout: layout.id, silhouette: layout.silhouette });
  return { slide_id: slideSpec.id, layout: layout.id, silhouette: layout.silhouette };
}

function renderDeck(pptx, spec, context) {
  const resolved = {
    history: [],
    imageStrategy: spec.meta?.image_source || 'hybrid-adaptive',
    topic: spec.meta?.topic,
    ...context,
  };
  H.applyTokens(pptx, resolved.tokens, resolved.lang);
  const preflight = spec.slides.map((slideSpec) => preflightSlide(slideSpec, resolved));
  const blockers = preflight.filter((item) => !item.ok);
  if (blockers.length)
    throw new RangeError(
      `Deck preflight failed on slides: ${blockers.map((item) => item.slide_id).join(', ')}`,
    );
  const rendered = spec.slides.map((slideSpec) =>
    renderSlide(pptx.addSlide(), slideSpec, resolved),
  );
  return { preflight, rendered };
}

module.exports = { preflightSlide, resolveSlideComposition, renderSlide, renderDeck };
