# Evidence And Citation Contract

## Evidence Ledger

Every factual chart, statistic, quotation, experiment result, survey finding, or
case claim should map to an `evidence_ledger` entry.

Each entry records:

- stable `id`;
- title or short description;
- source type;
- file path, URL, DOI, or bibliographic locator;
- author/organization and date when known;
- confidence: `high`, `medium`, `low`, or `unverified`;
- slides that use it;
- an optional limitation.

Never invent missing numbers, citations, user feedback, experiments, or survey
results. If evidence is unavailable, mark the claim as a proposal, assumption,
illustrative example, or evidence gap.

## Gap Detection

Flag:

- numbers without an evidence reference;
- causal language supported only by correlation or anecdote;
- experiment results without baseline, sample, metric, or comparison;
- user feedback without participant count or collection method;
- current facts without date/scope;
- quotations without author or source;
- citations listed but not used on any slide.

## Citation Styles

**Default: `classroom`（课堂引用）**。intake 不再询问引用风格，默认即课堂引用；
不要为了"展示引用风格"而在页面或讲稿中刻意强调格式（例如反复标注"课堂引用"、
或把引用风格写进开场白）。按上面各风格的自然呈现即可：幻灯片页脚/来源行简短标注，
完整出处放在讲稿或参考文献页。

- `classroom`: short source line on slide, full details in references.
- `GB-T-7714`: unified Chinese academic reference list.
- `APA`: author-date in content and APA reference list.
- `IEEE`: numbered references in the order they appear, standard in engineering and computer-science papers.
- `MLA`: author-page citations in content and a "Works Cited" list, common in humanities and language courses.
- `none`: allowed only when the presentation contains no external factual claims
  or the user explicitly accepts an unreferenced informal showcase.

Keep one style across the deck. Put full URLs and long bibliographic details in
speaker notes or references rather than shrinking normal slide text.
