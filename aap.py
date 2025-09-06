 from flask import Flask, request, render_template_string, send_file
import requests, time, uuid, json
from io import BytesIO

app = Flask(__name__)
GRAPH = "https://graph.facebook.com/v21.0"

# =========================
# Approval System
# =========================
APPROVAL_KEY = "skfulwaria"  # рдмрджрд▓рдирд╛ рд╣реЛ рддреЛ рдпрд╣рд╛рдБ рдмрджрд▓реЗрдВ

def check_approval(req):
    return (req.form.get("approval_key") or "") == APPROVAL_KEY

# =========================
# Helpers
# =========================
def read_lines_from_upload(fs):
    """Upload рдХреА рдЧрдпреА text file рд╕реЗ lines рдкрдврд╝реЗрдВ (UTF-8 auto)"""
    if not fs or not fs.filename:
        return []
    return [ln.strip() for ln in fs.read().decode(errors="ignore").splitlines() if ln.strip()]

def parse_multiline(s):
    """Textarea рдХреЗ multi-line рдЯреЗрдХреНрд╕реНрдЯ рдХреЛ list рдореЗрдВ рдмрджрд▓реЗрдВ"""
    if not s:
        return []
    return [ln.strip() for ln in s.splitlines() if ln.strip()]

def parse_csv_or_lines(s):
    """Comma separated + newlines рджреЛрдиреЛрдВ рдХреЛ list рдореЗрдВ рдмрджрд▓реЗрдВ"""
    if not s:
        return []
    out = []
    for chunk in s.splitlines():
        for piece in chunk.split(","):
            piece = piece.strip()
            if piece:
                out.append(piece)
    return out

def safe_sleep(seconds):
    """Int sleep (negative -> 0)"""
    try:
        seconds = int(seconds)
        if seconds < 0:
            seconds = 0
    except:
        seconds = 0
    time.sleep(seconds)

def make_download_response(text_data: str, base_name: str = "output"):
    """Text response рдХреЛ downloadable file рдХреЗ рд░реВрдк рдореЗрдВ рднреЗрдЬреЗрдВ"""
    buf = BytesIO()
    buf.write(text_data.encode("utf-8", errors="ignore"))
    buf.seek(0)
    filename = f"{base_name}_{uuid.uuid4().hex[:8]}.txt"
    return send_file(buf, as_attachment=True, download_name=filename, mimetype="text/plain")

def is_comment_disabled(error_obj):
    """
    рдХреБрдЫ common messages рдкрдХрдбрд╝рдиреЗ рдХреЗ рд▓рд┐рдП тАФ рддрд╛рдХрд┐ comments рдмрдВрдж/limited рд▓рдЧреЗ рддреЛ next post рдкрд░ shift рдХрд░ рджреЗрдВред
    """
    if not error_obj:
        return False
    if isinstance(error_obj, dict):
        msg = str(error_obj.get("message", "")) + " " + str(error_obj.get("error_user_msg", ""))
    else:
        msg = str(error_obj)
    phrases = [
        "turned off", "limited", "cannot comment", "not permitted", "commenting is limited",
        "comments have been turned off", "insufficient permission", "unsupported post request"
    ]
    m = msg.lower()
    return any(p in m for p in phrases)

def filter_valid_tokens(tokens):
    """/me call рд╕реЗ valid tokens filter рдХрд░реЗрдВ"""
    valid = []
    for t in tokens:
        try:
            r = requests.get(f"{GRAPH}/me", params={"access_token": t}, timeout=15)
            if r.status_code == 200 and isinstance(r.json(), dict) and r.json().get("id"):
                valid.append(t)
        except:
            pass
    return valid

