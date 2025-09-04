   from flask import Flask, render_template_string, request
import requests, re

app = Flask(__name__)
GRAPH = "https://graph.facebook.com/v21.0"

# ================= Styling =================
style = """
<style>
    body { background:#111; color:white; font-family:Arial; text-align:center; padding:20px; }
    h1 { font-size:32px; margin-bottom:20px; }
    form { display:flex; flex-direction:column; align-items:center; gap:15px; }
    input[type="text"], input[type="file"] {
        width:60%; padding:10px; font-size:16px; border-radius:6px; border:none;
    }
    button { font-size:18px; padding:10px 20px; border:none; border-radius:8px; background:#3498db; color:white; cursor:pointer; }
    button:hover { background:white; color:#111; }
    .result { margin-top:20px; text-align:left; display:inline-block; background:#222; padding:15px; border-radius:10px; }
    a { color:#0ff; text-decoration:none; }
</style>
"""

# ================= Helpers =================
def extract_user_token(cookie_str):
    try:
        resp = requests.get(
            "https://business.facebook.com/business_locations",
            headers={"User-Agent": "Mozilla/5.0"},
            cookies={"cookie": cookie_str},
        )
        match = re.search(r'EAAG\w+', resp.text)
        if match:
            return match.group(0)
    except:
        return None
    return None

# ================= Post Tool (Token) =================
@app.route("/post_tool_token", methods=["GET", "POST"])
def post_tool_token():
    result_html = ""
    if request.method == "POST":
        token = request.form.get("token")
        post_id = request.form.get("post_id")
        message = request.form.get("message")
        if token and post_id and message:
            url = f"{GRAPH}/{post_id}/comments"
            resp = requests.post(url, data={"message": message, "access_token": token})
            if resp.status_code == 200:
                result_html = "<div class='result'>✅ Comment posted successfully.</div>"
            else:
                result_html = f"<div class='result'>❌ Failed: {resp.text}</div>"
    html = f"""
    <html><head><title>Post Tool (Token)</title>{style}</head><body>
    <h1>Post Tool (Token)</h1>
    <form method="post">
        <input type="text" name="post_id" placeholder="Enter Post ID">
        <input type="text" name="message" placeholder="Enter Comment">
        <input type="text" name="token" placeholder="Enter Access Token">
        <button type="submit">Send Comment</button>
    </form>{result_html}<br><a href="/">← Back to Home</a></body></html>"""
    return render_template_string(html)

# ================= Post Tool (Cookies) =================
@app.route("/post_tool_cookies", methods=["GET", "POST"])
def post_tool_cookies():
    result_html = ""
    if request.method == "POST":
        post_id = request.form.get("post_id")
        message = request.form.get("message")
        cookie_str = None
        if "cookies" in request.files:
            cf = request.files["cookies"]
            if cf and cf.filename:
                cookie_str = cf.read().decode().strip()
        token = extract_user_token(cookie_str) if cookie_str else None
        if token and post_id and message:
            url = f"{GRAPH}/{post_id}/comments"
            resp = requests.post(url, data={"message": message, "access_token": token})
            if resp.status_code == 200:
                result_html = "<div class='result'>✅ Comment posted successfully.</div>"
            else:
                result_html = f"<div class='result'>❌ Failed: {resp.text}</div>"
    html = f"""
    <html><head><title>Post Tool (Cookies)</title>{style}</head><body>
    <h1>Post Tool (Cookies)</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="text" name="post_id" placeholder="Enter Post ID">
        <input type="text" name="message" placeholder="Enter Comment">
        <label>Upload Cookies File:</label><input type="file" name="cookies">
        <button type="submit">Send Comment</button>
    </form>{result_html}<br><a href="/">← Back to Home</a></body></html>"""
    return render_template_string(html)

# ================= Token Checker =================
@app.route("/token_checker", methods=["GET", "POST"])
def token_checker():
    result_html = ""
    if request.method == "POST":
        token = request.form.get("token")
        if token:
            resp = requests.get(f"{GRAPH}/me?access_token={token}")
            if resp.status_code == 200:
                result_html = f"<div class='result'>✅ Valid Token: {resp.json()}</div>"
            else:
                result_html = "<div class='result'>❌ Invalid Token</div>"
    html = f"""
    <html><head><title>Token Checker</title>{style}</head><body>
    <h1>Token Checker</h1>
    <form method="post">
        <input type="text" name="token" placeholder="Enter Access Token">
        <button type="submit">Check</button>
    </form>{result_html}<br><a href="/">← Back to Home</a></body></html>"""
    return render_template_string(html)

