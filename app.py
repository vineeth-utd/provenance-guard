import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import audit
from detection import calculate_confidence, groq_detect, stylometric_detect

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=[],
)


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute")
@limiter.limit("100 per day")
def submit():
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    creator_id = body.get("creator_id", "").strip()

    if not text or not creator_id:
        return jsonify({"error": "Both 'text' and 'creator_id' are required."}), 400

    content_id = str(uuid.uuid4())
    llm_result = groq_detect(text)
    llm_score = llm_result["llm_score"]
    stylometric_result = stylometric_detect(text)
    stylometric_score = stylometric_result["stylometric_score"]
    combined = calculate_confidence(llm_score, stylometric_score)
    confidence = combined["confidence"]
    attribution = combined["attribution"]
    label = combined["label"]
    timestamp = datetime.now(timezone.utc).isoformat()

    audit.append_log({
        "timestamp": timestamp,
        "content_id": content_id,
        "creator_id": creator_id,
        "text_preview": text[:100],
        "attribution": attribution,
        "llm_score": llm_score,
        "stylometric_score": stylometric_score,
        "confidence": confidence,
        "label": label,
    })

    audit.save_submission({
        "content_id": content_id,
        "creator_id": creator_id,
        "text": text,
        "attribution": attribution,
        "llm_score": llm_score,
        "stylometric_score": stylometric_score,
        "confidence": confidence,
        "label": label,
        "status": "reviewed",
    })

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": label,
    }), 200


@app.route("/appeal", methods=["POST"])
def appeal():
    body = request.get_json(silent=True) or {}
    content_id = body.get("content_id", "").strip()
    creator_reasoning = body.get("creator_reasoning", "").strip()

    if not content_id or not creator_reasoning:
        return jsonify({"error": "Both 'content_id' and 'creator_reasoning' are required."}), 400

    submission = audit.get_submission(content_id)
    if submission is None:
        return jsonify({"error": "No submission found for the given content_id."}), 404

    submission["status"] = "under_review"
    audit.save_submission(submission)

    timestamp = datetime.now(timezone.utc).isoformat()
    audit.append_log({
        "event": "appeal",
        "timestamp": timestamp,
        "content_id": content_id,
        "creator_reasoning": creator_reasoning,
        "attribution": submission["attribution"],
        "confidence": submission["confidence"],
        "label": submission["label"],
    })

    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": "Your appeal has been received and is under review.",
    }), 200


@app.route("/log", methods=["GET"])
def log():
    return jsonify(audit.get_log()), 200


if __name__ == "__main__":
    app.run(debug=True)
