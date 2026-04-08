# Mental Health Genetics & Actionable Recommendations: UX Research Report

**Date:** 2026-04-04
**Purpose:** Inform design decisions for genome-toolkit's mental health features

---

## Part 1: Mental Health Genetics — What Users Actually Want

### 1.1 The Most-Requested Genes and SNPs

Users across Reddit communities (r/23andme, r/genetics, r/Nootropics, r/biohacking) and DTC genetics forums consistently ask about a small cluster of mental-health-relevant genes:

| Gene | SNP(s) | Why Users Care |
|------|--------|----------------|
| **MTHFR** | rs1801133 (C677T), rs1801131 (A1298C) | Methylation, folate metabolism, depression risk. The single most-discussed mental health SNP in consumer genetics communities. |
| **COMT** | rs4680 (Val158Met) | "Warrior vs. Worrier" — dopamine clearance speed, stress response, anxiety tendency. Users want to know if they're slow or fast metabolizers. |
| **MAO-A** | VNTR (2R/3R/3.5R/4R/5R) | "Warrior gene" — monoamine oxidase activity, aggression, mood regulation. Frequently discussed alongside COMT. |
| **SLC6A4** (5-HTTLPR) | rs25531, VNTR | Serotonin transporter — stress sensitivity, SSRI response, depression vulnerability. |
| **BDNF** | rs6265 (Val66Met) | Brain-derived neurotrophic factor — neuroplasticity, treatment response, exercise-mood connection. |
| **MTRR / MTR** | rs1801394, rs1805087 | B12 metabolism — part of the methylation cycle, frequently asked about alongside MTHFR. |
| **GAD1** | rs3749034 | GABA synthesis — anxiety, sleep quality. |
| **APOE** | rs429358, rs7412 | Primarily Alzheimer's risk, but users also ask about cognitive decline anxiety. |

**Key pattern:** Users don't just want to know their genotype — they want to know what the *combination* of variants means. The interaction between slow COMT and low MAO-A is a frequent topic. Having slow COMT + MTHFR C677T homozygous is discussed as a "double hit" for methylation-related mood issues.

