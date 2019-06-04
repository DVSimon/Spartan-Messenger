from concurrent import futures
import time
import os
import grpc
import yaml
import copy
import SpartanMessenger_pb2
import SpartanMessenger_pb2_grpc
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

LRU_cache = {}

class Messenger(SpartanMessenger_pb2_grpc.MessengerServicer):
    def group(self, request, context):
        with open("config.yaml", 'r') as f:
            try:
                yamlconfig = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)
        for group in yamlconfig['groups']:
            if request.userName in yamlconfig['groups'][group]:
                userList = []
                for user in yamlconfig['groups'][group]:
                    userList.append(user)
                users = str(userList)
                return SpartanMessenger_pb2.GroupResponse(group=group, users=users)
        return SpartanMessenger_pb2.GroupResponse(group='none', users='')

    def login(self, request, context):
        with open("config.yaml", 'r') as f:
            try:
                yamlconfig = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)
        if request.user in yamlconfig['users']:
            return SpartanMessenger_pb2.Response(messages='verified')
        else:
            return SpartanMessenger_pb2.Response(messages='unverified')


    def message(self, request, context):
        global LRU_cache
        #import config for LRU #
        with open("config.yaml", 'r') as f:
            try:
                yamlconfig = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)
        #timestamps
        request.timestamp.GetCurrentTime()
        sTime = request.timestamp.ToSeconds()

        #one to one
        # if str(request.sender) > str(request.receiver):
        #     group = request.sender + request.receiver
        # else:
        #     group = request.receiver + request.sender

        group = request.receiver
        #create new message for cache
        new_Message = create_message(request.sender, request.receiver, request.message, sTime)

        #check to see if time btwn msgs is too fast...
        if group in LRU_cache:
            if withinRateLimit(LRU_cache[group], new_Message):
                if LRU_cache_check(LRU_cache[group]):
                    LRU_cache[group].pop(0)
                    LRU_cache[group].append(new_Message)
                    return SpartanMessenger_pb2.Response(messages='Sent')
                else:
                    LRU_cache[group].append(new_Message)
                    return SpartanMessenger_pb2.Response(messages='Sent')
            else:
                return SpartanMessenger_pb2.Response(messages='Exceeded')
        else:
            temp_list = []
            temp_list.append(new_Message)
            LRU_cache[group] = temp_list
            return SpartanMessenger_pb2.Response(messages='Sent')


    def receive(self, request, context):
        yield SpartanMessenger_pb2.ChatResponse(messages=b'accepted', sender = '')
        global LRU_cache

        with open("config.yaml", 'r') as f:
            try:
                yamlconfig = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)

        # if str(request.sender) > str(request.receiver):
        #     group = request.sender + request.receiver
        # else:
        #     group = request.receiver + request.sender
        group = request.receiver


        # if group doesnt exist create empty one
        if group not in LRU_cache:
            temp_list = []
            LRU_cache[group] = temp_list
        indexer = 0
        # retrieve old messages first by self as well
        while len(LRU_cache[group]) > indexer:
            unread_sender = LRU_cache[group][indexer]['sender']
            unread = LRU_cache[group][indexer]['message']
            old_msg = copy.deepcopy(LRU_cache[group])
            indexer += 1
            yield SpartanMessenger_pb2.ChatResponse(messages=unread, sender=unread_sender)
        #continously retrieve new messages only by other chatter
        max_cache = yamlconfig['max_num_messages_per_user']
        while True:
            while len(LRU_cache[group]) > indexer:
                unread_sender = LRU_cache[group][indexer]['sender']
                unread = LRU_cache[group][indexer]['message']
                old_msg = copy.deepcopy(LRU_cache[group])
                indexer += 1
                #prof said always yield own msgs...
                # if unread_sender != request.sender:
                yield SpartanMessenger_pb2.ChatResponse(messages=unread, sender=unread_sender)
            if (len(LRU_cache[group]) == max_cache) and (old_msg != LRU_cache[group]):
                indexer = indexer -1
                unread_sender = LRU_cache[group][indexer]['sender']
                unread = LRU_cache[group][indexer]['message']
                old_msg = copy.deepcopy(LRU_cache[group])
                indexer += 1
                # prof said always yield own msgs...
                # if unread_sender != request.sender:
                yield SpartanMessenger_pb2.ChatResponse(messages=unread, sender=unread_sender)


def create_message(sender, receiver, message, time):
    new_msg = {'sender': sender, 'receiver': receiver, 'message': message, 'time': time}
    return new_msg


def lru_cache(func):
    def wrapper_lru(*args, **kwargs):
        with open("config.yaml", 'r') as f:
            try:
                yamlconfig = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)
        kwargs['max_msg'] = yamlconfig['max_num_messages_per_user']
        return func(*args, **kwargs)
    return wrapper_lru


@lru_cache
def LRU_cache_check(LRU_cache_group, *args, **kwargs):
    with open("config.yaml", 'r') as f:
        try:
            yamlconfig = yaml.load(f)
        except yaml.YAMLError as exc:
            print(exc)
    if len(LRU_cache_group) >= kwargs['max_msg']:
        return True
    else:
        return False


def rate(func):
    def wrapper_rate(*args, **kwargs):
        with open("config.yaml", 'r') as f:
            try:
                yamlconfig = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)
        kwargs['max_call'] = yamlconfig['max_call_per_30_seconds_per_user']
        return func(*args, **kwargs)
    return wrapper_rate


@rate
def withinRateLimit(convolist, messagecheck, *args, **kwargs):
    count_Time = 0
    for message in convolist:
        if message['sender'] == messagecheck['sender']:
            duration = messagecheck['time'] - message['time']
            if duration <= 30:
                count_Time += 1
    if count_Time < kwargs['max_call']:
        return True
    else:
        return False


def serve():
    with open("config.yaml", 'r') as f:
        try:
            yamlconfig = yaml.load(f)
        except yaml.YAMLError as exc:
            print(exc)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    SpartanMessenger_pb2_grpc.add_MessengerServicer_to_server(Messenger(), server)
    print('port: ' + str(yamlconfig['port']))
    server.add_insecure_port('[::]:' + str(yamlconfig['port']))
    # server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        print('Closing')
        server.stop(0)


if __name__ == '__main__':
    serve()

