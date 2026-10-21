# Word manuscript delivery and remaining native review

Date: 2026-10-07. **DOCX generation and structural validation complete;
CP-09 remains partial because native Word page review is unavailable.**

Open `Graph_Search_Research_Paper.docx` for the complete graph-search paper.
Author: Madhav Joshi, Marwadi University. The unrelated QENN reference is unchanged.

The document matches the reference's A4 geometry, 0.7-inch top/bottom and
0.6-inch side margins, Times New Roman, centered 14pt title/11pt author/9pt
affiliation, single-column opening, two-column body with 440-twip gap,
Roman main headings/table numbers, italic lettered subsections, numbered
equations and 9pt captions. Reference body size is implicit; Word's 11pt default
is made explicit and recorded as an assumption. Unconfirmed department/location/
email fields are omitted. Header/footer remain blank like the reference.

All 130 text blocks match the bound source/formatting ledger. All cells in ten
tables (one literature comparison plus nine measured-result tables) match the
reviewed source. Seven column-sized figures use the same audited values; their
panels are stacked so labels stay readable. Two equations are native editable
Office Math objects, and nine bibliography links point to verified sources.
Only two project-workflow sentences were omitted from scientific limitations;
no result or scientific limitation was removed or changed.

The independent PDF `Graph_Search_Research_Paper_preview.pdf` is generated from
the actual DOCX text, tables and embedded images. It has 12 pages with no text
or images beyond page bounds. It approximates column flow with ReportLab and
uses the checked CP-08 equation rasters. It is **not an export from Word**, and
does not verify Word's own page breaks or equation/table layout. All-page overview,
critical pages and figure review are recorded separately. Preview inspection
found oversized lazy-loaded equation images and wrapped number labels; both
were fixed, with regression checks for image bounds and intact `(1)`/`(2)`.

Actual native export was attempted using installed Microsoft Word. COM activation
failed with HRESULT `-2147023584`: "A specified logon session does not exist.
It may already have been terminated." No active Word instance was accessible.
LibreOffice was absent; downloading another renderer failed because network
access was unavailable. These limitations were not bypassed or hidden.

From an ordinary interactive Windows terminal with Word available, run:

```powershell
python -m paper.render_word
python -m paper.check_word
python -m paper.review_word --native
```

The exporter opens the new DOCX read-only and creates
`Graph_Search_Research_Paper.pdf`; it never saves changes to the DOCX or touches
QENN. `review_word --native` rejects missing/failed/stale exports. Inspect every
native page for table widths, column flow, equations, captions and references.
Fix any layout issues, repeat the relevant checks, and update `task.md` and
`everythingtoknow.md` before marking CP-09 complete. Until that happens, the
document is delivered for review, with final native pagination acceptance pending.
