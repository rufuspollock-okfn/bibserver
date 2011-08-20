import os
from flask import Flask, jsonify, json, request, redirect, abort
from flaskext.mako import init_mako, render_template


app = Flask(__name__)
app.config['MAKO_DIR'] = 'templates'
init_mako(app)


@app.route("/")
def home():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