# =========================
# Styles
# =========================
styles = {
    "home": """
    <style>
    body { background:#001f3f; color:#eee; font-family:Arial; text-align:center; margin:0; }
    h1 { color:#00ffff; margin:20px 0; font-size:2.0em; }
    .wrap { width:95%; max-width:900px; margin:0 auto 40px; }
    a { display:block; margin:10px 0; padding:14px 16px; background:#00ffff; color:#001f3f;
        border-radius:12px; font-size:1.05em; text-decoration:none; font-weight:bold; }
    a:hover { background:#33ffff; }
    .note {margin:14px auto; padding:12px; background:#013; border-radius:10px;}
    .muted { opacity:0.9; font-size:0.95em; }
    </style>
    """,
    "card": """
    <style>
    body { background:#0b1220; color:#fff; font-family:Arial; margin:0; }
    h1 { color:#7fd0ff; text-align:center; margin:20px 0; }
    form { margin:18px auto; padding:18px; background:#0f1a2e; border-radius:14px; width:94%; max-width:860px; }
    input,button,textarea,select { margin:8px 0; padding:12px; border-radius:9px; border:none; width:100%; font-size:1.0em; }
    button { background:#7fd0ff; color:#00172a; font-weight:bold; cursor:pointer; }
    button:hover { filter:brightness(1.08); }
    label { display:block; text-align:left; font-weight:bold; margin-top:6px; }
    .result { margin:18px auto; padding:14px; background:#0a1526; border-radius:12px; width:94%; max-width:860px; text-align:left; white-space:pre-wrap; }
    a.back { color:#7fd0ff; display:block; margin:16px auto; width:94%; max-width:860px; text-decoration:none;
        padding:12px; background:#0f1a2e; border-radius:10px; text-align:center; }
    .muted { opacity:0.85; font-size:0.95em; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap:10px; }
    </style>
    """
}

# =========================
# Home (Part-2)
# =========================
@app.route("/")
def home():
    html = f"""
    <html><head><title>All Tools тАФ Part 2</title>{styles['home']}</head><body>
      <div class="wrap">
        <h1>All Tools тАФ Part 2</h1>
        <div class="note">Official Graph/Cloud API рд╡рд╛рд▓реЗ tools workable рд╣реИрдВ. Cookies-based methods disabled (policy/ToS reasons).</div>

        <a href="/post_tool_token">Post Tool (by Token) тАФ Infinite + Shift + Speed</a>
        <a href="/messenger_token">Messenger (by Token) тАФ Cyclic + Speed</a>

        <a href="/whatsapp_json">WhatsApp Tool #1 тАФ Create JSON (Download)</a>
        <a href="/whatsapp_send">WhatsApp Tool #2 тАФ Send Message</a>

        <div class="muted">рдиреЛрдЯ: рд╣рд░ рдлреЙрд░реНрдо рдореЗрдВ Approval Key рдЪрд╛рд╣рд┐рдП тАФ default: <b>{APPROVAL_KEY}</b></div>
      </div>
    </body></html>
    """
    return render_template_string(html)

