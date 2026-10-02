## MODIFIED Requirements

### Requirement: Anchored harms block, and drift has its own tier

`skills/mf-converge/SKILL.md` SHALL name the **anchors** — data loss or an irreversible delete, spend, exposure of
personal data or secrets, silent wrong output — and SHALL grade an anchored finding `blocking` in review and at least
`high` in security. Review SHALL grade `blocking | drift | nit`, where `drift` is docs, comments, README or CHANGELOG
text the code contradicts; `drift` SHALL NOT block. A spec scenario the code contradicts SHALL stay `blocking`.

#### Scenario: Converge and the method page name the anchors and the drift tier
- **Key:** `sdd:converge-audit:anchors-and-drift`
- **Layers:** unit
- **WHEN** `skills/mf-converge/SKILL.md` is scanned
- **THEN** it names `blocking | drift | nit`
- **AND** it names each anchor: `data loss`, `spend`, `exposure`, `silent wrong output`
