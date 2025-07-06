# Flask-based OSINTDog web backend (no config file, no key system, full functionality)

from flask import Flask, request, jsonify, send_file, render_template
from datetime import datetime
import aiohttp
import asyncio
import json
import io

app = Flask(__name__)

# Hardcoded API key
API_KEY = "f84294f83330bc3fd48b66aea704ecbb"

def remove_credit(data):
    """Remove credit field from API responses recursively"""
    if isinstance(data, dict):
        # Remove credit field if it exists
        data.pop("credit", None)
        # Recursively clean nested dictionaries
        for key, value in data.items():
            if isinstance(value, dict):
                remove_credit(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        remove_credit(item)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                remove_credit(item)
    return data

@app.route("/")
def home():
    return render_template("index.html")

async def api_post(endpoint, payload):
    url = f"https://osintdog.com{endpoint}"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            return await resp.json()

async def api_get(endpoint, params=None):
    url = f"https://osintdog.com{endpoint}"
    headers = {"X-API-Key": API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            return await resp.json()

# General search endpoint
@app.route("/search", methods=["POST"])
def search():
    data = request.json
    search_type = data.get("search_type")
    query = data.get("query")
    endpoint = data.get("endpoint")
    is_get = data.get("is_get", False)
    params = data.get("params")
    post_body = data.get("post_body")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if is_get:
            result = loop.run_until_complete(api_get(endpoint, params))
        else:
            if post_body is None:
                if endpoint == "/api/search":
                    post_body = {"field": [{search_type: query}]}
                elif endpoint in ["/api/snusbase", "/api/breachbase", "/api/hackcheck", "/api/intelvault"]:
                    post_body = {"term": query, "search_type": search_type}
                elif endpoint == "/api/oathnet/search":
                    post_body = {"query": query, "type": "text", "includeSnus": True}
                elif endpoint == "/api/oathnet/ghunt":
                    post_body = {"email": query}
                else:
                    post_body = {}
            result = loop.run_until_complete(api_post(endpoint, post_body))
        
        # Remove credit from result
        result = remove_credit(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/seon_email", methods=["GET"])
def seon_email():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing email parameter"}), 400
    
    async def get_seon():
        url = f"https://osintdog.com/api/seon/email?email={email}"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                return await resp.json()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(get_seon())
        
        # Remove credit from result
        result = remove_credit(result)
        
        # Process the result to flatten nested objects
        if isinstance(result, dict):
            processed_result = {}
            for key, value in result.items():
                if isinstance(value, dict):
                    # Flatten nested dictionaries
                    for nested_key, nested_value in value.items():
                        processed_result[f"{key}_{nested_key}"] = nested_value
                elif isinstance(value, list):
                    # Convert lists to comma-separated strings
                    processed_result[key] = ', '.join(str(item) for item in value) if value else 'None'
                else:
                    processed_result[key] = value
            return jsonify(processed_result)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/seon_phone", methods=["GET"])
def seon_phone():
    phone = request.args.get("phone")
    if not phone:
        return jsonify({"error": "Missing phone parameter"}), 400
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(api_get("/api/seon/phone", params={"phone": phone}))
        
        # Remove credit from result
        result = remove_credit(result)
        
        # Process the result to flatten nested objects
        if isinstance(result, dict):
            processed_result = {}
            for key, value in result.items():
                if isinstance(value, dict):
                    # Flatten nested dictionaries
                    for nested_key, nested_value in value.items():
                        processed_result[f"{key}_{nested_key}"] = nested_value
                elif isinstance(value, list):
                    # Convert lists to comma-separated strings
                    processed_result[key] = ', '.join(str(item) for item in value) if value else 'None'
                else:
                    processed_result[key] = value
            return jsonify(processed_result)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# All additional endpoints
@app.route("/snusbase", methods=["POST"])
def snusbase():
    data = request.json
    return search_proxy("/api/snusbase", data)

@app.route("/intelvault", methods=["POST"])
def intelvault():
    data = request.json
    return search_proxy("/api/intelvault", data)

@app.route("/breachbase", methods=["POST"])
def breachbase():
    data = request.json
    return search_proxy("/api/breachbase", data)

@app.route("/hackcheck", methods=["POST"])
def hackcheck():
    data = request.json
    return search_proxy("/api/hackcheck", data)

@app.route("/leakcheck", methods=["GET"])
def leakcheck():
    term = request.args.get("term")
    if not term:
        return jsonify({"error": "Missing term parameter"}), 400
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(api_get("/api/leakcheck", params={"term": term}))
        result = remove_credit(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/oathnet_ip", methods=["GET"])
def oathnet_ip():
    ip = request.args.get("ip")
    if not ip:
        return jsonify({"error": "Missing IP parameter"}), 400
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(api_get("/api/oathnet/ip-info", params={"ip": ip}))
        result = remove_credit(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/oathnet_roblox", methods=["GET"])
def oathnet_roblox():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Missing username parameter"}), 400
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(api_get("/api/oathnet/roblox-userinfo", params={"username": username}))
        result = remove_credit(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/oathnet_discord_roblox", methods=["GET"])
def oathnet_discord_roblox():
    discordid = request.args.get("discordid")
    if not discordid:
        return jsonify({"error": "Missing discordid parameter"}), 400
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(api_get("/api/oathnet/discord-to-roblox", params={"discordid": discordid}))
        result = remove_credit(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/oathnet_holhe", methods=["GET"])
def oathnet_holhe():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing email parameter"}), 400
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(api_get("/api/oathnet/holhe", params={"email": email}))
        result = remove_credit(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/oathnet_ghunt", methods=["POST"])
def oathnet_ghunt():
    data = request.json
    email = data.get("email")
    if not email:
        return jsonify({"error": "Missing email field"}), 400
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(api_post("/api/oathnet/ghunt", {"email": email}))
        result = remove_credit(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ping")
def ping():
    return "API is online."

@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

# Helper for POST-based searches
def search_proxy(endpoint, data):
    search_type = data.get("search_type")
    query = data.get("query")
    if not query or not search_type:
        return jsonify({"error": "Missing required fields"}), 400
    payload = {"term": query, "search_type": search_type}
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(api_post(endpoint, payload))
        result = remove_credit(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
