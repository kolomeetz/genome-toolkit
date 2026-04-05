# Mental Health & Harm Reduction UX — Design Spec

**Date:** 2026-04-04
**Status:** Approved
**Scope:** Mental health dashboard, action cards, PGx panel, gene interaction map, harm reduction, mortality landscape, psychiatric conditions, export

**Mockups:** `.superpowers/brainstorm/` — 5 screens designed and approved:
1. `01-mental-health-dashboard.html` — Interwoven narrative + card grid
2. `02-pgx-panel.html` — Drug metabolism with substance coverage
3. `03-addiction-profile.html` — Reward sensitivity + per-substance harm reduction
4. `04-risk-landscape.html` — Mortality causes with inline-expandable gene details
5. `05-condition-gad.html` — Psychiatric condition view (GAD example)

---

## 1. Core Principles

### 1.1 Design for the anxious user
Assume the person reading their mental health genetics report is already worried. Every screen must feel safe before it feels informative.

### 1.2 Never show risk without a path forward
Every finding that requires attention must be paired with at least one actionable suggestion — supplement, lifestyle change, doctor talking point, or biomarker to monitor.

### 1.3 Drug-friendly, non-judgmental
The product supports honest conversation about substance use. No stigmatizing language ("abuse", "clean/dirty"). Harm reduction framing: "if you use X, here's what your genetics mean for you." This is a core product value, not an edge case.

### 1.4 Privacy enables trust
Local-first processing. Mental health genetic interpretations and substance use data never leave the user's machine. This is what makes honest self-reporting possible.

### 1.5 Evidence quality is visible
Every recommendation carries an evidence tier badge (E1-E5) with study count and review date. Users trust tools that are honest about uncertainty.

---

## 2. Emotional Tone — Adaptive

Warm earth-tone base (current genome_toolkit theme), with context-sensitive shifts:

| Context | Tone | Palette emphasis |
|---------|------|-----------------|
| Mental health findings | Supportive, normalizing | Amber, green, warm gray |
| PGx / drug metabolism | Clinical, precise | Blue, structured |
| Harm reduction / substances | Non-judgmental, practical | Neutral, direct |
| Action plans | Empowering, optimistic | Green, amber |
| Safety-critical (PGx contraindications) | Clear, urgent | Red (only context where red appears) |

---

## 3. Color System

