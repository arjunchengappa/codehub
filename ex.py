from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select

engine = create_engine('sqlite:///scamhub.db', echo = True)
meta = MetaData()
conn = engine.connect()

command = "DROP TABLE IF EXISTS {};".format('users')
conn.execute(command)
command = "DROP TABLE IF EXISTS {};".format('repository_table')
conn.execute(command)
conn.close()

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

import os
import shutil
dir = os.getcwd() + '/static/root'
shutil.rmtree(dir)
os.mkdir(dir)
