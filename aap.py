from flask import Flask, request, render_template_string, jsonify
import requests
import time
import threading
import random
import os
from datetime import datetime
import logging

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Global variables for task management
active_tasks = {}
task_status = {}
comments_data = []
messages_data = []

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Facebook API Helper
# ---------------------------
class FacebookAutomation:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.session = requests.Session()

    def extract_token_from_cookies(self, cookies_string):
        """Cookies से token extract करें"""
        try:
            cookies = {}
            for cookie in cookies_string.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
            token_keys = ['access_token', 'EAAB', 'token', 'fb_access_token']
            for key in cookies.keys():
                for pattern in token_keys:
                    if pattern in key and len(cookies[key]) > 50:
                        return cookies[key]
            return None
        except Exception as e:
            logger.error(f"Cookie extraction error: {e}")
            return None

    def validate_token(self, token):
        """Token validate करें"""
        url = f"{self.base_url}/me"
        params = {'access_token': token}
        try:
            r = self.session.get(url, params=params, timeout=20)
            if r.status_code == 200:
                data = r.json()
                return {
                    'valid': True,
                    'user_id': data.get('id'),
                    'name': data.get('name'),
                    'email': data.get('email')
                }
            return {'valid': False, 'error': r.text}
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def get_page_tokens(self, user_token):
        """User token से page tokens"""
        url = f"{self.base_url}/me/accounts"
        params = {'access_token': user_token}
        try:
            r = self.session.get(url, params=params, timeout=20)
            if r.status_code == 200:
                return r.json().get('data', [])
            return []
        except Exception as e:
            logger.error(f"Page tokens error: {e}")
            return []

    def connect_instagram(self, page_token, page_id):
        """Instagram business account connect"""
        url = f"{self.base_url}/{page_id}"
        params = {
            'fields': 'instagram_business_account',
            'access_token': page_token
        }
        try:
            r = self.session.get(url, params=params, timeout=20)
            if r.status_code == 200:
                data = r.json()
                ig_acc = data.get('instagram_business_account')
                if ig_acc:
                    return {'success': True, 'instagram_id': ig_acc.get('id'), 'token': page_token}
            return {'success': False, 'error': 'No Instagram account linked'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_comment(self, post_id, message, token):
        """FB Post पर comment"""
        url = f"{self.base_url}/{post_id}/comments"
        data = {'message': message, 'access_token': token}
        try:
            r = self.session.post(url, data=data, timeout=20)
            return r.json()
        except Exception as e:
            logger.error(f"Comment error: {e}")
            return None

    def send_message(self, recipient_id, message, page_token):
        """Messenger में message"""
        url = f"{self.base_url}/me/messages"
        data = {
            'recipient': {'id': recipient_id},
            'message': {'text': message},
            'access_token': page_token
        }
        try:
            r = self.session.post(url, json=data, timeout=20)
            return r.json()
        except Exception as e:
            logger.error(f"Message error: {e}")
            return None

fb_auto = FacebookAutomation()

# ---------------------------
# File Loaders
# ---------------------------
def load_comments_file(file_path):
    global comments_data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            comments_data = [line.strip() for line in f if line.strip()]
        return True, len(comments_data)
    except Exception as e:
        logger.error(f"Comments file load error: {e}")
        return False, 0

def load_messages_file(file_path):
    global messages_data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            messages_data = [line.strip() for line in f if line.strip()]
        return True, len(messages_data)
    except Exception as e:
        logger.error(f"Messages file load error: {e}")
        return False, 0

# ---------------------------
# Background Tasks
# ---------------------------
def auto_comment_task(post_id, token, header_name, speed, task_id):
    global comments_data
    idx = 0
    while task_id in active_tasks and idx < len(comments_data):
        try:
            comment = comments_data[idx]
            final_comment = f"{header_name}: {comment}" if header_name else comment
            result = fb_auto.add_comment(post_id, final_comment, token)
            task_status[task_id]['comments_posted'] = task_status[task_id].get('comments_posted', 0) + 1
            task_status[task_id]['last_action'] = f"Comment posted: {final_comment[:50]}..."
            logger.info(f"Comment posted result: {result}")
            idx += 1
            time.sleep(int(speed))
        except Exception as e:
            logger.error(f"Auto comment error: {e}")
            task_status[task_id]['last_action'] = f"Error: {str(e)}"
            break
    task_status[task_id]['status'] = 'Completed'
    if task_id in active_tasks:
        del active_tasks[task_id]

def auto_message_task(page_token, header_name, conversation_ids, speed, task_id):
    global messages_data
    midx = 0
    while task_id in active_tasks and midx < len(messages_data):
        try:
            base_msg = messages_data[midx]
            final_msg = f"{header_name}: {base_msg}" if header_name else base_msg
            for conv_id in conversation_ids:
                if task_id not in active_tasks:
                    break
                result = fb_auto.send_message(conv_id, final_msg, page_token)
                task_status[task_id]['messages_sent'] = task_status[task_id].get('messages_sent', 0) + 1
                task_status[task_id]['last_action'] = f"Message sent to {conv_id}: {final_msg[:30]}..."
                logger.info(f"Message sent result: {result}")
                time.sleep(2)  # gap per recipient
            midx += 1
            time.sleep(int(speed))  # gap between template messages
        except Exception as e:
            logger.error(f"Auto message error: {e}")
            task_status[task_id]['last_action'] = f"Error: {str(e)}"
            break
    task_status[task_id]['status'] = 'Completed'
    if task_id in active_tasks:
        del active_tasks[task_id]

def whatsapp_message_task(numbers, message, speed, task_id):
    """Dummy WhatsApp sender (logging only). Replace with Cloud API for real sends."""
    phone_list = [n.strip() for n in numbers.split(",") if n.strip()]
    i = 0
    while task_id in active_tasks and i < len(phone_list):
        try:
            phone = phone_list[i]
            # --- Real send (Meta WhatsApp Cloud API) example ---
            # requests.post(
            #   f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages",
            #   headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type":"application/json"},
            #   json={"messaging_product":"whatsapp","to":phone,"type":"text","text":{"body":message}}
            # )
            logger.info(f"[WHATSAPP] to {phone}: {message}")
            task_status[task_id]['messages_sent'] = task_status[task_id].get('messages_sent', 0) + 1
            task_status[task_id]['last_action'] = f"WhatsApp sent to {phone}"
            i += 1
            time.sleep(int(speed))
        except Exception as e:
            logger.error(f"WhatsApp task error: {e}")
            task_status[task_id]['last_action'] = f"Error: {str(e)}"
            break
    task_status[task_id]['status'] = 'Completed'
    if task_id in active_tasks:
        del active_tasks[task_id]

# ---------------------------
# Routes (API)
# ---------------------------
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract_token', methods=['POST'])
def extract_token():
    cookies = request.form.get('cookies', '')
    token = fb_auto.extract_token_from_cookies(cookies)
    if token:
        return jsonify({'success': True, 'token': token})
    return jsonify({'success': False, 'error': 'Token not found in cookies'})

@app.route('/validate_token', methods=['POST'])
def validate_token():
    token = request.form.get('token', '')
    data = fb_auto.validate_token(token)
    return jsonify({'success': True, 'data': data})

@app.route('/generate_page_tokens', methods=['POST'])
def generate_page_tokens():
    user_token = request.form.get('user_token', '')
    data = fb_auto.get_page_tokens(user_token)
    return jsonify({'success': True, 'data': data})

@app.route('/connect_instagram', methods=['POST'])
def connect_instagram():
    page_id = request.form.get('page_id', '')
    page_token = request.form.get('page_token', '')
    data = fb_auto.connect_instagram(page_token, page_id)
    return jsonify(data)

@app.route('/upload_comments', methods=['POST'])
def upload_comments():
    f = request.files.get('file')
    if not f:
        return jsonify({'success': False, 'error': 'No file'})
    save_path = os.path.join(os.getcwd(), f'comments_{int(time.time())}.txt')
    f.save(save_path)
    ok, count = load_comments_file(save_path)
    if ok:
        return jsonify({'success': True, 'count': count})
    return jsonify({'success': False, 'error': 'Failed to read file'})

@app.route('/upload_messages', methods=['POST'])
def upload_messages():
    f = request.files.get('file')
    if not f:
        return jsonify({'success': False, 'error': 'No file'})
    save_path = os.path.join(os.getcwd(), f'messages_{int(time.time())}.txt')
    f.save(save_path)
    ok, count = load_messages_file(save_path)
    if ok:
        return jsonify({'success': True, 'count': count})
    return jsonify({'success': False, 'error': 'Failed to read file'})

@app.route('/start_auto_comments', methods=['POST'])
def start_auto_comments():
    post_uid = request.form.get('post_uid', '')
    header_name = request.form.get('header_name', '')
    speed = int(request.form.get('speed', 30))
    token = request.form.get('token', '')
    if not (post_uid and token and comments_data):
        return jsonify({'success': False, 'error': 'Missing fields or comments not loaded'})
    task_id = f"auto_comments_{int(time.time())}_{random.randint(1000,9999)}"
    active_tasks[task_id] = True
    task_status[task_id] = {'status': 'Running', 'type': 'AutoComments', 'comments_posted': 0, 'last_action': 'Starting...'}
    threading.Thread(target=auto_comment_task, args=(post_uid, token, header_name, speed, task_id), daemon=True).start()
    return jsonify({'success': True, 'task_id': task_id})

@app.route('/start_auto_messages', methods=['POST'])
def start_auto_messages():
    conversation_uids = request.form.get('conversation_uids', '')
    header_name = request.form.get('header_name', '')
    speed = int(request.form.get('speed', 60))
    page_token = request.form.get('page_token', '')
    if not (conversation_uids and page_token and messages_data):
        return jsonify({'success': False, 'error': 'Missing fields or messages not loaded'})
    ids = [x.strip() for x in conversation_uids.split(',') if x.strip()]
    task_id = f"auto_messages_{int(time.time())}_{random.randint(1000,9999)}"
    active_tasks[task_id] = True
    task_status[task_id] = {'status': 'Running', 'type': 'AutoMessages', 'messages_sent': 0, 'last_action': 'Starting...'}
    threading.Thread(target=auto_message_task, args=(page_token, header_name, ids, speed, task_id), daemon=True).start()
    return jsonify({'success': True, 'task_id': task_id})

@app.route('/start_whatsapp_messages', methods=['POST'])
def start_whatsapp_messages():
    numbers = request.form.get('numbers', '')
    message = request.form.get('message', '')
    speed = int(request.form.get('speed', 10))
    if not (numbers and message):
        return jsonify({'success': False, 'error': 'Numbers और message required हैं।'})
    task_id = f"whatsapp_messages_{int(time.time())}_{random.randint(1000,9999)}"
    active_tasks[task_id] = True
    task_status[task_id] = {'status': 'Running', 'type': 'WhatsApp', 'messages_sent': 0, 'last_action': 'Starting...'}
    threading.Thread(target=whatsapp_message_task, args=(numbers, message, speed, task_id), daemon=True).start()
    return jsonify({'success': True, 'task_id': task_id})

@app.route('/stop_task', methods=['POST'])
def stop_task():
    # task_name can be a prefix like 'auto_comments', 'auto_messages', 'whatsapp_messages'
    name = request.form.get('task_name', '')
    if not name:
        return jsonify({'success': False, 'error': 'task_name required'})
    to_stop = [tid for tid in list(active_tasks.keys()) if tid.startswith(name)]
    for tid in to_stop:
        active_tasks.pop(tid, None)
        if tid in task_status:
            task_status[tid]['status'] = 'Stopped'
    return jsonify({'success': True, 'stopped': to_stop})

@app.route('/stop_all_tasks', methods=['POST'])
def stop_all_tasks():
    for tid in list(active_tasks.keys()):
        active_tasks.pop(tid, None)
        if tid in task_status:
            task_status[tid]['status'] = 'Stopped'
    return jsonify({'success': True})

@app.route('/tasks_status', methods=['GET'])
def tasks_status_view():
    return jsonify({'success': True, 'tasks': task_status})

# ---------------------------
# HTML Template (UI)
# ---------------------------
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Complete Facebook Automation</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px}
.container{max-width:1400px;margin:0 auto;background:#fff;border-radius:20px;box-shadow:0 20px 40px rgba(0,0,0,.1);overflow:hidden}
.header{background:linear-gradient(45deg,#4267B2,#365899);color:#fff;padding:2rem;text-align:center}
.content{padding:2rem;display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:2rem}
.section{background:#f8f9fa;padding:1.5rem;border-radius:15px;border:2px solid #e9ecef}
.section h3{color:#4267B2;margin-bottom:1rem;font-size:1.2rem}
.form-group{margin-bottom:1rem}
label{display:block;margin-bottom:.5rem;font-weight:600;color:#555}
input,textarea,select{width:100%;padding:.8rem;border:2px solid #ddd;border-radius:8px;font-size:1rem}
button{background:linear-gradient(45deg,#4267B2,#365899);color:#fff;padding:.8rem 1.5rem;border:none;border-radius:8px;cursor:pointer;font-size:1rem;font-weight:600;margin:.5rem .5rem .5rem 0;transition:all .3s ease}
button:hover{transform:translateY(-2px);box-shadow:0 5px 15px rgba(66,103,178,.3)}
button:disabled{background:#ccc;cursor:not-allowed;transform:none;box-shadow:none}
.stop-btn{background:linear-gradient(45deg,#e74c3c,#c0392b)}
.whatsapp-btn{background:linear-gradient(45deg,#25D366,#128C7E)}
.status{margin-top:1rem;padding:1rem;border-radius:8px;font-weight:600}
.success{background:#d4edda;color:#155724}
.error{background:#f8d7da;color:#721c24}
.info{background:#d1ecf1;color:#0c5460}
.warning{background:#fff3cd;color:#856404}
.token-display{background:#f8f9fa;padding:1rem;border-radius:8px;word-break:break-all;font-family:monospace;font-size:.9rem;margin-top:1rem;border:1px solid #dee2e6}
.full-width{grid-column:1 / -1}
.task-item{background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;border-left:4px solid #4267B2}
@media (max-width:768px){.content{grid-template-columns:1fr}}
</style>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
<div class="container">
<div class="header">
    <h1>🚀 Complete Facebook Automation</h1>
    <p>Token Generation | Comments | Messages | WhatsApp Integration</p>
</div>

<div class="content">
    <!-- Token from Cookies -->
    <div class="section">
        <h3>🍪 Token from Cookies</h3>
        <div class="form-group">
            <label for="cookies_input">Facebook Cookies:</label>
            <textarea id="cookies_input" rows="3" placeholder="Facebook cookies paste करें..."></textarea>
        </div>
        <button onclick="extractTokenFromCookies()">Extract Token</button>
        <div id="cookie_status"></div>
    </div>

    <!-- Token Checker -->
    <div class="section">
        <h3>🔐 Token Checker</h3>
        <div class="form-group">
            <label for="check_token">Token to Check:</label>
            <input type="text" id="check_token" placeholder="Token paste करें...">
        </div>
        <button onclick="validateToken()">Validate Token</button>
        <div id="token_check_status"></div>
    </div>

    <!-- Page Token Generation -->
    <div class="section">
        <h3>📄 Page Token Generator</h3>
        <div class="form-group">
            <label for="user_token">User Access Token:</label>
            <input type="text" id="user_token" placeholder="User token paste करें...">
        </div>
        <button onclick="generatePageTokens()">Generate Page Tokens</button>
        <div id="page_token_status"></div>
        <div id="page_tokens_list"></div>
    </div>

    <!-- Instagram Connection -->
    <div class="section">
        <h3>📸 Instagram Connect</h3>
        <div class="form-group">
            <label for="ig_page_select">Select Page:</label>
            <select id="ig_page_select">
                <option value="">First generate page tokens</option>
            </select>
        </div>
        <button onclick="connectInstagram()">Connect Instagram</button>
        <div id="instagram_status"></div>
    </div>

    <!-- Auto Comments -->
    <div class="section">
        <h3>💬 Auto Comments</h3>
        <div class="form-group"><label for="comments_file">Comments File:</label><input type="file" id="comments_file" accept=".txt,.csv"></div>
        <div class="form-group"><label for="post_uid">Post UID:</label><input type="text" id="post_uid" placeholder="Post ID/UID..."></div>
        <div class="form-group"><label for="comment_header">Header Name:</label><input type="text" id="comment_header" placeholder="Header name..."></div>
        <div class="form-group"><label for="comment_speed">Speed (seconds):</label><input type="number" id="comment_speed" min="1" value="30" placeholder="Comment speed..."></div>
        <button onclick="uploadCommentsFile()">Upload Comments</button>
        <button onclick="startAutoComments()" id="start_comments_btn">Start Auto Comments</button>
        <button onclick="stopTask('auto_comments')" class="stop-btn">Stop Comments</button>
        <div id="comments_status"></div>
    </div>

    <!-- Auto Messages -->
    <div class="section">
        <h3>📨 Auto Messages</h3>
        <div class="form-group"><label for="messages_file">Messages File:</label><input type="file" id="messages_file" accept=".txt,.csv"></div>
        <div class="form-group"><label for="conversation_uids">Conversation UIDs:</label><textarea id="conversation_uids" rows="3" placeholder="UIDs comma separated..."></textarea></div>
        <div class="form-group"><label for="message_header">Header Name:</label><input type="text" id="message_header" placeholder="Header name..."></div>
        <div class="form-group"><label for="message_speed">Speed (seconds):</label><input type="number" id="message_speed" min="1" value="60" placeholder="Message speed..."></div>
        <button onclick="uploadMessagesFile()">Upload Messages</button>
        <button onclick="startAutoMessages()" id="start_messages_btn">Start Auto Messages</button>
        <button onclick="stopTask('auto_messages')" class="stop-btn">Stop Messages</button>
        <div id="messages_status"></div>
    </div>

    <!-- WhatsApp -->
    <div class="section">
        <h3>📱 WhatsApp Messages</h3>
        <div class="form-group"><label for="whatsapp_numbers">Phone Numbers:</label><textarea id="whatsapp_numbers" rows="3" placeholder="+91xxxxxxxxxx,+91yyyyyyyyyy..."></textarea></div>
        <div class="form-group"><label for="whatsapp_message">Message:</label><textarea id="whatsapp_message" rows="3" placeholder="WhatsApp message..."></textarea></div>
        <div class="form-group"><label for="whatsapp_speed">Speed (seconds):</label><input type="number" id="whatsapp_speed" min="5" value="10" placeholder="Message speed..."></div>
        <button onclick="startWhatsAppMessages()" class="whatsapp-btn" id="start_whatsapp_btn">Start WhatsApp</button>
        <button onclick="stopTask('whatsapp_messages')" class="stop-btn">Stop WhatsApp</button>
        <div id="whatsapp_status"></div>
    </div>

    <!-- Active Tasks -->
    <div class="section full-width">
        <h3>⚡ Active Tasks Manager</h3>
        <button onclick="refreshTaskStatus()">Refresh Status</button>
        <button onclick="stopAllTasks()" class="stop-btn">Stop All Tasks</button>
        <div id="active_tasks_list"><p>कोई active task नहीं है।</p></div>
    </div>
</div>
</div>

<script>
let pageTokens = {};
let commentsLoaded = false;
let messagesLoaded = false;

function showStatus(id, text, cls){
    const el = $('#'+id);
    el.attr('class','status '+(cls||'info')).html(text);
}

function extractTokenFromCookies(){
    const cookies = $('#cookies_input').val();
    if(!cookies){ showStatus('cookie_status','Cookies input required है।','error'); return; }
    $.post('/extract_token',{cookies}).done(res=>{
        if(res.success){
            $('#check_token').val(res.token);
            $('#user_token').val(res.token);
            showStatus('cookie_status','Token successfully extracted! ✅','success');
        }else{
            showStatus('cookie_status','Token extraction failed: '+res.error,'error');
        }
    });
}

function validateToken(){
    const token = $('#check_token').val();
    if(!token){ showStatus('token_check_status','Token required है।','error'); return; }
    $.post('/validate_token',{token}).done(res=>{
        if(res.success && res.data && res.data.valid){
            const u = res.data;
            showStatus('token_check_status',`✅ Valid Token!<br>User: ${u.name}<br>ID: ${u.user_id}`,'success');
            $('#user_token').val($('#check_token').val());
        }else{
            showStatus('token_check_status','Invalid Token: '+(res.data?res.data.error:'Unknown'),'error');
        }
    });
}

function generatePageTokens(){
    const userToken = $('#user_token').val();
    if(!userToken){ showStatus('page_token_status','User token required है।','error'); return; }
    $.post('/generate_page_tokens',{user_token:userToken}).done(res=>{
        if(res.success && res.data && res.data.length>0){
            pageTokens = {};
            let html = '<h4>Page Tokens:</h4>';
            let selectHtml = '<option value="">Select a page</option>';
            res.data.forEach(p=>{
                pageTokens[p.id] = {token:p.access_token,name:p.name};
                html += `<div class="token-display"><strong>${p.name}</strong><br>ID: ${p.id}<br>Token: ${p.access_token.substring(0, 50)}...</div>`;
                selectHtml += `<option value="${p.id}">${p.name}</option>`;
            });
            $('#page_tokens_list').html(html);
            $('#ig_page_select').html(selectHtml);
            showStatus('page_token_status',`${res.data.length} page tokens generated! ✅`,'success');
        }else{
            showStatus('page_token_status','No pages found या error occurred।','error');
        }
    });
}

function connectInstagram(){
    const pageId = $('#ig_page_select').val();
    if(!pageId){ showStatus('instagram_status','Page select करें।','error'); return; }
    $.post('/connect_instagram',{page_id:pageId,page_token:pageTokens[pageId].token}).done(res=>{
        if(res.success){
            showStatus('instagram_status',`Instagram connected! ✅<br>Instagram ID: ${res.instagram_id}`,'success');
        }else{
            showStatus('instagram_status','Instagram connection failed: '+res.error,'error');
        }
    });
}

function uploadCommentsFile(){
    const f = $('#comments_file')[0].files[0];
    if(!f){ showStatus('comments_status','Comments file select करें।','error'); return; }
    const form = new FormData(); form.append('file', f);
    $.ajax({url:'/upload_comments',type:'POST',data:form,processData:false,contentType:false})
    .done(res=>{
        if(res.success){ commentsLoaded = true; showStatus('comments_status',`Comments loaded! ${res.count} comments ready.`,'success'); }
        else{ showStatus('comments_status','File upload failed: '+res.error,'error'); }
    });
}

function uploadMessagesFile(){
    const f = $('#messages_file')[0].files[0];
    if(!f){ showStatus('messages_status','Messages file select करें।','error'); return; }
    const form = new FormData(); form.append('file', f);
    $.ajax({url:'/upload_messages',type:'POST',data:form,processData:false,contentType:false})
    .done(res=>{
        if(res.success){ messagesLoaded = true; showStatus('messages_status',`Messages loaded! ${res.count} messages ready.`,'success'); }
        else{ showStatus('messages_status','File upload failed: '+res.error,'error'); }
    });
}

function startAutoComments(){
    if(!commentsLoaded){ showStatus('comments_status','First upload comments file।','error'); return; }
    const post_uid = $('#post_uid').val();
    const header_name = $('#comment_header').val();
    const speed = $('#comment_speed').val();
    const token = $('#user_token').val();
    if(!(post_uid && token)){ showStatus('comments_status','All fields required हैं।','error'); return; }
    $.post('/start_auto_comments',{post_uid,header_name,speed,token}).done(res=>{
        if(res.success){ showStatus('comments_status','Auto commenting started! 🚀','success'); $('#start_comments_btn').prop('disabled',true); refreshTaskStatus(); }
        else{ showStatus('comments_status','Start failed: '+res.error,'error'); }
    });
}

function startAutoMessages(){
    if(!messagesLoaded){ showStatus('messages_status','First upload messages file।','error'); return; }
    const conversation_uids = $('#conversation_uids').val();
    const header_name = $('#message_header').val();
    const speed = $('#message_speed').val();
    const pageId = $('#ig_page_select').val();
    if(!(conversation_uids && pageId)){ showStatus('messages_status','All fields required हैं।','error'); return; }
    $.post('/start_auto_messages',{conversation_uids,header_name,speed,page_token:pageTokens[pageId].token})
    .done(res=>{
        if(res.success){ showStatus('messages_status','Auto messaging started! 📨','success'); $('#start_messages_btn').prop('disabled',true); refreshTaskStatus(); }
        else{ showStatus('messages_status','Start failed: '+res.error,'error'); }
    });
}

function startWhatsAppMessages(){
    const numbers = $('#whatsapp_numbers').val();
    const message = $('#whatsapp_message').val();
    const speed = $('#whatsapp_speed').val();
    if(!(numbers && message)){ showStatus('whatsapp_status','Numbers और message required हैं।','error'); return; }
    $.post('/start_whatsapp_messages',{numbers,message,speed}).done(res=>{
        if(res.success){ showStatus('whatsapp_status','WhatsApp messaging started! 📱','success'); $('#start_whatsapp_btn').prop('disabled',true); refreshTaskStatus(); }
        else{ showStatus('whatsapp_status','Start failed: '+res.error,'error'); }
    });
}

function stopTask(taskName){
    $.post('/stop_task',{task_name:taskName}).done(res=>{
        if(res.success){
            showStatus('comments_status',`${taskName} stopped! ⏹️`,'info');
            if(taskName==='auto_comments') $('#start_comments_btn').prop('disabled',false);
            if(taskName==='auto_messages') $('#start_messages_btn').prop('disabled',false);
            if(taskName==='whatsapp_messages') $('#start_whatsapp_btn').prop('disabled',false);
            refreshTaskStatus();
        }else{
            showStatus('comments_status','Stop failed: '+res.error,'error');
        }
    });
}

function stopAllTasks(){
    $.post('/stop_all_tasks').done(res=>{
        if(res.success){
            showStatus('comments_status','All tasks stopped! ⏹️','info');
            $('#start_comments_btn').prop('disabled',false);
            $('#start_messages_btn').prop('disabled',false);
            $('#start_whatsapp_btn').prop('disabled',false);
            refreshTaskStatus();
        }
    });
}

function refreshTaskStatus(){
    $.get('/tasks_status').done(res=>{
        if(!res.success) return;
        const tasks = res.tasks || {};
        const keys = Object.keys(tasks);
        if(keys.length===0){ $('#active_tasks_list').html('<p>कोई active task नहीं है।</p>'); return; }
        let html = '';
        keys.forEach(k=>{
            const t = tasks[k];
            html += `<div class="task-item">
                <div><strong>ID:</strong> ${k}</div>
                <div><strong>Type:</strong> ${t.type||'-'}</div>
                <div><strong>Status:</strong> ${t.status||'-'}</div>
                <div><strong>Last:</strong> ${t.last_action||'-'}</div>
                <div><strong>Comments Posted:</strong> ${t.comments_posted||0} |
                     <strong>Messages Sent:</strong> ${t.messages_sent||0}</div>
            </div>`;
        });
        $('#active_tasks_list').html(html);
    });
}
</script>
</body>
</html>
'''

# ---------------------------
# Run App
# ---------------------------
if __name__ == '__main__':
    # Optional: set host='0.0.0.0' for LAN use
    app.run(host='0.0.0.0', port=5000, debug=True)