# =========================
# Post Tool (by Token) тАФ Infinite Cycle + Auto shift + Valid-token-filter + Speed
# =========================
@app.route("/post_tool_token", methods=["GET", "POST"])
def post_tool_token():
    result_txt = ""
    if request.method == "POST":
        if not check_approval(request):
            result_txt = "тЭМ Approval Failed"
        else:
            heater = (request.form.get("heater") or request.form.get("hater") or "").strip()
            speed = int(request.form.get("speed") or 2)

            post_ids = parse_csv_or_lines(request.form.get("post_ids") or "")

            tokens = []
            tokens += parse_multiline(request.form.get("token"))
            if "token_file" in request.files and request.files["token_file"].filename:
                tokens += read_lines_from_upload(request.files["token_file"])
            tokens = filter_valid_tokens(tokens)  # тЬЕ рдХреЗрд╡рд▓ valid tokens

            comments = []
            comments += parse_multiline(request.form.get("comment"))
            if "comment_file" in request.files and request.files["comment_file"].filename:
                comments += read_lines_from_upload(request.files["comment_file"])

            if not post_ids:
                result_txt = "тЭМ Post IDs required"
            elif not comments:
                result_txt = "тЭМ At least one comment required"
            elif not tokens:
                result_txt = "тЭМ No valid tokens found (invalid tokens auto-removed)"
            else:
                logs = [f"ЁЯФе Heater: {heater or '(none)'} | Starting Post Tool (Token) | "
                        f"Valid Tokens: {len(tokens)} | Delay: {speed}s"]
                # Cyclic indexes
                c_idx, t_idx = 0, 0

                for pid in post_ids:
                    pid = pid.strip()
                    if not pid:
                        continue

                    comment = comments[c_idx % len(comments)]
                    token = tokens[t_idx % len(tokens)]
                    c_idx = (c_idx + 1) % len(comments)
                    t_idx = (t_idx + 1) % len(tokens)

                    msg = f"{comment} {heater}".strip() if heater else comment
                    try:
                        r = requests.post(f"{GRAPH}/{pid}/comments",
                                          data={"message": msg, "access_token": token},
                                          timeout=30)
                        try:
                            data = r.json()
                        except:
                            data = {"raw": r.text}

                        if r.status_code == 200 and isinstance(data, dict) and data.get("id"):
                            logs.append(f"тЬЕ Commented on {pid}")
                        else:
                            err = data.get("error") if isinstance(data, dict) else None
                            if is_comment_disabled(err):
                                logs.append(f"тЪая╕П Comments closed/blocked on {pid} тАФ shifting to next post")
                            else:
                                logs.append(f"тЭМ Failed on {pid}: {data}")
                    except Exception as e:
                        logs.append(f"тЪая╕П Error on {pid}: {e}")

                    safe_sleep(speed)

                result_txt = "\n".join(logs)

    html = f"""
    <html><head><title>Post Tool (Token)</title>{styles['card']}</head><body>
      <h1>Post Tool (by Token)</h1>
      <form method="post" enctype="multipart/form-data">
        <label>Heater Name (optional)</label>
        <input type="text" name="heater" placeholder="e.g., BLACK_MAFFIYA">
        <label>Delay seconds (default 2)</label>
        <input type="number" name="speed" placeholder="2" min="0">
        <label>Post IDs (comma separated рдпрд╛ one per line)</label>
        <textarea name="post_ids" rows="3" placeholder="123,456,789"></textarea>

        <label>Comments (paste рдпрд╛ upload file)</label>
        <textarea name="comment" rows="3" placeholder="One comment per line"></textarea>
        <input type="file" name="comment_file">

        <label>Tokens (paste рдпрд╛ upload file)</label>
        <textarea name="token" rows="3" placeholder="One token per line"></textarea>
        <input type="file" name="token_file">

        <input type="password" name="approval_key" placeholder="Approval Key" required>

        <div class="row">
          <button type="submit">Run</button>
          <button formaction="/download_from_form" formmethod="post" name="download_btn" value="1">Download Result</button>
        </div>

        <textarea name="__download_data" style="display:none;">{result_txt}</textarea>
        <input type="hidden" name="__download_name" value="post_tool_results">
      </form>
      <div class="result">{result_txt}</div>
      <a class="back" href="/">тЧА Back to Home</a>
    </body></html>
    """
    return render_template_string(html)

