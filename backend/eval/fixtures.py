"""Fixed, hand-written labelled data for the ranking eval.

50 synthetic-but-realistic paper records (title + abstract + date) and 4 topic
profiles. Each topic has a ground-truth relevance set: the paper ids a human
would call relevant to that topic, judged from the paper's actual content, not
from whether it happens to contain the topic's literal terms.

That distinction is the point of the fixture set. About a third of the
"relevant" papers per topic are written as paraphrases that deliberately avoid
every literal term in that topic's term list (they're marked PARAPHRASE below),
so a keyword-only ranker cannot find them at all, and tfidf/bm25 have to do real
work through the vocabulary they share with the topic terms rather than the
terms themselves. The rest use the field's normal vocabulary, term hits and all.
Twelve papers (p39-p50) are distractors from unrelated fields — some of them
share generic ML jargon ("transformer", "deep learning", "foundation model")
with the topic papers on purpose, so a ranker that over-weights generic
vocabulary shows up as false positives in the metrics.

Committed as plain data so `python -m eval.evaluate` is reproducible offline,
with no network calls and no dependency on when it's run.
"""

TOPICS = {
    "single_cell": {
        "weight": 3,
        "terms": [
            "single-cell RNA",
            "scRNA-seq",
            "cell type annotation",
            "batch integration",
            "single cell transcriptom",
        ],
    },
    "glioma": {
        "weight": 3,
        "terms": ["glioma", "glioblastoma", "brain tumor", "IDH mutation", "WHO grade"],
    },
    "comp_neuro": {
        "weight": 3,
        "terms": ["connectomics", "neural circuit", "neuronal morphology", "zebrafish", "brain atlas"],
    },
    "clinical_nlp": {
        "weight": 2,
        "terms": ["clinical notes", "electronic health record", "MIMIC", "ICU", "mortality prediction"],
    },
}

