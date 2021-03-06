# cs.py
# author: Guillaume de Moffarts, Christophe Simon
# version: March 31, 2017
# inspierd by: https://github.com/ECAM-Brussels/PythonAdvanced2BA/tree/master/CodeExamples/network

import socket 
import sys
import time
import json
import threading

SERVERADDRESS = (socket.gethostname(),6005)
address = None

class ChatServer:
        def __init__(self):
                 self.__s = socket.socket()
                 self.__s.bind(SERVERADDRESS)
                 self.__curClient = ()
                 self._connected = {}

        def run(self):
                self.__s.listen()
                while True:
                        self.__curClient = self.__s.accept()
                        try:
                                data = self.__curClient[0].recv(1024).decode()
                                data = data.split(',')
                                try:
                                        #run method in data[0] as a sting with data[1:] in parameter 
                                        getattr(self,data[0])(data[1:])
                                except Exception as e:
                                        print(e)
                                        print ("commande non valide")
                                        
                        except OSError:
                                print("erreur lors de la requète")

                        finally:
                                self.__curClient[0].close()
                                

        def connect(self, cmd):
                stat = cmd[0] == 'True'
                if stat:
                        self._connected[self.__curClient[1][0]] = {'port' : cmd[1],'pseudo' : 'Jhon Doe'}
                elif not stat:
                        try:
                                del self._connected[self.__curClient[1][0]]
                        except:
                                pass

        def connected(self,*args):
                self.send(json.dumps(self._connected))

        def editPseudo(self,pseudo):
                # the argument is a list of one elemet due to the way the metods are called 
                pseudo = pseudo[0]
                self._connected[self.__curClient[1][0]]["pseudo"] = pseudo

        def send(self, message):
                msg = message.encode()
                totalsent = 0
                while totalsent < len(msg):
                        sent = self.__curClient[0].send(msg[totalsent:])
                        totalsent += sent       

class ChatClient:
        def __init__(self,command):
                self.__s = socket.socket()
                self.command = command
                self.__s.settimeout(0.5)

        def run(self):
                try:
                        self.__s.connect(SERVERADDRESS)
                        try:
                                self.send(",".join(self.command))
                        except Exception as e:
                                
                                print ("commande non valide: ",e)

                        data = json.loads(self.__s.recv(1024).decode())
                        self.connectedRecv(data)
                        
                except socket.timeout:
                        pass
                except OSError as e:
                        print("Problème lors de la connection au server",e)
                except json.decoder.JSONDecodeError:
                        pass
                finally:
                        self.__s.close()
                        
        def connectedRecv(self, data):
                i = 1
                connected = []
                for ip in data:
                        connected.append({"ip":ip,"pseudo":data[ip]["pseudo"],"port": int(data[ip]["port"])})
                        print("Avec qui voulez vous parler?")
                        print("\n{}. [{}]    {}".format(i,data[ip]["pseudo"],ip))
                        i+=1
                        print("{}. personne".format(i))
                if i >> 1:
                        line = sys.stdin.readline().rstrip() + ' '
                        try:
                                if int(line) == 2:
                                        return  
                                else:
                                        self.join(connected[(int(line) - 1)])
                        except:
                                print("choix non valide ")
                else:
                        print("personne n'est connecter")
                                
        def send(self, message):
                msg = message.encode()
                totalsent = 0
                while totalsent  < len(msg):
                        sent = self.__s.send(msg[totalsent:])
                        totalsent += sent

        def join(self, param):
                try:
                        Chat.pseudo = param['pseudo']
                        Chat.addr = (socket.gethostbyaddr(param['ip'])[0], param['port'])
                        print('Connecté à {}'.format(param['pseudo']))

                except OSError:
                        print("Erreur lors de l'envoi du message.")

class Chat:
        addr = None
        pseudo = ''
        def __init__(self, host=socket.gethostname(), port=5001):
                s = socket.socket(type=socket.SOCK_DGRAM)
                s.settimeout(0.5)
                s.bind(("0.0.0.0", port))
                self.__s = s
                print('Écoute sur {}:{}'.format(host, port))
                self.__port = port
                self.__running = True
                

        def run(self):
                param = []
                handlers = {
                '/exit': self._exit,
                '/quit': self._quit,
                '/connect': ChatClient(['connect','True', str(self.__port)]).run,
                '/disconnect': ChatClient(['connect','False']).run,
                '/connected': ChatClient(['connected']).run,
                '/editPseudo': ChatClient(['editPseudo',param]).run
            }
                
                threading.Thread(target=self._receive).start()
                while self.__running:
                        line = sys.stdin.readline().rstrip() + ' '
                        if line[0] != '/' and self.addr is not None:      
                                self._send(line)
                        else:
                                # Extract the command and the param
                                command = line[:line.index(' ')]
                                param = line[line.index(' ')+1:].rstrip()
                                # Call the command handler
                                if command in handlers:
                                        try:
                                                # /!\ code bourriner. A réparer 
                                                if command == '/connected': ChatClient(['connected']).run()
                                                elif command == '/connect': ChatClient(['connect','True', str(self.__port)]).run()
                                                elif command == '/disconnect':  ChatClient(['connect','False']).run()
                                                elif command == '/editPseudo': ChatClient(['editPseudo',param]).run()
                                                else: handlers[command]() if param == '' else handlers[command](param)
                                                #handlers[command]() if param == '' else handlers[command](param)
                                        
                                        except Exception as e:
                                                print (e)
                                                print("Erreur lors de l'exécution de la commande.")
                                else:
                                        print('Command inconnue:', command)
        def _receive(self):
                while self.__running:
                        try:
                                data, address = self.__s.recvfrom(1024)
                                print('['+ self.pseudo + ']    ' + data.decode())
                                sys.stdout.flush()
                
                        except socket.timeout:
                                pass
                        except OSError:
                                return

        def _exit(self):
                self.__running = False
                self.addr = None
                ChatClient(['connect','False']).run()
                self.__s.close()
    
        def _quit(self):
                self.addr = None

        def _send(self, param):
                if self.addr is not None:
                        try:
                                message = param.encode()
                                totalsent = 0
                                while totalsent < len(message):
                                        sent = self.__s.sendto(message[totalsent:], self.addr)
                                        totalsent += sent
                        except OSError:
                                print('Erreur lors de la réception du message.')

if __name__ == '__main__':
        if len(sys.argv) == 2 and sys.argv[1] == 'server':
                ChatServer().run()
        elif len(sys.argv) >= 3 and sys.argv[1] == 'client':
                ChatClient(sys.argv[2:]).run()
        elif len(sys.argv) == 3:
                Chat(sys.argv[1], int(sys.argv[2])).run()
        else:
                Chat().run()