Sources:
- [Genetic Lifehacks — MTHFR C677T](https://www.geneticlifehacks.com/mthfr-c677t/)
- [Genetic Lifehacks — MAO-A](https://www.geneticlifehacks.com/maoa/)
- [Genetic Lifehacks — COMT and Supplement Interactions](https://www.geneticlifehacks.com/comt-and-supplement-interactions/)
- [xCode Life — COMT Warrior Gene](https://www.xcode.life/23andme-raw-data/genetic-variants-comt-gene/)
- [Gene Food — COMT Worrier vs Warrior](https://www.mygenefood.com/blog/comt-worrier-warrior/)

### 1.2 User Frustrations with Current Tools

**Promethease: Information overload without guidance**
- Reports show 20,000+ entries; without filters, most are noise based on weak evidence
- Primarily text-based, lacking visual aids for comprehension
- No actionable advice — users are told about risks but get zero guidance on what to do
- Technical language makes reports inaccessible to non-specialists
- Users report significant anxiety from seeing dozens of schizophrenia-risk SNPs without context about effect size or absolute risk

**23andMe: Too cautious, too limited**
- Mental health reports are deliberately vague or absent
- The company "blackboxes their representation of predicted risks" — users can't understand how scores are calculated
- Results "only become meaningful through individual users' continuous interpretive work upon the data"
- Users turn to Reddit to crowdsource interpretations because automated reports are insufficient

**SelfDecode: Better but expensive**
- Provides actionable recommendations and supplement suggestions
- Criticized for being a subscription model ($97-199/year)
- Some users question whether recommendations are truly personalized vs. generic health advice attached to genotypes

**Genetic Lifehacks: Best for deep dives, worst for overview**
- Detailed, well-referenced articles per gene
- No unified dashboard — users must read article by article
- Requires significant self-directed research to build a personal picture

**Common across all tools:**
- Users want human-like interpretation, not raw data dumps
- The gap between "here's your genotype" and "here's what to do" is the central frustration
- Users feel abandoned after receiving results — "I know I have slow COMT, now what?"

Sources:
- [Promethease Report Guide — Nucleus](https://mynucleus.com/blog/how-to-read-promethease-report)
- [SelfDecode Reviews — Innerbody](https://www.innerbody.com/selfdecode-reviews)
- [SelfDecode Review — Outliyr](https://outliyr.com/selfdecode-review)
- [JMIR — Reddit DTC Genetic Test Discussions](https://infodemiology.jmir.org/2022/2/e35702)
- [PMC — Medicalizing Risk](https://pmc.ncbi.nlm.nih.gov/articles/PMC9352100/)

### 1.3 What "Actionable" Means to Users

Based on community analysis, users define "actionable" across four tiers:

**Tier 1: Supplements and nutrition (highest demand)**
- "I have MTHFR C677T — should I take methylfolate or folinic acid?"
- "Slow COMT — should I avoid high-dose methyl donors?"
- Specific dosages, forms (methylfolate vs folic acid), and timing
- Food sources: folate-rich foods, choline sources, B12 forms

**Tier 2: Lifestyle modifications**
- Exercise recommendations matched to BDNF/COMT genotype
- Stress management strategies for slow COMT/short 5-HTTLPR
- Sleep optimization based on genetic chronotype and GABAergic variants
- Caffeine and alcohol guidance based on metabolism genes

**Tier 3: Doctor talking points**
- "What should I ask my psychiatrist about my COMT status?"
- Pharmacogenomics: "Which SSRIs work better for my SLC6A4 genotype?"
- Users want a printable summary to bring to appointments
- GeneSight-style medication compatibility information is highly desired

**Tier 4: Monitoring and tracking**
- Which biomarkers to test (homocysteine for MTHFR, catecholamines for COMT)
- How often to retest
- What symptom changes to watch for when implementing changes

**The pharmacogenomics demand is intense.** Users consistently ask which psychiatric medications will work for them based on their genetics. GeneSight and Genomind are the main clinical tools, but users want this information integrated with their DTC data. A meta-analysis found patients who underwent pharmacogenetic testing for depression were nearly twice as likely to achieve remission compared to treatment-as-usual.

Sources:
- [NAMI — Pharmacogenomic Testing](https://www.nami.org/treatments-and-approaches/mental-health-medications/pharmacogenomic-testing/)
- [GeneSight](https://genesight.com/)
- [Genomind — Pharmacogenetics Explained](https://genomind.com/patients/explained-what-is-pharmacogenetics-for-mental-health-treatment/)
- [Psychiatric News — Pharmacogenomic Testing Outcomes](https://psychiatryonline.org/doi/full/10.1176/appi.pn.2022.08.8.47)
- [SelfDecode — Nootropics and Genetics](https://selfdecode.com/en/pages/nootropics-genetics-cognitive-performance/)

### 1.4 Privacy Concerns Specific to Mental Health Genetics

Mental health genetic data carries unique privacy risks that users actively discuss:

**Legal gaps:**
- GINA protects against discrimination by health insurers and employers
- GINA does NOT cover life insurance, disability insurance, or long-term care insurance
- Life insurers can legally ask if you've had genetic testing and make coverage decisions based on results
- Only 8.8-20% of patients are aware GINA even exists

**User-specific concerns:**
- Mental health genetic markers carry social stigma beyond physical health markers
- Users worry about data breaches exposing psychiatric risk profiles
- Concerns about employer access if genetic data is linked to health records
- 23andMe's 2023 data breach heightened anxiety about DTC genetic data security
- Users on Reddit frequently discuss using pseudonyms and separate email accounts for genetic testing

**Design implication:** Any mental health genetics tool must prominently address data handling, clearly explain what GINA does and does not cover, and provide options for local-only data processing.

Sources:
- [PMC — GINA Awareness and Discrimination Concerns](https://pmc.ncbi.nlm.nih.gov/articles/PMC9165621/)
- [MIT Technology Review — Genetic Discrimination Safeguards](https://www.technologyreview.com/2024/07/19/1095120/why-we-need-safeguards-against-genetic-discrimination/)
- [23andMe — GINA FAQ](https://customercare.23andme.com/hc/en-us/articles/202907860)
- [Genetic Lifehacks — Privacy and Your Genes](https://www.geneticlifehacks.com/privacy-and-your-genes/)
- [Genetic Data Governance Policy Recommendations](https://arxiv.org/html/2502.09716v1)

---

## Part 2: How Users Want Actionable Recommendations Presented

### 2.1 Risk Communication Formats — What Works

Research and user feedback point to clear preferences:

**What users prefer:**
- **Narrative explanations with visual support** beat raw numbers. "You have a variant that slows dopamine clearance, which may make you more sensitive to stress but also more focused in calm environments" is better than "rs4680 A/A, OR 1.3 for anxiety"
- **Categorized severity** (Noteworthy vs. Less Noteworthy, as FoundMyFitness uses) helps users triage
- **Multiple numerical formats together** improve comprehension: "25% chance" alongside "25 in 100" alongside a visual icon array
- **Traffic light systems** are intuitive but must be used carefully — red/yellow/green implies medical urgency that may not be appropriate for polygenic risk

**What causes harm:**
- Raw odds ratios without context (users misinterpret OR 1.2 as "20% chance of getting the disease")
- Long undifferentiated lists (Promethease's 20,000 entries)
- Medical jargon without plain-language equivalents
- Presenting risk without presenting absolute baseline rates

**Best practice from research:**
- Risk figures should use smaller denominators (100 vs 10,000) for comprehensibility
- The most important finding should be the first thing the eye is drawn to
- Technical methodology details should be separated from the main message
- Condensed education (brief, focused) performs as well as extended education for comprehension and causes no additional anxiety

Sources:
- [PMC — Recommendations for Designing Genetic Test Reports](https://pmc.ncbi.nlm.nih.gov/articles/PMC7316722/)
- [PMC — Communicating Genetic Information: Health Literacy](https://pmc.ncbi.nlm.nih.gov/articles/PMC2909377/)
- [PMC — Communicating Genetic Risk in Genomic Medicine Era](https://pmc.ncbi.nlm.nih.gov/articles/PMC3862080/)

### 2.2 How Existing Tools Present Recommendations

**FoundMyFitness (Rhonda Patrick)**
- Curated, focused report — only SNPs with meaningful health impact
- Two-tier organization: "Noteworthy" (act on this) and "Less Noteworthy" (normal)
- Detailed scientific references per variant
- Science-heavy language but still accessible to motivated laypeople
- Strength: focused curation. Weakness: no personalized action plans

**SelfDecode**
- Dashboard with body diagram showing exclamation points at risk areas
- Trait reports as clickable cards
- Recommendations prioritized by "likelihood of impact" from genetic data
- Integrates genetics + lab results + lifestyle for multi-layered recommendations
- User-friendly language with simple explanations
- Subscription model enables ongoing, updated recommendations

**Promethease**
- Raw data dump organized by magnitude score and frequency
- Color-coded entries (green = good, red = bad, gray = neutral)
- Magnitude score (0-10) attempts to show importance
- No actionable recommendations — information only
- Filters available but require user knowledge to configure
- $12 one-time cost is accessible

**Genetic Lifehacks**
- Article-based format with "Lifehacks" section per gene
- Members see personalized genotype inline with recommendations
- Supplement suggestions with specific forms and dosages
- Lifestyle modifications with scientific rationale
- Strongest evidence citations of any consumer tool

**StrateGene (Seeking Health / Dr. Ben Lynch)**
- Pathway-based visualization (methylation cycle diagrams)
- Shows how genes interact in biochemical pathways
- Color-coded enzyme function speed
- Supplement recommendations tied to pathway bottlenecks

### 2.3 UX Formats That Get Best Engagement

From health app research and genetic tool user feedback:

**Highest engagement:**
1. **Priority-ranked action cards** — "Your top 3 things to focus on" with expandable detail
2. **Checklists with progress tracking** — users want to mark actions as done
3. **Dashboard with body/system overview** — visual entry point to detailed reports
4. **Tiered urgency system** — "Act now" / "Discuss with doctor" / "Monitor over time"

**Medium engagement:**
- Detailed gene-by-gene reports (for deep-dive users)
- Comparison tables (your genotype vs. population)
- Timeline-based recommendations ("Week 1: start folate, Week 4: retest homocysteine")

**Low engagement:**
- Dense text reports without visual hierarchy
- Raw data tables
- PDFs without interactive elements

**Critical finding from health app research:** Thoughtful UX design can increase patient engagement by up to 60% and improve medication adherence by up to 40%. Smart reminders, gamified progress, and behavior nudges without being intrusive are key patterns.

Sources:
- [Diversido — UX/UI Impact on Wellness Apps](https://www.diversido.io/blog/how-does-ux-ui-impact-your-wellness-app/)
- [Eleken — Healthcare UI Design 2026](https://www.eleken.co/blog-posts/user-interface-design-for-healthcare-applications)
- [FoundMyFitness — Genetics](https://www.foundmyfitness.com/genetics)
- [SelfDecode — Health Overview Report](https://selfdecode.com/en/health-overview-report/)
- [FoundMyFitness Review — Nebula](https://nebula.org/blog/foundmyfitness-review/)
- [SelfDecode Review — My Gene Food](https://www.mygenefood.com/blog/self-decode-review-why-i-trust-the-platform/)

### 2.4 Communicating Severity Without Causing Anxiety

This is the hardest UX challenge in mental health genetics. Key principles from research:

**Language framing:**
- Use "increased tendency" not "risk of disorder"
- Use "your variant is associated with" not "you are predisposed to"
- Frame protective factors equally prominently as risk factors
- Always include: "This variant is one of many factors. Environment, lifestyle, and other genes all play roles."

**Visual design:**
- Avoid pure red for risk indicators — use amber/warm tones instead
- Always pair a risk indicator with an action indicator
- Never show a warning without showing a mitigation path
- Use gradient scales (spectrum) rather than binary good/bad categories

**Contextual anchoring:**
- Show population frequency: "30% of people carry this variant" normalizes the finding
- Show effect size context: "This variant increases risk by a small amount (1.2x) compared to variants that increase risk substantially (5-10x)"
- Separate statistical significance from clinical significance

**Progressive disclosure:**
- Summary layer: plain-language sentence + action suggestion
- Detail layer: genotype, population data, effect size
- Evidence layer: study references, sample sizes, replication status
- Let the user control how deep they go

**What NOT to do (lessons from Promethease anxiety incidents):**
- Never list all risk variants for a serious psychiatric condition without context
- Never show odds ratios without explaining baseline population risk
- Never present genetic risk as deterministic
- Never leave a risk finding without at minimum a "learn more" path to coping strategies

Sources:
- [UXMatters — Designing for Mental Health](https://www.uxmatters.com/mt/archives/2023/06/designing-for-mental-health-creating-user-experiences-that-support-well-being.php)
- [Halo Lab — UX in Reducing Anxiety](https://www.halo-lab.com/blog/the-role-of-ux-in-reducing-anxiety)
- [PMC — Health Literacy in Genomic Era](https://pmc.ncbi.nlm.nih.gov/articles/PMC12463499/)
- [PMC — Clinician Conceptualization of Actionability](https://pmc.ncbi.nlm.nih.gov/articles/PMC9959215/)

### 2.5 The Role of Evidence Quality in User Trust

Users of genetic tools are increasingly savvy about evidence quality. Key findings:

**What builds trust:**
- Showing the number of studies behind each claim
- Distinguishing between genome-wide significant findings and candidate gene studies
- Citing specific papers, not just "research shows"
- Acknowledging when evidence is preliminary or conflicting
- Showing when a finding has been replicated across populations

**What erodes trust:**
- Presenting all findings with equal confidence regardless of evidence quality
- Making definitive supplement recommendations based on a single small study
- Claiming gene-disease associations that have not replicated
- Not disclosing conflicts of interest (e.g., selling the supplements being recommended)

**Tiered evidence system (recommended):**
- **Strong evidence**: Multiple large studies, GWAS-significant, clinical guidelines exist
- **Moderate evidence**: Several studies, consistent direction, not yet in guidelines
- **Preliminary evidence**: Small studies, candidate gene approach, needs replication
- **Theoretical/Mechanistic**: Biological plausibility but limited human outcome data

The ClinGen actionability framework provides a standardized protocol: it assesses severity of outcome, likelihood of disease, effectiveness of intervention, and nature of intervention (medical vs. lifestyle) to produce a composite actionability score.

Sources:
- [NCBI — Evidence Framework for Genetic Testing](https://www.ncbi.nlm.nih.gov/books/NBK425809/)
- [ClinGen — Actionability Protocol](https://www.sciencedirect.com/science/article/pii/S1098360021014180)
- [PMC — Clinician Actionability Conceptualization](https://pmc.ncbi.nlm.nih.gov/articles/PMC9959215/)
- [Precision Medicine Advisors — Evaluating Genetic Tests](https://www.precisionmedicineadvisors.com/precisionmedicine-blog/2019/8/2/how-to-evaluate-health-related-genetic-tests)

---

## Part 3: Design Implications for Genome-Toolkit

### 3.1 Core Design Principles

Based on this research, the following principles should guide mental health genetics features:

1. **Never show risk without showing a path forward.** Every risk finding must be paired with at least one actionable suggestion, even if it's "discuss with your doctor."

2. **Use progressive disclosure.** Summary > Detail > Evidence. Let users control depth. Default to the reassuring, contextualized summary layer.

3. **Separate signal from noise.** Curate like FoundMyFitness, not dump like Promethease. Show the 10-20 mental health SNPs that matter most, not hundreds of marginal associations.

4. **Make evidence quality visible.** Use a tiered badge system (Strong / Moderate / Preliminary) on every recommendation. Users trust tools that are honest about uncertainty.

5. **Address privacy proactively.** Explain GINA coverage and gaps. Process data locally where possible. Never store mental health genetic interpretations on remote servers without explicit consent.

6. **Design for the anxious user.** Assume the person reading their mental health genetics report is already worried. Use warm language, normalize common variants, emphasize polygenicity and environmental factors.

### 3.2 Recommended Feature Architecture

**Mental Health Overview Dashboard**
- Body/brain system diagram (similar to SelfDecode) as entry point
- 3-5 "headline findings" as cards with plain-language summaries
- Color coding: blue spectrum (calm tones) rather than red/green traffic lights
- Each card shows: gene name, your variant, one-sentence meaning, evidence tier badge

**Gene Detail Pages**
- Genotype display with population frequency context
- "What this means for you" narrative paragraph
- Expandable "The Science" section with study references
- Related genes section (e.g., COMT page links to MAO-A and MTHFR)

**Action Plan**
- Priority-ranked recommendations grouped by type:
  - "Consider" (supplements, nutrition) — with specific forms and dosages
  - "Try" (lifestyle changes) — with concrete suggestions
  - "Discuss" (pharmacogenomics, clinical testing) — with doctor talking points
  - "Monitor" (biomarkers to track) — with target ranges
- Checklist format with progress tracking
- Printable "Doctor Visit Summary" one-pager

**Pharmacogenomics Section**
- Separate section with clear disclaimers
- Show metabolism speed for common psych med categories (SSRIs, SNRIs, antipsychotics)
- Frame as "conversation starters with your prescriber" not as prescriptive guidance
- Link to clinical PGx resources (GeneSight, Genomind)

**Evidence & Methodology**
- Dedicated page explaining how evidence tiers work
- Per-finding: number of studies, total sample size, replication status
- Acknowledge conflicting evidence where it exists
- Date-stamp recommendations so users know how current the information is

### 3.3 What NOT to Build

- Do not build a Promethease-style data dump for mental health SNPs
- Do not assign letter grades (A/B/C/F) to mental health genetic profiles — too reductive and stigmatizing
- Do not make definitive claims about psychiatric diagnosis based on SNPs
- Do not recommend specific psychiatric medications — only metabolism information
- Do not use red color coding for mental health risk indicators
- Do not present polygenic risk scores for psychiatric conditions without extensive context about their current limitations

### 3.4 Competitive Differentiation Opportunities

| Gap in Market | Opportunity |
|---------------|-------------|
| No tool shows gene *interactions* clearly | Build a "gene interaction map" showing how COMT + MAO-A + MTHFR interact |
| PGx data locked in clinical tools | Surface basic metabolism information from DTC raw data with appropriate caveats |
| Privacy is an afterthought everywhere | Make local-first processing a headline feature |
| No tool tracks outcomes | Add symptom/supplement tracking to close the feedback loop |
| Evidence quality hidden or absent | Make evidence tiers a first-class UI element |
| No tool provides printable doctor summaries | Generate concise clinical-facing summaries for appointments |

---

## Appendix: Key Sources

### Academic / Clinical
- [Recommendations for Designing Genetic Test Reports (European Journal of Human Genetics)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7316722/)
- [Communicating Genetic Information: Health Literacy Considerations](https://pmc.ncbi.nlm.nih.gov/articles/PMC2909377/)
- [How Clinicians Conceptualize Actionability in Genomic Screening](https://pmc.ncbi.nlm.nih.gov/articles/PMC9959215/)
- [ClinGen Actionability Protocol](https://www.sciencedirect.com/science/article/pii/S1098360021014180)
- [NCBI Evidence Framework for Genetic Testing](https://www.ncbi.nlm.nih.gov/books/NBK425809/)
- [GINA Awareness and Discrimination Concerns](https://pmc.ncbi.nlm.nih.gov/articles/PMC9165621/)
- [Third-Party Genetic Interpretation Tools: Consumer Motivation](https://pmc.ncbi.nlm.nih.gov/articles/PMC6612532/)
- [NAMI — Pharmacogenomic Testing](https://www.nami.org/treatments-and-approaches/mental-health-medications/pharmacogenomic-testing/)

### Industry / Product Reviews
- [SelfDecode Reviews — Innerbody (2026)](https://www.innerbody.com/selfdecode-reviews)
- [SelfDecode Review — Outliyr (2026)](https://outliyr.com/selfdecode-review)
- [FoundMyFitness Genetics](https://www.foundmyfitness.com/genetics)
- [Genetic Lifehacks — MTHFR](https://www.geneticlifehacks.com/mthfr/)
- [Genetic Lifehacks — COMT Supplements](https://www.geneticlifehacks.com/comt-and-supplement-interactions/)
- [Genetic Lifehacks — MAO-A](https://www.geneticlifehacks.com/maoa/)
- [GeneSight](https://genesight.com/)
- [Genomind — Pharmacogenetics](https://genomind.com/patients/explained-what-is-pharmacogenetics-for-mental-health-treatment/)

### UX / Design
- [UXMatters — Designing for Mental Health](https://www.uxmatters.com/mt/archives/2023/06/designing-for-mental-health-creating-user-experiences-that-support-well-being.php)
- [Halo Lab — UX in Reducing Anxiety](https://www.halo-lab.com/blog/the-role-of-ux-in-reducing-anxiety)
- [Eleken — Healthcare UI Design 2026](https://www.eleken.co/blog-posts/user-interface-design-for-healthcare-applications)
- [Diversido — UX/UI Wellness App Impact](https://www.diversido.io/blog/how-does-ux-ui-impact-your-wellness-app/)
- [mHAT — Mobile Health App Trustworthiness](https://pmc.ncbi.nlm.nih.gov/articles/PMC7404005/)

### Privacy / Policy
- [MIT Technology Review — Genetic Discrimination Safeguards (2024)](https://www.technologyreview.com/2024/07/19/1095120/why-we-need-safeguards-against-genetic-discrimination/)
- [Genetic Data Governance Policy Recommendations (2025)](https://arxiv.org/html/2502.09716v1)
- [Genetic Lifehacks — Privacy and Your Genes](https://www.geneticlifehacks.com/privacy-and-your-genes/)
