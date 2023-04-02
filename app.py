# ? Cross-origin Resource Sharing - here it allows the view and core applications deployed on different ports to communicate. No need to know anything about it since it's only used once
from multiprocessing import connection
from flask_cors import CORS, cross_origin
# ? Python's built-in library for JSON operations. Here, is used to convert JSON strings into Python dictionaries and vice-versa
import json
# ? flask - library used to write REST API endpoints (functions in simple words) to communicate with the client (view) application's interactions
# ? request - is the default object used in the flask endpoints to get data from the requests
# ? Response - is the default HTTP Response object, defining the format of the returned data by this api
from flask import Flask, render_template, request, Response, url_for, flash, redirect, request
# ? sqlalchemy is the main library we'll use here to interact with PostgresQL DBMS
import sqlalchemy
# ? Just a class to help while coding by suggesting methods etc. Can be totally removed if wanted, no change
from typing import Dict
# Importing datetime to work with app = Flask(__name__)

from datetime import date

# Importing our register and login forms
from forms import RegistrationForm, LoginForm,PostForm

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required

# ? web-based applications written in flask are simply called apps are initialized in this format from the Flask base class. You may see the contents of `__name__` by hovering on it while debugging if you're curious
app = Flask(__name__)

# Initiate our login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Setting our secret key
app.config['SECRET_KEY'] = '375a627673770da29deabd8de4ec1711'

#Creating our user class
class User(UserMixin):
    def __init__(self, id, username, password, creation_date):
        self.id = id
        self.username = username
        self.password = password
        self.creation_date = creation_date
    



# ? Just enabling the flask app to be able to communicate with any request source
CORS(app)

# ? building our `engine` object from a custom configuration string
# ? for this project, we'll use the default postgres user, on a database called `postgres` deployed on the same machine

YOUR_POSTGRES_PASSWORD = "postgres"
connection_string = f"postgresql://postgres:{YOUR_POSTGRES_PASSWORD}@localhost/postgres"
engine = sqlalchemy.create_engine(
    "postgresql://postgres:postgres@localhost/postgres",
    future=True
)

# ? `db` - the database (connection) object will be used for executing queries on the connected database named `postgres` in our deployed Postgres DBMS
db = engine.connect()

# Creating our home page which is where the posts would show up

@app.route("/")
@app.route("/home")
def home():
    template = ('post_id', 'owner', 'isbn10', 'availability', 'date_posted')
    allposts = []
    try:
        post_retrieval_command = sqlalchemy.text(f"""SELECT * FROM post;""")
        post_res = db.execute(post_retrieval_command)  
        db.commit()
        allposts = post_res.fetchall()
    except Exception as e:
        db.rollback()

    def convert_to_dict(tuple1, tuple2):
        resultDictionary = {tuple1[i] : tuple2[i] for i, _ in enumerate(tuple2)}
        return(resultDictionary)

    post = []
    for i in allposts:
        i = i[0:4] + (i[4].strftime("%Y-%m-%d"),)
        i = tuple(map(str, i))
        result = convert_to_dict(template, i)
        try:
            title_retrieval_command = sqlalchemy.text(f"""SELECT b.title FROM book b WHERE b.isbn10 = '{result['isbn10']}';""")
            retrieved_res = db.execute(title_retrieval_command)
            db.commit()
            thetitle = retrieved_res.fetchall()
            result['title'] = thetitle[0][0]
        except Exception as e:
            db.rollback()    
        post.append(result)
    return render_template('home.html', post=post, title='Home')