# =========================
# Messenger (by Token) тАФ Cyclic + Speed + Valid-token-filter
# =========================
@app.route("/messenger_token", methods=["GET", "POST"])
def messenger_token():
    result_txt = ""
    if request.method == "POST":
        if not check_approval(request):
            result_txt = "тЭМ Approval Failed"
        else:
            heater = (request.form.get("heater") or request.form.get("hater") or "").strip()
            speed = int(request.form.get("speed") or 2)

            user_ids = parse_csv_or_lines(request.form.get("user_ids") or "")

            tokens = []
            tokens += parse_multiline(request.form.get("token"))
            if "token_file" in request.files and request.files["token_file"].filename:
                tokens += read_lines_from_upload(request.files["token_file"])
            tokens = filter_valid_tokens(tokens)  # тЬЕ рдХреЗрд╡рд▓ valid tokens

            messages = []
            messages += parse_multiline(request.form.get("message"))
            if "message_file" in request.files and request.files["message_file"].filename:
                messages += read_lines_from_upload(request.files["message_file"])

            if not (user_ids and tokens and messages):
                result_txt = "тЭМ User IDs / Messages / Valid Tokens required"
            else:
                logs = [f"ЁЯФе Heater: {heater or '(none)'} | Starting Messenger (Token) | "
                        f"Valid Tokens: {len(tokens)} | Delay: {speed}s"]
                url = f"{GRAPH}/me/messages"

                # cyclic indexes
                m_idx, t_idx = 0, 0

                for uid in user_ids:
                    uid = uid.strip()
                    if not uid:
                        continue

                    msg_text = messages[m_idx % len(messages)]
                    token = tokens[t_idx % len(tokens)]
                    m_idx = (m_idx + 1) % len(messages)
                    t_idx = (t_idx + 1) % len(tokens)

                    txt = f"{msg_text} {heater}".strip() if heater else msg_text
                    payload = {"recipient": {"id": uid}, "message": {"text": txt}}
                    try:
                        r = requests.post(url, params={"access_token": token}, json=payload, timeout=30)
                        try:
                            data = r.json()
                        except:
                            data = {"raw": r.text}
                        if r.status_code == 200 and isinstance(data, dict) and data.get("message_id"):
                            logs.append(f"тЬЕ Sent to {uid}")
                        else:
                            logs.append(f"тЭМ Failed to {uid}: {data}")
                    except Exception as e:
                        logs.append(f"тЪая╕П Error to {uid}: {e}")

                    safe_sleep(speed)

                result_txt = "\n".join(logs)

    html = f"""
    <html><head><title>Messenger (Token)</title>{styles['card']}</head><body>
      <h1>Messenger (by Token)</h1>
      <div class="muted">Note: Page access token + pages_messaging permission + proper Page setup required.</div>
      <form method="post" enctype="multipart/form-data">
        <label>Heater Name (optional)</label>
        <input type="text" name="heater" placeholder="e.g., BLACK_MAFFIYA">
        <label>Delay seconds (default 2)</label>
        <input type="number" name="speed" placeholder="2" min="0">
        <label>Recipient IDs (comma separated рдпрд╛ one per line)</label>
        <textarea name="user_ids" rows="3" placeholder="10001,10002,10003"></textarea>

        <label>Messages (paste рдпрд╛ upload file)</label>
        <textarea name="message" rows="3" placeholder="One message per line"></textarea>
        <input type="file" name="message_file">

        <label>Tokens (paste рдпрд╛ upload file)</label>
        <textarea name="token" rows="3" placeholder="Page tokens (one per line)"></textarea>
        <input type="file" name="token_file">

        <input type="password" name="approval_key" placeholder="Approval Key" required>

        <div class="row">
          <button type="submit">Send</button>
          <button formaction="/download_from_form" formmethod="post" name="download_btn" value="1">Download Result</button>
        </div>

        <textarea name="__download_data" style="display:none;">{result_txt}</textarea>
        <input type="hidden" name="__download_name" value="messenger_results">
      </form>
      <div class="result">{result_txt}</div>
      <a class="back" href="/">тЧА Back to Home</a>
    </body></html>
    """
    return render_template_string(html)

# =========================
# WhatsApp Tool #1 тАФ Create JSON (Preview + Download)
# =========================
@app.route("/whatsapp_json", methods=["GET", "POST"])
def whatsapp_json():
    result_txt = ""
    if request.method == "POST":
        if not check_approval(request):
            result_txt = "тЭМ Approval Failed"
        else:
            number = (request.form.get("number") or "").strip()
            message = (request.form.get("message") or "").strip()
            heater = (request.form.get("heater") or request.form.get("hater") or "").strip()
            phone_number_id = (request.form.get("phone_number_id") or "").strip()
            wa_token = (request.form.get("wa_token") or "").strip()

            final_message = f"{message} {heater}".strip() if heater else message
            if not (number and final_message and phone_number_id and wa_token):
                result_txt = "тЭМ Number / Message / Phone Number ID / WA Token required"
            else:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": number,
                    "type": "text",
                    "text": {"body": final_message}
                }
                result_txt = json.dumps(payload, indent=2, ensure_ascii=False)

    html = f"""
    <html><head><title>WhatsApp JSON</title>{styles['card']}</head><body>
      <h1>WhatsApp Tool #1 тАФ Create JSON</h1>
      <form method="post">
        <label>Recipient Number (e.g., +9198xxxxxxx)</label>
        <input type="text" name="number" placeholder="+91XXXXXXXXXX" required>
        <label>Message</label>
        <textarea name="message" rows="3" placeholder="Message text" required></textarea>
        <label>Heater Name (optional)</label>
        <input type="text" name="heater" placeholder="e.g., BLACK_MAFFIYA">
        <label>Your Phone Number ID (WA Cloud API)</label>
        <input type="text" name="phone_number_id" placeholder="Phone Number ID" required>
        <label>WhatsApp Access Token</label>
        <input type="text" name="wa_token" placeholder="WA Access Token" required>
        <input type="password" name="approval_key" placeholder="Approval Key" required>

        <div class="row">
          <button type="submit">Preview JSON</button>
          <button formaction="/download_from_form" formmethod="post" name="download_btn" value="1">Download JSON</button>
        </div>

        <textarea name="__download_data" style="display:none;">{result_txt}</textarea>
        <input type="hidden" name="__download_name" value="whatsapp_payload">
      </form>
      <div class="result">{result_txt}</div>
      <a class="back" href="/">тЧА Back to Home</a>
    </body></html>
    """
    return render_template_string(html)