# id, title, abstract, date. Dates are spread across a few weeks; they don't
# matter for the eval (evaluate.py scores the lexical signal alone, with
# recency excluded — see radar.rank(..., include_recency=False)).
PAPERS = [
    # -- single_cell: exact-term ------------------------------------------------
    dict(id="p01", date="2026-08-01",
         title="scRNA-seq atlas of the developing human kidney reveals rare progenitor populations",
         abstract="We profile the developing human kidney with single-cell RNA sequencing across "
                  "12 donors, performing cell type annotation against a curated marker set and "
                  "batch integration across sequencing runs to build a unified progenitor atlas."),
    dict(id="p02", date="2026-08-02",
         title="Batch integration methods for large-scale single-cell atlases: a benchmark",
         abstract="We benchmark eight batch integration methods for single-cell RNA-seq atlas "
                  "construction across tissue, donor, and platform batch effects, reporting "
                  "mixing and biological-conservation scores for each."),
    dict(id="p03", date="2026-08-03",
         title="Automated cell type annotation from single-cell transcriptomic profiles",
         abstract="A reference-based classifier performs cell type annotation directly from "
                  "single cell transcriptomic profiles, avoiding manual marker-gene curation "
                  "while matching expert-level accuracy on held-out atlases."),
    dict(id="p04", date="2026-08-04",
         title="Mapping cellular heterogeneity in tumor microenvironments via droplet-based transcriptomic profiling",
         # PARAPHRASE (single_cell): no literal term from the topic's term list.
         abstract="Using droplet-based transcriptomic profiling at the individual-cell level, "
                  "we resolve stromal and immune heterogeneity within solid tumor "
                  "microenvironments, distinguishing rare populations invisible to bulk assays."),
    dict(id="p05", date="2026-08-05",
         title="A foundation model for single-cell gene expression pretrained on 50 million cells",
         abstract="We pretrain a transformer on 50 million single-cell RNA-seq profiles spanning "
                  "human and mouse tissues, then fine-tune for cell type annotation and "
                  "perturbation-response prediction."),
    dict(id="p06", date="2026-08-06",
         title="Integrating spatial and single-cell RNA-seq data to resolve tissue architecture",
         abstract="A joint embedding of spatial transcriptomics and single-cell RNA-seq data "
                  "recovers the spatial organization of cell types identified by single cell "
                  "transcriptomic clustering, validated in mouse brain sections."),
    dict(id="p07", date="2026-08-07",
         title="Correcting technical batch effects across multi-donor droplet sequencing experiments",
         # PARAPHRASE (single_cell): "batch effects" and "droplet sequencing", not the topic's terms.
         abstract="Multi-donor droplet sequencing experiments show strong technical batch effects "
                  "driven by reagent lot and processing date; we propose a mixture-model "
                  "correction that preserves biological variation better than linear methods."),
    dict(id="p08", date="2026-08-08",
         title="scRNA-seq reveals novel immune cell subsets in the tumor-draining lymph node",
         abstract="scRNA-seq profiling of tumor-draining lymph nodes identifies two previously "
                  "unreported dendritic cell subsets whose abundance correlates with response "
                  "to checkpoint blockade."),
    dict(id="p09", date="2026-08-09",
         title="Cell-type annotation transfer learning across single-cell RNA-seq atlases of different species",
         abstract="A transfer-learning approach carries cell type annotation labels from a "
                  "well-annotated single-cell RNA-seq atlas in mouse to a sparsely labelled "
                  "human atlas, without requiring shared orthology tables."),
    dict(id="p10", date="2026-08-10",
         title="Reference-free integration of single-cell RNA-seq datasets across tissues",
         abstract="We introduce a reference-free batch integration algorithm for single-cell "
                  "RNA-seq datasets collected across unrelated tissues, avoiding the need for a "
                  "predefined anchor dataset."),

    # -- glioma: exact-term, plus p15 double-labelled with single_cell ---------
    dict(id="p11", date="2026-08-01",
         title="IDH mutation status predicts survival outcomes across WHO grade II and III gliomas",
         abstract="In a cohort of 400 diffuse gliomas, IDH mutation status stratifies survival "
                  "independently of WHO grade, refining the current grading scheme for grade II "
                  "and III tumors."),
    dict(id="p12", date="2026-08-02",
         title="Multi-omic subtyping of glioblastoma identifies four distinct molecular subtypes",
         abstract="Integrated genomic, transcriptomic, and methylation profiling of glioblastoma "
                  "recovers four molecular subtypes with distinct treatment response, extending "
                  "the classical proneural/classical/mesenchymal scheme."),
    dict(id="p13", date="2026-08-03",
         title="Deep learning classification of brain tumor grade from routine MRI",
         abstract="A convolutional network classifies brain tumor grade from routine, "
                  "non-contrast MRI sequences, matching radiologist agreement on an "
                  "independent multi-center test set."),
    dict(id="p14", date="2026-08-04",
         title="Molecular stratification of diffuse low-grade brain neoplasms using methylation profiling",
         # PARAPHRASE (glioma): "brain neoplasms", not "brain tumor"/"glioma"/"WHO grade".
         abstract="Genome-wide methylation profiling separates diffuse low-grade brain neoplasms "
                  "into clinically distinct clusters that better predict time to malignant "
                  "transformation than histology alone."),
    dict(id="p15", date="2026-08-05",
         title="Single-cell dissection of the glioblastoma immune microenvironment",
         abstract="single-cell RNA sequencing of glioblastoma resections maps the tumor-infiltrating "
                  "myeloid compartment, revealing an immunosuppressive macrophage state absent "
                  "from lower-grade glioma."),
    dict(id="p16", date="2026-08-06",
         title="WHO grade IV glioma recurrence patterns following chemoradiation",
         abstract="Longitudinal imaging of WHO grade IV glioma patients after chemoradiation "
                  "shows recurrence concentrated within 2cm of the original resection cavity in "
                  "most cases."),
    dict(id="p17", date="2026-08-07",
         title="Genomic drivers of high-grade astrocytic tumors in pediatric patients",
         # PARAPHRASE (glioma): "astrocytic tumors", not "brain tumor"/"glioma".
         abstract="Whole-exome sequencing of high-grade pediatric astrocytic tumors identifies "
                  "recurrent histone H3 mutations distinct from the driver landscape of adult "
                  "disease."),
    dict(id="p18", date="2026-08-08",
         title="IDH-mutant glioma metabolism revealed by spatial mass spectrometry imaging",
         abstract="Spatial mass spectrometry imaging of IDH-mutant glioma sections maps the "
                  "oncometabolite 2-HG at micron resolution, showing sharp boundaries at the "
                  "tumor margin."),
    dict(id="p19", date="2026-08-09",
         title="Brain tumor segmentation benchmark for the BraTS challenge",
         abstract="We report results from the annual BraTS brain tumor segmentation challenge, "
                  "comparing top-performing architectures on multimodal MRI from newly "
                  "contributed clinical sites."),
    dict(id="p20", date="2026-08-10",
         title="Longitudinal MRI radiomics tracks glioblastoma treatment response",
         abstract="Radiomic features extracted from serial MRI in glioblastoma patients "
                  "undergoing standard chemoradiation predict progression an average of six "
                  "weeks before it is visible to a radiologist."),

    # -- comp_neuro: exact-term ---------------------------------------------
    dict(id="p21", date="2026-08-01",
         title="Whole-brain connectomics of the larval zebrafish nervous system",
         abstract="Serial electron microscopy of a larval zebrafish yields a whole-brain "
                  "connectomics reconstruction, resolving synaptic connectivity across every "
                  "major neuronal cell class."),
    dict(id="p22", date="2026-08-02",
         title="Neural circuit dynamics underlying decision-making in mice",
         abstract="Two-photon recordings of a frontal-parietal neural circuit during a "
                  "perceptual decision task in mice reveal ramping activity that predicts choice "
                  "before movement onset."),
    dict(id="p23", date="2026-08-03",
         title="A digital brain atlas of neuronal morphology across cortical layers",
         abstract="We release a digital brain atlas cataloguing neuronal morphology across six "
                  "cortical layers in mouse visual cortex, reconstructed from over 3,000 "
                  "individually traced neurons."),
    dict(id="p24", date="2026-08-04",
         title="Reconstructing synaptic wiring diagrams from serial electron microscopy volumes",
         # PARAPHRASE (comp_neuro): no literal topic term.
         abstract="An automated pipeline reconstructs synaptic wiring diagrams from serial "
                  "electron microscopy volumes at nanometer resolution, cutting manual proofreading "
                  "time by an order of magnitude."),
    dict(id="p25", date="2026-08-05",
         title="Zebrafish whole-brain imaging reveals circuit-level correlates of arousal",
         abstract="Light-sheet imaging of the entire zebrafish brain during spontaneous behavior "
                  "identifies a distributed circuit whose activity tracks an animal's arousal "
                  "state on a trial-by-trial basis."),
    dict(id="p26", date="2026-08-06",
         title="Neuronal morphology reconstruction at scale using deep learning segmentation",
         abstract="A deep segmentation model automates neuronal morphology reconstruction from "
                  "confocal image stacks, reducing the manual tracing bottleneck that has "
                  "limited large morphology atlases."),
    dict(id="p27", date="2026-08-07",
         title="Mapping functional micro-circuits in the mouse visual cortex with two-photon imaging",
         # PARAPHRASE (comp_neuro): "micro-circuits", not "neural circuit".
         abstract="Two-photon calcium imaging across cortical layers maps functional "
                  "micro-circuits in mouse visual cortex, showing that orientation-tuned neurons "
                  "cluster more tightly than previously reported."),
    dict(id="p28", date="2026-08-08",
         title="Cross-species comparison of brain atlases in rodents and primates",
         abstract="We align existing brain atlases from mouse, rat, and macaque into a common "
                  "coordinate framework, enabling direct cross-species comparison of "
                  "cytoarchitecture."),
    dict(id="p29", date="2026-08-09",
         title="Neural dynamics of working memory in prefrontal circuits",
         abstract="Population recordings from prefrontal circuits during a delayed-match task "
                  "show that neural dynamics during the delay period encode a low-dimensional, "
                  "rotating representation of the remembered item."),
    dict(id="p30", date="2026-08-10",
         title="Connectomics-informed models of information flow in the fly brain",
         abstract="Combining connectomics reconstructions with activity recordings, we build a "
                  "circuit model of information flow through the fly central complex that "
                  "reproduces observed navigation behavior."),

    # -- clinical_nlp: exact-term --------------------------------------------
    dict(id="p31", date="2026-08-01",
         title="Predicting ICU mortality from clinical notes using a transformer-based model",
         abstract="A transformer fine-tuned on clinical notes predicts ICU mortality within 48 "
                  "hours of admission, outperforming the standard APACHE II severity score on a "
                  "held-out cohort."),
    dict(id="p32", date="2026-08-02",
         title="Extracting adverse drug events from electronic health record narratives",
         abstract="A named-entity and relation extraction pipeline over electronic health record "
                  "narratives identifies adverse drug events with higher recall than existing "
                  "structured-code-based surveillance."),
    dict(id="p33", date="2026-08-03",
         title="MIMIC-IV benchmark for clinical outcome prediction tasks",
         abstract="We release standardized MIMIC-IV benchmark splits for six clinical outcome "
                  "prediction tasks, including mortality prediction and length-of-stay "
                  "regression, to make model comparisons reproducible."),
    dict(id="p34", date="2026-08-04",
         title="Natural language processing of hospital discharge summaries to flag readmission risk",
         # PARAPHRASE (clinical_nlp): no literal topic term.
         abstract="We apply natural language processing to free-text hospital discharge "
                  "summaries to flag patients at elevated risk of 30-day readmission, "
                  "outperforming a model built only on structured diagnosis codes."),
    dict(id="p35", date="2026-08-05",
         title="Mortality prediction in critical care using structured and unstructured EHR data",
         abstract="Combining structured vitals with unstructured EHR text improves mortality "
                  "prediction in critical care over either data source alone, with the largest "
                  "gains in patients with atypical presentations."),
    dict(id="p36", date="2026-08-06",
         title="Clinical NLP pipeline for de-identifying protected health information in notes",
         abstract="An open-source clinical NLP pipeline de-identifies protected health "
                  "information in free-text clinical notes, achieving recall above 0.98 on "
                  "held-out hospital data."),
    dict(id="p37", date="2026-08-07",
         title="Deep learning on nursing progress notes to predict sepsis onset in the intensive care unit",
         # PARAPHRASE (clinical_nlp): "intensive care unit" spelled out, not "ICU"; "nursing progress notes", not "clinical notes".
         abstract="A recurrent model trained on nursing progress notes predicts sepsis onset in "
                  "the intensive care unit up to six hours before the standard SIRS criteria are "
                  "met."),
    dict(id="p38", date="2026-08-08",
         title="Electronic health record foundation models for phenotype prediction",
         abstract="We pretrain a foundation model on longitudinal electronic health record "
                  "sequences and fine-tune it for rare-disease phenotype prediction, showing "
                  "gains over task-specific baselines with limited labelled data."),

    # -- distractors: unrelated fields, some sharing generic ML jargon --------
    dict(id="p39", date="2026-08-01",
         title="Scaling laws for large language model pretraining on web text",
         abstract="We measure how validation loss scales with parameter count and training "
                  "tokens for language models pretrained on filtered web text, extending prior "
                  "scaling-law fits to a larger compute range."),
    dict(id="p40", date="2026-08-02",
         title="A benchmark for autonomous drone navigation in cluttered environments",
         abstract="We introduce a simulated benchmark for autonomous drone navigation through "
                  "cluttered indoor environments, evaluating policies on collision rate and "
                  "time-to-goal."),
    dict(id="p41", date="2026-08-03",
         title="Diffusion models for photorealistic image synthesis",
         abstract="A latent diffusion model trained on a large image-caption corpus produces "
                  "photorealistic images from text prompts, matching prior state of the art on "
                  "standard FID benchmarks."),
    dict(id="p42", date="2026-08-04",
         title="Transformer architectures for machine translation between low-resource languages",
         abstract="We adapt transformer architectures for machine translation between "
                  "low-resource language pairs, using back-translation to compensate for "
                  "limited parallel data."),
    dict(id="p43", date="2026-08-05",
         title="Reinforcement learning for robotic grasping in cluttered bins",
         abstract="A reinforcement learning policy trained in simulation transfers to robotic "
                  "grasping in cluttered bins, achieving a higher success rate than a "
                  "hand-engineered grasp planner."),
    dict(id="p44", date="2026-08-06",
         title="Climate model projections of Arctic sea ice loss through 2100",
         abstract="An ensemble of climate models projects continued Arctic sea ice loss through "
                  "2100 under all emissions scenarios considered, with an ice-free summer "
                  "possible as early as the 2050s."),
    dict(id="p45", date="2026-08-07",
         title="Gravitational wave detection from binary neutron star mergers",
         abstract="We report a new gravitational wave detection consistent with a binary "
                  "neutron star merger, with an electromagnetic counterpart identified within "
                  "hours of the trigger."),
    dict(id="p46", date="2026-08-08",
         title="Battery materials discovery using graph neural networks",
         abstract="A graph neural network trained on density functional theory calculations "
                  "screens candidate battery materials for ionic conductivity, prioritizing "
                  "compounds for experimental synthesis."),
    dict(id="p47", date="2026-08-09",
         title="Macroeconomic forecasting with large-scale panel regression models",
         abstract="We compare large-scale panel regression models against standard "
                  "autoregressive baselines for macroeconomic forecasting across 40 countries "
                  "and two decades of data."),
    dict(id="p48", date="2026-08-10",
         title="Self-supervised pretraining for satellite imagery classification",
         abstract="Self-supervised pretraining on unlabeled satellite imagery improves downstream "
                  "land-cover classification accuracy, especially in regions with few labelled "
                  "examples."),
    dict(id="p49", date="2026-08-11",
         title="Foundation models for protein structure prediction from sequence alone",
         abstract="A foundation model trained on evolutionary sequence data predicts protein "
                  "structure directly from a single sequence, without a multiple-sequence "
                  "alignment step."),
    dict(id="p50", date="2026-08-12",
         title="Attention mechanisms for tabular data classification in financial fraud detection",
         abstract="We evaluate attention-based architectures against gradient-boosted trees for "
                  "tabular financial fraud detection, finding gains only on datasets with "
                  "high-cardinality categorical features."),
]

# Ground-truth relevance per topic, judged from content (not from literal term
# hits). p15 is intentionally relevant to both single_cell and glioma.
LABELS = {
    "single_cell": {f"p{i:02d}" for i in range(1, 11)} | {"p15"},
    "glioma": {f"p{i:02d}" for i in range(11, 21)},
    "comp_neuro": {f"p{i:02d}" for i in range(21, 31)},
    "clinical_nlp": {f"p{i:02d}" for i in range(31, 39)},
}

assert {p["id"] for p in PAPERS} == {f"p{i:02d}" for i in range(1, 51)}, \
    "fixture ids must be exactly p01..p50"
