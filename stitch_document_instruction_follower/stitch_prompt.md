# Eye of Abyss — Stitch UI Generation Prompt

Use the prompt blocks below sequentially in Stitch. Start with the Design System prompt
to establish the visual identity, then generate each screen separately referencing it.

---

## PROMPT 0 — Design System & Identity

Establish this before generating any screens. Reference it in every subsequent prompt.

---

Design a UI system for **Eye of Abyss**, a cybercrime intelligence platform used by law enforcement investigators, financial intelligence analysts, and cybercrime cell officers in India.

**Platform context:** Investigators use this to build cases against cybercriminals — detecting synthetic voice fraud in real time, attributing dark web identities to criminal actors, and tracing cryptocurrency flows. The platform converges all three into a tamper-proof case file anchored on the Polygon blockchain.

**Philosophical identity:** The platform is named after Nietzsche's aphorism — "if you gaze long into an abyss, the abyss also gazes back." The visual language should embody this: a point of precise, amber-gold light in profound darkness. Institutional authority that does not flinch from what it sees.

**Color palette — use exactly these values:**
- Background (Abyss): `#0D0B14` — deep violet-black. Never pure black.
- Surface (Void): `#13111E` — cards, panels
- Card surface (Shadow): `#1C1929` — nested elements, inputs
- Borders (Mist): `#2A2640`
- Primary accent (Gaze): `#F0A500` — amber gold. THIS is the eye. Use for active states, key numbers, critical verdicts, CTAs.
- Graph/confidence color (Signal): `#6B4FFF` — electric indigo
- Alert/threat: `#C92A2A` — deep crimson
- Safe/confirmed: `#2A9D4E` — forest green
- Primary text: `#E8E6F2`
- Secondary text: `#8884A8`
- Muted text: `#4A4768`

**Typography:**
- Headings, labels, UI: Space Grotesk (Google Fonts) — weights 400, 500, 600
- Data, hashes, wallet addresses, technical strings: JetBrains Mono — weights 400, 500
- Never use Inter or Roboto

**Layout rules:**
- Left navigation rail: 56px wide (icon-only), icons only — no labels in collapsed state
- Main content: left-aligned, not centered
- Right context panel: 320px, appears when a case is selected
- Grid: 8px base unit
- Border radius: 4px on all elements — precise, not soft
- No rounded-pill buttons. No gradient washes as decoration.
- Data density: high. Investigators need information. Do not pad generously.

**Avoid these generic patterns:**
- Cyan or acid-green as accent (this reads as generic hacker)
- Glowing neon borders
- Animated particle backgrounds
- Soft drop shadows (rgba(0,0,0,0.1)) under every card
- ALL-CAPS labels everywhere
- The "·" separator pattern between metadata strings

**What should feel distinctive:**
The amber gold accent in deep violet-black is the entire visual identity. Every other color is supporting cast. The interface should feel like an instrument — precise, purposeful, weighted. Not a dashboard for showing off. An investigation tool that knows what it is.

---

## PROMPT 1 — Main Dashboard (Command Center)

Generate the main dashboard screen for Eye of Abyss.

Reference the design system from Prompt 0 exactly.

**Screen name:** Command Center

**Layout:**
- Left navigation rail (56px): icons for Dashboard, Cases, VoiceGuard, ShadowTrace, ChainEye, Settings. The Dashboard icon is active (highlighted in `#F0A500`).
- Top bar (48px height): "Eye of Abyss" wordmark in Space Grotesk 600 on the left. On the right: officer name "Insp. R. Mehta", notification bell (3 unread, amber dot), and a small circular avatar.
- Main content area: left-aligned
- Right context panel: collapsed (no case selected yet)

**Main content — three rows:**

**Row 1 — Stat bar (4 cards, horizontal):**
Show four metric cards in a horizontal row. Each card has a number in JetBrains Mono large (40px), a label in Space Grotesk small, and a subtle trend indicator.
- Active Cases: **23** / +3 this week (amber)
- Evidence Anchored Today: **7** / Polygon confirmed (indigo)
- Synthetic Voice Alerts: **2** / Last 24h (crimson)
- Predicted Withdrawal Alerts: **1** / Action required (crimson, slightly pulsing border)

**Row 2 — Active Cases table:**
Header: "Active Cases" in Space Grotesk 600 16px, with a "New Case" button (amber outlined, not filled) on the right.

Table with these columns: Case ID (JetBrains Mono), Complainant Type, Modules Active (small icon chips — VG/ST/CE), Status, Threat Tier, Last Updated

