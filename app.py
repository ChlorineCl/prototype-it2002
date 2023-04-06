# ? Cross-origin Resource Sharing - here it allows the view and core applications deployed on different ports to communicate. No need to know anything about it since it's only used once
from multiprocessing import connection
from flask_cors import CORS, cross_origin
# ? Python's built-in library for JSON operations. Here, is used to convert JSON strings into Python dictionaries and vice-versa
import json
# ? flask - library used to write REST API endpoints (functions in simple words) to communicate with the client (view) application's interactions
# ? request - is the default object used in the flask endpoints to get data from the requests
# ? Response - is the default HTTP Response object, defining the format of the returned data by this api
from flask import Flask, render_template, request, Response, url_for, flash, redirect, request, abort
# ? sqlalchemy is the main library we'll use here to interact with PostgresQL DBMS
import sqlalchemy
# ? Just a class to help while coding by suggesting methods etc. Can be totally removed if wanted, no change
from typing import Dict
# Importing datetime to work with app = Flask(__name__)

from datetime import date

# Importing our register and login forms
from forms import RegistrationForm, LoginForm, PostForm, UpdateForm, BorrowForm, ReturnForm, AddBookForm, DeleteBookForm, ISBN10Form, UpdateBookForm, DeleteUserForm

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
# from flask_wtf import FlaskForm
# from wtforms_alchemy import QuerySelectMultipleField
# from wtforms import widgets

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

@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    template = ('post_id', 'owner', 'isbn10', 'availability', 'date_posted')
    allposts = []

    if request.method == 'POST': #if there is a filter submission
        title = request.form.getlist('title_search')
        availability = request.form.getlist('avail_radio')
        dateorder = request.form.getlist('date_radio')
        ordering = request.form.getlist('order_radio')

        str1 = "SELECT p.post_id, p.owner, p.isbn10, p.availability, p.post_date FROM post p, book b WHERE p.isbn10 = b.isbn10 "
        if title:
            str1 += "AND  b.title LIKE '%" + title[0] + "%' "
        if availability:
            str1 += "AND p.availability = " + availability[0] + " "
        if dateorder:
            str1 += "ORDER BY p.post_date " + dateorder[0]
            if ordering:
                str1 += ", b.title " + ordering[0]
        else:
            if ordering:
                str1 += "ORDER BY b.title " + ordering[0]
        # print(str1)

        try:
            post_retrieval_command = sqlalchemy.text(str1)
            post_res = db.execute(post_retrieval_command)  
            db.commit()
            allposts = post_res.fetchall()
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)

            
    else: #if there is no filters
        try:
            post_retrieval_command = sqlalchemy.text(f"""SELECT * FROM post ORDER BY post_date DESC ;""")
            post_res = db.execute(post_retrieval_command)  
            db.commit()
            allposts = post_res.fetchall()
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)

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
            return Response(str(e), 403)    
        post.append(result)
    return render_template('home.html', post=post, title='Home')

