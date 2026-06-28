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

## Transparency Labels

Instead of only showing a confidence score, Provenance Guard displays a plain-language transparency label that explains the result in a way that is easy for non-technical users to understand.

| Result                   | Label Text                                                                                                                                        |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Likely AI-generated**  | **This content is likely AI-generated.** Our analysis found strong signs that this text was created with the help of AI.                          |
| **Uncertain**            | **We could not determine how this content was created with high confidence.** The available signals were mixed, so no strong conclusion was made. |
| **Likely Human-written** | **This content is likely human-written.** Our analysis found strong signs that this text was written by a person.                                 |

The labels are designed to communicate the system's assessment without making absolute claims. AI attribution is not a solved problem, so the system uses words such as **"likely"** and provides an **Uncertain** category whenever the available evidence does not strongly support either outcome. This helps reduce the risk of presenting an overconfident or misleading result to users.

## Appeals Workflow

Provenance Guard allows creators to appeal a classification if they believe their content was incorrectly identified. This provides a way to challenge the system's decision instead of treating the classification as final.

To submit an appeal, the creator provides:

* The `content_id` returned by the original submission.
* A short explanation describing why they believe the classification is incorrect.

When an appeal is received, the system:

1. Validates that the provided `content_id` exists.
2. Updates the submission status to `under_review`.
3. Records the creator's reasoning.
4. Appends a new appeal entry to the audit log while preserving the original classification details.
5. Returns a confirmation that the appeal has been received.

The system does not automatically reclassify the content after an appeal is submitted. Instead, the appeal is recorded for manual review, allowing the original classification and the creator's explanation to be reviewed together.

## Rate Limiting

To prevent abuse and protect the Groq API from excessive requests, the submission endpoint is protected using **Flask-Limiter**.

The following limits are applied to the `POST /submit` endpoint:

| Limit                      | Purpose                                                                                   |
| -------------------------- | ----------------------------------------------------------------------------------------- |
| **10 requests per minute** | Prevents rapid bursts of requests from a single client while allowing normal usage.       |
| **100 requests per day**   | Prevents excessive API usage over a longer period and helps control resource consumption. |

These limits were chosen based on the expected behavior of a writing platform. Most creators submit completed drafts or occasional revisions rather than dozens of requests every minute. Allowing up to **10 submissions per minute** provides enough flexibility for legitimate users while discouraging automated abuse. The **100 requests per day** limit acts as a safeguard against scripts repeatedly calling the API and consuming unnecessary resources.

The implementation was verified by sending more than ten requests within one minute. The first ten requests returned **HTTP 200**, while subsequent requests returned **HTTP 429 (Too Many Requests)**, confirming that the rate limiting was working as expected.

## Audit Log

Every submission and appeal is recorded in a structured audit log. The log provides a complete history of the system's decisions, making it easier to review classifications, investigate issues, and track appeals.

Each submission entry includes:

* Timestamp
* Content ID
* Creator ID
* Attribution result
* LLM detection score
* Stylometric detection score
* Combined confidence score
* Transparency label

Appeal entries additionally include:

* Event type (`appeal`)
* Creator reasoning
* Updated submission status

The audit log is stored as structured JSON and can be viewed through the `GET /log` endpoint. This makes it easy to inspect previous classifications and verify that the system is recording the information needed for transparency and debugging.

### Sample Audit Log Entry

```json
{
    "timestamp": "2026-06-28T02:33:32.360799+00:00",
    "content_id": "33d93f23-98b4-418e-93d2-6beedc250644",
    "creator_id": "test",
    "text_preview": "The meeting went well. We discussed the quarterly targets and agreed on next steps. Everyone seemed ",
    "attribution": "Likely Human-written",
    "llm_score": 0.21,
    "stylometric_score": 0.5006,
    "confidence": 0.3553,
    "label": "This content is likely human-written. Our analysis found strong signs that this text was written by a person."
}
```

## Setup and Running the Project

### Prerequisites

* Python 3.11 or later
* A Groq API key

### Installation

Clone the repository:

```bash
git clone <repository-url>
cd provenance-guard
```

Create and activate a virtual environment:

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (Git Bash)
source .venv/Scripts/activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root and add your Groq API key:

```text
GROQ_API_KEY=your_api_key_here
```

### Run the Application

Start the Flask server:

```bash
python app.py
```

The API will be available at:

```text
http://127.0.0.1:5000
```

### Available Endpoints

| Method | Endpoint  | Description                                     |
| ------ | --------- | ----------------------------------------------- |
| POST   | `/submit` | Submit text for AI attribution analysis.        |
| POST   | `/appeal` | Submit an appeal for a previous classification. |
| GET    | `/log`    | View the structured audit log.                  |

### Example Request

```bash
curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a sample submission.",
    "creator_id": "demo-user"
  }'
```

## Known Limitations

Although Provenance Guard uses two independent detection signals, it is not able to classify every type of writing perfectly.

### Formal Human Writing

Academic papers, research articles, or other highly structured writing may be classified as **Uncertain** or even **Likely AI-generated**. Formal writing often shares characteristics with AI-generated text, such as consistent sentence structure and polished language, which can influence both the LLM and stylometric signals.

### Heavily Edited AI-generated Content

If AI-generated text has been significantly rewritten by a human, the writing may no longer contain many of the patterns used by the detection signals. In these cases, the system may classify the content as **Likely Human-written** or **Uncertain**.

### Creative Writing

Poems, song lyrics, or experimental writing often use unusual sentence structures, repeated words, or unconventional punctuation. These characteristics can affect the stylometric heuristics, making them less reliable for creative content.

These limitations highlight why the system communicates uncertainty through confidence scores and transparency labels instead of making absolute claims about how a piece of content was created.

## Spec Reflection

Writing the project specification before starting the implementation made the development process much smoother. Defining the system architecture, confidence score thresholds, transparency labels, and API endpoints early helped keep the implementation focused and reduced the number of design decisions that had to be made while coding.

One area where the implementation differed from the original plan was the storage design. Instead of storing everything in a single audit log, the project uses two JSON files: `submissions.json` stores the current state of each submission, while `audit_log.json` maintains an append-only history of submissions and appeals. Separating the current state from the historical log made it easier to update submission status during the appeals workflow while preserving a complete audit trail.

## AI Usage

AI tools were used to assist with implementation, but every generated change was reviewed, tested, and adjusted before being accepted.

### Instance 1: Flask API and Project Structure

I used Claude Code to generate the initial Flask application structure, including the `/submit` and `/log` endpoints, JSON storage helpers, and the basic project scaffolding.

Before accepting the implementation, I reviewed the proposed file structure, simplified a few implementation details, and chose to separate the current submission state (`submissions.json`) from the append-only audit history (`audit_log.json`) to better support the appeals workflow.

---

### Instance 2: Detection Pipeline and Production Features

I used Claude Code to help implement the Groq detection signal, the stylometric detection function, confidence scoring, transparency labels, the appeals workflow, and rate limiting.

Each milestone was completed independently using a plan-first workflow. Before any code was generated, I reviewed the proposed implementation, requested changes where necessary, and verified the completed functionality through manual API testing. Examples of changes I made included refining the detection prompts, adjusting implementation details to match the project specification, and ensuring the confidence scoring, transparency labels, and appeals workflow followed the design documented in `planning.md`.