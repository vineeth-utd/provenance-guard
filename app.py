import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

import audit
from detection import calculate_confidence, groq_detect, stylometric_detect

app = Flask(__name__)


@app.route("/submit", methods=["POST"])
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
    label = "Analysis pending"
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


@app.route("/log", methods=["GET"])
def log():
    return jsonify(audit.get_log()), 200


if __name__ == "__main__":
    app.run(debug=True)