#Creating Books route
@app.route("/books", methods=['GET', 'POST'])
def books():
    template = ('isbn10', 'title', 'authors', 'publisher', 'genre')
    allbooks = []

    #get the genre list
    retrieval_command_3 = sqlalchemy.text(f"""SELECT b.genre, COUNT(b.genre) FROM book b 
                                                GROUP BY b.genre
                                                ORDER BY COUNT(b.genre) ;
                                                """)
    res_3 = db.execute(retrieval_command_3)
    db.commit()
    res_3 = res_3.fetchall()

    most_pop_genres = []
    for i in res_3:
        i = map(str, i[0].split('|'))
        most_pop_genres += i
    most_pop_genres_unique = []
    for i in most_pop_genres:
        if i not in most_pop_genres_unique:
            most_pop_genres_unique.append(i)

    if request.method == 'POST': #if there is a filter submission
        filters = request.form.getlist('genre_checkbox')
        ordering = request.form.getlist('order_radio')
        pops = request.form.getlist('pops_radio')
        title = request.form.getlist('title_search')

        if pops:
            newstr1 ="""SELECT b.isbn10, b.title, b.authors, b.publisher, b.genre
                            FROM post p, transactions t, book b
                            WHERE p.post_id = t.post_id AND p.isbn10 = b.isbn10 AND t.type = 'borrow'"""
            newstr2 = ""
            newstr21 = ""
            newstr3 = """ GROUP BY b.isbn10
                            ORDER BY COUNT(b.isbn10) """ + pops[0] 
            newstr4 = ""
            if filters:
                genre = filters[0]
                newstr2 = "AND (b.genre LIKE '%" + genre + "%' "
                for genre in filters[1:]:
                    newstr2 += "OR b.genre LIKE '%" + genre + "%' "
                newstr2 += ") "
            if title:
                newstr21 = "AND b.title LIKE '%" + title[0] + "%' "
            if ordering:
                newstr4 = ", b.title " + ordering[0]
            strng = newstr1 + newstr2 + newstr21 + newstr3 + newstr4
            
        #appending all the genres to a string of query
        else:
            if filters:
                genre = filters[0]
                strng = "SELECT * FROM book b WHERE b.genre LIKE '%" + genre + "%' "
                for genre in filters[1:]:
                    newstr = "UNION SELECT * FROM book b WHERE b.genre LIKE '%" + genre + "%' "
                    strng += newstr
                
            if title:
                if filters:
                    strng += "INTERSECT SELECT * FROM book b WHERE b.title LIKE '%" + title[0] + "%' "
                else:
                    strng = "SELECT * FROM book b WHERE b.title LIKE '%" + title[0] + "%' "

            if ordering:
                newstr = "ORDER BY b.title " + ordering[0]
                strng += newstr
            
        strng = strng + ";"
        #print(strng) 
        #doing the retrieval
        try:
            book_retrieval_command = sqlalchemy.text(strng)
            book_res = db.execute(book_retrieval_command)  
            db.commit()
            allbooks = book_res.fetchall()
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)

    #if no filter submission
    else:
        try:
            book_retrieval_command = sqlalchemy.text(f"""SELECT * FROM book ORDER BY title ASC ;""")
            book_res = db.execute(book_retrieval_command)  
            db.commit()
            allbooks = book_res.fetchall()
        except Exception as e:
            db.rollback()

    def convert_to_dict(tuple1, tuple2):
        resultDictionary = {tuple1[i] : tuple2[i] for i, _ in enumerate(tuple2)}
        return(resultDictionary)

    books = []
    for i in allbooks:
        result = convert_to_dict(template, i) 
        books.append(result)
    return render_template('books.html', books=books, title='Books', genres = most_pop_genres_unique )

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
    user_stats = {}
    
    # Books that current user is currently borrowing
    retrieval_command_1 = sqlalchemy.text(f"""SELECT p.isbn10, b.title 
                                                    FROM book b, post p , ( SELECT * 
                                                                    FROM transactions t
                                                                    WHERE t.borrower_email = '{current_user.id}'
                                                                    AND t.type = 'borrow'
                                                                    AND NOT EXISTS( SELECT *
                                                                                    FROM transactions t1
                                                                                    WHERE t1.borrower_email = t.borrower_email
                                                                                    AND t.post_id = t1.post_id
                                                                                    AND t1.transaction_id > t.transaction_id
                                                                                    AND t1.type = 'return')) AS latest_transaction
                                                    WHERE p.post_id = latest_transaction.post_id
                                                    AND b.isbn10 = p.isbn10 
                                                    AND latest_transaction.type = 'borrow';""") 
    res_1 = db.execute(retrieval_command_1)
    db.commit()
    res_1 = res_1.fetchall()
    books = []
    for i in res_1:
        book = [str(i[0]), str(i[1])]
        books.append(book)
    user_stats['books_borrowed'] = books

    # Books that current user is currently lending
    retrieval_command_2 = sqlalchemy.text(f"""SELECT latest_transaction.borrower_email, p.isbn10, b.title 
                                                    FROM book b, post p , ( SELECT * 
                                                                    FROM transactions t
                                                                    WHERE t.lender_email = '{current_user.id}'
                                                                    AND t.type = 'borrow'
                                                                    AND NOT EXISTS( SELECT *
                                                                                    FROM transactions t1
                                                                                    WHERE t1.lender_email = t.lender_email
                                                                                    AND t.post_id = t1.post_id
                                                                                    AND t1.transaction_id > t.transaction_id
                                                                                    AND t1.type = 'return')) AS latest_transaction
                                                    WHERE p.post_id = latest_transaction.post_id
                                                    AND b.isbn10 = p.isbn10 
                                                    AND latest_transaction.type = 'borrow';""") 
    res_2 = db.execute(retrieval_command_2)
    db.commit()
    res_2 = res_2.fetchall()
    books2 = []
    for i in res_2:
        book2 = [str(i[0]), str(i[1]), str(i[2])]
        books2.append(book2)
    user_stats['books_lended'] = books2

    # posts made by the user
    retrieval_command_3 = sqlalchemy.text(f"""SELECT * FROM post WHERE owner = '{current_user.id}' ORDER BY post_date DESC ;""")
    res_3 = db.execute(retrieval_command_3)
    db.commit()
    res_3 = res_3.fetchall()

    template = ('post_id', 'owner', 'isbn10', 'availability', 'date_posted')

    def convert_to_dict(tuple1, tuple2):
            resultDictionary = {tuple1[i] : tuple2[i] for i, _ in enumerate(tuple2)}
            return(resultDictionary)
    post = []

    for i in res_3:
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
            return Response(str(e), 403)    
        post.append(result)

    #finding how many days the user has been active
    creation_date_command = sqlalchemy.text(f"""SELECT creation_date FROM users u WHERE u.email = 'wbare0@ow.ly'""")
    creation_res = db.execute(creation_date_command)
    db.commit()
    creation_date = creation_res.fetchall()

    curr_date_command = sqlalchemy.text(f"""SELECT CAST(now() as date);""")
    curr_res = db.execute(curr_date_command)
    db.commit()
    curr_date = curr_res.fetchall()
    no_days = curr_date[0][0]-creation_date[0][0]
    no_days = str(no_days.days)

    return render_template('account.html', title='Account', user_stats = user_stats, post=post, no_days=no_days)
    
