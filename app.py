import os
from os.path import join, dirname
from dotenv import load_dotenv

import datetime
import jwt
import hashlib
from flask import (
    Flask,
    render_template,
    jsonify,
    redirect,
    request,
    url_for,
    session,
    make_response,
)
from http import client
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from jwt.exceptions import ExpiredSignatureError, DecodeError

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]

app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = './static/upload'

SECRET_KEY = 'SPARTA'
TOKEN_KEY = 'mytoken'

app = Flask(__name__)

# Index /
@app.route('/')
def main():
    docters = list(db.doctors.find({},{'_id':False}))
    inventors = list(db.inventors.find({},{'_id':False}))
    return render_template("index.html" , active_page='home',doctors=docters, inventors=inventors)


# Home 
@app.route('/home')
def home():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        docters = list(db.doctors.find({},{'_id':False}))
        inventors = list(db.inventors.find({},{'_id':False}))
        return render_template("home.html" , active_page='home',user_info=payload,doctors=docters,inventors=inventors)
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))


@app.route('/profile/<keyword>')
def profile(keyword):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        docters = db.doctors.find({'name' : keyword},{'_id':False})
        return render_template("profile.html" ,user_info=payload,docters=docters)
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))


# Artikel 
@app.route('/artikel')
def artikel():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        articles = list(db.articles.find({},{'_id':False}))
        return render_template("artikel.html", active_page='artikel',user_info=payload,articles=articles)
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))
    

# @app.route('/show_artikel', methods=['GET'])
# def show_artikel():
#     token_receive = request.cookies.get(TOKEN_KEY)
#     try:
#         payload = jwt.decode(
#             token_receive,
#             SECRET_KEY,
#             algorithms=['HS256']
#         )
#         articles = list(db.articles.find({},{'_id':False}))
#         return jsonify({'articles': articles})
#     except jwt.ExpiredSignatureError:
#         msg = 'Your Token has expired'
#         return redirect(url_for('login', msg=msg))
#     except jwt.exceptions.DecodeError:
#         msg = ' There was a problem logging you in'
#         return redirect(url_for('login', msg=msg))
    

@app.route('/search')
def search():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        query = request.args.get('cari', '')
        result = db.articles.find({"title": query},{'_id':False})
        print(result)
        return render_template("search.html", active_page='artikel',user_info=payload,result=result)
        
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))
    


# Detail artikel 
@app.route("/detail/<keyword>")
def detail(keyword):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        articles = db.articles.find({},{'_id':False})
        detail = db.articles.find({'title' : keyword},{'_id':False})
        comments = db.comments.find({'title' : keyword},{'_id':False})
        return render_template("detail.html", detail=detail, articles=articles, comments=comments,user_info=payload)
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))
    


# About 
@app.route('/about')
def about():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        return render_template("about.html",active_page='about', user_info=payload)
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))
    

# Login 
@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/sign_in', methods=['POST'])
def sign_in():
    email_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.users.find_one({
            "email": email_receive,
            "password": pw_hash,
        })
    if result and 'admin' in result:
        payload = {
            "id": email_receive,
            "username": result['username'],
            "admin":True,
            # the token will be valid for 24 hours
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"result": "success", "token": token,})
    elif result and 'admin' not in result:
        payload = {
            "id": email_receive,
            "username": result['username'],
            # the token will be valid for 24 hours
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"result": "success", "token": token,})
        
    # Let's also handle the case where the id and
    # password combination cannot be found
    else:
        return jsonify({"result": "fail","msg": "We could not find a user with that id/password combination",
            })


