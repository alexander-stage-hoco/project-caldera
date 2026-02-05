"""Test file for command injection vulnerability detection.

Contains patterns detected by p/python ruleset.
"""

import os
import subprocess

# COMMAND_INJECTION: os.system with user input
def unsafe_os_system(user_command):
    os.system(user_command)


# COMMAND_INJECTION: os.popen with user input
def unsafe_os_popen(user_command):
    return os.popen(user_command).read()


# COMMAND_INJECTION: subprocess shell=True
def unsafe_subprocess_shell(user_command):
    subprocess.run(user_command, shell=True)


# COMMAND_INJECTION: subprocess.Popen shell=True
def unsafe_popen_shell(user_command):
    proc = subprocess.Popen(user_command, shell=True, stdout=subprocess.PIPE)
    return proc.communicate()[0]


# COMMAND_INJECTION: subprocess.call shell=True
def unsafe_call_shell(user_command):
    subprocess.call(user_command, shell=True)


# UNSAFE_DESERIALIZATION: yaml.load without Loader
import yaml

def unsafe_yaml_load(yaml_content):
    return yaml.load(yaml_content)


# UNSAFE_DESERIALIZATION: pickle.loads
import pickle

def unsafe_pickle_load(pickled_data):
    return pickle.loads(pickled_data)


# INSECURE_CRYPTO: MD5 hashing
import hashlib

def unsafe_md5_hash(data):
    return hashlib.md5(data.encode()).hexdigest()


# INSECURE_CRYPTO: SHA1 hashing
def unsafe_sha1_hash(data):
    return hashlib.sha1(data.encode()).hexdigest()


# INSECURE_CRYPTO: requests verify=False
import requests

def unsafe_no_verify(url):
    return requests.get(url, verify=False)


# SECURITY_MISCONFIGURATION: Flask debug mode
from flask import Flask

app = Flask(__name__)
app.debug = True  # SECURITY_MISCONFIGURATION


# PATH_TRAVERSAL: flask send_file with user input
from flask import send_file, request

@app.route('/download')
def unsafe_send_file():
    filename = request.args.get('file')
    return send_file(filename)


# SAFE: subprocess with list arguments
def safe_subprocess(args):
    subprocess.run(args, shell=False)


# SAFE: yaml.safe_load
def safe_yaml_load(yaml_content):
    return yaml.safe_load(yaml_content)


# SAFE: SHA256 hashing
def safe_sha256_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()


# SAFE: requests with verification
def safe_https_request(url):
    return requests.get(url, verify=True)
