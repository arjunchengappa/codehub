from flask import Flask, render_template, request, session, redirect, url_for
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select
from cryptography.fernet import Fernet
import re
import os
import json
from datetime import datetime

#declare the base directory where all the repos are going to be stored
_BASE_DIR = os.getcwd() + '/static/root/'

#initialize flask app
app = Flask(__name__)
app.secret_key = 'Codehub'

#fernet key for encryption of password
key = b'pRmgNa8W0USjWBfkfaq2aafzoWWEuwMI7wDe4c1F8AY='
cipher_suite = Fernet(key)

#creating database using sqlalchemy
engine = create_engine('sqlite:///Codehub.db', echo = True)
meta = MetaData()

#creating user table that contains userdata
users = Table(
   'users', meta,
    Column('user_id', Integer, primary_key = True),
    Column('name', String),
    Column('username', String),
    Column('email', String),
    Column('password', String),
    Column('repos_owned', Integer),
    sqlite_autoincrement=True
)

#creating repositories table that contains data about repositories
repository_table = Table(
    'repository_table', meta,
    Column('repo_id', Integer, primary_key = True),
    Column('repo_name', String),
    Column('repo_owner', String),
    Column('repo_description', String),
    Column('contributors_list', String),
    sqlite_autoincrement=True
)

