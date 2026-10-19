from flask import Flask, jsonify, request
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

API_ENDPOINTS = [
    "https://test1-production-05ea.up.railway.app",
    "https://test2-production-628e.up.railway.app",
    "https://test3-production-91c2.up.railway.app",
    "https://test4-production-5847.up.railway.app",
    "https://test5-production-151d.up.railway.app",
]

API_NAME = "FreeFire Spam API (External JWT API)"
ACTIVE_TOKENS = 700
TOKEN_UPDATE_INTERVAL_HOURS = 6.0
REQUEST_TIMEOUT = 10

executor = ThreadPoolExecutor(max_workers=len(API_ENDPOINTS))

def call_endpoint(url, params=None, method="GET"):
    try:
        if method == "GET":
            r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        else:
            r = requests.post(url, json=params, timeout=REQUEST_TIMEOUT)
        try:
            data = r.json()
        except Exception:
            data = r.text
        return {
            "url": url,
            "status_code": r.status_code,
            "success": r.status_code < 400,
            "response": data,
        }
    except Exception as e:
        return {
            "url": url,
            "status_code": None,
            "success": False,
            "error": str(e),
        }


def broadcast(path, params=None, method="GET"):
    futures = [
        executor.submit(call_endpoint, f"{base}{path}", params, method)
        for base in API_ENDPOINTS
    ]
    return [f.result() for f in futures]


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "active_tokens": ACTIVE_TOKENS,
        "commands": {
            "reload": "/reload_tokens",
            "start": "/spm?uid=9763926639",
            "status": "/status?uid=9763926639",
            "stop": "/stp?uid=9763926639",
            "tokens": "/tokens",
        },
        "name": API_NAME,
        "status": "running",
        "token_update_interval_hours": TOKEN_UPDATE_INTERVAL_HOURS,
    })


@app.route("/spm", methods=["GET"])
def spm():
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400
    results = broadcast("/spm", {"uid": uid})
    return jsonify({
        "command": "start",
        "uid": uid,
        "total": len(results),
        "results": results,
    })


@app.route("/stp", methods=["GET"])
def stp():
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400
    results = broadcast("/stp", {"uid": uid})
    return jsonify({
        "command": "stop",
        "uid": uid,
        "total": len(results),
        "results": results,
    })


@app.route("/status", methods=["GET"])
def status():
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "uid parameter is required"}), 400
    results = broadcast("/status", {"uid": uid})
    return jsonify({
        "command": "status",
        "uid": uid,
        "total": len(results),
        "results": results,
    })


@app.route("/tokens", methods=["GET"])
def tokens():
    results = broadcast("/tokens")
    return jsonify({
        "command": "tokens",
        "total": len(results),
        "results": results,
    })


@app.route("/reload_tokens", methods=["GET"])
def reload_tokens():
    results = broadcast("/reload_tokens")
    return jsonify({
        "command": "reload",
        "total": len(results),
        "results": results,
    })


@app.route("/proxy/<path:subpath>", methods=["GET", "POST"])
def proxy(subpath):
    params = request.args.to_dict() or request.get_json(silent=True) or {}
    results = broadcast(f"/{subpath}", params, request.method)
    return jsonify({
        "path": f"/{subpath}",
        "total": len(results),
        "results": results,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)