#create post
@app.route("/post/new", methods=['GET', 'POST'])
@login_required 
def new_post():
    form = PostForm() 
    user_id = current_user.id 
    if form.validate_on_submit(): 
        try:
            retrieve_book = sqlalchemy.text(f"""SELECT b.title FROM book b WHERE b.isbn10 ='{form.data['isbn10']}';""")
            res = db.execute(retrieve_book)
            db.commit()
            retrieved_title = res.fetchone() 
            if retrieved_title:
                retrieve_post_id = sqlalchemy.text(f"""SELECT MAX(post_id) FROM post;""")
                res2 = db.execute(retrieve_post_id)
                db.commit()
                retrieved_post_id = res2.fetchone()
                insertion_command = sqlalchemy.text(f"""INSERT INTO post (post_id, owner, isbn10, availability, post_date) 
                                                    VALUES ('{retrieved_post_id[0] + 1}','{user_id}', '{form.data['isbn10']}', '{form.data['availability']}', '{date.today()}');""")
                db.execute(insertion_command) 
                db.commit() 
                flash(f'Post created for {retrieved_title[0]} successfully!', 'success') 
                return redirect(url_for('home'))
            else:
                flash(f'You have either input a wrong isbn10, or tried to create a post for a book that is not registered on our website', 'danger')
        except Exception as e:
            db.rollback() 
            return Response(str(e), 403)
    return render_template('create_post.html', title='Create Post', form=form) 

@app.route("/post/<int:post_id>")
@login_required # Adding login_required decorator to ensure only logged in users can access this route
def post(post_id):
    post = []
    borrower = ""
    try:
        retrieve_post = sqlalchemy.text(f"""SELECT * FROM post WHERE post_id='{post_id}';""")
        res = db.execute(retrieve_post)
        db.commit()
        retrieved_post = res.fetchone()
        if retrieved_post:
            template = ('post_id', 'owner', 'isbn10', 'availability', 'date_posted')

            def convert_to_dict(tuple1, tuple2):
                resultDictionary = {tuple1[i] : tuple2[i] for i, _ in enumerate(tuple2)}
                return(resultDictionary)
            
            retrieved_post = retrieved_post[0:4] + (retrieved_post[4].strftime("%Y-%m-%d"),)
            retrieved_post = tuple(map(str, retrieved_post))
            result = convert_to_dict(template, retrieved_post)

            title_retrieval_command = sqlalchemy.text(f"""SELECT b.title FROM book b WHERE b.isbn10 = '{result['isbn10']}';""")
            retrieved_res = db.execute(title_retrieval_command)
            db.commit()
            thetitle = retrieved_res.fetchone()
            result['title'] = thetitle[0]

            post.append(result)

            try:
                retrieve_borrower = sqlalchemy.text(f"""SELECT latest_transaction.borrower_email 
                                                        FROM post p , (SELECT t.borrower_email, t.post_id, t.type
                                                                        FROM transactions t
                                                                        WHERE t.borrower_email = '{current_user.id}'
                                                                        AND t.post_id = {post_id}
                                                                        ORDER BY transaction_id DESC LIMIT 1 ) AS latest_transaction
                                                        WHERE p.post_id = latest_transaction.post_id 
                                                        AND latest_transaction.type = 'borrow';""")
                borrower_res = db.execute(retrieve_borrower)
                db.commit()
                retrieved_borrower = borrower_res.fetchone()
                if retrieved_borrower:
                    borrower = retrieved_borrower[0]
            except Exception as e:
                db.rollback() 
                return Response(str(e), 403)

            return render_template('post.html', title=result['title'], post=post, borrower=borrower)
        else:
            return Response('Post not found', 404)
    except Exception as e:
            db.rollback() 
            return Response(str(e), 403)