Show 5 rows of realistic data:
- EOA-2026-0041 / Corporate Fraud / VG+CE / ANCHORED / T3 / 2 min ago (highlight this row in `#1C1929` with a left amber border — it's the selected case)
- EOA-2026-0039 / Investment Fraud / CE / EVIDENCE_SUBMITTED / T2 / 14 min ago
- EOA-2026-0037 / Voice Vishing / VG / ACTIVE / T1 / 1 hr ago
- EOA-2026-0035 / Dark Web Vendor / ST+CE / CONVERGENCE_COMPUTED / T2 / 3 hr ago
- EOA-2026-0031 / Ransomware / VG+ST+CE / FILED / T3 / Yesterday

Status badges: use pill shapes ONLY for status badges (exception to no-pill rule). Color: ANCHORED=indigo, ACTIVE=amber, FILED=green, EVIDENCE_SUBMITTED=muted text.

**Row 3 — Two panels side by side:**

Left panel (60% width): "Recent Evidence Anchors"
A timeline list showing the last 4 blockchain anchor events:
- Each row: amber diamond icon, case ID, module name, tx hash (JetBrains Mono truncated: `0x3f4a...d821`), timestamp, green "Verified" label
- Background `#13111E`, very subtle `#2A2640` dividers between rows

Right panel (40% width): "Module Status"
Three module status indicators stacked:
- VoiceGuard: green dot, "Operational", "Avg latency 148ms"
- ShadowTrace: green dot, "Operational", "Corpus: 847 actors"
- ChainEye: amber dot, "Processing", "EOA-2026-0041 — trace in progress"

---

## PROMPT 2 — ChainEye Investigation View

Generate the ChainEye module view for an active case (EOA-2026-0041).

Reference the design system from Prompt 0 exactly.

**Layout:**
- Left rail: same as dashboard, ChainEye icon now active (amber)
- Top bar: breadcrumb "Cases / EOA-2026-0041 / ChainEye" in Space Grotesk. Right side: "Submit Evidence" button (amber filled, 4px radius), "Anchor" button (indigo outlined, disabled until supervisor approves)
- Main content: two columns (65% / 35%)
- Right context panel (320px): visible, showing case summary

**Left column — Wallet Graph:**
Show a large graph visualization panel titled "Wallet Cluster Graph" in Space Grotesk 500.

The graph panel (`#13111E` background, `#2A2640` border, 4px radius):
- Central node: large amber circle labeled "SUSPECT WALLET" with address `1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2` in JetBrains Mono 10px below
- From the central node, 6 connected nodes:
  - 2 nodes labeled "BINANCE" in indigo — exchange attribution (these are rectangular/diamond shaped in indigo)
  - 2 nodes in crimson labeled "MIXER" 
  - 1 node labeled "MULE WALLET" in muted crimson
  - 1 node labeled "UNKNOWN" in muted grey
- Edge labels: BTC amounts in JetBrains Mono 9px (e.g., "0.43 BTC", "1.2 BTC")
- Graph controls bar at top-right: zoom in, zoom out, fit, export icons

Below the graph, a horizontal "Transaction Timeline" strip:
- X-axis: dates (last 30 days)
- Small bar chart showing daily inflow (indigo bars) vs outflow (amber bars)
- Red vertical line labeled "Complaint Filed" at day 22
- Amber vertical line labeled "Predicted Window" at day 28 with a shaded amber band (±12h)

**Right column — Analysis Panel:**

Section 1: "VASP Attribution" card (`#1C1929` bg)
- VASP: **Binance Global** — confidence bar in indigo (82%)
- Sub-accounts detected: 3
- KYC status: "Subpoena Required"
- Jurisdiction: "Cayman Islands"
All labels in Space Grotesk 12px text-secondary; values in Space Grotesk 14px text-primary

Section 2: "Withdrawal Prediction" card — this is the most important card, give it amber left border
- Status badge: amber "ACTION REQUIRED"
- Predicted window: **Sep 16, 02:00–04:00 UTC** in Space Grotesk 600 18px amber
- Confidence: 74% (indigo bar)
- Basis: "Dormancy cycle day 12/14 — matches T2 withdrawal pattern"
- Button: "Draft Freeze Request" — amber filled

Section 3: "Wallet Statistics" — monospace data table
Key-value pairs in JetBrains Mono:
- Total inflow: 4.73 BTC (~₹2.4 Cr)
- Cluster size: 12 wallets
- Mixer usage: Detected (Wasabi)
- Chain hop: BTC → USDT → BNB
- Oldest tx: 2026-07-14

**Right context panel (320px):**
Case summary for EOA-2026-0041:
- Complainant: Axis Bank Corporate (Redacted)
- Reported loss: ₹2.4 Cr
- Modules: VoiceGuard (complete ✓), ShadowTrace (pending), ChainEye (active)
- Case status: ACTIVE
- Convergence: "Awaiting ShadowTrace submission"
- Small "View Full Case" link in amber

---

## PROMPT 3 — VoiceGuard Live Analysis View

Generate the VoiceGuard module view showing a real-time analysis in progress.

Reference the design system from Prompt 0 exactly.

**Layout:**
- Left rail: VoiceGuard icon active
- Top bar: breadcrumb "Cases / EOA-2026-0037 / VoiceGuard". Right: "Stop Analysis" (crimson outlined), "Save Evidence" (amber filled, disabled until analysis completes)
- Main content: single wide column, centered (this is the exception — audio analysis benefits from focus)
- No right context panel on this screen

**Top section — Live status bar:**
A full-width status banner in `#1C1929` with `#2A2640` border.
Left side: pulsing crimson dot + "LIVE ANALYSIS — 02:14 elapsed" in Space Grotesk 500
Center: "EOA-2026-0037 — Vishing Call Recording" 
Right side: current verdict chip — "SYNTHETIC DETECTED" on crimson background in Space Grotesk 600, with confidence "91.4%" next to it in JetBrains Mono

**Waveform section:**
Large waveform visualization panel (`#13111E` bg, full width):
- Title: "Audio Waveform" in Space Grotesk 500
- Waveform rendered in `#8884A8` (muted default)
- Highlighted segments in crimson where synthetic was detected (three segments visible)
- Highlighted segments in green where real speech detected
- Playhead: amber vertical line at ~60% position
- Timeline labels below in JetBrains Mono 10px: 00:00, 00:30, 01:00, 01:30, 02:00, 02:14
- Below the waveform, a confidence track: a thin strip showing confidence over time — amber for uncertain, crimson for synthetic, green for real

**Middle section — Two cards side by side:**

Left card: "Segment Analysis"
Table of detected segments:
| Time | Duration | Verdict | Confidence | Type |
|---|---|---|---|---|
| 00:08 | 12s | REAL | 94% | Clean speech |
| 00:23 | 8s | SYNTHETIC | 96% | TTS |
| 00:45 | 22s | SYNTHETIC | 89% | Voice conversion |
| 01:12 | 15s | SYNTHETIC | 91% | TTS |
| 01:31 | 43s | REAL | 87% | Clean speech |

Verdicts colored: REAL in green, SYNTHETIC in crimson.

Right card: "Spectral Analysis"
Show a mel spectrogram visualization — a heatmap-style image (use a realistic looking purple-to-amber heat gradient showing frequency distribution). Label: "Mel Spectrogram — Synthetic segment 00:23"
Below it: two data points in JetBrains Mono:
- GAN artifact signature: **Detected** (crimson)
- Spectral flatness delta: **+0.34** (anomalous)

**Bottom section — Evidence Summary:**
A card with `#1C1929` background and amber left border (4px).
Title: "Analysis Summary" Space Grotesk 600
- Overall verdict: **SYNTHETIC — AI-generated voice detected** (crimson, large)
- Confidence: 91.4%
- Synthetic duration: 1m 02s of 2m 14s total (46%)
- Detected types: TTS (2 segments), Voice Conversion (1 segment)
- Model: DistilWav2Vec2 + ECAPA-TDNN ensemble
- Inference time: 162ms avg per chunk
Bottom: "Attach to Case EOA-2026-0037" amber button

---

## PROMPT 4 — ShadowTrace Actor Attribution View

Generate the ShadowTrace module view showing actor attribution results.

Reference the design system from Prompt 0 exactly.

**Layout:**
- Left rail: ShadowTrace icon active
- Top bar: breadcrumb "Cases / EOA-2026-0035 / ShadowTrace". Right: "Add to Corpus" (mist outlined), "Submit Evidence" (amber filled)
- Main content: two columns (55% left, 45% right)

**Left column:**

Section 1: "Text Sample Input" card
`#13111E` bg, `#2A2640` border. 
A textarea-style display (not an actual form — show filled content) containing sample dark web forum text:
```
lookin for buyers fr the full drop, min 50 pcs, 
verified vendors only no new accs. payment btc 
or xmr. dnt waste my time with questions check 
my prev listings. delivery in 48h max
```
Below it: metadata row in JetBrains Mono 10px text-secondary: "Source: AlphaBay Archive | Platform: Dark Web Forum | Timestamp: 2026-08-14 02:17 UTC"

Section 2: "Linguistic Fingerprint" card
Title: "Fingerprint Analysis" Space Grotesk 500
A radar/spider chart with 6 axes (render as a hexagonal radar chart in indigo with `#6B4FFF` fill at 30% opacity, `#6B4FFF` line):
- Axes: Vocabulary Richness, Syntactic Complexity, Punctuation Density, Avg Sentence Length, Code-Switching Rate, Typo Rate
- The actor's profile plotted on the radar
Below the chart: 4 key features in JetBrains Mono monospace table:
- Type-token ratio: 0.61
- Avg sentence length: 8.2 tokens
- Punctuation rate: 0.04/sentence
- Typo rate: 0.08

Section 3: "Temporal Activity Profile"
24-bar histogram (indigo bars, very compact, 4px wide bars with 2px gaps):
- Title: "Posting Activity by Hour (UTC)"
- Bars spike at hours 01:00–04:00 UTC and 21:00–23:00 UTC
- Highlighted peak with amber marker: "Peak: 02:00 UTC"
- Below: "Inferred timezone: UTC+5:30 (IST) — confidence 73%"

**Right column:**

Section 1: "Attribution Results" — the most important element
Large card with amber left border (4px).
Title: "Top Matches" Space Grotesk 600

Three match cards stacked inside:

Match 1 (top, amber-highlighted background `#2A2100`):
- Rank badge: "1" in amber
- Handle: **"d4rk_exch4nger"** JetBrains Mono 500
- Platform: AlphaBay / Telegram
- Confidence: 87% — amber filled confidence bar
- Signals: "Lexical: 91% | Syntactic: 84% | Temporal: 79%"
- Cross-platform: "AlphaBay ↔ Telegram — confirmed"

Match 2:
- Rank badge: "2" in muted text
- Handle: **"vendorX_88"** JetBrains Mono
- Platform: Hansa / IRC
- Confidence: 61% — indigo half-filled bar
- Signals: "Lexical: 67% | Syntactic: 59% | Temporal: 55%"

Match 3:
- Rank badge: "3" in muted text
- Handle: **"anonymous_drop"** JetBrains Mono
- Platform: Empire Market
- Confidence: 34% — muted grey bar

Section 2: "Actor Network Graph" (smaller, 200px height)
A compact force-directed graph:
- Central node: "d4rk_exch4nger" in amber
- 4 connected nodes: co-posters, referral links
- Edge labels: "co-posted", "referred", "transacted"
- Color: indigo edges, node size proportional to activity volume
- "Expand in full view" link bottom right in amber

Section 3: "Cross-Module Signal" card — amber border
If ChainEye has also submitted evidence on this case:
"ChainEye Correlation Detected" — amber badge
- Timezone overlap: **IST (UTC+5:30) — match**
- Activity overlap score: **0.78** 
- Operational period: **Overlap: Jul–Aug 2026**
- "View Convergence Report" amber link

---

## PROMPT 5 — Case Engine: Unified Case File View

Generate the Case Engine unified case view for a completed case ready for anchoring.

Reference the design system from Prompt 0 exactly.

**Layout:**
- Left rail: Cases icon active
- Top bar: "EOA-2026-0035" in Space Grotesk 600. Status badge: "CONVERGENCE_COMPUTED" in indigo. Right: "Anchor Evidence" (indigo filled — primary action here), "Export PDF" (muted outlined)
- Main content: full width, structured as a document-style case file
- Right context panel: visible showing anchor history

**Top — Case Header Card:**
Full-width card `#13111E`:
Left side:
- Case ID: **EOA-2026-0035** JetBrains Mono 500 large
- Complainant: Redacted (Corporate Entity)
- Reported loss: **₹47.3 Lakhs**
- Filed: 2026-08-22

Right side — 3 module status chips:
- VoiceGuard: green checkmark chip "Evidence Submitted"
- ShadowTrace: green checkmark chip "Evidence Submitted"  
- ChainEye: green checkmark chip "Evidence Submitted"

Center: large convergence score — "Convergence Confidence: **81%**" in amber, large Space Grotesk 600 24px

**Middle — Three evidence cards in a row (equal width):**

VoiceGuard Evidence Card (green left border):
- Title: "VoiceGuard" + module icon
- Verdict: "SYNTHETIC DETECTED" crimson badge
- Confidence: 91.4%
- Key finding: "AI-generated voice (TTS) confirmed in 3 call segments"
- Evidence ID: `EV-VG-2026-0891` JetBrains Mono
- Anchor status: "Pending" muted
- Artifacts: 2 (waveform, spectrogram) — small attachment icons

ShadowTrace Evidence Card (indigo left border):
- Title: "ShadowTrace" + module icon
- Attribution: "d4rk_exch4nger" JetBrains Mono amber
- Confidence: 87%
- Key finding: "Cross-platform identity confirmed — AlphaBay ↔ Telegram"
- Evidence ID: `EV-ST-2026-0445` JetBrains Mono
- Artifacts: 3 (fingerprint, graph, report)

ChainEye Evidence Card (amber left border — this is the action item):
- Title: "ChainEye" + module icon
- VASP: "Binance Global" 
- Confidence: 82%
- Key finding: "4.73 BTC traced across 12 wallets. Withdrawal window: Sep 16"
- Evidence ID: `EV-CE-2026-0312` JetBrains Mono
- Artifacts: 2 (graph, transaction log)

**Bottom — Convergence Report section:**
Full-width card `#13111E` with title "Cross-Module Convergence Report" Space Grotesk 600

Three convergence signals displayed as a structured list with indigo left markers:

Signal 1: "Timezone Alignment"
"ShadowTrace temporal profile (IST/UTC+5:30) matches ChainEye withdrawal hour distribution (peak 02:00–04:00 IST). Overlap confidence: 79%."

Signal 2: "Operational Period Overlap"
"Both ShadowTrace actor profile and ChainEye wallet activity show active periods Jul–Aug 2026. 100% period overlap."

Signal 3: "Actor Graph Link"
"ChainEye wallet `1BvBMSE...` appears in ShadowTrace actor network graph as a referenced transaction counterpart. Direct graph edge confirmed."

Bottom of convergence section: 
"Composite Convergence Confidence: **81%**" — large amber, Space Grotesk 600
"Three independent investigation tracks converge on a single actor."

Below that: "Anchor All Evidence" button — large, indigo filled, full section width.

**Right context panel — Anchor History:**
Title: "Blockchain Record"
- EOA-2026-0035 not yet anchored — shows "No anchors recorded" in empty state
- Empty state text: "Submit evidence for anchoring to create a tamper-proof record."
- Polygon Mumbai Testnet indicator: green dot "Connected"

---

## PROMPT 6 — Mobile Responsive: Active Case Alert View

Generate a mobile view (390px wide) for Eye of Abyss — specifically the alert screen an investigator sees when a withdrawal prediction fires.

Reference the design system from Prompt 0 exactly.

**Context:** An investigator receives a push notification. They open the app on mobile. They see an urgent alert requiring action.

**Layout (mobile, 390px):**
- No left rail — hamburger menu icon top-left
- Top bar: "Eye of Abyss" wordmark center, notification bell right (amber dot)
- Full-screen alert state — this screen is ALL about the one alert

**Full-bleed alert banner at top:**
Crimson background `#C92A2A` (exception — only for critical alerts).
Text: "WITHDRAWAL ALERT" Space Grotesk 600 14px white caps
Below: "EOA-2026-0041 — ChainEye" Space Grotesk 400 12px white
Amber animated pulse ring around a warning icon — the only animation on this screen

**Alert detail card (below banner):**
`#1C1929` background, amber 4px left border.
- "Predicted window opens in" — Space Grotesk 400 12px text-secondary
- **3h 42m** — JetBrains Mono 700 48px amber (countdown timer display)
- "Sep 16, 02:00–04:00 UTC" — JetBrains Mono 12px text-secondary
- Confidence: 74% — indigo compact bar

**Key data below (compact monospace list):**
```
Wallet     1BvBMSE...VN2
Amount     4.73 BTC (~₹2.4 Cr)
VASP       Binance Global
Pattern    T2 dormancy cycle
```

**Two action buttons stacked:**
1. "Draft Freeze Request" — amber filled, full width, Space Grotesk 500
2. "View Full Case" — `#2A2640` background outlined, full width

**Bottom — Recent module status (compact):**
Three horizontal chips:
- VoiceGuard ✓ (green)
- ShadowTrace — (muted, not submitted)
- ChainEye ⚠ (amber, active alert)
