# CLAUDE.md

## Project Overview

This project builds **Provenance Guard**, a Flask backend that estimates whether submitted text is more likely to be human-written or AI-generated. The system combines multiple detection signals, produces a confidence score, displays a transparency label, maintains an audit log, and allows creators to appeal classifications.

## Development Guidelines

* Treat `planning.md` as the source of truth for architecture and implementation decisions.
* Implement only the current milestone unless explicitly asked to work on future milestones.
* Before making significant changes, explain the implementation plan and wait for approval.
* Preserve the existing project structure unless a change is clearly beneficial.

## Coding Style

* Keep the code simple, readable, and beginner-friendly.
* Avoid unnecessary abstraction or over-engineering.
* Prefer clear function and variable names over clever implementations.
* Reuse existing code instead of duplicating logic.
* Keep functions focused on a single responsibility.

## Project Structure

* `app.py` contains the Flask application and API routes.
* `audit.py` manages reading and writing JSON storage files.
* `audit_log.json` is an append-only history of system events.
* `submissions.json` stores the current state of each submission.
* Runtime JSON files should never be committed to Git.

## API Design

* Keep API responses consistent with `planning.md`.
* Validate user input before processing requests.
* Return structured JSON responses.
* Preserve existing endpoints unless changes are requested.

## Implementation Preferences

* Build and test one feature at a time.
* Verify new functionality before moving to the next milestone.
* Do not introduce new dependencies unless they provide a clear benefit.
* Prefer modifying existing files over creating new ones when appropriate.

## AI Assistance

* Read only the relevant sections of `planning.md` needed for the current task.
* Stay within the requested scope.
* Explain any suggested design changes before implementing them.
