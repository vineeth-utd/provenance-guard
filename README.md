# Provenance Guard

Provenance Guard is a Flask-based backend service that analyzes text submissions and estimates whether they are more likely to be human-written or AI-generated. Instead of making a simple binary decision, the system combines multiple detection signals to produce a confidence score and a transparency label that explains the result in plain language.

The system is designed to be transparent and fair. Every classification is recorded in a structured audit log, creators can appeal decisions they disagree with, and rate limiting helps protect the service from misuse.

## Technologies Used

* Python
* Flask
* Groq API (`llama-3.3-70b-versatile`)
* Flask-Limiter
* JSON file storage

## Architecture Overview

Provenance Guard follows a multi-stage pipeline to analyze every submitted piece of text. The system combines an LLM-based detection signal with stylometric heuristics to generate a confidence score before returning a transparency label to the user. Every submission is also recorded in a structured audit log, allowing the system to maintain a history of all classification decisions.

### Submission Flow

```text
                POST /submit
                      │
                      ▼
            Validate Request
                      │
                      ▼
        +-----------------------+
        |  LLM Detection Signal |
        +-----------------------+
                      │
         LLM Score (0 - 1)
                      │
                      ▼
    +-----------------------------+
    | Stylometric Detection Signal|
    +-----------------------------+
                      │
     Stylometric Score (0 - 1)
                      │
                      ▼
        Confidence Score Calculator
          (Average of both scores)
                      │
                      ▼
      Transparency Label Generator
                      │
                      ├──────────────► Audit Log
                      │
                      ▼
             JSON Response
```

### Appeal Flow

```text
              POST /appeal
                    │
                    ▼
          Validate Content ID
                    │
                    ▼
       Save Creator's Reasoning
                    │
                    ▼
      Update Status: under_review
                    │
                    ▼
          Append to Audit Log
                    │
                    ▼
          Confirmation Response
```

The submission endpoint accepts a piece of text and analyzes it using two independent detection signals. Their scores are averaged to produce a confidence score, which is then mapped to an attribution result and a transparency label. The complete decision is recorded in the audit log before the response is returned.

If a creator disagrees with the result, they can submit an appeal. The system records the creator's reasoning, updates the submission status to **under_review**, adds a new appeal entry to the audit log, and returns a confirmation message.

## Features

* **Content Submission API**
  Accepts text submissions through a REST API and analyzes them for AI-generated content.

* **Multi-Signal Detection Pipeline**
  Uses two independent detection signals:

  * Groq LLM-based classification
  * Stylometric heuristics

* **Confidence Scoring**
  Combines both detection signals into a single confidence score instead of making a simple binary decision.

* **Transparency Labels**
  Displays a plain-language explanation that helps users understand the classification result.

* **Appeals Workflow**
  Allows creators to challenge a classification by submitting an appeal with supporting reasoning.

* **Rate Limiting**
  Protects the submission endpoint from excessive requests using Flask-Limiter.

* **Structured Audit Log**
  Records every submission and appeal, including confidence scores, detection results, timestamps, and appeal information for traceability.

## Detection Signals

Provenance Guard uses two independent detection signals to estimate whether a piece of text is more likely to be human-written or AI-generated. Using two different approaches provides a more balanced result than relying on a single signal.

### 1. LLM-based Detection (Groq)

The first signal sends the submitted text to a Groq LLM (`llama-3.3-70b-versatile`) and asks it to estimate how likely the text is to be AI-generated.

**What it measures**

* Overall writing style
* Sentence flow
* Tone and coherence
* Patterns commonly seen in AI-generated writing

**Why it was chosen**

An LLM can understand the text as a whole instead of relying only on statistics. It can identify writing patterns that are difficult to capture with simple rules.

**What it misses**

The model may misclassify formal human writing as AI-generated or fail to detect AI-generated text that has been heavily edited by a person.

---

### 2. Stylometric Detection

The second signal uses simple Python-based heuristics to measure structural properties of the text.

The current implementation evaluates:

* Sentence length variation
* Vocabulary diversity (Type-Token Ratio)
* Punctuation density

These measurements are combined into a single stylometric score between 0 and 1.

**Why it was chosen**

Stylometric features provide an independent structural view of the text. They are fast to compute, require no external libraries, and complement the semantic analysis performed by the LLM.

**What it misses**

Stylometric heuristics cannot understand the meaning or context of the text. Creative writing, academic writing, or heavily edited AI content may produce patterns that resemble either human or AI-generated writing.

---

### Why Two Signals?

Each signal has different strengths and weaknesses.

The LLM focuses on meaning, writing style, and overall language patterns, while the stylometric signal focuses on measurable characteristics of the text. Combining both signals produces a more balanced confidence score than relying on either signal alone and helps reduce the chances of making an overconfident classification.

## Confidence Scoring

Each detection signal produces a score between **0** and **1**, where a higher value indicates that the text is more likely to be AI-generated.

The final confidence score is calculated by taking the average of the two detection signals:

* LLM detection score
* Stylometric detection score

Both signals contribute equally because they measure different properties of the text. The LLM focuses on writing style and semantics, while the stylometric signal focuses on measurable structural characteristics.

The final confidence score is mapped to one of three categories:

| Confidence Score | Result               |
| ---------------- | -------------------- |
| **0.00 – 0.39**  | Likely Human-written |
| **0.40 – 0.69**  | Uncertain            |
| **0.70 – 1.00**  | Likely AI-generated  |

These thresholds were intentionally chosen to be conservative. If the two detection signals disagree or neither signal is confident enough, the system returns an **Uncertain** result instead of making a strong claim. This helps reduce false positives, where human-written content is incorrectly labeled as AI-generated.

### Example Results

The confidence scoring approach was tested using four representative writing samples.

| Sample                                | LLM Score | Stylometric Score | Final Confidence | Result               |
| ------------------------------------- | --------: | ----------------: | ---------------: | -------------------- |
| Clearly AI-generated paragraph        |      0.82 |            0.5790 |       **0.6995** | Likely AI-generated  |
| Clearly Human-written paragraph       |      0.21 |            0.4213 |       **0.3156** | Likely Human-written |
| Formal Human-written paragraph        |      0.42 |            0.5349 |       **0.4775** | Uncertain            |
| Lightly Edited AI-generated paragraph |      0.42 |            0.5039 |       **0.4619** | Uncertain            |

The examples represent four different writing styles: a clearly AI-generated passage, a casual human-written paragraph, a formal human-written paragraph, and a lightly edited AI-generated paragraph.

These results show that the confidence score varies meaningfully across different types of writing instead of always producing similar values. Clearly human-written and AI-generated text receive noticeably different confidence scores, while more ambiguous cases fall into the **Uncertain** range.