# Update post route
@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    try:
        retrieve_post = sqlalchemy.text(f"""SELECT * FROM post WHERE post_id='{post_id}';""")
        res = db.execute(retrieve_post)
        db.commit()
        retrieved_post = res.fetchone()
        if retrieved_post[1] != current_user.id:
            abort(403)
        if retrieved_post:
            form = UpdateForm()
            form.isbn10.data = retrieved_post[2]
            if form.validate_on_submit():
                try:
                    update_command = sqlalchemy.text(f"""UPDATE post SET availability = '{form.data['availability']}' WHERE post_id='{post_id}';""")
                    db.execute(update_command)
                    db.commit()
                    flash(f'Post availability updated successfully', 'success')
                    return redirect(url_for('post', post_id = post_id))
                except Exception as e:
                    db.rollback() 
                    return Response(str(e), 403)
            return render_template('update_post.html', title='Update Post', form=form)
        else:
            return Response('Post not found', 404)
    except Exception as e:
            db.rollback() 
            return Response(str(e), 403)

@app.route("/borrow")
@login_required
def borrow():
    template = ('post_id', 'owner', 'isbn10', 'availability', 'date_posted')
    allposts = []
    try:
        post_retrieval_command = sqlalchemy.text(f"""SELECT * FROM post WHERE availability=True ORDER BY post_date DESC ;""")
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
    return render_template('borrow_post.html', post=post, title='Books available to borrow')

@app.route("/post/<int:post_id>/borrow_book", methods=['GET', 'POST'])
@login_required
def borrow_book(post_id):
    try:
        retrieve_post = sqlalchemy.text(f"""SELECT * FROM post WHERE post_id='{post_id}';""")
        res = db.execute(retrieve_post)
        db.commit()
        retrieved_post = res.fetchone()
        if retrieved_post:
            if retrieved_post[3] != True:
                flash('This book is not available to be borrowed', 'danger')
                return redirect(url_for('post', post_id = post_id))
            
            retrieve_title = sqlalchemy.text(f"""SELECT b.title FROM book b WHERE b.isbn10='{retrieved_post[2]}';""")
            res2 = db.execute(retrieve_title)
            db.commit()
            retrieved_title = res2.fetchone()

            form = BorrowForm()
            form.post_id.data = retrieved_post[0]
            form.title.data = retrieved_title[0]
            form.isbn10.data = retrieved_post[2]
            form.owner.data = retrieved_post[1]
            if form.validate_on_submit():
                if current_user.id == retrieved_post[1]:
                    flash('You cannot borrow books owned by you', 'danger')
                    return redirect(url_for('post', post_id = post_id))
                try:
                    borrower = current_user.id
                    retrieve_transaction_id = sqlalchemy.text(f"""SELECT MAX(transaction_id) FROM transactions;""")
                    res3 = db.execute(retrieve_transaction_id)
                    db.commit()
                    retrieved_transaction_id = res3.fetchone()

                    insert_command = sqlalchemy.text(f"""INSERT INTO transactions (transaction_id, post_id, borrower_email, lender_email, transaction_date, type) VALUES
                    ('{retrieved_transaction_id[0] + 1}', '{post_id}', '{borrower}', '{retrieved_post[1]}', '{date.today()}', 'borrow');""")
                    db.execute(insert_command)
                    db.commit()

                    update_post_command = sqlalchemy.text(f"""UPDATE post SET availability=False WHERE post_id={post_id};""")
                    db.execute(update_post_command)
                    db.commit()

                    flash(f'Book borrowed successfully. Enjoy it!', 'success')
                    return redirect(url_for('home'))
                except Exception as e:
                    db.rollback() 
                    return Response(str(e), 403)
            return render_template('borrow_book.html', title='Book Borrowing', form=form)
        else:
            return Response('Post not found', 404)
    except Exception as e:
                    db.rollback() 
                    return Response(str(e), 403)

