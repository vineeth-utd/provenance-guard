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
