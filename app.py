import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, abort, redirect
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant, ChatGrant
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()
twilio_account_sid = "AC574e31283298bd9c08801be42875d2a7"
twilio_api_key_sid = "SKb985afa3d0fbbc7145fad9d41e0ecb74"
twilio_api_key_secret = "cpSrlUkNhEMYQUfFrqLSrAaatMwWFEcI"
twilio_client = Client(twilio_api_key_sid, twilio_api_key_secret,
                       twilio_account_sid)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


def get_chatroom(name):
    for conversation in twilio_client.conversations.conversations.list():
        if conversation.friendly_name == name:
            return conversation

    # a conversation with the given name does not exist ==> create a new one
    return twilio_client.conversations.conversations.create(
        friendly_name=name)


@app.route('/', methods = ["POST", "GET"])
def index():
    if request.method == "POST":
        d = request.form.to_dict()
        username = d['username']
        if username:
            return render_template('call.html', username=username)
        else:
            return redirect('/')
    else:
        return render_template('index.html')

@app.route('/call', methods = ["POST", "GET"])
def call():
    if request.method == 'POST':
        return redirect('/thanks')
    else:
        return redirect('/')

@app.route('/thanks')
def thanks():
    return render_template('thanks.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.get_json(force=True).get('username')
    if not username:
        abort(401)

    conversation = get_chatroom('My Room')
    try:
        conversation.participants.create(identity=username)
    except TwilioRestException as exc:
        # do not error if the user is already in the conversation
        if exc.status != 409:
            raise

    token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                        twilio_api_key_secret, identity=username)
    token.add_grant(VideoGrant(room='My Room'))
    token.add_grant(ChatGrant(service_sid=conversation.chat_service_sid))

    return {'token': token.to_jwt().decode(),
            'conversation_sid': conversation.sid}


if __name__ == '__main__':
    app.run(host='127.0.0.1')
