from __future__ import print_function
import threading
import grpc
import yaml
import sys
import SpartanMessenger_pb2
import SpartanMessenger_pb2_grpc
import os
from Crypto.Cipher import AES


def get_messages(stub, sender_name, receiver_name, key, iv):
    try:
        responses = stub.receive(SpartanMessenger_pb2.Receive(sender=sender_name, receiver=receiver_name))
        while (next(responses)):
            for request in responses:
                # Decryption
                decryption_suite = AES.new(key, AES.MODE_CFB, iv)
                plain_text_b = decryption_suite.decrypt(request.messages)
                plain_text = plain_text_b.decode('utf-8')
                # print('test')
                print('[' + request.sender + '] ' + plain_text)
        # print(responses)
    except Exception as error:
        print(str(error))
        os._exit(1)


def run():
    with open("config.yaml", 'r') as f:
        try:
            yamlconfig = yaml.load(f)
        except yaml.YAMLError as exc:
            print(exc)
    sender_name = sys.argv[1]
    # login(sender_name)

    with grpc.insecure_channel('localhost:' + str(yamlconfig['port'])) as channel:
        stub = SpartanMessenger_pb2_grpc.MessengerStub(channel)
        loginAttempt = stub.login(SpartanMessenger_pb2.LoginRequest(user=sender_name))
        if loginAttempt.messages == 'unverified':
            print('[Spartan] User not found in config. Try rerunning.')
            sys.exit()
        elif loginAttempt.messages == 'verified':
            print('[Spartan] Connected to Spartan Server at port ' + str(yamlconfig['port']) + '.')

        # # requesting who to chat with One to one
        # receiver_name = chat(sender_name)
        # if str(sender_name) > str(receiver_name):
        #     group = sender_name + receiver_name
        # else:
        #     group = receiver_name + sender_name

        #finding group group chat
        groupresponse = stub.group(SpartanMessenger_pb2.GroupRequest(userName=sender_name))
        if groupresponse.group == 'none':
            print('[Spartan] group not found...')
            sys.exit()
        else:
            group = groupresponse.group
            userList = groupresponse.users
            print('[Spartan] Connected to ' + group + ' with users: ' + userList)

        #security AES
        key = getGroupKey(group)
        iv = getGroupIV(group)

        threading.Thread(target=get_messages, args=(stub, sender_name, group, key, iv)).start()
        while True:
            # messaging loop
            input_message = input()

            # Encryption
            encryption_suite = AES.new(key, AES.MODE_CFB, iv)
            cipher_text = encryption_suite.encrypt(input_message)

            response = stub.message(SpartanMessenger_pb2.SendMessage(message=cipher_text, sender=sender_name, receiver=group))
            if response.messages == 'Exceeded':
                print('Exceeded 3 message limit within 30s. Message not sent.')



# def chat(username):
#     with open("config.yaml", 'r') as f:
#         try:
#             userList = yaml.load(f)
#         except yaml.YAMLError as exc:
#             print(exc)
#
#     users = str(userList['users']).strip('[]')
#     users = users.replace("'", "")
#     users = users.replace(" ", "")
#     print('[Spartan] User List: ' + users)
#
#     while True:
#         #need to change here to it removes whitespace, etc around input?
#         chatName = input('[Spartan] Enter User to chat with: ')
#         if chatName == username:
#             print('[Spartan] Cant talk to yourself!')
#             continue
#         elif chatName not in userList['users']:
#             print('[Spartan] User does not exist, please use a valid User')
#             continue
#         elif chatName in userList['users']:
#             print('[Spartan] You are now ready to chat with ' + chatName + '.')
#             return chatName

def getGroupKey(group):
    for x in range(32):
        group += '#'
    return group[:32]

def getGroupIV(group):
    for x in range(16):
        group += '!'
    return group[:16]


if __name__ == '__main__':
    run()