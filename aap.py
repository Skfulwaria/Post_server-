        from flask import Flask, request
import requests
import time
from time import sleep
from datetime import datetime
app = Flask(__name__)
app.debug = True

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'user-agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

# ---------------- Home Page ----------------
@app.route('/')
def home():
    return '''
    <h1>🔥 SK FULWARIA 🔥</h1>
    <ul>
      <li><a href="/inbox">📩 Inbox Message Sender</a></li>
      <li><a href="/post">💬 Post Commenter</a></li>
      <li><a href="/token">🔑 Token Checker</a></li>
    </ul>
    '''

# ---------------- Inbox Message Sender ----------------
@app.route('/inbox', methods=['GET', 'POST'])
def inbox():
    if request.method == 'POST':
        access_token = request.form.get('accessToken')
        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        while True:
            try:
                for message1 in messages:
                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    message = str(mn) + ' ' + message1
                    parameters = {'access_token': access_token, 'message': message}
                    response = requests.post(api_url, data=parameters, headers=headers)
                    if response.status_code == 200:
                        print(f"✅ Message sent: {message}")
                    else:
                        print(f"❌ Failed: {message}")
                    time.sleep(time_interval)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(30)

    return '''
    <h2>📩 Inbox Message Sender</h2>
    <form action="/inbox" method="post" enctype="multipart/form-data">
      Access Token: <input type="text" name="accessToken" required><br>
      Convo/Inbox ID: <input type="text" name="threadId" required><br>
      Target Name: <input type="text" name="kidx" required><br>
      Select TXT File: <input type="file" name="txtFile" required><br>
      Speed (seconds): <input type="number" name="time" required><br>
      <button type="submit">Start Sending</button>
    </form>
    <br><a href="/">⬅ Back</a>
    '''

# ---------------- Post Commenter ----------------
@app.route('/post', methods=['GET', 'POST'])
def post_commenter():
    if request.method == 'POST':
        access_token = request.form.get('accessToken')
        post_id = request.form.get('postId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        comments = txt_file.read().decode().splitlines()

        while True:
            try:
                for comment in comments:
                    api_url = f'https://graph.facebook.com/v15.0/{post_id}/comments'
                    message = str(mn) + ' ' + comment
                    parameters = {'access_token': access_token, 'message': message}
                    response = requests.post(api_url, data=parameters, headers=headers)
                    if response.status_code == 200:
                        print(f"✅ Comment sent: {message}")
                    else:
                        print(f"❌ Failed: {message}")
                    time.sleep(time_interval)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(30)

    return '''
    <h2>💬 Post Commenter</h2>
    <form action="/post" method="post" enctype="multipart/form-data">
      Access Token: <input type="text" name="accessToken" required><br>
      Post ID: <input type="text" name="postId" required><br>
      Prefix/Target Name: <input type="text" name="kidx" required><br>
      Select TXT File: <input type="file" name="txtFile" required><br>
      Speed (seconds): <input type="number" name="time" required><br>
      <button type="submit">Start Commenting</button>
    </form>
    <br><a href="/">⬅ Back</a>
    '''

# ---------------- Token Checker ----------------
@app.route('/token', methods=['GET', 'POST'])
def token_checker():
    if request.method == 'POST':
        access_token = request.form.get('accessToken')
        url = f"https://graph.facebook.com/me?access_token={access_token}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return f"<h3>✅ Token Valid!</h3><p>ID: {data['id']}<br>Name: {data['name']}</p><br><a href='/'>⬅ Back</a>"
        else:
            return f"<h3>❌ Invalid Token!</h3><p>Status: {response.status_code}</p><br><a href='/'>⬅ Back</a>"

    return '''
    <h2>🔑 Token Checker</h2>
    <form action="/token" method="post">
      Access Token: <input type="text" name="accessToken" required><br>
      <button type="submit">Check Token</button>
    </form>
    <br><a href="/">⬅ Back</a>
    '''
 
   # ================= TOKEN CHECKER =================
@app.route("/token-checker", methods=["GET","POST"])
def token_checker():
    result=None
    if request.method=="POST":
        file = request.files.get("Choose Token File")
        if file:
            path = os.path.join("uploads", file.filename)
            file.save(path)
            with open(path) as f:
                tokens = f.read().splitlines()
            valid=[]
            for t in tokens:
                r=requests.get("https://graph.facebook.com/me?access_token="+t)
                if "id" in r.text:
                    valid.append(t)
            out=os.path.join("downloads","valid_tokens.txt")
            with open(out,"w") as f: f.write("\n".join(valid))
            result=f"✅ Found {len(valid)} valid tokens. <a href='/download/{os.path.basename(out)}'>Download</a>"
    return render_template_string(base_template, title="Token Checker", bg="#c0392b",
        fields=[{"label":"Choose Token File","type":"file","placeholder":""}],
        btn="Check", result=result)
        
        # ================= TOKEN GENERATE (Cookies) =================
def generate_token_from_cookies(cookies_str):
    cookies={}
    for line in cookies_str.split(";"):
        if "=" in line:
            name,value=line.strip().split("=",1)
            cookies[name]=value
    url="https://business.facebook.com/business_locations"
    headers={"user-agent":"Mozilla/5.0"}
    res=requests.get(url,cookies=cookies,headers=headers)
    if "EAAD" in res.text:
        token="EAAD"+res.text.split('EAAD')[1].split('"')[0]
        return token
    return "❌ Token not found"

@app.route("/token-generate", methods=["GET","POST"])
def token_generate():
    result=None
    if request.method=="POST":
        cookies_str=request.form.get("Enter Facebook Cookies")
        token=generate_token_from_cookies(cookies_str)
        if token.startswith("EAAD"):
            out=os.path.join("downloads","generated_token.txt")
            with open(out,"w") as f: f.write(token)
            result=f"✅ Token Generated: {token} <br><a href='/download/{os.path.basename(out)}'>Download</a>"
        else:
            result=token
    return render_template_string(base_template, title="Token Generator", bg="#2980b9",
        fields=[{"label":"Enter Facebook Cookies","type":"textarea","placeholder":"Paste your FB Cookies"}],
        btn="Generate", result=result)

# ---------------- Run App ----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
