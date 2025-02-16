import math
import sys
import socket
import pickle
import numpy
import threading
import random
import time

f = open("FLdata/global_loss.txt", "w")
f.write("")
f.close()

f = open("FLdata/global_loss.txt", "w+")

fa = open("FLdata/global_accuracy.txt", "w")
fa.write("")
fa.close()

fa = open("FLdata/global_accuracy.txt", "w+")

port = int(sys.argv[1])
n_sub_client = int(sys.argv[2])
n_features = 0
total_sample_size = 0

address = ("10.16.70.137", port)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(address)

num_user = 1
users = {}
userModels = {}

s.listen(5)

client_sockets = []


class WaiteClients(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        global s
        global users
        global n_features
        global total_sample_size
        global num_user
        global client_sockets
        i = 0

        while True:
            client, addr = s.accept()
            register = client.recv(2048)
            # client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 62980)
            register = pickle.loads(register)
            client_id = register[0]
            sample_size = int(register[1])
            total_sample_size += sample_size
            n_feature = int(register[2])
            n_features = n_feature
            client_port = 6000 + int(register[0][6])
            users[client_id] = [sample_size, n_feature, client_port]
            print(addr)
            client_sockets.append(client)
            print("connected with " + client_id + ", " + "sample size is " + str(
                sample_size) + ", feature size is " + str(n_feature))


n_features = 785
waiteClients = WaiteClients()
waiteClients.start()

numpy.random.seed(123)
W_init = numpy.random.randn(n_features, 10)
W_0 = numpy.zeros((n_features, 10))
if_send = True
total_epochs = 100
test = pickle.dumps(W_init)
average_accuracy_recorder = []


def evaluate(cur_round):
    global users
    global f
    global fa
    total_accuracy = 0
    total_loss = 0

    print()
    for user_id in users.keys():
        file = open(user_id + '_log.txt')
        loss = float(file.readline())
        accuracy = float(file.readline())
        # total_accuracy += accuracy

        total_accuracy += accuracy * (users[user_id][0] / total_sample_size)

        total_loss += loss * (users[user_id][0] / total_sample_size)
        print('Accuracy of ' + user_id + ' is: {:.2f}%'.format(accuracy))

    print('Global Round : ' + str(cur_round) + ', Average accuracy across all clients : {:.2f}%'.format(total_accuracy))

    f.write(str(total_loss) + " ")
    fa.write(str(total_accuracy) + " ")
    print()
    return total_accuracy / len(users)


def aggregate_parameters():
    global W_init
    if n_sub_client == 0:
        W_init = numpy.zeros((n_features, 10))
        agg_sample_size = total_sample_size
        for user_id in userModels.keys():
            if not math.isnan((userModels[user_id][0][0])):
                print("no nan")

            for i in range(len(W_init)):
                for j in range(len(W_init[i])):
                    W_init[i][j] += (users[user_id][0] / agg_sample_size) * userModels[user_id][i][j]

    else:
        entry_list = list(userModels.items())
        client_1_entry = random.choice(entry_list)
        client_1 = client_1_entry[0]

        client_2_entry = random.choice(entry_list)
        while client_2_entry == client_1_entry:
            client_2_entry = random.choice(entry_list)
        client_2 = client_2_entry[0]

        if not math.isnan((userModels[client_1][0][0])) and not math.isnan((userModels[client_2][0][0])):
            W_init = numpy.zeros((n_features, 10))
            print("no nan")
            cur_total_sample_size = users[client_1][1] + users[client_1][2]
            for i in range(len(W_init)):
                for j in range(len(W_init[i])):
                    W_init[i][j] += (users[client_1][1] / cur_total_sample_size) * userModels[client_1][i][j]
                    W_init[i][j] += (users[client_2][1] / cur_total_sample_size) * userModels[client_2][i][j]

        # if math.isnan((userModels[client_1][0][0])) and math.isnan((userModels[client_2][0][0])):
        #     print("both nan")

    return W_init


cur_epoch = 0
start_time = time.time()

flag = 0
while flag != '1':
    flag = input('输入1开始训练')

while cur_epoch < total_epochs:
    if if_send:
        t = 0
        for user_id in userModels.keys():
            t += users[user_id][0]
        print('Boardcasting new global model')
        # buffer = pickle.dumps(W_init)
        buffer = pickle.dumps(W_init)
        i = 0
        for user in users.keys():
            client_sockets[i].send(buffer)
            i += 1
        if_send = False
    else:
        cur_epoch += 1
        print("")
        print("_____________________________________")
        print("")
        print('Global Iteration ' + str(cur_epoch) + ':')
        print('Total Number of clients: ' + str(len(users)))
        client_received = 0
        while client_received < len(users):
            client_received += 1

            # buffer_receive = client_sockets[client_received - 1].recv(1024)
            # client_sockets[client_received - 1].setblocking(0)
            # while True:  # 循环接收
            #     try:
            #         time.sleep(0.001)
            #         data = client_sockets[client_received - 1].recv(4096)  # 接收1024字节
            #         buffer_receive += data  # 拼接到结果中
            #         print('data', len(data))
            #         print('buffer', len(buffer_receive))
            #     except BlockingIOError as e:  # 如果没有数据了
            #         break  # 退出循环

            # client_sockets[client_received - 1].setblocking(1)

            buffer_receive = b""
            while True:
                time.sleep(0.5)
                data = client_sockets[client_received - 1].recv(65536)
                if data is not None:
                    buffer_receive += data
                # if data is None or len(data) < 1024:
                print(len(buffer_receive))
                print("data", len(data))
                break
                # if len(buffer_receive) == 62980:
                #     break
                # else if

            print(len(buffer_receive))
            buffer_receive = pickle.loads(buffer_receive)

            client_id = buffer_receive[0]
            if isinstance(buffer_receive[1], int):
                # late connection
                bufferReceiver = buffer_receive
                client_idReceiver = bufferReceiver[0]
                sample_sizeReceiver = int(bufferReceiver[1])
                total_sample_size += sample_sizeReceiver
                n_featureReceiver = int(bufferReceiver[2])
                n_features = n_featureReceiver
                client_portReceiver = 6000 + int(bufferReceiver[0][6])
                users[client_idReceiver] = [sample_sizeReceiver, n_featureReceiver, client_portReceiver]
                print("connected to " + client_idReceiver + ", " + "sample size is " + str(
                    sample_sizeReceiver) + ", feature size is " + str(n_featureReceiver))
            else:
                userModels[client_id] = buffer_receive[1]
                print('Getting local model from ' + client_id)

            # print("cur_epoch:" + cur_epoch)
            if cur_epoch == total_epochs:
                client_sockets[client_received - 1].send(pickle.dumps('finish'))

        average_accuracy = evaluate(cur_epoch)
        average_accuracy_recorder.append(average_accuracy)

        print('Aggregating new global model')
        aggregate_parameters()

        if_send = True

print("\n--- The total running time is %s seconds ---" % (time.time() - start_time))