# Creating our register route
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            insertion_command = sqlalchemy.text(f"INSERT INTO users (email, username, password, creation_date) VALUES ('{form.data['email']}', '{form.data['username']}', '{form.data['password']}', '{date.today()}');")
            db.execute(insertion_command)
            db.commit()
            flash(f'Account created for {form.username.data} successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    return render_template('register.html', title='Registration', form=form)

# Creating our login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            retrieval_command = sqlalchemy.text(f"""SELECT * FROM users u WHERE u.email ='{form.data['email']}';""") 
            res = db.execute(retrieval_command)
            db.commit()
            retrieved_result = res.fetchone()
            retrieved_result = retrieved_result[0:3] + (retrieved_result[3].strftime("%Y-%m-%d"),)
            retrieved_result = tuple(map(str, retrieved_result))
            if retrieved_result[2] == form.data['password']:
                user = User(retrieved_result[0], retrieved_result[1], retrieved_result[2], retrieved_result[3])
                login_user(user, remember= form.data['remember'])
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            else:
                flash(f'Login Unsuccessful. Kindly check whether you have input the correct email and/or password', 'danger')
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    return render_template('login.html', title='Login', form=form)

@login_manager.user_loader
def load_user(user_id):
    retrieval_command = sqlalchemy.text(f"""SELECT * FROM users u WHERE u.email ='{user_id}';""") 
    res = db.execute(retrieval_command)
    db.commit()
    retrieved_result = res.fetchone()
    retrieved_result = retrieved_result[0:3] + (retrieved_result[3].strftime("%Y-%m-%d"),)
    retrieved_result = tuple(map(str, retrieved_result))
    return User(retrieved_result[0], retrieved_result[1], retrieved_result[2], retrieved_result[3])

# Creating our logout route
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# Creating our account route
@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')



# ? A dictionary containing
data_types = {
    'boolean': 'BOOL',
    'integer': 'INT',
    'text': 'TEXT',
    'time': 'TIME',
}

# ? @app.get is called a decorator, from the Flask class, converting a simple python function to a REST API endpoint (function)


@app.get("/table")
def get_relation():
    # ? This method returns the contents of a table whose name (table-name) is given in the url `http://localhost:port/table?name=table-name`
    # ? Below is the default way of parsing the arguments from http url's using flask's request object
    relation_name = request.args.get('name', default="", type=str)
    # ? We use try-except statements for exception handling since any wrong query will crash the whole flow
    try:
        # ? Statements are built using f-strings - Python's formatted strings
        # ! Use cursors for better results
        statement = sqlalchemy.text(f"SELECT * FROM {relation_name};")
        # ? Results returned by the DBMS after execution are stored into res object defined in sqlalchemy (for reference)
        res = db.execute(statement)
        # ? committing the statement writes the db state to the disk; note that we use the concept of rollbacks for safe DB management
        db.commit()
        # ? Data is extracted from the res objects by the custom function for each query case
        # ! Note that you'll have to write custom handling methods for your custom queries
        data = generate_table_return_result(res)
        # ? Response object is instantiated with the formatted data and returned with the success code 200
        return Response(data, 200)
    except Exception as e:
        # ? We're rolling back at any case of failure
        db.rollback()
        # ? At any error case, the error is returned with the code 403, meaning invalid request
        # * You may customize it for different exception types, in case you may want
        return Response(str(e), 403)


# ? a flask decorator listening for POST requests at the url /table-create
@app.post("/table-create")
def create_table():
    # ? request.data returns the binary body of the POST request
    data = request.data.decode()
    try:
        # ? data is converted from stringified JSON to a Python dictionary
        table = json.loads(data)
        # ? data, or table, is an object containing keys to define column names and types of the table along with its name
        statement = generate_create_table_statement(table)
        # ? the remaining steps are the same
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/table-insert")
# ? a flask decorator listening for POST requests at the url /table-insert and handles the entry insertion into the given table/relation
# * You might wonder why PUT or a similar request header was not used here. Fundamentally, they act as POST. So the code was kept simple here
def insert_into_table():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        insertion = json.loads(data)
        statement = generate_insert_table_statement(insertion)
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/table-update")
# ? a flask decorator listening for POST requests at the url /table-update and handles the entry updates in the given table/relation
def update_table():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        update = json.loads(data)
        statement = generate_update_table_statement(update)
        db.execute(statement)
        db.commit()
        return Response(statement.text, 200)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


@app.post("/entry-delete")
# ? a flask decorator listening for POST requests at the url /entry-delete and handles the entry deletion in the given table/relation
def delete_row():
    # ? Steps are common in all of the POST behaviors. Refer to the statement generation for the explanatory
    data = request.data.decode()
    try:
        delete = json.loads(data)
        statement = generate_delete_statement(delete)
        db.execute(statement)
        db.commit()
        return Response(statement.text)
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)


def generate_table_return_result(res):
    # ? An empty Python list to store the entries/rows/tuples of the relation/table
    rows = []

    # ? keys of the SELECT query result are the columns/fields of the table/relation
    columns = list(res.keys())

    # ? Constructing the list of tuples/rows, basically, restructuring the object format
    for row_number, row in enumerate(res):
        rows.append({})
        for column_number, value in enumerate(row):
            rows[row_number][columns[column_number]] = value

    # ? JSON object with the relation data
    output = {}
    output["columns"] = columns  # ? Stores the fields
    output["rows"] = rows  # ? Stores the tuples

    """
        The returned object format:
        {
            "columns": ["a","b","c"],
            "rows": [
                {"a":1,"b":2,"c":3},
                {"a":4,"b":5,"c":6}
            ]
        }
    """
    # ? Returns the stringified JSON object
    return json.dumps(output)


def generate_delete_statement(details: Dict):
    # ? Fetches the entry id for the table name
    table_name = details["relationName"]
    id = details["deletionId"]
    # ? Generates the deletion query for the given entry with the id
    statement = f"DELETE FROM {table_name} WHERE id={id};"
    return sqlalchemy.text(statement)