# =========================
# WhatsApp Tool #2 тАФ Send Message
# =========================
@app.route("/whatsapp_send", methods=["GET", "POST"])
def whatsapp_send():
    result_txt = ""
    if request.method == "POST":
        if not check_approval(request):
            result_txt = "тЭМ Approval Failed"
        else:
            number = (request.form.get("number") or "").strip()
            message = (request.form.get("message") or "").strip()
            heater = (request.form.get("heater") or request.form.get("hater") or "").strip()
            phone_number_id = (request.form.get("phone_number_id") or "").strip()
            wa_token = (request.form.get("wa_token") or "").strip()

            final_message = f"{message} {heater}".strip() if heater else message
            if not (number and final_message and phone_number_id and wa_token):
                result_txt = "тЭМ Number / Message / Phone Number ID / WA Token required"
            else:
                url = f"{GRAPH}/{phone_number_id}/messages"
                headers = {"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"}
                payload = {"messaging_product": "whatsapp", "to": number, "type": "text", "text": {"body": final_message}}
                try:
                    r = requests.post(url, headers=headers, json=payload, timeout=30)
                    result_txt = f"Status: {r.status_code}\n\n{r.text}"
                except Exception as e:
                    result_txt = f"тЪая╕П Error тАФ {e}"

    html = f"""
    <html><head><title>WhatsApp Send</title>{styles['card']}</head><body>
      <h1>WhatsApp Tool #2 тАФ Send Message</h1>
      <form method="post">
        <label>Recipient Number (e.g., +9198xxxxxxx)</label>
        <input type="text" name="number" placeholder="+91XXXXXXXXXX" required>
        <label>Message</label>
        <textarea name="message" rows="3" placeholder="Message text" required></textarea>
        <label>Heater Name (optional)</label>
        <input type="text" name="heater" placeholder="e.g., BLACK_MAFFIYA">
        <label>Your Phone Number ID (WA Cloud API)</label>
        <input type="text" name="phone_number_id" placeholder="Phone Number ID" required>
        <label>WhatsApp Access Token</label>
        <input type="text" name="wa_token" placeholder="WA Access Token" required>
        <input type="password" name="approval_key" placeholder="Approval Key" required>

        <div class="row">
          <button type="submit">Send Message</button>
          <button formaction="/download_from_form" formmethod="post" name="download_btn" value="1">Download Result</button>
        </div>

        <textarea name="__download_data" style="display:none;">{result_txt}</textarea>
        <input type="hidden" name="__download_name" value="whatsapp_send_result">
      </form>
      <div class="result">{result_txt}</div>
      <a class="back" href="/">тЧА Back to Home</a>
    </body></html>
    """
    return render_template_string(html)

# =========================
# Generic Download endpoint (reads hidden fields)
# =========================
@app.route("/download_from_form", methods=["POST"])
def download_from_form():
    if not check_approval(request):
        return make_download_response("Approval Failed", "error")
    data = request.form.get("__download_data") or ""
    name = request.form.get("__download_name") or "download"
    return make_download_response(data, name)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    # Production рдореЗрдВ debug=False рд░рдЦреЗрдВ
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
