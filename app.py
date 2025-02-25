from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
app = Flask(__name__)

import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient
import certifi

ca = certifi.where()
client = MongoClient('mongodb+srv://sparta:test@cluster0.ervhju3.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'SPARTA'

# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: pyjwt)
import jwt

# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime

# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib

@app.route('/')
def home():
    return render_template('index.html')

#회원 가입 페이지 표시
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

# [회원가입 API]
# id, pw, nickname을 받아서, mongoDB에 저장합니다.
# 저장하기 전에, pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']
    retype_pw_receive = request.form['retype_pw_give']

    if not id_receive or not pw_receive or not nickname_receive or not retype_pw_receive :
        # 필수 입력 항목이 비어 있는지 확인하고, 하나라도 비어 있다면 오류 메시지를 반환함
        return jsonify({'result': '입력되지 않은 값이 있습니다.'})
    
    if pw_receive != retype_pw_receive:
        # 입력받은 비밀번호가 일치하는지 하고 일치하지 않으면 오류 메세지를 반환함
        # 클라이언트에서 처리할 수 있음 -> js로 구현하여 api 요청하는 횟수를 줄이도록 개선 할 것. 
        return jsonify({'result': '비밀번호가 일치하지 않습니다.'})
    
    # 입력받은 사용자 ID가 이미 사용 중인지 확인
    if db.user.find_one({'$or': [{'id': id_receive}, {'nick': nickname_receive}]}):
        return jsonify({'result': '이미 사용 중인 아이디 또는 닉네임입니다.'})

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest() # 비밀번호를 해싱하여 보안 강화

    # 사용자 ID가 사용 가능하면, 사용자 정보를 데이터베이스에 저장함
    db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive})

    return jsonify({'result': 'success'}) #성공 메세지 반환


#김보슬 작성
    # [로그인 API]
    # id, pw를 받아서, DB에서 조회 후, 맞으면 JWT token을 생성하여 반환합니다.
    # 만약, 조회된 사용자 정보가 없으면, 오류 메시지를 반환합니다.
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']
    
    if id_receive == "" or pw_receive == "" or nickname_receive =="":
            # 필수 입력 항목이 비어 있는지 확인하고, 하나라도 비어 있다면 오류 메시지를 반환함
        return jsonify({'msg': 'error : 입력되지 않은 값이 있습니다.'})

    user = db.user.find_one({'id': id_receive})
    
    if not user:
    # 사용자 정보가 없으면, 오류 메시지를 반환함
        return jsonify({'msg': 'error : 일치하는 사용자 정보가 없습니다.'})
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest() # 입력받은 비밀번호를 해싱하여 비교함
    if pw_hash != user['pw']:
    # 비밀번호가 일치하지 않으면, 오류 메시지를 반환함
        return jsonify({'msg': 'error : 비밀번호가 일치하지 않습니다.'})

# JWT 토큰 생성
    payload = {
    'user_id': str(user['_id']),  # MongoDB document ID를 문자열로 변환하여 사용
    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  # 30분 후 만료
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

    return jsonify({'result': 'success', 'token': token})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)