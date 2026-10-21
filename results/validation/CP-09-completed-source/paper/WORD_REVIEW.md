# Word manuscript delivery and remaining native review

Date: 2026-10-07. **CP-09 complete: final DOCX and 11-page native Word PDF
validated; all native pages visually inspected.**

The later dated entries below supersede the earlier rendering limitations.
No new export is needed for the accepted saved version.

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


## Native review follow-up (2026-10-07)

The user exported the first version with Word 16.0: 11 pages, PDF SHA256
`c52f365eff093b5765ea00ff06fbd57f015dc5a71529d1a5d4f4cb14b98525b8`.
Every page was inspected; some table decimals/counts wrapped across lines.
The builder now reduces cell padding to 20 twips without changing measured values.
Structural checks and three focused tests pass. Revised DOCX SHA256:
`baf2e053877109b28b6592bfe84f24da53c9127dc227a32577063b6362c03426`.

First DOCX/PDF/proofs are preserved under
`../results/validation/CP-09-native-first-export/`. The old root PDF is named
`Graph_Search_Research_Paper_first_export.pdf`; it is not the final PDF for the
revised DOCX. Run the three native commands above again, then inspect every new
page, especially table decimals and counts. CP-09 stays partial until they pass.


## Second native review and numeric-width correction (2026-10-07)

All 11 pages of PDF `ff33d3604a71232a6a1e0714e99ac45f3a3987df33b8b2e6de2fd9ce8ad04b72`
were inspected. Most numbers fit; long Table X totals still wrapped. The builder
now assigns measured minimum numeric column widths, preserving all data, fonts
and overall table width. Strengthened numeric-width/content/tamper/preview checks
passed (three tests, 10.980s).

Latest DOCX SHA256:
`c77ec6f2fa852cf55588fdb138c4e64c3187589644d43da058bf42ec49626349`.
The previous native export is saved as
`Graph_Search_Research_Paper_padding_export.pdf` and in
`../results/validation/CP-09-native-padding-export/`. Neither earlier PDF validates
the newest DOCX. Rerun the three native commands and inspect all revised pages,
including Table X long totals. CP-09 remains partial until this review passes.


## Final native acceptance (2026-10-07)

Accepted DOCX SHA256:
`c77ec6f2fa852cf55588fdb138c4e64c3187589644d43da058bf42ec49626349`.
Accepted native PDF SHA256:
`e0e7a8e6b0e9e08613c61828303b71afae52060412b499ab6a67617695be0823`.
User exported with Word 16.0; automatic review found 11 pages and zero out-of-page
text/images. All native pages 01-11 were visually inspected, including Table X
long numbers, complete charts, numbered equations, captions and references.
Numeric wrapping corrected. Tables continue with repeated headers; Table V's
caption/header starts at the end of page 7 before its continued body. No values
are lost. Structural checks passed again and the unchanged DOCX has the earlier
three passing strengthened checks (10.980s). CP-09 is complete.

Accepted files: `Graph_Search_Research_Paper.docx` and
`Graph_Search_Research_Paper.pdf`. Independent preview remains an approximate
12-page reconstruction, not the accepted native output. Earlier PDF filenames
with first_export/padding_export are historical review versions only. The
acceptance record is `../results/validation/CP-09-acceptance.json`. Any future
DOCX edit requires a new export and review. No journal acceptance is claimed.
