# PPTX Runtime Provenance

An initial adaptation audit on 2026-07-22 examined the locally cached Anthropic
`document-skills` PPTX skill at revision directory `fa0fa64bdc96`. That upstream material
identified itself as proprietary/source-available and is not covered by this repository's MIT
license.

No file from that snapshot is distributed by this plugin. The temporary
`skills/sp-deck/scripts/pptx_skill/` copy and the imported guide were removed.
The current implementation under `shared/pptx_runtime/`, its `scripts/pptx_tool.py` facade,
workflow documents, adapters, and tests are suite-owned code maintained in this repository.
The Linux AF_UNIX compatibility source under `shared/pptx_runtime/assets/` is a new suite-owned
implementation and is not copied from the audited cache snapshot.

Markup/schema validation is provided by `DocumentFormat.OpenXml` 3.5.1 through a small
suite-owned .NET adapter, supplemented by suite-owned OPC semantic checks. This is not a claim
that the plugin bundles every PML/DML/OPC XSD. The SDK is MIT-licensed and restored from NuGet
during the managed build; no ECMA/ISO XSD files from the proprietary cache snapshot are copied
or redistributed.

On 2026-07-26, a follow-up audit confirmed and removed residual `__pycache__/` bytecode files
that remained under `skills/sp-deck/scripts/pptx_skill/` after the source
deletion. The entire directory tree has been removed.

The upstream cache path is retained here only as historical audit provenance. Runtime consumers
must use `scripts/pptx_tool.py`; they must not import an installed external plugin, reference the
original cache path, or recreate the deleted embedded snapshot.