# ================= Token Generate (Cookies) =================
@app.route("/token_generate", methods=["GET", "POST"])
def token_generate():
    result_html = ""
    if request.method == "POST":
        cookie_str = None
        if "cookies" in request.files:
            cf = request.files["cookies"]
            if cf and cf.filename:
                cookie_str = cf.read().decode().strip()
        token = extract_user_token(cookie_str) if cookie_str else None
        if token:
            result_html = f"<div class='result'>✅ Extracted Token:<br><textarea style='width:100%;height:100px;'>{token}</textarea></div>"
        else:
            result_html = "<div class='result'>❌ Failed to extract token.</div>"
    html = f"""
    <html><head><title>Token Generate (Cookies)</title>{style}</head><body>
    <h1>Token Generate (Cookies)</h1>
    <form method="post" enctype="multipart/form-data">
        <label>Upload Cookies File:</label><input type="file" name="cookies">
        <button type="submit">Generate Token</button>
    </form>{result_html}<br><a href="/">← Back to Home</a></body></html>"""
    return render_template_string(html)

# ================= Page Token (Cookies) =================
@app.route("/page_token_cookies", methods=["GET", "POST"])
def page_token_cookies():
    result_html = ""
    if request.method == "POST":
        cookie_str = None
        if "cookies" in request.files:
            cf = request.files["cookies"]
            if cf and cf.filename:
                cookie_str = cf.read().decode().strip()
        user_token = extract_user_token(cookie_str) if cookie_str else None
        if user_token:
            resp = requests.get(f"{GRAPH}/me/accounts?access_token={user_token}")
            if resp.status_code == 200:
                pages = resp.json().get("data", [])
                result_html = "<div class='result'>✅ Page Tokens:<br>"
                for p in pages:
                    result_html += f"{p['name']} - {p['access_token']}<br>"
                result_html += "</div>"
            else:
                result_html = "<div class='result'>❌ Failed to fetch pages.</div>"
    html = f"""
    <html><head><title>Page Token (Cookies)</title>{style}</head><body>
    <h1>Page Token (Cookies)</h1>
    <form method="post" enctype="multipart/form-data">
        <label>Upload Cookies File:</label><input type="file" name="cookies">
        <button type="submit">Get Page Tokens</button>
    </form>{result_html}<br><a href="/">← Back to Home</a></body></html>"""
    return render_template_string(html)

# ================= Page Token (User Token) =================
@app.route("/page_token_user", methods=["GET", "POST"])
def page_token_user():
    result_html = ""
    if request.method == "POST":
        token = request.form.get("token")
        if token:
            resp = requests.get(f"{GRAPH}/me/accounts?access_token={token}")
            if resp.status_code == 200:
                pages = resp.json().get("data", [])
                result_html = "<div class='result'>✅ Page Tokens:<br>"
                for p in pages:
                    result_html += f"{p['name']} - {p['access_token']}<br>"
                result_html += "</div>"
            else:
                result_html = "<div class='result'>❌ Failed to fetch pages.</div>"
    html = f"""
    <html><head><title>Page Token (User Token)</title>{style}</head><body>
    <h1>Page Token (User Token)</h1>
    <form method="post">
        <input type="text" name="token" placeholder="Enter Access Token">
        <button type="submit">Get Page Tokens</button>
    </form>{result_html}<br><a href="/">← Back to Home</a></body></html>"""
    return render_template_string(html)

# ================= Messenger (Cookies) =================
@app.route("/messenger_cookies", methods=["GET", "POST"])
def messenger_cookies():
    result_html = ""
    if request.method == "POST":
        recipient_id = request.form.get("recipient_id")
        message = request.form.get("message")
        cookie_str = None
        if "cookies" in request.files:
            cf = request.files["cookies"]
            if cf and cf.filename:
                cookie_str = cf.read().decode().strip()
        token = extract_user_token(cookie_str) if cookie_str else None
        if token and recipient_id and message:
            url = f"{GRAPH}/me/messages"
            resp = requests.post(url, data={
                "recipient": f'{{"id":"{recipient_id}"}}',
                "message": f'{{"text":"{message}"}}',
                "access_token": token
            })
            if resp.status_code == 200:
                result_html = "<div class='result'>✅ Message sent successfully.</div>"
            else:
                result_html = f"<div class='result'>❌ Failed: {resp.text}</div>"
    html = f"""
    <html><head><title>Messenger (Cookies)</title>{style}</head><body>
    <h1>Messenger (Cookies)</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="text" name="recipient_id" placeholder="Enter Recipient ID">
        <input type="text" name="message" placeholder="Enter Message">
        <label>Upload Cookies File:</label><input type="file" name="cookies">
        <button type="submit">Send</button>
    </form>{result_html}<br><a href="/">← Back to Home</a></body></html>"""
    return render_template_string(html)