# Register 
@app.route('/register')
def register():
    return render_template("register.html" )


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form.get('username_give')
    email_recive = request.form.get('email_give')
    password_receive = request.form.get('password_give')
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # id
        "email" : email_recive,                                     # email
        "password": password_hash,                                  # password
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form.get('username_give')
    exists = bool(db.users.find_one({"email": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


# Add Artikel 
@app.route('/add')
def add():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        if 'admin' in payload:
            return render_template("add.html", user_info=payload)
        else:
            return redirect(url_for('/home', msg='You are not admin'))
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))
    

# Delete Artikel 
@app.route('/artikel_delete',methods=['POST'])
def delete():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        delete = request.form["delete_give"]
        db.articles.delete_one({'title': delete})
        db.comments.delete_many({'title' : delete})
        return jsonify({"result": "success"})
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))

# Add Artikel 
@app.route('/post_add', methods=['POST'])
def post_add():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        file = request.files["file_give"]
        creator_receive = request.form["creator_give"]
        title_receive = request.form["title_give"]
        sinopsis_receive = request.form["sinopsis_give"]
        genre_receive = request.form["genre_give"]
        content_receive = request.form["content_give"]
        
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

        extension = file.filename.split('.')[-1]
        filename = f'file-{mytime}.{extension}'
        save_to = f'./static/upload/{filename}'
        file.save(save_to)

        time = today.strftime('%B . %d . %Y')

        doc = {
        'file': filename,
        'creator' : creator_receive,
        'title': title_receive,
        'sinopsis' : sinopsis_receive,
        'genre' : genre_receive,
        'content': content_receive,
        'time' : time
        }
        db.articles.insert_one(doc)
        # return jsonify({'msg':'Upload complete!'})
        return redirect(url_for('artikel', msg='Upload complete!'))
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))
    


# Edit Artikel 
@app.route("/edit/<keyword>")
def edit(keyword):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        if 'admin' in payload:
            edit = db.articles.find({'title': keyword})
            return render_template("edit.html", edit=edit, user_info=payload ,keyword=keyword)
        else:
            return redirect(url_for('/home', msg='You are not admin'))
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))
    

# Edit Post 
@app.route('/post_edit', methods=['POST'])
def post_edit():
    file = request.files["file_give"]
    creator_receive = request.form["creator_give"]
    title_receive = request.form["title_give"]
    sinopsis_receive = request.form["sinopsis_give"]
    genre_receive = request.form["genre_give"]
    content_receive = request.form["content_give"]
    
    edit_give = request.form["edit_give"]
    
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

    extension = file.filename.split('.')[-1]
    filename = f'file-{mytime}.{extension}'
    save_to = f'./static/upload/{filename}'
    file.save(save_to)

    time = today.strftime('%B . %d . %Y')

    change = {'title' : edit_give}

    doc = {'$set' : {
    'file': filename,
    'creator' : creator_receive,
    'title': title_receive,
    'sinopsis' : sinopsis_receive,
    'genre' : genre_receive,
    'content': content_receive,
    'time' : time
    }}
    print(edit_give)
    db.articles.update_one(change,doc)
    return jsonify({'msg':'Upload complete!'})

#Chat Post
@app.route("/posting", methods=["POST"])
def posting():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        title_receive = request.form["title_give"]
        comment_receive = request.form["comment_give"]
        today = datetime.now()
        time = today.strftime('%B . %d . %Y')
        doc = {
            "title": title_receive,
            "comment": comment_receive,
            "date": time,
            "username": payload["username"]
        }
        db.comments.insert_one(doc)
        return jsonify({"result": "success", "msg": "Posting successful!"})
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))
        

# Calculator 
@app.route("/kalkulator" )
def kalkulator():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        return render_template("calculator.html",active_page='imt',user_info=payload)
    except jwt.ExpiredSignatureError:
        msg = 'Your Token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = ' There was a problem logging you in'
        return redirect(url_for('login', msg=msg))
    
    

# # calculator 
# @app.route("/kalkulator/bmi", methods=["POST"] )
# def bmi():
#     kelamin = request.files["kelamin_give"]
#     berat = request.files["berat_give"]
#     tinggi = request.files["tinggi_give"]
#     return jsonify

#     berat = berat * berat 
#     hasil = tinggi / berat
#     return hasil

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)