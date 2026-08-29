# Source ingestion

Scanner: `course-materials/**` for ipynb, pdf, pptx.

- Jupyter via `nbformat`. Never execute.
- PDF via PyMuPDF when installed.
- PPTX via python-pptx when installed.

Safety flags: kubectl, helm, docker, rm, bash magics, exec/eval, nvidia-smi, from_pretrained, network.

Provenance pointer: `{source_type, file, cell_index|page|slide}`.
