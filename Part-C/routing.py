import sys
import os
import time
import socket
import threading
import json
class BellmanFord():
    def __init__(self, host, IP, neighbors, outfile):
        self.routing_table = self.getDistances(host)
        self.host = host
        self.IP = IP
        self.neighbors = neighbors
        self.lock = threading.Lock()
        self.terminate = False
        self.t1 = time.time()
        self.outfile = outfile
    def getDistances(self, host):
        routing_table = {}  
        for h in ['H1', 'H2', 'R1', 'R2', 'R3', 'R4']: 	
            routing_table[h] = [float("inf"), h]
        routing_table[host][0] = 0        return routing_table
    def printRoutingTables(self):         file = open(self.outfile, 'a+')
        out = '\nRouting Table of Node %s\n' % self.host
        out += 'Dest.\tCost\tNext\n'
        out += '+++++++++++++++++++++++\n'
        for k, v in self.routing_table.items():
            if v[0] != float("inf"):
                c = str(v[0])
            else:
                c = 'inf'            
            out += '%s\t%s\t%s\n' % (k, c, v[1])
        out += '+++++++++++++++++++++++\n'
        file.write(out)
        file.close               
    def updateRoutingTables(self, modData, node):
        self.lock.acquire()
        modified = False              
        for k, v in modData.items():
            dist = self.routing_table[node][0] + v[0]
            if dist < self.routing_table[k][0]:
                modified = True
                self.routing_table[k] = [dist, node]
        for k, v in modData.items():
            dist = self.routing_table[node][0] + v[0]
            if dist < self.routing_table[k][0]:
                self.terminate = True
                self.lock.release()
                return False
        if modified:
            self.printRoutingTables()        
            self.broadcastToNeighbors()
        self.lock.release()
        return True
    def broadcastToNeighbors(self):
        modData = json.dumps((self.routing_table, self.host))
        s = None
        try:
            for key, val in self.neighbors.items():        
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((val, 8001))
                s.sendall(modData.encode('utf8'))
                s.close
        except Exception as e:
            print e
            if s:
                s.close
    def checkDistance(self):
        modTime = None
        while True:             
            if self.terminate:
                break
            time.sleep(1)
            fileMod = os.stat('vectors.txt').st_mtime	    
            if not modTime or modTime < fileMod:
                modData = {}
                self.routing_table = self.getDistances(self.host)
                with open('vectors.txt') as file:          
                    for line in file:
                        line = line.strip()
                        d = line.split(',')
                        if d[1] == self.host:
                            modData[d[0]] = int(d[2])
                        elif d[0] == self.host:
                            modData[d[1]] = int(d[2])
                self.lock.acquire()
                modified = False
                dkeys = modData.keys()
                for key, val in self.routing_table.items():
                    if val[1] in dkeys:
                        self.routing_table[key][0] = modData[val[1]]
                        modified = True		
                if modified:
                    self.broadcastToNeighbors()
                self.lock.release()
                modTime = fileMod              
    def communicator(self):	
        try:		 
            nodeSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            nodeSocket.bind((self.IP, 8001))            nodeSocket.listen(5)
        except Exception as e:
            print e   
        while True:
            try:                               
                c, addr = nodeSocket.accept()
                data, node = json.loads(c.recv(4096).decode('utf8'))
                ret = self.updateRoutingTables(data, node)
                if not ret:
                    raise Exception("Negative-weight cycle found")
                c.close()
            except Exception as e:
                print e
                self.terminate = True
                nodeSocket.close()
                break
def getIP(node):
    if node == "H1":
        return "162.0.0.1"
    if node == "R1":
        return "162.0.0.2"
    if node == "R2":
        return "163.0.0.1"
    if node == "R3":
        return "164.0.0.1"
    if node == "R4":
        return "167.0.0.2"
    if node == "H2":
        return "167.0.0.1"
def getNeighbors(host):
    if host == "H1":
        return {"R1" : getIP("R1")}
    if host == "H2": 
        return {"R4" : getIP("R4")}
    if host == "R1": 
        return {"H1" : getIP("H1"), "R2" : getIP("R2"), "R3" : getIP("R3")}
    if host == "R2": 
        return {"R1" : getIP("R1"), "R4" : getIP("R4")}
    if host == "R3": 
        return {"R1" : getIP("R1"), "R4" : getIP("R4")}
    if host == "R4": 
        return {"H2" : getIP("H2"), "R2" : getIP("R2"), "R3" : getIP("R3")}
def main():	        	
    host = sys.argv[1]
    outfile = sys.argv[1]
    IP = getIP(host)
    neighbors = getNeighbors(host)    
    node = BellmanFord(host, IP, neighbors, outfile)
         
    mainThread = threading.Thread(target=node.checkDistance, args=())
    mainThread.start()    
    node.communicator()
    mainThread.join()
if __name__ == "__main__":    	    
    main()