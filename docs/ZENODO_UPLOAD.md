# Zenodo upload details for this preprint

Prepared 2026-10-07. This is a manual form guide, not an API upload or a published record.

## Files to select

Use the files in `final submission/zenodo/`:

- `Madhav_Joshi_Graph_Search_Preprint_v1.0.pdf`: main public manuscript.
- `Madhav_Joshi_Graph_Search_Preprint_v1.0.docx`: optional editable version.

The earlier PDF in `final submission/` does not contain your added programme/email.
Do not upload that earlier PDF as the revised version. Never upload Word lock files
starting with `~$`, validation JSON, the unrelated QENN reference or the whole
project folder as this manuscript record.

The revised DOCX retains the author details supplied in your edits, with a centered
11pt bold name and 9pt programme/university/email, ordered name, programme,
university, email. Restored the canonical abstract/index-term dash styling and
verified equation symbols. Scientific text, all ten tables, seven embedded figures,
two editable equations and nine reference links match the audited paper.

The new PDF is typeset from that revised DOCX with ReportLab. It is a publication
PDF with a preprint/version footer, not a native Word export. Word COM activation
failed in the agent session; no matching native Word pagination is claimed. The
12-page publication PDF was checked separately and every page visually inspected.
The original CP-09 native DOCX/PDF acceptance is preserved unchanged.

## Form fields

| Field | Value/action |
|---|---|
| Resource type | Publication / Preprint |
| Title | A Comparative Study of Deep Q-Networks and Traditional Algorithms for Multi-Agent Shortest-Path Search in Dynamic Graphs |
| Creator type | Person |
| Given name | Madhav |
| Family name | Joshi |
| Affiliation | Marwadi University; choose its matching autocomplete entry if available |
| Programme | Artificial Intelligence & Machine Learning is shown in the manuscript; no invented department title |
| ORCID | Enter your own valid ORCID if you have one; otherwise leave blank |
| Language | English |
| Version | 1.0 |
| Publication date | The date this preprint first becomes publicly available; use an earlier real date only if already publicly released |
| Already have a DOI? | No if this preprint has never received a DOI; reserve a new one with Get a DOI now! |
| Visibility | Public for an openly shared preprint |
| License | Recommended CC BY 4.0, subject to your choice; not applied automatically |
| Publisher | Keep Zenodo's default if offered |
| Funding/grants | Leave blank unless there is actual funding to acknowledge |
| Contributors | Add only real contributors; do not list a supervisor as an author without authorship |
| Journal/conference details | Leave blank; no journal/conference publication is established |
| Communities | Optional; choose only a community relevant to your work |
| Related identifiers | Add an actual GitHub/code/data URL or DOI once available; no placeholder URL |
| Description | Paste the abstract below |
| Notes | Research preprint; not peer reviewed |

Zenodo supports separate family/given names and optional affiliations/identifiers.
The email appears in the paper; it is not an ORCID or a substitute for a creator
identifier. Do not add it to a field requesting an ORCID.

## Abstract to paste

This study compares prioritized breadth-first search, Dijkstra and A* with solo-trained and shared-policy deep Q-networks for navigation on static and changing unit-cost grids. Ten policies from five training seeds were frozen after static 5×5 training and evaluated without learning on 120 new geometries spanning 5×5, 10×10 and 15×15 sizes, one/two/four agents and two wall probabilities. The final protocol produced 15,120 unique evaluation episodes; three fresh timing rollouts per episode were not treated as extra outcome samples. Across all conditions, replanning A* completed 642/720 episodes (89.17%), shared DQN 799/3600 (22.19%), and solo DQN 870/3600 (24.17%). All recorded first trajectories passed replay auditing, and actual collisions were zero under the common rejection rules. Success-conditioned paths, matched comparisons and descriptive variation across model seeds are reported alongside failures. The findings apply to fixed small-map-trained policies and current-map prioritized planners under this protocol; they do not establish a universal algorithm ranking or a general reinforcement-learning adaptation advantage.

## Keywords

graph search, deep reinforcement learning, deep Q-network, multi-agent pathfinding, dynamic graphs, prioritized planning, policy transfer, reproducibility

## License choice

CC BY 4.0 lets readers share and adapt the paper, including commercially, while
requiring attribution and an indication of changes. Zenodo requires a license
and defaults to CC BY 4.0. This is a recommendation for the manuscript; no code
license or public grant of rights has been applied by this preparation step.
Choose the license you intend to grant in the upload form.

## Steps before Publish

1. New upload: select the revised PDF; add the revised DOCX only if you want it public.
2. Select Publication / Preprint and enter the metadata above.
3. If no existing DOI for this same preprint, answer No and reserve a DOI.
   It is registered when the record is published. Do not reuse the QENN DOI or
   a DOI belonging to a different paper/dataset. DOI text inside the PDF is optional.
4. Save draft, then Preview. Check title, author, affiliation, license and uploaded
   PDF opening page. This preparation has not created or published a Zenodo draft.
5. Publish when you have reviewed the record. A Zenodo DOI identifies the deposited
   work; it does not establish journal acceptance or peer review.

For a code release, use a separate Software record. For a substantial dataset,
use a separate dataset record and link it to the manuscript. Choose a license
appropriate to each resource; do not assume a manuscript license covers the code.
Zenodo explicitly supports splitting mixed resources into separate records.

## Official sources checked

- [Resource types](https://help.zenodo.org/docs/deposit/describe-records/resource-type/)
- [Upload, visibility and preview](https://help.zenodo.org/docs/deposit/create-new-upload/)
- [Creators](https://help.zenodo.org/docs/deposit/describe-records/creators/)
- [Publication date](https://help.zenodo.org/docs/deposit/describe-records/publication-date/)
- [Reserve DOI](https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/)
- [Descriptions](https://help.zenodo.org/docs/deposit/describe-records/descriptions/)
- [Zenodo licenses](https://help.zenodo.org/docs/deposit/describe-records/licenses/)
- [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Metadata values are also saved in `docs/zenodo_metadata.json` for copying. It is
not a payload for direct API publication. File validation evidence lives in
`results/validation/zenodo-submission-checks.json` and page rasters are stored
under `results/validation/zenodo-pages/`.
