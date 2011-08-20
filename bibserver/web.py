import os
from flask import Flask, jsonify, render_template, json, request, redirect, abort

app = Flask(__name__)

@app.route("/")
def home():
    return 'Home page'

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

