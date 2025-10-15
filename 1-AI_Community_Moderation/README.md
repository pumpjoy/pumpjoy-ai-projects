  

## 1. Executive Summary: AI for Scalable Moderation

The project successfully developed a scalable solution for automated content moderation based on complex community guidelines. By employing Transfer Learning and a specialized prompting strategy, a robust model is built, capable of classifying multiple violation types.

|Metric|Result|Interpretation|
|---|---|---|
|**Model**|Fine-Tuned **RoBERTa-base**|Stable, NLU-optimized architecture chosen over Qwen due to memory and task-fit constraints.|
|**Validation AUC**|**0.8695**|Strong discriminatory power; the model correctly ranks a violating comment higher than a compliant one ≈87% of the time.|
|**Data Strategy**|Few-Shot Prompting|Successfully leveraged contextual rules to overcome small dataset limitations.|


---
## 2. Technical Strategy and Architecture

### Architecture Justification
The **RoBERTa-base** (125M parameters) model was selected for its robust **Natural Language Understanding (NLU)** capabilities, natively suited for text classification. This choice balances predictive power with resource efficiency, enabling practical deployment.

### Few-Shot Prompting Technique
To enable the model to generalize across specific rules, a **Few-Shot Prompting** technique was used to structure the input as a single sequence. This provides the model with the necessary **context and ruleset** for a zero-shot-like classification.

$\text{[Comment] [SEP] [Rule Text] [SEP] [Rule Examples]}$

This provides the model with the necessary **context and ruleset** in a single sequence, maximizing the learning potential from each training sample. tokens showing comment, rule, and examples.
*(The tokenizer replaces the `[SEP]` placeholder with the model's native separator token)*

---
## 3. Deep Dive: Error Analysis & System Limitations

Analyzing the model's highest-confidence failures reveals critical insights necessary for real-world deployment.

### A. False Positive (FP) Vulnerability

| Error Type | Key Rule Affected | Confidence |
| :--- | :--- | :--- |
| **False Positive** | **No Legal Advice** | High ($\approx 0.95$) |

* **Root Cause:** The model exhibits **oversensitivity to prescriptive language**. It struggles to differentiate between benign, casual life advice (often sarcastic or hypothetical) and genuinely prohibited legal/financial guidance, due to reliance on strong instructional verbs (e.g., "you should," "report to HR").
* **Business Action:** To minimize unfair flags, set a very high confidence threshold (e.g., **$> 0.95$**) for automated filtering, pushing all ambiguous cases to mandatory human review. 

### B. False Negative (FN) Vulnerability

| Error Type | Key Rule Affected | Confidence |
| :--- | :--- | :--- |
| **False Negative** | **No Advertising** | Low ($\approx 0.05$) |

* **Root Cause (Critical):** The model is effectively blind to **link-only spam** because the preprocessing pipeline stripped the primary signal (the URL/Link presence) during cleaning. The model relies too heavily on long-form text features.
* **Critical Fix:** This requires immediate **Feature Engineering** to extract link presence (e.g., a `URL_PRESENT` binary flag) and add it to the input sequence before retraining the model.

---
## 4. Deployment and Future Roadmap

The project is structured to transition smoothly into a production environment, featuring two key next steps to ensure reliability.

### Deployment Concept: ACGE API Endpoint
The final, saved RoBERTa model is ready to be loaded onto a server (e.g., using FastAPI or Flask) to serve predictions via a low-latency REST API:

|API Action|Input (JSON)|Output (JSON)|
|---|---|---|
|`POST /predict`|`{"comment": "...", "rule": "..."}`|`{"violation_predicted": true, "rule": "No Advertising", "confidence_score": 0.8695}`|

### Prioritized Future Work

1. **Hybrid Modeling for Spam:** The most urgent task is to address the FN vulnerability. This requires implementing a **hybrid ensemble model** where a simple model (e.g., Logistic Regression) detects spam based _only_ on the new URL presence feature, and the RoBERTa model handles the complex semantic rules.

2. **Adversarial Fine-Tuning:** Systematically collect the observed **False Positive** samples (ambiguous legal advice) and incorporate them into the training set to make the model more robust against common human language nuances.


3. **Human-in-the-Loop (HITL) System:** Implement a feedback mechanism where human-corrected labels for samples within the uncertainty margin (e.g., 0.4 to 0.6 confidence) are fed back into the training data for continuous model improvement.
