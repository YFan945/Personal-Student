'use strict';

const registry = require('../skills/sp-deck/references/layout-library.json');

const layoutsById = new Map(registry.layouts.map((layout) => [layout.id, layout]));

function getLayout(id) {
  const layout = layoutsById.get(id);
  if (!layout) throw new Error(`Unknown layout: ${id}`);
  return JSON.parse(JSON.stringify(layout));
}

function stableHash(value) {
  let hash = 2166136261;
  for (const char of String(value)) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function includesOrWildcard(values, value) {
  return !value || !Array.isArray(values) || values.length === 0 || values.includes(value);
}

function isFeasible(layout, context) {
  if (!includesOrWildcard(layout.eligible_kinds, context.slideKind || context.kind)) return false;
  if (!includesOrWildcard(layout.visual_families, context.visualFamily)) return false;

  const requirements = layout.requirements || {};
  if (requirements.asset === 'required' && !context.hasAsset) return false;
  if (requirements.data === 'required' && !context.hasData) return false;
  if (requirements.quote === 'required' && !context.hasQuote) return false;

  const itemCount = Number.isFinite(context.itemCount) ? context.itemCount : null;
  if (itemCount !== null && Array.isArray(requirements.items)) {
    if (itemCount < requirements.items[0] || itemCount > requirements.items[1]) return false;
  }
  return true;
}

function historySilhouettes(history) {
  return (history || [])
    .map((entry) => {
      if (typeof entry === 'string' && layoutsById.has(entry))
        return layoutsById.get(entry).silhouette;
      return (
        entry && (entry.silhouette || (entry.layout && layoutsById.get(entry.layout)?.silhouette))
      );
    })
    .filter(Boolean);
}

function scoreLayout(layout, context, tokens, history) {
  let score = 0;
  const dna = (tokens && tokens.style_dna) || {};
  const composition = dna.composition || {};
  const preferredTags = new Set(
    composition.preferred_layout_tags || dna.preferred_layout_tags || [],
  );
  const preferredIds = new Set(composition.signature_layouts || []);

  for (const tag of layout.style_tags || []) if (preferredTags.has(tag)) score += 7;
  if (preferredIds.has(layout.id)) score += 12;
  if (context.density && context.density === layout.density) score += 5;
  if ((context.layout || context.layoutId) === layout.id) score += 40;

  const silhouettes = historySilhouettes(history);
  const last = silhouettes.at(-1);
  const previous = silhouettes.at(-2);
  if (layout.silhouette === last) score -= 12;
  if (layout.silhouette === last && layout.silhouette === previous) score -= 1000;

  const seed = context.seed || `${context.slideId || 'slide'}:${context.title || ''}`;
  score += (stableHash(`${seed}:${layout.id}`) % 1000) / 10000;
  return score;
}

function selectLayouts(context = {}, tokens = {}, history = [], count = 3) {
  const requestedCount = Math.max(1, Number(count) || 3);
  let candidates = registry.layouts.filter((layout) => isFeasible(layout, context));

  if (candidates.length === 0 && context.layout && layoutsById.has(context.layout)) {
    const requested = layoutsById.get(context.layout);
    const fallback = layoutsById.get(requested.fallback);
    if (fallback && isFeasible(fallback, context)) candidates = [fallback];
  }
  if (candidates.length === 0) {
    candidates = registry.layouts.filter((layout) =>
      includesOrWildcard(layout.eligible_kinds, context.slideKind || context.kind),
    );
  }

  return candidates
    .map((layout) => ({
      ...getLayout(layout.id),
      score: scoreLayout(layout, context, tokens, history),
    }))
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id))
    .slice(0, requestedCount);
}

function resolveLayout(id, safeArea, options = {}) {
  const layout = getLayout(id);
  const area = {
    x: Number(safeArea?.x ?? 0),
    y: Number(safeArea?.y ?? 0),
    w: Number(safeArea?.w ?? safeArea?.width ?? 1),
    h: Number(safeArea?.h ?? safeArea?.height ?? 1),
  };
  if (!(area.w > 0 && area.h > 0)) throw new Error('safeArea width and height must be positive');

  const mirror = Boolean(options.mirror);
  const zones = {};
  for (const [name, normalized] of Object.entries(layout.zones)) {
    const [nx, ny, nw, nh] = normalized;
    const resolvedX = mirror ? 1 - nx - nw : nx;
    zones[name] = {
      x: area.x + resolvedX * area.w,
      y: area.y + ny * area.h,
      w: nw * area.w,
      h: nh * area.h,
    };
  }
  return { ...layout, safeArea: area, mirrored: mirror, zones };
}

module.exports = {
  getLayout,
  selectLayouts,
  resolveLayout,
  registry,
};
