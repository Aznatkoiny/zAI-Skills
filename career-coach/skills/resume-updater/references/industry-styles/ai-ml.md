# AI/ML — Industry Style Reference

Formatting instructions for resumes, cover letters, and career documents targeting AI, machine
learning, data science, and research roles: ML Engineer, Research Scientist, Applied Scientist,
Data Scientist, Applied AI Engineer. Read this file when `preferences.industry_style` in
career-profile.json is `ai-ml`. Follow these rules exactly.

## Section Order

Use this order, top to bottom:

1. **Header** — name, email, location, Google Scholar / arXiv profile, GitHub, LinkedIn
2. **Experience** — first, because applied roles are judged on shipped models and measurable
   impact; recruiters look for production ML experience before anything else
3. **Publications / Research** — second, and promote it above Experience only for research
   scientist roles at labs where publication record is the primary credential
4. **Projects** — open source models, Kaggle results, reproduction studies, demos
5. **Skills** — grouped inventory (see format below)
6. **Education** — last for practitioners; degrees (especially PhD) still matter more here than
   in general software engineering, so never trim this section to a single line

Rationale: AI/ML hiring blends academic and engineering credibility. The order above sells
practical impact first while keeping research visible; adjust Publications placement to the
role's research-vs-applied balance.

## Skills Format

Group into labeled rows:

- **Models / Architectures**: e.g., Transformers, diffusion models, CNNs, GBMs, RLHF pipelines
- **Frameworks**: PyTorch, JAX, TensorFlow, Hugging Face, scikit-learn
- **Data Tools**: Spark, Pandas, Airflow, dbt, SQL
- **Cloud ML**: SageMaker, Vertex AI, Azure ML, Ray, Kubernetes for training/serving
- **Research Tools**: Weights & Biases, MLflow, experiment design, ablation studies

List architectures the candidate has actually trained or fine-tuned, not just read about.

## Bullet Writing Rules

- Every bullet needs a quantified metric. Prefer these metric families:
  - **Model quality**: accuracy, F1, AUC, BLEU/ROUGE, perplexity, win-rate vs. baseline
  - **Training efficiency**: GPU-hours, cost per run, convergence speedup, throughput
  - **Data scale**: examples, tokens, TB processed, labeling throughput
  - **Business impact**: revenue lift, cost saved, latency, adoption — always pair a model
    metric with the downstream business outcome when one exists
- Name the architecture, dataset scale, and evaluation methodology — reviewers are peers and
  will probe vague claims.
- State baselines: "improved X from A to B against baseline C" beats "achieved B".
- 3-5 bullets per role. Publications get a separate section in standard citation format with
  venue and year; bold the candidate's name in the author list.

## Example Bullets

Use these as the voice and density target — every bullet carries a metric:

1. Fine-tuned a 7B-parameter LLM with LoRA on 2M domain-specific examples, raising answer
   accuracy from 71% to 89% on the internal eval set while cutting inference cost 4x vs. the
   previous 70B model.
2. Built a real-time fraud detection model (XGBoost → distilled to a 3-layer MLP) scoring 12K
   transactions/sec at p99 8ms, reducing fraud losses by $4.2M/year at a stable 0.3% false
   positive rate.
3. Reduced training time for the ranking model from 18h to 3.5h by migrating to distributed
   data-parallel training on 32 A100s and mixed precision, enabling daily instead of weekly
   retrains.
4. Designed the offline/online evaluation harness (counterfactual replay + interleaving) that
   caught a 6% CTR regression before launch; adopted by 4 teams as the standard eval gate.
5. Led RLHF pipeline development — preference data collection (400K comparisons), reward model
   training, and PPO fine-tuning — improving human preference win-rate from 52% to 68%.
6. Shipped a computer-vision defect detector (fine-tuned ViT) to 9 factory lines, achieving
   97.8% recall at 1.2% false alarm rate and cutting manual inspection hours by 60%.
7. Curated and deduplicated a 1.4TB multilingual pretraining corpus (18 languages), improving
   downstream XNLI accuracy by 3.1 points over the previous data mix.
8. Published 3 first-author papers (NeurIPS, EMNLP, ICML workshop) on efficient fine-tuning;
   open-source implementation has 2.3K GitHub stars and 40+ citing works.
9. Cut feature-store serving latency from 45ms to 9ms by precomputing embeddings and moving
   retrieval to an ANN index (FAISS), unblocking real-time personalization for 8M users.
10. Ran systematic ablations across 60+ experiments (tracked in W&B) to isolate a data-quality
    intervention worth +2.4 F1, then productionized it as an automated data-cleaning stage.
11. Built drift monitoring for 14 production models (PSI + shadow scoring), catching 5 silent
    degradations in the first quarter and cutting mean time-to-detection from weeks to hours.

## ATS Keyword Bank

Weave these naturally into skills and bullets when truthful:

- **Core**: machine learning, deep learning, NLP, computer vision, transformers, LLMs,
  fine-tuning, RLHF, prompt engineering, retrieval-augmented generation (RAG), embeddings
- **Engineering**: MLOps, model deployment, model serving, distributed training, GPU
  optimization, feature engineering, data pipelines, A/B testing, experiment tracking
- **Methods**: supervised learning, reinforcement learning, recommendation systems, anomaly
  detection, statistical modeling, causal inference, evaluation methodology, ablation studies
- **Stack**: PyTorch, TensorFlow, JAX, Hugging Face, Spark, Ray, SageMaker, Vertex AI

## Tone and Formatting Rules

- Academic-practitioner voice: precise, methodology-aware, never hype. Ban "cutting-edge",
  "state-of-the-art" unless attached to a benchmark result that was actually SOTA (and say
  where and when).
- Report metrics with their evaluation context (dataset, split, baseline). Honesty about
  marginal gains reads as credibility to expert reviewers.
- One to two pages; two is acceptable when Publications is substantive.
- Link Scholar/arXiv and GitHub in the header. For research roles, include talk/poster venues.

## Career Ladder Framing

Frame advice around the research-vs-applied fork: Research Scientist / Applied Scientist /
ML Engineer / Data Scientist titles carry different expectations. Growth signals: publications
and citations (research track), models in production and business impact (applied track),
conference talks, open-source model releases, and dataset/benchmark contributions. Advise
candidates to pick the track their evidence supports and to backfill the other deliberately.

## Interview Weighting

Allocate prep time roughly:

- **ML system design + technical deep-dive: 40%** — design an end-to-end ML system (data,
  training, serving, monitoring) and defend past project decisions layer by layer
- **Coding (Python/ML): 30%** — data manipulation, algorithm implementation, debugging a
  training loop; practice in plain Python and PyTorch
- **Research discussion: 20%** — paper walk-throughs, experiment design, "how would you
  evaluate X"; expect probing on methodology and failure modes
- **Behavioral: 10%** — collaboration with product/infra teams, handling ambiguous problems

Cover letters for AI/ML roles: methodical and research-oriented — reference the team's
publications, models, or open problems, and anchor claims to the metrics above.
