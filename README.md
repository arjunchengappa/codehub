# Codehub
A dummy version of GitHub for code management and version control for OOADSE LAB 2021 Jan - May

## Libraries used:
 - flask
 - sqlalchemy
 - cryptography
 - re
 - os
 - json
 - datetime
  
## Setting up the Server
### Setting up Flask:
- Installing Flask
https://flask.palletsprojects.com/en/1.1.x/installation/
- Setting the app.py as the main python file
```export FLASK_APP=app.py```
- Put flask in debug mode to avoid server crashes
```export FLASK_DEBUG=1```
 
### Installing sqlalchemy:
 - Install the latest version of sqlalchemy 
```pip install sqlalchemy```

### Installing cryptography:
 - Install the latest version of cryptography 
```pip install cryptography```

### Before starting the server:
 - run setup.py to create the database and set up the filesystem as required
```python3 setup.py```

### Starting the server
- start the server
```flask run```
