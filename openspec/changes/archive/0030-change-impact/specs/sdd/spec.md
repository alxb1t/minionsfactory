## ADDED Requirements

### Requirement: A repository opts into metrics with a catalogue

A repository SHALL be measured only when it holds `metrics/catalogue.toml`. Without it, `mf-build` and
`mf-release` SHALL collect nothing, render nothing and check nothing, and each SHALL state `metrics: none — no
catalogue` in its report. No metric SHALL be measured for a repository that declares none.

#### Scenario: A repository without a catalogue
- **WHEN** the build or the release reaches its metrics step in a repository with no `metrics/catalogue.toml`
- **THEN** it writes no data file and no page
- **AND** its report states `metrics: none — no catalogue`

#### Scenario: A repository with a catalogue
- **WHEN** the build or the release reaches its metrics step and `metrics/catalogue.toml` exists
- **THEN** it collects a value, or `unavailable` with a reason, for every metric the catalogue declares

### Requirement: A metric is a Python script the collector runs without a shell

Each `[[metric]]` in `metrics/catalogue.toml` SHALL declare `id`, `title`, `group`, `unit` and `better`
(`lower` or `higher`), MAY declare `watch` and `noise`, and SHALL declare either `script` with `args` or
`source = "station"`. The collector SHALL run a metric's script as `uv run --script <script> <args>` from the
repository root, never through a shell, with a 300-second timeout. A run that exits 0 with a number on its last
stdout line SHALL record that number; any other outcome SHALL record `unavailable` with its reason. A failing
metric SHALL NOT fail the station. A catalogue that does not parse, lacks a required field or repeats an `id`
SHALL halt the station, naming the entry.

#### Scenario: A metric script prints its value
- **WHEN** a metric's script exits 0 and its last stdout line is a number
- **THEN** the data file records that number for the metric's `id`

#### Scenario: A metric script fails
- **WHEN** a metric's script exits non-zero, prints no number, or runs past its timeout
- **THEN** the data file records `unavailable` with the reason
- **AND** the station carries on with the other metrics

#### Scenario: The catalogue is broken
- **WHEN** the catalogue does not parse, an entry lacks a required field, or two entries share an `id`
- **THEN** the station halts, naming the entry

### Requirement: The build collects a draft of the metrics after simplify

When the repository has a catalogue, `skills/mf-build/SKILL.md` SHALL, after its simplify commit or no-op, collect
the metrics into `.minions/metrics/<change-id>.json` and render `.minions/metrics/<change-id>.html`, both
gitignored. Its close-out SHALL name the page and the count of metrics that crossed their watch in this change or
moved the wrong way. The build SHALL NOT halt on a watch.

#### Scenario: A change crosses a watch
- **WHEN** a metric's value crosses its `watch` in this change
- **THEN** the build's close-out names the page and counts the metric
- **AND** the build stops as it always does, leaving the choice to the person

### Requirement: The release records the shipped metrics in its commit

When the repository has a catalogue, `skills/mf-release/SKILL.md` SHALL, after the version file and before its
final gate, collect the metrics on the release's own tree into `metrics/changes/<change-id>.json`, passing the
gate time of precondition 1, and SHALL stage that file into the release commit. A collector that crashes, rather
than recording a metric `unavailable`, SHALL halt the release.

#### Scenario: A release with a catalogue
- **WHEN** the release reaches its metrics step and the catalogue exists
- **THEN** `metrics/changes/<change-id>.json` is written on the folded, archived tree
- **AND** the final gate judges a tree that holds it, and the release commit contains it

### Requirement: The page classifies each metric against the previous release

The page SHALL compare each metric with the previous release — the tracked data file whose version is the highest
below this change's — and classify it as steady (the change within `noise`), improved or worsened by `better`,
crossed here (the previous value on the good side of `watch`, this one past it), over (both past it), back under,
or new. It SHALL list crossed here, then worsened, then over, then the rest, before the charts. A chart SHALL show
an `unavailable` value as a gap, never as zero. The page SHALL be a self-contained HTML file with inline SVG, and
SHALL be renderable again from any change's data file.

#### Scenario: A metric already over its watch
- **WHEN** a metric was past its `watch` in the previous release and still is
- **THEN** the page classifies it as over, not as crossed here

#### Scenario: A metric with no value
- **WHEN** a metric is `unavailable` in a data file
- **THEN** its chart shows a gap at that version

### Requirement: A data file records where its values came from

Each data file SHALL record the change, its version, the base and the analyzed revisions, `measured_on`,
`mf_version`, `executor` and `model`. `mf_version` SHALL come from the collector's own package, or be `unknown`;
`executor` SHALL be what the station's executor selection reported; `model` SHALL be the station's own report, or
`unidentified`. None SHALL be guessed from a name.

#### Scenario: The collector runs from a frozen copy
- **WHEN** the collector's package is not inside a git checkout
- **THEN** the data file records `mf_version: unknown`