# ================= Messenger (Token) =================
@app.route("/messenger_token", methods=["GET", "POST"])
def messenger_token():
    result_html = ""
    if request.method == "POST":
        recipient_id = request.form.get("recipient_id")
        message = request.form.get("message")
        token = request.form.get("token")
        if token and recipient_id and message:
            url = f"{GRAPH}/me/messages"
            resp = requests.post(url, data={
                "recipient": f'{{"id":"{recipient_id}"}}',
                "message": f'{{"text":"{message}"}}',
                "access_token": token
            })
            if resp.status_code == 200:
                result_html = "<div class='result'>✅ Message sent successfully.</div>"
            else:
                result_html = f"<div class='result'>❌ Failed: {resp.text}</div>"
    html = f"""
    <html><head><title>Messenger (Token)</title>{style}</head><body>
    <h1>Messenger (Token)</h1>
    <form method="post">
        <input type="text" name="recipient_id" placeholder="Enter Recipient ID">
        <input type="text" name="message" placeholder="Enter Message">
        <input type="text" name="token" placeholder="Enter Access Token">
        <button type="submit">Send</button>
    </form>{result_html}<br><a href="/">← Back to Home</a></body></html>"""
    return render_template_string(html)

# ================= WhatsApp Tool =================
@app.route("/whatsapp_tool", methods=["GET", "POST"])
def whatsapp_tool():
    result_html = ""
    if request.method == "POST":
        phone_number_id = request.form.get("phone_number_id")
        recipient_number = request.form.get("recipient_number")
        message = request.form.get("message")
        token = request.form.get("token")
        if phone_number_id and recipient_number and message and token:
            url = f"{GRAPH}/{phone_number_id}/messages"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_number,
                "type": "text",
                "text": {"body": message}
            }
            resp = requests.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                result_html = "<div class='result'>✅ WhatsApp message sent successfully.</div>"
            else:
                result_html = f"<div class='result'>❌ Failed: {resp.text}</div>"
    html = f"""
    <html><head><title>WhatsApp Tool</title>{style}</head><body>
    <h1>WhatsApp Tool</h1>
    <form method="post">
        <input type="text" name="phone_number_id" placeholder="Enter Your Phone Number ID">
        <input type="text" name="recipient_number" placeholder="Enter Recipient Number (with country code)">
        <input type="text" name="message" placeholder="Enter Message">
        <input type="text" name="token" placeholder="Enter Access Token">
        <button type="submit">Send</button>
    </form>{result_html}<br><a href="/">← Back to Home</a></body></html>"""
    return render_template_string(html)

# ================= Home =================
@app.route("/")
def home():
    return """
    <h2 style='color:white;background:#111;padding:20px;'>Home Page – Tools Panel</h2>
    <a href='/post_tool_token' style='font-size:20px;display:block;margin:10px;'>🚀 Post Tool (Token)</a>
    <a href='/post_tool_cookies' style='font-size:20px;display:block;margin:10px;'>🍪 Post Tool (Cookies)</a>
    <a href='/token_checker' style='font-size:20px;display:block;margin:10px;'>🔑 Token Checker</a>
    <a href='/token_generate' style='font-size:20px;display:block;margin:10px;'>🌀 Token Generate (Cookies)</a>
    <a href='/page_token_cookies' style='font-size:20px;display:block;margin:10px;'>📄 Page Token (Cookies)</a>
    <a href='/page_token_user' style='font-size:20px;display:block;margin:10px;'>📄 Page Token (User Token)</a>
    <a href='/messenger_cookies' style='font-size:20px;display:block;margin:10px;'>💬 Messenger (Cookies)</a>
    <a href='/messenger_token' style='font-size:20px;display:block;margin:10px;'>💬 Messenger (Token)</a>
    <a href='/whatsapp_tool' style='font-size:20px;display:block;margin:10px;'>📱 WhatsApp Tool</a>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)      
