# Code written in python3
# Title: Link state Router
# Author: Jagadish Raghavan
# zid: z5226835
# Date: 09/08/2019

import sys
import threading
from socket import * 
import time
import heapq
from copy import deepcopy
from collections import defaultdict

file_name = sys.argv[1]

weight = dict()
neighbour = dict()
graph = dict()

# Reading config file and creating neighbour dictionary
file = open(file_name, 'r') 
i = 0
for line in file: 
    content = line.split()
    if i == 0:
        starting_node = content[0]
        serverPort = content[1]
    if i > 1:
        neighbour[content[0]] = [content[1], content[2]]
    i = i + 1
        
broadcastMessage = str(starting_node)
temp_dict = dict()

# Formation of the broadcast message
for ne in neighbour:
    broadcastMessage = broadcastMessage + " " + ne + " " + neighbour[ne][0]
    temp_dict[ne] = float(neighbour[ne][0])
graph[starting_node] = temp_dict

serverName = "127.0.0.1"    

# Thread to send broadcastMessage to neighbours at intervals of 1 second 
def send_data():
    global broadcastMessage
    seq_id = 0
    while 1:
        seq_id += 1
        if seq_id > 10000:
            seq_id = 0
        broadcastMessage_seq = str(seq_id) + " " + broadcastMessage
        for ne in neighbour: 
            serverSocket.sendto(broadcastMessage_seq.encode(), (serverName, int(neighbour[ne][1]))) 
        broadcastMessage = str(starting_node)
        for ne in neighbour:
            broadcastMessage = broadcastMessage + " " + ne + " " + neighbour[ne][0]
        time.sleep(1)
    return broadcastMessage

# Thread for Dijkstra Algorithm to find the shortest paths. This algorithm runs every 30 seconds
def dij_alg():
    while True:
        time.sleep(30)
        new_stuff = [[0,starting_node]]
        for node in graph:
            if node != starting_node:
                new_stuff.append([1000000, node, starting_node])

        heapq.heapify(new_stuff)

        tracker = dict()

        while new_stuff:
            new_low = heapq.heappop(new_stuff)
            if new_low[1] != starting_node:
                tracker[new_low[1]] = [new_low[2], new_low[0]] 
            for val in graph[new_low[1]]:
                flag = 0
                for i in range(len(new_stuff)):
                    if val == new_stuff[i][1]:
                        flag = 1
                        break
                if flag == 0:
                    continue
                if not new_stuff:
                    break
                if (new_low[0] + graph[new_low[1]][val]) < new_stuff[i][0]:
                    new_stuff[i][0] = round((new_low[0] + graph[new_low[1]][val]), 2)
                    new_stuff[i][2] = new_low[1]
                    heapq.heapify(new_stuff)

        order_tracker = sorted(tracker)
		
        print('I am Router ' + str(starting_node))
        for node in order_tracker:
            n = node
            temp_arr = []
            while n != starting_node:
                temp_arr.append(n)
                n = tracker[n][0]

            temp_arr.append(starting_node)
            temp_arr.reverse()
            path = "".join(temp_arr)
            print('Least cost path to router '+str(node)+':'+ str(path)+' and the cost is '+ str(round(tracker[node][1], 2)))


hbMessage = str("hb ") + str(starting_node)

# Thread for sending a heartbeat message every 600 milliseconds
def heart_beat():
    while True:
        global hbMessage
        for ne in neighbour: 
            serverSocket.sendto(hbMessage.encode(), (serverName, int(neighbour[ne][1]))) 
        time.sleep(0.6)
    return hbMessage

hb_dict = defaultdict(int)
prev_val = defaultdict(lambda: -1)
del_dict = dict()

# Thread for checking if a node has failed. Runs every 4 seconds.
def heart_beat_check():
    global broadcastMessage
    while True:
        flag = 0
        missingMessage = 'Missing'
        time.sleep(4)
        temp = dict()
        del_group = []
        for ne in hb_dict:
            if (hb_dict[ne] == prev_val[ne]):
                temp = graph[starting_node]
                temp.pop(ne, None)
                graph[starting_node] = deepcopy(temp)
                del_group.append(ne)
                flag = 1
            prev_val[ne] = hb_dict[ne]
        del_set = set(del_group)
        if flag == 1:
            broadcastMessage = starting_node
            for ne in del_set:
                del_dict[ne] = neighbour[ne]
                neighbour.pop(ne, None)
                graph.pop(ne, None)
                hb_dict.pop(ne, None)
                prev_val.pop(ne, None)
                missingMessage = missingMessage + " " + ne
            for ne in neighbour:
                broadcastMessage = broadcastMessage + " " + ne + " " + neighbour[ne][0]
            broadcastMessage = broadcastMessage + " " + missingMessage
            del_set.clear()
    return broadcastMessage

serverSocket = socket(AF_INET, SOCK_DGRAM) 
serverSocket.bind(("127.0.0.1", int(serverPort))) 
bcast = threading.Thread(target=send_data)
bcast.start()
dijkstra = threading.Thread(target=dij_alg)
dijkstra.start()
hb = threading.Thread(target=heart_beat)
hb.start()
hbc = threading.Thread(target=heart_beat_check)
hbc.start()
check_list = defaultdict(list)

# Server always active and transmits the recieved broadcast messages to it's neighbours. 
# Also takes care of the heart beat signals.
while True:    
    k = -1
    message, clientAddress = serverSocket.recvfrom(2048)  
    modifiedMessage = message.decode() 
    w_and_nodes = []
    w_and_nodes_seq = []
    w_and_nodes_seq = modifiedMessage.split()
    w_and_nodes = w_and_nodes_seq[1:]
    source_point = w_and_nodes[0]
    if str(source_point) in del_dict:
        temp_dict.clear()
        neighbour[str(source_point)] = del_dict[str(source_point)]
        del_dict.pop(str(source_point), None)
        for ne in neighbour:
            temp_dict[ne] = float(neighbour[ne][0])
        graph[starting_node] = deepcopy(temp_dict)

    if str(w_and_nodes_seq[0]) == 'hb':
        if hb_dict[str(w_and_nodes_seq[1])] > 10000:
            hb_dict[str(w_and_nodes_seq[1])] = 0
            prev_val[str(w_and_nodes_seq[1])] = -1
        hb_dict[str(w_and_nodes_seq[1])] += 1   
        continue
    if int(w_and_nodes_seq[0]) >= 10000:
        check_list[str(w_and_nodes_seq[1])] = []
    if int(w_and_nodes_seq[0]) in check_list[str(w_and_nodes_seq[1])]:
        continue
    else:
        check_list[str(w_and_nodes_seq[1])].append(int(w_and_nodes_seq[0]))
    mes_len = int(len(w_and_nodes)/2)
    for i in range(mes_len):
        if(str(w_and_nodes[(2*i) + 1]) == 'Missing'):
            k = ((2*i) + 1)
            break
        weight[str(w_and_nodes[(2*i) + 1])] = float(w_and_nodes[(2*i) + 2])
    graph[str(w_and_nodes[0])] = deepcopy(weight)
    weight.clear()
    if k != -1:
        for i in w_and_nodes[(k + 1):]:
            graph.pop(i, None)
    for ne in neighbour: 
        if ne == str(source_point):
            continue
        serverSocket.sendto(modifiedMessage.encode(), (serverName, int(neighbour[ne][1])))