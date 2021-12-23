import sqlite3
from sqlite3.dbapi2 import connect

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

import logging

# Function to get a database connection.
# This function connects to database with the name `database.db`

connection_count = 0


def get_db_connection():
    global connection_count

    connection_count += 1
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID


def close_connection(connection):
    global connection_count

    connection.close()
    connection_count -= 1


def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    close_connection(connection)
    return post


def get_post_count():
    connection = get_db_connection()
    post_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    close_connection(connection)
    return post_count


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application


@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown


@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.warning("Unable to find post id: " + str(post_id))
        return render_template('404.html'), 404
    else:
        app.logger.info("Article \"" + post["title"] + "\" retrieved!")
        return render_template('post.html', post=post)

# Define the About Us page


@app.route('/about')
def about():
    app.logger.info("The About US page is retrieved")
    return render_template('about.html')

# Define the post creation functionality


@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()
            app.logger.info("A new article is created. Title:" + title)

            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz')
def healthz():
    data = {
        "result": "OK - healthy"
    }

    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )

    return response


@app.route("/metrics")
def metrics():
    data = {
        "db_connection_count": connection_count,
        "post_count": get_post_count()
    }

    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype="application/json"
    )

    return response


# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%d/%m/%Y %H:%M:%S'
        )
    app.debug = True
    app.run(host='0.0.0.0', port='3111')
