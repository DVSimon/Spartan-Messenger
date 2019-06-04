# Spartan Messenger
Terminal/console based messenger for users to securely communicate in a group setting with message saving through sessions.

Supports group chat with the users of the following lists
![group](https://i.gyazo.com/fdb55a0d42818e44cecf613d103f8da1.png "Group List")

* Uses end to end message encryption using AES encryption from pycrypto library.
* Has implemented LRU Cache for saving recent messages from users(last 10) across user sessions.
* Has login through terminal allowing only users/names on config.yaml to be allowed in.
* Limits messaging rate to protect server.
* Supports group chat. 
