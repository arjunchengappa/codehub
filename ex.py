'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        try:
            if session['user']:
                return redirect(url_for('index'))
        except:
            return render_template('login.html', data=None)
    if request.method == 'POST':
        if request.form['email'] and request.form['password']:
            email = request.form['email']
            password = request.form['password']
            conn = sql.connect('scamhub.db')
            cur = conn.cursor()
            cur.execute('select username, password from users where email = ?', (email,))
            row = cur.fetchall()
            if len(row) == 1:
                dcy_password = cipher_suite.decrypt(row[0][1])
                if dcy_password.decode() == password:
                    session['user'] = row[0][0]
                    return redirect(url_for('index'))
            data = dict()
            data['message'] = 'Incorrect Email/Password'
            return render_template('login.html', data=data)
        return render_template('login.html', data=None)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    try:
        session.pop('user', None)
    except:
        pass
    return redirect(url_for('index'))

@app.route('/createRepository', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        try:
            if session['user']:
                return render_template('createRepo1.html', data=None)
            return redirect(url_for('index'))
        except:
            return redirect(url_for('index'))
    if request.method == 'POST':
        repo_name = request.form['name']
        description = request.form['description']
        num_of_contributors = request.form['numContributors']
        conn = sql.connect('scamhub.db')
        cur = conn.cursor()
        cur.execute('select * from repositories where repo_name = ?', (repo_name,))
        row = cur.fetchall()
        if len(row) != 0:
            data = {'message': repo_name, 'description': description}
            return render_template('createRepo1.html', data=data)
        print(type(num_of_contributors))
        if num_of_contributors == '0':
            contributors_list = "[]"
            cur.execute('insert into repositories (repo_name, repo_owner, repo_description, contributors_list) values (?, ?, ?, ?)', (repo_name, description, session['user'], contributors_list))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            cur.execute('insert into repositories (repo_name, repo_owner, repo_description) values (?, ?, ?)', (repo_name, description, session['user']))
            conn.commit()
            conn.close()
            session['numContributors'] = num_of_contributors
            session['repo_name'] = repo_name
            return redirect(url_for('contributors'))

@app.route('/contributors', methods=['GET', 'POST'])
def contributors():
    if request.method == 'GET':
        try:
            if session['user']:
                if session['numContributors']:
                    data = {'numContributors': int(session['numContributors'])}
                    return render_template('createRepo2.html', data=data)
            return redirect(url_for('index'))
        except:
            return redirect(url_for('index'))
    if request.method == 'POST':
        contributors = list(dict(request.form).values())
        contributors_list = '[\'' + '\',\''.join(contributors)+'\']'
        conn = sql.connect('scamhub.db')
        cur = conn.cursor()
        for i in range(len(contributors)):
            cur.execute('select * from users where username = ?', (contributors[i],))
            row = cur.fetchall()
            if len(row) != 1:
                data = {'numContributors': session['numContributors'], 'error' : i, 'error_contributor' : contributors[i]}
                return render_template('createRepo2.html', data=data)
        cur.execute('update repositories set contributors_list = ? where repo_name = ?', (contributors_list, session['repo_name']))
        conn.commit()
        conn.close()
        session.pop('repo_name', None)
        session.pop('numContributors', None)
        return redirect(url_for('index'))



@app.route('/repositories')
def repositories():
    username = session['user']
    return 'hi'
    return render_template('repositories.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    if request.files['file']:
        f = request.files['file']
        f.save('root/' + f.filename)
        return 'Hello'
'''
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select

engine = create_engine('sqlite:///scamhub.db', echo = True)
meta = MetaData()

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

repository_table = Table(
    'repository_table', meta,
    Column('repo_id', Integer, primary_key = True),
    Column('repo_name', String),
    Column('repo_owner', String),
    Column('repo_description', String),
    Column('contributors_list', String),
    sqlite_autoincrement=True
)

meta.create_all(engine)
conn = engine.connect()

res = conn.execute(users.select())
for row in res:
    print(row)
