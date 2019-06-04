# Spartan Messenger
Terminal/console based messenger for users to securely communicate in a group setting with message saving through sessions.

* Uses end to end message encryption using AES encryption from pycrypto library.
* Has implemented LRU Cache for saving recent messages from users(last 10) across user sessions.
* Has login through terminal allowing only users/names on config.yaml to be allowed in.
* Limits messaging rate to protect server.
* Supports group chat. 

Supports group chat with the users of the following lists

* Group 1: [alice,bob,charlie,eve]
* Group 2: [foo,bar,baz,qux]

Run server first in a seperate terminal using: python server.py

then run each additional client/user in terminals using: python client.py *username*
