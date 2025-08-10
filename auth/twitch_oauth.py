import os
import requests
import webbrowser
from flask import Flask, request

from dotenv import load_dotenv

load_dotenv()  # loads variables from .env

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
# TWITCH_TOKEN = os.getenv('TWITCH_TOKEN')
REDIRECT_URI = 'http://localhost:8080'
SCOPES = 'chat:read chat:edit'  # scopes your bot needs

app = Flask(__name__)
auth_code = None

@app.route('/')
def index():
    global auth_code
    code = request.args.get('code')
    if code:
        auth_code = code
        return 'Authorization code received! You can close this window.'
    else:
        return 'No code found in request.'

def get_auth_url():
    url = (
        f'https://id.twitch.tv/oauth2/authorize?response_type=code'
        f'&client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}'
        f'&scope={SCOPES.replace(" ", "+")}'
    )
    return url

def exchange_code_for_token(code):
    token_url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    resp = requests.post(token_url, params=params)
    return resp.json()

if __name__ == '__main__':
    # Step 1: Open Twitch authorization page in browser
    auth_url = get_auth_url()
    print(f'Opening this URL in your browser for authorization:\n{auth_url}\n')
    webbrowser.open(auth_url)

    # Step 2: Run Flask server to catch the redirect with code
    print('Starting local server at http://localhost:8080 to receive the authorization code...')
    app.run(port=8080)

    # Step 3: After Flask server closes (CTRL+C), exchange code for tokens
    if auth_code:
        print(f'Authorization code received: {auth_code}')
        tokens = exchange_code_for_token(auth_code)
        print('Tokens received:')
        print(tokens)
    else:
        print('No authorization code received.')