- **Amber / terracotta (#c4724e)** — "Actionable" — you can do something about this
- **Warm gold (#c49a4e)** — "Monitor" — worth knowing, no immediate action needed
- **Sage green (#5a8a5e)** — "Optimal" — protective factor, good news
- **Muted gray (#9a968e)** — "Neutral" — no clinical significance
- **Deep red (#b84a4a)** — "Safety-critical" — ONLY for PGx contraindications where a substance/medication + genotype combination creates real danger. Never used for tendency/risk findings in mental health.

Red never appears on the mental health dashboard for non-dangerous findings.

---

## 4. Mental Health Dashboard

### 4.1 Layout: Interwoven Narrative + Card Grid

Narrative blocks and gene card groups alternate vertically. Each narrative segment gives context and meaning to the cards that follow it. Cards are grouped by biochemical pathway.

Structure:
```
[Narrative: "Your methylation pathway shows reduced activity..."]
  [MTHFR card] [COMT card]

[Narrative: "Your serotonin and neuroplasticity pathways look good..."]
  [SLC6A4 card] [BDNF card]

[Narrative: "Your monoamine regulation shows moderate reduction..."]
  [MAO-A card] [Gene interaction teaser → Mermaid diagram]
```

### 4.2 Narrative Blocks

Styled with colored top tab label (pathway name), rich text body, priority summary, and gene/action count. Inspired by B-layout design from brainstorm. Not a boring label — a real content panel with personality.

Content is AI-generated from the user's vault notes and genotype data, regenerable on demand. Dated for freshness.

### 4.3 Gene Cards

Each card shows:
- Gene name + variant notation + rsID
- One-sentence plain-language meaning
- Status indicator (colored border: amber/gold/green/gray)
- Evidence tier badge (E1-E5 + study count)
- Action count ("2 actions available")

Cards are:
- Draggable (user reorders by priority)
- Filterable by category (Mood / Stress / Sleep / Focus) and by action type (Consider / Monitor / Discuss / Try)
- Clickable — expands to full detail with progressive disclosure

### 4.4 Filters

Two filter dimensions, combinable:
- **Category:** All / Mood / Stress / Sleep / Focus
- **Action type:** All / Consider / Monitor / Discuss / Try

Export (PDF and Markdown) respects active filters — exports only the currently filtered view.

---

## 5. Action Cards (Expanded Gene Detail)

When a gene card is clicked, it expands to show:

### 5.1 Gene Header
Gene name, variant, rsID, chromosome position, evidence tier badge.

### 5.2 Genotype Display
Two panels side by side:
- **Your genotype:** large genotype text (e.g., "T/T"), enzyme activity percentage, zygosity
- **Population:** frequency context ("~10% of Europeans carry this"), ancestry notes

### 5.3 Narrative Explanation
Plain-language paragraph. Blue left-border accent. Explains what this gene does, what the variant means functionally, and normalizes the finding.

### 5.4 Recommended Actions
Each action is a full card (not a label) with:
- **Type badge:** Consider (amber border) / Monitor (gold) / Discuss (blue) / Try (green)
- **Title:** what to do
- **Detail:** expandable — specific form, dosage, timing, interactions, doctor talking points
- **Checkbox:** mark as done (tracked)
- **Evidence tags:** tier + study count + category tags
- **Interaction warnings:** e.g., "if you also have slow COMT, switch to folinic acid"

### 5.5 Gene Interactions
Links to related genes. "MTHFR + COMT: methylation bottleneck." Opens Mermaid-based pathway diagram (v1) or Cytoscape.js interactive map (future).

### 5.6 Evidence Footer
Source count, last review date, "View all references" link. Export buttons: "Print for doctor", "Export PDF", "Export MD".

---

## 6. Pharmacogenomics Panel

### 6.1 Tone Shift
Clinical Companion mode. More structured, more precise. Disclaimer bar at top: "This is not medical advice. Always discuss medication changes with your prescriber."

### 6.2 Enzyme Cards
Each metabolizer enzyme (CYP2D6, CYP2C19, CYP2C9, CYP3A4, CYP1A2, CYP2B6, CYP2A6, etc.) gets a card with:
- Star allele notation
- **Metabolizer speed bar** — horizontal gradient (Poor → Intermediate → Normal → Ultrarapid) with dot marker at user's position
- Metabolizer phenotype label
- Plain-language explanation

### 6.3 Drug Impact Cards
Below each enzyme, full-width cards with colored left border:
- **Green border:** standard dosing expected
- **Amber border:** may need dose adjustment
- **Red border:** safety-critical, discuss with prescriber

Each card has: drug class name, explanation, specific drugs listed, and interaction notes. Dark readable text (#3a3a38), color only in border and status label.

### 6.4 Substance Coverage
PGx covers the full spectrum of what a user may actually take:

**Prescription:**
- SSRIs, SNRIs, antipsychotics, benzodiazepines (alprazolam/Xanax, diazepam, clonazepam), opioids, stimulant medications

**Recreational / self-administered:**
- Alcohol (ALDH2, ADH1B)
- Cannabis (CYP2C9, CYP3A4)
- Nicotine (CYP2A6)
- Cocaine (CYP3A4, butyrylcholinesterase)
- MDMA / amphetamines (CYP2D6)
- Psilocybin (MAO-A, CYP2D6, UGT)
- LSD (CYP2D6, CYP3A4)
- Ketamine (CYP2B6, CYP3A4) — dual framing: recreational + therapeutic (depression)
- GHB (ALDH)
- Benzodiazepines (Xanax etc.) in recreational context too

**Critical interaction warnings:**
- SSRI + MDMA + slow CYP2D6 = serotonin syndrome risk
- Benzodiazepines + alcohol + CYP3A4 status
- MAO-A variants + psychedelics (especially ayahuasca/DMT)
- Cocaine + CYP2D6 substrates
- Ketamine + CYP2B6 poor metabolizer

### 6.5 Filters
- By drug category: Antidepressants / Pain / Cardio / Substances / All
- "Safety notes only" filter
- Export respects filters

### 6.6 Print for Prescriber
Generates a clean, clinical one-page summary. Substance use section is opt-in for this export (user controls whether to include it).

---

## 7. Addiction Profile Section

### 7.1 Framing
Not "you are prone to addiction." Instead: "your reward and dopamine pathways work this way, here's what that means for sensitivity and risk."

### 7.2 Genes Covered
- DRD2 (dopamine receptors — reward sensitivity)
- OPRM1 (opioid receptors)
- GABRA2 (GABA receptors — alcohol/benzo sensitivity)
- COMT (dopamine clearance — already on mental health dashboard, cross-linked)
- SLC6A3 / DAT1 (dopamine transporter)
- ADH1B / ALDH2 (alcohol metabolism)
- CYP2A6 (nicotine metabolism)
- ANKK1/TaqIA (dopamine receptor density)

### 7.3 Content
- Genetic predisposition awareness without determinism
- Harm reduction recommendations tied to genotype
- "If you use X, consider monitoring Y"
- Interaction with current medications
- Links to relevant PGx cards

### 7.4 Language
- "substance use" not "abuse"
- "person who uses" not "addict" (unless user self-identifies)
- "harm reduction" not "quit using"
- "your sensitivity to X" not "your risk of addiction to X"

---

## 8. Psychiatric Conditions Section

### 8.1 Philosophy
Same as harm reduction: non-stigmatizing, non-deterministic, empowering. Genetics is one factor among many — environment, life events, and lifestyle all play major roles. Frame genetic findings as context for understanding, not as diagnosis or prediction.

### 8.2 Conditions Covered (by prevalence)

**Tier 1 — Most common, highest demand:**
- **Generalized Anxiety Disorder (GAD)** — COMT, SLC6A4, GABRA2, GAD1, CRHR1, FKBP5
- **Major Depressive Disorder (MDD)** — SLC6A4, MTHFR, BDNF, FKBP5, TPH2, HTR2A
- **ADHD** — DRD4, DAT1/SLC6A3, COMT, SNAP25, ADRA2A

**Tier 2 — Common, significant genetic component:**
- **Bipolar Disorder** — CACNA1C, ANK3, CLOCK, BDNF, COMT
- **PTSD** — FKBP5, CRHR1, ADCYAP1R1, SLC6A4, COMT
- **OCD** — SLC6A4, HTR2A, COMT, SLC1A1 (glutamate transporter)
- **Insomnia / Sleep Disorders** — PER2, CRY1, CLOCK, ADA, GABRA2

**Tier 3 — Less common but high user interest:**
- **Autism Spectrum** — SHANK3, NRXN1, CNTNAP2, OXTR
- **Schizophrenia** — COMT, DISC1, NRG1, DTNBP1 (present with extreme care — see 8.4)

### 8.3 Per-Condition View

Each condition gets a dedicated page accessible from the dashboard:
- **Plain-language overview:** what the condition is, how common it is, heritability estimate
- **Relevant genes:** cards for each gene with the user's genotype and what it means in this context
- **Gene interactions:** how variants combine (e.g., slow COMT + short 5-HTTLPR for anxiety)
- **What you can do:** action cards filtered to this condition — supplements, lifestyle, doctor talking points
- **PGx relevance:** which medications are commonly prescribed, linked to user's metabolizer status
- **Evidence context:** "Genetics explains ~30-40% of anxiety risk. These variants are part of that picture, not the whole story."
- **Resources:** links to evidence-based resources (not crisis lines plastered everywhere — but available if user looks)

### 8.4 Sensitive Conditions — Extra Care

For conditions with high stigma (schizophrenia, bipolar, personality disorders):
- Always lead with heritability context and polygenicity
- Never present as predictive or diagnostic
- Show population frequency of each variant to normalize
- Emphasize that carrying risk variants is extremely common and most carriers never develop the condition
- Progressive disclosure: summary is reassuring, detail is available for those who want it
- No aggregate "risk score" — show individual gene contributions only

### 8.5 Language Patterns

- "Variants associated with" not "risk genes for"
- "May contribute to tendency toward" not "predisposes you to"
- "People with your genotype sometimes report" not "you will experience"
- "This is one piece of a complex picture" — always
- Name the condition directly (no euphemisms) but frame genetics as context, not destiny

---

## 9. Mortality & Risk Landscape

### 9.1 Concept
Show the user the top causes of mortality for their demographic, then overlay their personal genetic risk factors. This turns abstract gene data into concrete, personally relevant context: "Here's what statistically kills people like you, and here's where your genetics put you relative to average."

### 9.2 Mortality Causes (by demographic)
Based on WHO/CDC data, adjusted for user's age, sex, and ancestry (from genetics.population setting):

1. Cardiovascular disease — APOE, PCSK9, LPA, LDLR, 9p21, MTHFR (homocysteine)
2. Cancer (by type) — BRCA1/2, CHEK2, APC, MLH1, TP53, MUTYH
3. Cerebrovascular disease (stroke) — APOE, Factor V Leiden, MTHFR, ACE
4. Chronic respiratory disease — SERPINA1 (alpha-1 antitrypsin), CHRNA3/5 (nicotine dependence link)
5. Diabetes (Type 2) — TCF7L2, PPARG, KCNJ11, FTO, SLC30A8
6. Alzheimer's / dementia — APOE, TREM2, CLU, PICALM
7. Accidents / substance-related — links to addiction profile + PGx panel
8. Suicide — links to psychiatric conditions section (SLC6A4, BDNF, TPH2) — handle with extreme care (see 9.4)
9. Liver disease — ALDH2, ADH1B, PNPLA3, HFE
10. Kidney disease — APOL1, PKD1/2

### 9.3 Personal Risk Overlay
For each mortality cause:
- **Your genetic factors:** which relevant variants you carry, with status (actionable / monitor / optimal / neutral)
- **What you can do:** linked action cards from the recommendation system
- **What to test:** relevant biomarkers (lipid panel for cardio, HbA1c for diabetes, etc.)
- **Color:** amber if you have actionable variants, green if optimal, gray if no data. Never red — this is a landscape view, not an alarm panel.

### 9.4 Sensitive Handling
- Suicide as mortality cause: present only the genetic context (serotonin transport, BDNF) without "risk scoring." Link to psychiatric conditions section. Include a subtle, non-intrusive link to crisis resources — not plastered across the screen, but findable.
- Cancer findings: link to appropriate screening guidelines, not predictions. "Consider discussing BRCA screening with your doctor" not "you have elevated cancer risk."
- Frame the entire section as: "knowledge is power — knowing where to focus attention lets you take informed action."

### 9.5 Presentation
A ranked list (or bar chart) of mortality causes with the user's genetic relevance highlighted beside each. Could be a horizontal bar with population average on one side and personal genetic factors on the other. Filterable — user can focus on a specific cause to see all relevant genes and actions.

---

## 10. Gene Interaction Map

### 10.1 V1: Mermaid Diagrams
Static but clear pathway diagrams rendered via Mermaid. Already supported in Obsidian and markdown export. Zero frontend dependencies.

Content:
- Methylation pathway (MTHFR → methyl donors → COMT)
- Neurotransmitter clearance (COMT + MAO-A)
- Serotonin pathway (SLC6A4 + MAO-A)
- Substance interaction flows (substance → enzyme → effect)

Diagrams are embedded in gene detail views and exportable.

### 10.2 Future: Cytoscape.js Interactive Map
Force-directed node graph as overview. Click edge → circuit diagram. Substance nodes as inputs. Low priority — implement after core dashboard is stable.

---

## 9. Export System

### 10.1 PDF Export
- Print-friendly layout, clean typography
- Respects active filters (category + action type)
- "Print for prescriber" variant: clinical language, structured, substance section opt-in
- Uses existing Eisvogel + EB Garamond PDF pipeline

### 10.2 Markdown Export
- Obsidian-compatible with wikilinks
- Respects active filters
- Frontmatter with metadata (date, filters applied, evidence tiers)

### 10.3 What Gets Exported
Only the currently visible/filtered content. If user filters to "Discuss" actions only, export contains only those. This makes "print for doctor" = filter to Discuss → export PDF.

---

## 11. Technical Approach

### 11.1 Frontend
- React components within existing genome_toolkit frontend
- New route/view for Mental Health Dashboard
- Cytoscape.js deferred to v2; Mermaid for v1 interaction diagrams
- Drag-and-drop: use existing @tanstack patterns or lightweight dnd library

### 11.2 Backend
- AI narrative generation via existing Claude Agent SDK chat endpoint
- New MCP tools for mental health queries (query by pathway, by action type)
- Vault integration: read gene notes, systems notes, phenotype notes for narrative context

### 11.3 Data
- Gene-action mappings stored in vault notes (existing Genes/ directory)
- Evidence tiers from existing evidence_tiers.yaml
- PGx data from CPIC/DPWG guidelines (new data source to integrate)
- Substance metabolism data (new dataset needed)

---

## 12. What NOT to Build

- No Promethease-style data dumps for mental health
- No letter grades (A/B/C/F) for mental health profiles
- No definitive claims about psychiatric diagnosis from SNPs
- No prescription recommendations — only metabolism information
- No red color on mental health dashboard for non-dangerous findings
- No polygenic risk scores for psychiatric conditions without extensive caveats
- No judgmental language about substance use
- No emoji anywhere

---

## 13. Implementation Priority

1. **Evidence & color system** — badges, color scale, evidence footer (foundation for everything)
2. **Gene cards + narrative blocks** — interwoven dashboard layout
3. **Action cards** — expanded detail with recommendations, checklists, filters
4. **Psychiatric conditions** — GAD, MDD, ADHD views with gene context and PGx links
5. **PGx panel** — metabolizer bars, drug cards, substance coverage
6. **Harm reduction / addiction profile** — substance interactions, non-judgmental framing
7. **Mortality & risk landscape** — top mortality causes with personal genetic overlay
8. **Export** — PDF + MD with filter-aware output
9. **Mermaid interaction diagrams** — pathway visualizations
10. **Cytoscape.js interactive map** — future, low priority