def generate_update_table_statement(update: Dict):

    # ? Fetching the table name, entry/tuple id and the update body
    table_name = update["name"]
    id = update["id"]
    body = update["body"]

    # ? Default for the SQL update statement
    statement = f"UPDATE {table_name} SET "
    # ? Constructing column-to-value maps looping
    for key, value in body.items():
        statement += f"{key}=\'{value}\',"

    # ?Finalizing the update statement with table and row details and returning
    statement = statement[:-1]+f" WHERE {table_name}.id={id};"
    return sqlalchemy.text(statement)


def generate_insert_table_statement(insertion: Dict):
    # ? Fetching table name and the rows/tuples body object from the request
    table_name = insertion["name"]
    body = insertion["body"]
    valueTypes = insertion["valueTypes"]

    # ? Generating the default insert statement template
    statement = f"INSERT INTO {table_name}  "

    # ? Appending the entries with their corresponding columns
    column_names = "("
    column_values = "("
    for key, value in body.items():
        column_names += (key+",")
        if valueTypes[key] == "TEXT" or valueTypes[key] == "TIME":
            column_values += (f"\'{value}\',")
        else:
            column_values += (f"{value},")

    # ? Removing the last default comma
    column_names = column_names[:-1]+")"
    column_values = column_values[:-1]+")"

    # ? Combining it all into one statement and returning
    #! You may try to expand it to multiple tuple insertion in another method
    statement = statement + column_names+" VALUES "+column_values+";"
    return sqlalchemy.text(statement)


def generate_create_table_statement(table: Dict):
    # ? First key is the name of the table
    table_name = table["name"]
    # ? Table body itself is a JSON object mapping field/column names to their values
    table_body = table["body"]
    # ? Default table creation template query is extended below. Note that we drop the existing one each time. You might improve this behavior if you will
    # ! ID is the case of simplicity
    statement = f"DROP TABLE IF EXISTS {table_name}; CREATE TABLE {table_name} (id serial NOT NULL PRIMARY KEY,"
    # ? As stated above, column names and types are appended to the creation query from the mapped JSON object
    for key, value in table_body.items():
        statement += (f"{key}"+" "+f"{value}"+",")
    # ? closing the final statement (by removing the last ',' and adding ');' termination and returning it
    statement = statement[:-1] + ");"
    return sqlalchemy.text(statement)

# ? This method can be used by waitress-serve CLI


def create_app():
    return app


# ? The port where the debuggable DB management API is served
PORT = 2223

# ? Running the flask app on the localhost/0.0.0.0, port 2222
# ? Note that you may change the port, then update it in the view application too to make it work (don't if you don't have another application occupying it)
if __name__ == "__main__":
    app.run("0.0.0.0", PORT)
    # ? Uncomment the below lines and comment the above lines below `if __name__ == "__main__":` in order to run on the production server
    # ? Note that you may have to install waitress running `pip install waitress`
    # ? If you are willing to use waitress-serve command, please add `/home/sadm/.local/bin` to your ~/.bashrc
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=PORT)


##create post

@app.route("/create_post", methods=['GET', 'POST'])

#@login_required # Adding login_required decorator to ensure only logged in users can access this route
def create_post():
    form = PostForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        try:
            # First, insert the new book (if it does not exist yet)
            insertion_command = sqlalchemy.text(f"""INSERT INTO book (isbn10, title, author) 
                                                    SELECT '{form.isbn10.data}', '{form.title.data}', '{form.author.data}' 
                                                    WHERE NOT EXISTS (SELECT 1 FROM book WHERE isbn10='{form.isbn10.data}');""")
            db.execute(insertion_command)
            db.commit()
            
            # Get the user's ID from the current_user variable ---prolly need to convert to dictionary
            user_id = current_user.get_id()
            
            # Then, insert the new post
            insertion_command = sqlalchemy.text(f"""INSERT INTO post (owner, isbn10, availability, post_date) 
                                                    VALUES ('{user_id}', '{form.isbn10.data}', '{form.availability.data}', '{date.today()}');""")
            db.execute(insertion_command)
            db.commit()
            flash(f'Post created for {form.title.data} successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    return render_template('create_post.html', title='Create Post', form=form)

###update post 

#@app.route("/post/<int:post_id>")
#def post(post_id):
    #post = Post.query.get_or_404(post_id)  ---prolly need to retrieve it from the dictionary
    #return render_template('post.html', title=post.title, post=post)

##Delete post
def delete_post(post_id):
    try:
        # Delete the post with the specified post_id
        deletion_command = sqlalchemy.text(f"""DELETE FROM post WHERE id='{post_id}'""")
        db.execute(deletion_command)
        db.commit()
        flash(f'Post with ID {post_id} has been deleted successfully!', 'success')
    except Exception as e:
        db.rollback()
        return Response(str(e), 403)