@app.route("/return")
@login_required
def return_post():
    template = ('post_id', 'owner', 'isbn10', 'availability', 'date_posted')
    allposts = []
    try:
        post_retrieval_command = sqlalchemy.text(f"""SELECT p.post_id, p.owner, p.isbn10, p.availability, p.post_date 
                                                    FROM post p , ( SELECT * 
                                                                    FROM transactions t
                                                                    WHERE t.borrower_email = '{current_user.id}'
                                                                    AND t.type = 'borrow'
                                                                    AND NOT EXISTS( SELECT *
                                                                                    FROM transactions t1
                                                                                    WHERE t1.borrower_email = t.borrower_email
                                                                                    AND t.post_id = t1.post_id
                                                                                    AND t1.transaction_id > t.transaction_id
                                                                                    AND t1.type = 'return')) AS latest_transaction
                                                    WHERE p.post_id = latest_transaction.post_id 
                                                    AND latest_transaction.type = 'borrow';""")
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

    return render_template('return_post.html', post=post, title='Books available to return')

@app.route("/post/<int:post_id>/return_book", methods=['GET', 'POST'])
@login_required
def return_book(post_id):
    try:
        retrieve_post = sqlalchemy.text(f"""SELECT * FROM post WHERE post_id='{post_id}';""")
        res = db.execute(retrieve_post)
        db.commit()
        retrieved_post = res.fetchone()
        if retrieved_post:
            if retrieved_post[3] == True:
                flash('This book belonging to this post has already been returned', 'danger')
                return redirect(url_for('post', post_id = post_id))
            
            retrieve_title = sqlalchemy.text(f"""SELECT b.title FROM book b WHERE b.isbn10='{retrieved_post[2]}';""")
            res2 = db.execute(retrieve_title)
            db.commit()
            retrieved_title = res2.fetchone()

            form = ReturnForm()
            form.post_id.data = retrieved_post[0]
            form.title.data = retrieved_title[0]
            form.isbn10.data = retrieved_post[2]
            form.owner.data = retrieved_post[1]
            if form.validate_on_submit():
                if current_user.id == retrieved_post[1]:
                    flash('You cannot return books owned by you', 'danger')
                    return redirect(url_for('post', post_id = post_id))
                
                retrieve_borrower = sqlalchemy.text(f"""SELECT borrower_email FROM transactions WHERE post_id='{post_id}';""")
                resb = db.execute(retrieve_borrower)
                db.commit()
                retrieved_borrower = resb.fetchone()
                if retrieved_borrower[0] != current_user.id:
                    flash('You are not the borrower of this book from this post', 'danger')
                    return redirect(url_for('post', post_id = post_id)) 

                try:
                    returner = current_user.id
                    retrieve_transaction_id = sqlalchemy.text(f"""SELECT MAX(transaction_id) FROM transactions;""")
                    res3 = db.execute(retrieve_transaction_id)
                    db.commit()
                    retrieved_transaction_id = res3.fetchone()

                    insert_command = sqlalchemy.text(f"""INSERT INTO transactions (transaction_id, post_id, borrower_email, lender_email, transaction_date, type) VALUES
                    ('{retrieved_transaction_id[0] + 1}', '{post_id}', '{returner}', '{retrieved_post[1]}', '{date.today()}', 'return');""")
                    db.execute(insert_command)
                    db.commit()

                    update_post_command = sqlalchemy.text(f"""UPDATE post SET availability=True WHERE post_id={post_id};""")
                    db.execute(update_post_command)
                    db.commit()

                    flash(f'Book returned successfully. Thanks!', 'success')
                    return redirect(url_for('home'))
                except Exception as e:
                    db.rollback() 
                    return Response(str(e), 403)
            return render_template('return_book.html', title='Book Returning', form=form)
        else:
            return Response('Post not found', 404)
    except Exception as e:
                    db.rollback() 
                    return Response(str(e), 403)

@app.route("/manage", methods=['GET', 'POST'])
@login_required
def manage():
    if current_user.id != 'group8@admin.nus':
        flash('You are not authorised to access this page', 'danger')
        return redirect(url_for('home'))
    return render_template('manage.html', title='Manage Books')

