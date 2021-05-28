import paramiko

from fixtures import *

def test_ssh_correct_login(clean_redis, create_user_set_image):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("containerssh", port=2222, username="testing", password="qwerty")

def test_ssh_wrong_login(clean_redis):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect("containerssh", port=2222, username="wrong", password="hello")
    except paramiko.AuthenticationException:
        return

    raise Exception("Paramiko successfully logged in with wrong creds")