#home page
@app.route('/')
def index():
    data = dict()

    #to display unknown contributors list after creating contributors
    if session.get('error_contributor'):
        data['error_contributor'] = session['error_contributor']
        session.pop('error_contributor', None)
    #to diplay dynamic website based on wether or not the user is logged in
    return render_template('index.html', data=data)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    #different fuctionality for different type of request
    if request.method == 'GET':
        if session.get('user'):
            return redirect(url_for('index'))
        return render_template('signup.html', data=None)

    if request.method == 'POST':
        #get all form data from POST message
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        enc_password = cipher_suite.encrypt(password.encode())

        #connecting to database
        conn = engine.connect()

        #checking if username is available
        query_1 = select(users.c.username).where(users.c.username == username)
        result = conn.execute(query_1)
        for row in result:
            data = {'message' : 'Username "' + username + '" already exists!'}
            return render_template('signup.html', data=data)

        #checking if email is already used
        query_2 = select(users.c.username).where(users.c.email == email)
        result = conn.execute(query_2)
        for row in result:
           data = {'message' : 'Email already linked to another account!'}
           return render_template('signup.html', data=data)

        #checking if password is strong enough
        if not bool(re.search(r'\d', password)) or not bool(re.search(r'[a-zA-Z]', password)):
           data = {'message' : 'Please include both alphabets and digits in Password!'}
           return render_template('signup.html', data=data)

        #inserting user data into the database
        insert = users.insert().values(name = name, email = email, username = username, password = enc_password, repos_owned = 0)
        result = conn.execute(insert)
        conn.close()

        #inserting profile pic into filesystem
        if request.files['image']:
            f = request.files['image']
            ext = f.filename.split('.')
            ext = ext[1]
            f.filename = username + '.' + ext
            f.save(os.getcwd()+'/static/img/profile/'+f.filename)

        #start a session when a user signs up --> direct login
        session['user'] = username
        return redirect(url_for('index'))
    return render_template('signup.html', data=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    #different fuctionality for different type of request
    if request.method == 'GET':
        if session.get('user'):
            return redirect(url_for('index'))
        return render_template('login.html', data=None)

    if request.method == 'POST':
        #get all form data from POST message
        username = request.form['username']
        password = request.form['password']

        #connecting to database
        conn = engine.connect()

        #checking is password matches
        query_1 = select(users.c.username, users.c.password).where(users.c.username == username)
        result = conn.execute(query_1)
        for row in result:
            dcy_password = cipher_suite.decrypt(row[1])
            if password == dcy_password.decode():
                session['user'] = row[0]
                return redirect(url_for('index'))
            else:
                data = {'message': 'Incorrect Email/Password'}
                return render_template('login.html', data=data)

        data = {'message': 'Incorrect Email/Password'}
        return render_template('login.html', data=data)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    #logout only if user is signed in
    if session.get('user'):
        session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/createRepository', methods=['GET', 'POST'])
def create():
    #different fuctionality for different type of request
    if request.method == 'GET':
        if session.get('user'):
            return render_template('createRepo1.html', data=None)
        return redirect(url_for('index'))

    if request.method == 'POST':
        repo_name = request.form['name'].replace(" ", "_").lower()
        repo_description = request.form['repo_description']
        numContributors = request.form['numContributors']

        #connecting to database
        conn = engine.connect()

        #checking if Repository name is available
        query_1 = select(repository_table.c.repo_name).where(repository_table.c.repo_name == repo_name)
        result = conn.execute(query_1)
        for row in result:
            data = {'message' : 'Repository name "' + row[0] + '" is unavailable!'}
            return render_template('createRepo1.html', data=data)

        #setting max number of contributors
        if int(numContributors) > 10:
            data = {'message' : 'Cannot have more than 10 contributors'}
            return render_template('createRepo1.html', data=data)

        #saving data for next connecting page
        data = dict()
        session['repo_name'] = repo_name
        session['repo_description'] = repo_description
        session['numContributors'] = numContributors

        return redirect(url_for('contributors'))


@app.route('/contributors', methods=['GET', 'POST'])
def contributors():
    #different fuctionality for different type of request
    if request.method == 'GET':
        if session.get('user'):
            #adding contributors
            data = {'numContributors': int(session['numContributors'])}
            session.pop('numContributors', None)
            return render_template('createRepo2.html', data=data)
        return redirect(url_for('index'))

    if request.method == 'POST':
        contributors = list(dict(request.form).values())

        #connecting to database
        conn = engine.connect()

        #checking if the contributor is valid or not
        error_contributor = contributors.copy()
        for i in contributors:
            query_1 = users.select().where(users.c.username == i)
            result = conn.execute(query_1)
            for row in result:
                error_contributor.remove(i)
        for i in error_contributor:
            contributors.remove(i)
        contributors_list = ','.join(contributors)

        #updating the repository database
        insert = repository_table.insert().values(repo_name = session['repo_name'], repo_owner = session['user'], repo_description = session['repo_description'], contributors_list = contributors_list)


        conn.execute(users.update(users.c.username == session['user']).values(repos_owned = users.c.repos_owned+1))
        result = conn.execute(insert)
        conn.close()

        #making a directory for new repository
        os.mkdir(_BASE_DIR+session['repo_name'])

        #adding repository data to its own metadata file for easier logging
        repo_meta = dict(
            repo_name = session['repo_name'],
            repo_owner = session['user'],
            repo_description = session['repo_description'],
            contributors_list = contributors,
            viewers_list = []
            )

        #create a meta file for the folder
        meta_file = open(_BASE_DIR+session['repo_name']+'/metadata.json', 'w')
        json.dump(repo_meta, meta_file)
        meta_file.close()

        repo_name = session['repo_name']
        session.pop('repo_name', None)
        session.pop('repo_description', None)

        #to display the invalid contributor names
        if len(error_contributor) != 0:
            session['error_contributor'] = error_contributor

        return redirect(url_for('manage', path = repo_name))

@app.route('/addContributor/<repo_name>', methods=['GET', 'POST'])
def addContributor(repo_name):
    #different fuctionality for different type of request
    if request.method == 'GET':
        if session.get('user'):
            return render_template('addContributor.html', data=None)
        return redirect(url_for('index'))

    if request.method == 'POST':
        numContributors = request.form['numContributors']
        return redirect(url_for('addContributor2', repo_name=repo_name, numContributors=numContributors))

@app.route('/addContributor/<repo_name>/<numContributors>', methods=['GET', 'POST'])
def addContributor2(repo_name, numContributors):
    #different fuctionality for different type of request
    if request.method == 'GET':
        if session.get('user'):
            data = dict()
            data['numContributors'] = numContributors
            return render_template('addContributor2.html', data=data)
        return redirect(url_for('index'))

    if request.method == 'POST':
        contributors = list(dict(request.form).values())

        #connecting to database
        conn = engine.connect()

        #checking if the contributor is valid or not
        error_contributor = contributors.copy()
        for i in contributors:
            query_1 = users.select().where(users.c.username == i)
            result = conn.execute(query_1)
            for row in result:
                error_contributor.remove(i)
        for i in error_contributor:
            contributors.remove(i)
        contributors_list = ','.join(contributors)

        #updating the repository database
        select = repository_table.select(repository_table.c.contributors_list).where(repository_table.c.repo_name == repo_name)
        result = conn.execute(select)
        for row in result:
            contributors_list = contributors_list + ',' + row['contributors_list']

        update = repository_table.update().values(contributors_list = contributors_list).where(repository_table.c.repo_name == repo_name)
        result = conn.execute(update)
        conn.close()

        meta_file = open(_BASE_DIR+repo_name+'/metadata.json', 'r')
        metadata = json.load(meta_file)
        meta_file.close()

        contributors = contributors_list.split(',')
        metadata['contributors_list'] = contributors

        #create a meta file for the folder
        meta_file = open(_BASE_DIR+repo_name+'/metadata.json', 'w')
        json.dump(metadata, meta_file)
        meta_file.close()

        #to display the invalid contributor names
        if len(error_contributor) != 0:
            session['error_contributor'] = error_contributor

        return redirect(url_for('manage', path = repo_name))

@app.route('/repositories')
def repositories():
    data = dict()
    repos = list()
    username = data['user'] = session['user']

    #connecting to database
    conn = engine.connect()

    #collecting all the repositories owned by the user
    query_1 = repository_table.select().where(repository_table.c.repo_owner == username)
    result = conn.execute(query_1)
    for row in result:
        print(row)
        repos.append({'repo_name': row[1], 'repo_owner': row[2], 'repo_description': row[3]})

    #collecting all the repositories the have the user as a contributor
    query_2 = repository_table.select().where(repository_table.c.contributors_list.contains(username))
    result = conn.execute(query_2)
    for row in result:
        print(row)
        repos.append({'repo_name': row[1], 'repo_owner': row[2], 'repo_description': row[3]})

    data['repositories'] = repos
    return render_template('repositories.html', data=data)

@app.route('/manage/<path>')
def manage(path):
    data = dict()

    #to display the invalid contributors that were added
    if session.get('error_contributor'):
        data['error_contributor'] = ','.join(session['error_contributor'])
        session.pop('error_contributor')

    #to avoid path disrepancies caused by '/' in the url
    data['path'] = path
    path_list = path.split('->')
    repo_name = path_list[0]
    if len(path_list) > 1:
        data['previous_path'] = '->'.join(path_list[:-1])
    else:
        data['previous_path'] = repo_name
    path = "/".join(path_list)
    data['actual_path'] = path
    data['repo_name'] = repo_name

    #to block unauthorised entry into the repository
    if session.get('user'):
        username = session['user']
        conn = engine.connect()
        meta = open(_BASE_DIR + repo_name +'/metadata.json', 'r')
        repo_metadata = json.load(meta)
        meta.close()

        #to customise the ui for different kind of users (not implemented yet)
        if username == repo_metadata['repo_owner']:
            data['owner'] = True
            data['rw'] = True
            data['ro'] = False
        else:
            data['owner'] = False
            if username in repo_metadata['contributors_list']:
                data['rw'] = True
                data['ro'] = False
            else:
                data['rw'] = False
                data['ro'] = True

        #to display the filesystem / repository
        files = list()
        folders = list()
        entries = os.scandir(_BASE_DIR+path)

        #scan all files and subdirectories
        for entry in entries:
            if entry.is_file():
                if entry.name != 'metadata.json':
                    files.append(entry.name)
            if entry.is_dir():
                folders.append(entry.name)
        data['files'] = files
        data['folders'] = folders

        return render_template('manage.html', data=data)

    return redirect(url_for('index'))

@app.route('/create_folder/<path>', methods=['GET', 'POST'])
def create_folder(path):
    #different fuctionality for different type of request
    if request.method == 'GET':
        if session.get('user'):
            data = dict()
            data['path'] = path
            return render_template('createFolder.html', data=data)
        return redirect(url_for('index'))

    if request.method == 'POST':
        #stripping whitespaces from foldername
        foldername = request.form['foldername'].replace(' ', '_')
        new_path = path.replace('->', '/') + '/' + foldername

        #creating new directory
        os.mkdir(_BASE_DIR+new_path)

        #creating a metadata file that will contain edit logs and other similar info
        new_meta = dict()
        new_meta['foldername'] = foldername
        metadata = open(_BASE_DIR+new_path+'/metadata.json', 'w')
        json.dump(new_meta, metadata)
        metadata.close()

        return redirect(url_for('manage', path=path))

@app.route('/upload_file/<path>', methods=['GET', 'POST'])
def upload_file(path):
    #different fuctionality for different type of request
    if request.method == 'GET':
        if session.get('user'):
            data = dict()
            data['path'] = path
            return render_template('uploadFiles.html', data=data)
        return redirect(url_for('index'))

    if request.method == 'POST':
        #getting actual path of the file
        new_path = path.replace('->', '/')

        #updating metada file of the directory
        time = datetime.now().strftime("%b %d, %Y %H:%M:%S")
        meta_file = open(_BASE_DIR+new_path+'/metadata.json', 'r')
        metadata = json.load(meta_file)
        meta_file.close()
        new_meta = open(_BASE_DIR+new_path+'/metadata.json', 'w')

        #updating the repository
        for f in request.files.getlist('files'):
            #updating the file and its logs if it already exists
            if os.path.exists(_BASE_DIR+new_path+'/'+f.filename):
                os.remove(_BASE_DIR+new_path+'/'+f.filename)
                log_entry = 'Updated by ' + session['user'] + ' on ' + time
                metadata[f.filename].append(log_entry)
                meta_file.close()
                f.save(_BASE_DIR+new_path+'/'+f.filename)
            #creating the logs and uploading the file if it doesn't exist
            else:
                log_entry = 'Created by ' + session['user'] + ' on ' + time
                metadata[f.filename] = [log_entry]
                meta_file.close()
                f.save(_BASE_DIR+new_path+'/'+f.filename)
        #updating the metadata file
        json.dump(metadata, new_meta)
        new_meta.close()

        return redirect(url_for('manage', path=path))

@app.route('/view/<path>', methods=['GET', 'POST'])
def view(path):
    if session.get('user'):
        data = dict()

        #getting the path of the file
        new_path = path.split('->')
        filename = new_path[-1]
        new_path = '/'.join(new_path[:-1])

        #fetching the metadata of the file
        meta_file = open(_BASE_DIR+new_path+'/metadata.json', 'r')
        metadata = json.load(meta_file)
        meta_file.close()

        #passing the path and the edit logs of the file
        data['path'] = 'root/'+path.replace('->', '/')
        data['logs'] = metadata[filename]
        return render_template('view.html', data=data)

    return redirect(url_for('index'))