@app.route("/add_book", methods=['GET', 'POST'])
@login_required
def add_book():
    if current_user.id != 'group8@admin.nus':
        flash('You are not authorised to access this page', 'danger')
        return redirect(url_for('home'))
    form = AddBookForm()
    if form.validate_on_submit():
        try:
            insertion_command = sqlalchemy.text(f"INSERT INTO book (isbn10, title, authors, publisher, genre) VALUES ('{form.data['isbn10']}', '{form.data['title']}', '{form.data['authors']}', '{form.data['publisher']}', '{form.data['genre']}');")
            db.execute(insertion_command)
            db.commit()
            flash(f"{form.data['title']} written by {form.data['authors']} added successfully!", 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    return render_template('add_book.html', title='Add a Book', form=form)

@app.route("/update_book", methods=['GET', 'POST'])
@login_required
def update_book():
    if current_user.id != 'group8@admin.nus':
        flash('You are not authorised to access this page', 'danger')
        return redirect(url_for('home'))
    form = ISBN10Form()
    if form.validate_on_submit():
            retrieval_command = sqlalchemy.text(f"""SELECT * FROM book WHERE isbn10='{form.data['isbn10']}';""")
            res = db.execute(retrieval_command)
            db.commit()
            retrieved_book = res.fetchone()
            if retrieved_book:
                return redirect(url_for('update_this_book', isbn10 = form.data['isbn10']))
            else:
                flash('This book does not exist. Please check.', 'danger')
                return redirect(url_for('update_book'))
    return render_template('update_book.html', title='Update a Book', form=form)

@app.route("/update_book/<string:isbn10>", methods=['GET', 'POST'])
@login_required
def update_this_book(isbn10):
    if current_user.id != 'group8@admin.nus':
        flash('You are not authorised to access this page', 'danger')
        return redirect(url_for('home'))

    form = UpdateBookForm()

    if form.validate_on_submit():
        try:
            update_command = sqlalchemy.text(f"""UPDATE book SET isbn10 = '{form.data['isbn10']}', 
                                                             title = '{form.data['title']}',
                                                             authors = '{form.data['authors']}',
                                                             publisher = '{form.data['publisher']}',
                                                             genre = '{form.data['genre']}'
                                                             WHERE isbn10='{isbn10}';""")
            db.execute(update_command)
            db.commit()
            flash(f'Book updated for {isbn10} successfully!', 'success')
            return redirect(url_for('manage'))
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    return render_template('update_this_book.html', title='Update the details for this Book', form=form)

    

@app.route("/delete_book", methods=['GET', 'POST'])
@login_required
def delete_book():
    if current_user.id != 'group8@admin.nus':
        flash('You are not authorised to access this page', 'danger')
        return redirect(url_for('home'))
    form = DeleteBookForm()
    if form.validate_on_submit():
        try:
            delete_command = sqlalchemy.text(f"DELETE FROM book WHERE isbn10='{form.data['isbn10']}';")
            db.execute(delete_command)
            db.commit()
            flash(f"Book with isbn10 {form.data['isbn10']} deleted successfully!", 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.rollback()
            return Response(str(e), 403)
    return render_template('delete_book.html', title='Delete a Book', form=form)

@app.route("/delete_user", methods=['GET', 'POST'])
@login_required
def delete_user():
    if current_user.id != 'group8@admin.nus':
        flash('You are not authorised to access this page', 'danger')
        return redirect(url_for('home'))
    form = DeleteUserForm()
    if form.validate_on_submit():
        retrieval_command = sqlalchemy.text(f"SELECT * FROM users WHERE email='{form.data['email']}';")
        res = db.execute(retrieval_command)
        db.commit()
        res = res.fetchone()
        if res:
            try:
                delete_command = sqlalchemy.text(f"DELETE FROM users WHERE email='{form.data['email']}';")
                db.execute(delete_command)
                db.commit()
                flash(f"User with email {form.data['email']} deleted successfully!", 'success')
                return redirect(url_for('home'))
            except Exception as e:
                db.rollback()
                return Response(str(e), 403)
        else:
            flash(f"User with {form.data['email']} not found. Kindly check whether you have input the correct email", "danger")
            return redirect(url_for('manage'))
    return render_template('delete_user.html', title='Delete a User', form=form)


@app.route("/stats")
def stats():

    stats = {}

    def convert_to_dict(tuple1, tuple2):
        resultDictionary = {tuple1[i] : tuple2[i] for i, _ in enumerate(tuple2)}
        return(resultDictionary)
    
    try:
        # Top 5 most popz books
        retrieval_command_1 = sqlalchemy.text(f"""SELECT b.title, COUNT(b.isbn10) FROM post p, transactions t, book b
                                                WHERE p.post_id = t.post_id AND p.isbn10 = b.isbn10 AND t.type = 'borrow'
                                                GROUP BY b.isbn10
                                                ORDER BY COUNT(b.isbn10) DESC
                                                LIMIT 5;;""")
        res_1 = db.execute(retrieval_command_1)
        db.commit()
        res_1 = res_1.fetchall()
        most_pop_books = [str(i[0]) for i in res_1]
        stats['most_pop_books'] = most_pop_books

        #Top 5 most popz authors
        retrieval_command_2 = sqlalchemy.text(f"""SELECT b.authors, COUNT(b.authors) FROM post p, transactions t, book b
                                                WHERE p.post_id = t.post_id AND p.isbn10 = b.isbn10 AND t.type = 'borrow'
                                                GROUP BY b.authors
                                                ORDER BY COUNT(b.authors) DESC
                                                LIMIT 5;""")
        res_2 = db.execute(retrieval_command_2)
        db.commit()
        res_2 = res_2.fetchall()
        most_pop_authors = [str(i[0]) for i in res_2]
        stats['most_pop_authors'] = most_pop_authors

        #Top 5 most popz genres
        retrieval_command_3 = sqlalchemy.text(f"""SELECT b.genre, COUNT(b.genre) FROM post p, transactions t, book b
                                                WHERE p.post_id = t.post_id AND p.isbn10 = b.isbn10 AND t.type = 'borrow'
                                                GROUP BY b.genre
                                                ORDER BY COUNT(b.genre) DESC;
                                                """)
        res_3 = db.execute(retrieval_command_3)
        db.commit()
        res_3 = res_3.fetchall()

        most_pop_genres = []
        for i in res_3:
            i = map(str, i[0].split('|'))
            most_pop_genres += i
        most_pop_genres_unique = []
        for i in most_pop_genres:
            if i not in most_pop_genres_unique:
                most_pop_genres_unique.append(i)
        if len(most_pop_genres_unique) <= 5:
            stats['most_pop_genres'] = most_pop_genres_unique
        else:
            stats['most_pop_genres'] = most_pop_genres_unique[0:5]
        

        # Top 5 most avid borrowers
        retrieval_command_4 = sqlalchemy.text(f"""SELECT u.username, u.email, COUNT(u.email) FROM users u, transactions t
                                                WHERE u.email = t.borrower_email AND t.type = 'borrow'
                                                GROUP BY u.email
                                                ORDER BY COUNT(u.email) DESC
                                                LIMIT 5;""")
        res_4 = db.execute(retrieval_command_4)
        db.commit()
        res_4 = res_4.fetchall()
        top_borrowers  = [str(i[0]) for i in res_4]
        stats['top_borrowers'] = top_borrowers  


        # Top 5 most avid lenders
        retrieval_command_5 = sqlalchemy.text(f"""SELECT u.username, u.email, COUNT(u.email) FROM users u, transactions t
                                                WHERE u.email = t.lender_email AND t.type = 'borrow'
                                                GROUP BY u.email
                                                ORDER BY COUNT(u.email) DESC
                                                LIMIT 5;""")
        res_5 = db.execute(retrieval_command_5)
        db.commit()
        res_5 = res_5.fetchall()
        top_lenders  = [str(i[0]) for i in res_5]
        stats['top_lenders'] = top_lenders

        # Top 5 most frequently posted books
        retrieval_command_6 = sqlalchemy.text(f"""SELECT b.title, COUNT(b.isbn10)
                                                FROM post p, book b
                                                WHERE p.isbn10 = b.isbn10
                                                GROUP BY b.isbn10
                                                ORDER BY COUNT(b.isbn10) DESC
                                                LIMIT 5;""")
        res_6 = db.execute(retrieval_command_6)
        db.commit()
        res_6 = res_6.fetchall()
        frequently_posted  = [str(i[0]) for i in res_6]
        stats['frequently_posted'] = frequently_posted 

        # Top 5 books borrowed for the longest period of time
        retrieval_command_7 = sqlalchemy.text(f"""SELECT DISTINCT(b2.title), temp2.duration
                                                FROM
                                                    (
                                                    SELECT temp.post_id, (temp.end_date-temp.start_date) duration
                                                    FROM 
                                                        (
                                                        SELECT b.post_id, b.transaction_date start_date, r.transaction_date end_date
                                                        FROM 
                                                            (SELECT * FROM transactions t1
                                                            WHERE t1.type = 'borrow') AS b,
                                                            (SELECT * FROM transactions t2
                                                            WHERE t2.type = 'return') AS r
                                                        WHERE b.borrower_email = r.borrower_email
                                                        AND b.lender_email = r.lender_email
                                                        AND b.post_id = r.post_id
                                                        ) AS temp
                                                    ORDER BY (temp.end_date-temp.start_date) DESC
                                                    ) AS temp2,
                                                    book b2,
                                                    post p
                                                WHERE temp2.post_id = p.post_id
                                                AND p.isbn10 = b2.isbn10
                                                ORDER BY temp2.duration DESC;""")
        res_7 = db.execute(retrieval_command_7)
        db.commit()
        res_7 = res_7.fetchall()
        longest = []
        for i in res_7:
            if i[0] not in longest:
                longest.append(str(i[0]))
        stats['longest'] = longest[0:5]

        # Top 5 books borrowed for the shortest period of time
        retrieval_command_8 = sqlalchemy.text(f"""SELECT DISTINCT(b2.title), temp2.duration
                                                FROM
                                                    (
                                                    SELECT temp.post_id, (temp.end_date-temp.start_date) duration
                                                    FROM 
                                                        (
                                                        SELECT b.post_id, b.transaction_date start_date, r.transaction_date end_date
                                                        FROM 
                                                            (SELECT * FROM transactions t1
                                                            WHERE t1.type = 'borrow') AS b,
                                                            (SELECT * FROM transactions t2
                                                            WHERE t2.type = 'return') AS r
                                                        WHERE b.borrower_email = r.borrower_email
                                                        AND b.lender_email = r.lender_email
                                                        AND b.post_id = r.post_id
                                                        ) AS temp
                                                    ORDER BY (temp.end_date-temp.start_date) DESC
                                                    ) AS temp2,
                                                    book b2,
                                                    post p
                                                WHERE temp2.post_id = p.post_id
                                                AND p.isbn10 = b2.isbn10
                                                ORDER BY temp2.duration ASC;""")
        res_8 = db.execute(retrieval_command_8)
        db.commit()
        res_8 = res_8.fetchall()
        shortest = []
        for i in res_8:
            if (i[0] not in shortest) and (i[0] not in longest[0:5]):
                shortest.append(str(i[0]))
        stats['shortest'] = shortest[0:5]

        # For each genre in transactions, find the lender who lends most of it
        retrieval_command_8 = sqlalchemy.text(f"""SELECT B.genre, A.username, B.lender_email, B.count
                                                    FROM
                                                        users AS A,
                                                        (SELECT temp1.genre, temp2.lender_email, temp2.count
                                                        FROM 
                                                            (SELECT temp.genre, MAX(temp.count)
                                                            FROM 
                                                                (SELECT b.genre, t.lender_email, COUNT(t.transaction_id)
                                                                FROM transactions t, post p, book b
                                                                WHERE t.type='borrow'
                                                                AND t.post_id = p.post_id AND p.isbn10 = b.isbn10
                                                                GROUP BY t.lender_email, b.genre
                                                                ORDER BY COUNT(t.transaction_id) DESC, b.genre) AS temp
                                                        GROUP BY temp.genre) AS temp1,
                                                        (SELECT b.genre, t.lender_email, COUNT(t.transaction_id)
                                                        FROM transactions t, post p, book b
                                                        WHERE t.type='borrow'
                                                        AND t.post_id = p.post_id AND p.isbn10 = b.isbn10
                                                        GROUP BY t.lender_email, b.genre
                                                        ORDER BY COUNT(t.transaction_id) DESC, b.genre) AS temp2
                                                        WHERE temp1.genre = temp2.genre AND temp1.max = temp2.count) AS B
                                                    WHERE A.email = B.lender_email""")
        res_8 = db.execute(retrieval_command_8)
        db.commit()
        res_8 = res_8.fetchall()
        # lends_most  = {}
        # for i in res_8:
        #     lends_most[str(i[0])] = str(i[1])
        # stats['lends_most'] = lends_most
        dict = {}
        for i in res_8:
            genrelist = list(map(str, i[0].split('|')))
            for j in genrelist:
                if j not in dict:
                    dict[j] = []
                    dict[j].append( [ str(i[1]), int(i[3]) ] )
                else:
                    dict[j].append( [ str(i[1]), int(i[3]) ] )
        for k,v in dict.items():
            v.sort(key=lambda x:x[1], reverse=True)
            v = v[0]
        stats['lends_most'] = dict

    except Exception as e:
        db.rollback()

    return render_template('stats.html', title= 'What\'s Hot', stats=stats)



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




