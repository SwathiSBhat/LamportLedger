import socket
import threading
import heapq
import traceback

from os import _exit
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from sys import stdout
from sys import argv
from time import sleep
from utils import Blockchain

# Keeps map of client id to socket connection
pidToSock = {}

# global variables to store useful objects
local_lamport_time = 0
process_id = int(argv[1])
queue = []
reply_count = {} # Number of replies received for a request
release_count = {} # Number of releases received for a request
server_response_count = {}
# Initialize balance table with $10 for each client
balance_table = {1: 10, 2: 10, 3: 10}
update_count = {} # Number of clients that have updated their balance table
blockchain = Blockchain()

def execute_transaction():
	# Check if operation is valid and if yes, execute the transaction
	top_lamport_time, top_pid, user_input = queue[0]
    # user_input if of the form 'transfer 1 2 100'
	words = user_input.split()
	src = int(words[1])
	dest = int(words[2])
	amount = float(words[3])
	
	global pid
	global update_count
    
    # reset reply count to ensure another thread doesn't execute the same transaction
	reply_count[(top_lamport_time, top_pid)] = 0
    
	# abort transaction if the balance is insufficient
	if balance_table.get(src, 0) < amount:
		print(f"FAILURE: Insufficient balance in account of client {src} to transfer {amount}")
		# Send release message to all clients
		send_release_msg((top_lamport_time, top_pid))
		return

    # We have already checked if the balance is sufficient before starting the lamport's algorithm
	# Hence, we can directly execute the transaction
	balance_table[src] -= amount
	balance_table[dest] = balance_table.get(dest, 0) + amount
    # Add the transaction to the blockchain
	blockchain.add_block(user_input)
	print(f"SUCCESS: Transaction '{user_input}' successfully executed at client {pid}")
    
    # Send message to update balance table at all clients
	for pid, sock in pidToSock.items():
		sock.sendall(bytes(f"update {top_lamport_time} {top_pid} {user_input}", "utf-8"))
		
	# Wait until update_count for the request equals the number of clients
	while update_count.get((top_lamport_time, top_pid), 0) < len(pidToSock):
		sleep(0.1)
	
	print(f"SUCCESS: Balance table updated at all clients for request ({top_lamport_time}, {top_pid})")
	# Reset update count
	update_count[(top_lamport_time, top_pid)] = 0
	
	# Send release message to all clients
	send_release_msg((top_lamport_time, top_pid))

# keep waiting and asking for user inputs
def get_user_input():
	while True:
		# wait for user input
		user_input = input()
		cmd = user_input.split()[0]

		if cmd == "exit":
			# close all client sockets
			for sock in out_socks:
				sock[0].close()
			stdout.flush()
			# exit program with status 0
			_exit(0)
		elif cmd == "wait":
			words = user_input.split()
			sleep(int(words[1]))
		elif cmd == "balance":
			try:
				clientNum = int(user_input.split()[1])
				# Simple read operation to read balance
				# Return balance from local balance table
				print(f"Balance for client {clientNum} is {balance_table.get(clientNum, 0)}")
			except:
				print("exception in retrieving balance")
				continue
		elif cmd == "transfer":
			try:
				# Check if balance table has enough balance to transfer
				words = user_input.split()
				src = int(words[1])
				dst = int(words[2])
				amount = float(words[3])
				if src == dst:
					print("Source and destination clients cannot be the same")
				elif amount < 0:
					print("Amount cannot be lesser than 0")
				else:
					threading.Thread(target=start_lamport_algo, args=(user_input,)).start()
			except:
				print("Exception in lamport's algorithm")
				continue
		elif cmd == "help":
			print("Available commands:")
			print("1. balance <client_id>")
			print("2. transfer <src_client_id> <dest_client_id> <amount>")
			print("3. print balance table")
			print("4. print blockchain")
			print("5. help")
		elif user_input.startswith("print balance table"):
			# Print the balance table
			table = Table(title="Balance Table")
			table.add_column("Client ID", style="cyan", no_wrap=True)
			table.add_column("Balance", style="magenta")
			for client_id, balance in balance_table.items():
				table.add_row(str(client_id), str(balance))
			console = Console()
			console.print(table)
		elif user_input.startswith("print blockchain"):
			# Print the blockchain
			blockchain.print_blockchain()
		else:
			print("Invalid command")

def send_release_msg(request):
    # Send release message to all other processes
    global pidToSock
    global local_lamport_time
    global queue
	
    print(f"Sending release message")
    
    #with muLock: TODO - Fix this
    heapq.heappop(queue)
		
    for pid, sock in pidToSock.items():
        print(f"Sending release for request {request} to Client {pid}")
        sock.sendall(bytes(f"release {request[0]} {request[1]}", "utf-8"))

def start_lamport_algo(user_input):
	# 1. Add new request to the queue
	# 2. Initialize reply_count and release_count for the new request
	# 3. Send request to all other processes
	# 4. Increment local lamport time
	global local_lamport_time
	global reply_count
	global release_count
	global queue

	# Increment local lamport time before sending a request
	with muLock:
		local_lamport_time += 1
	
	# A new request is of the form (timestamp, processid, 'insert x y' or 'lookup x') 
	# where the user_input corresponds to the action associated with that request
	new_request = (local_lamport_time, process_id, user_input)

	with muLock:
		heapq.heappush(queue, new_request)

	for pid, sock in pidToSock.items():
		print(f"Sending request ({local_lamport_time}, {process_id}) to Client {pid}")
		sock.sendall(bytes(f"request {local_lamport_time} {process_id} {user_input}", "utf-8"))

def handle_client_msg(conn, data):
	global pidToSock
	global local_lamport_time
	global reply_count
	global release_count
	global queue
	global update_count

	sleep(3)
	data = data.decode()
	words = data.split()

	try:
		# When a client is first initialized, it sends a 'Client <clientid>' message to the 
		# other clients whose connection is then stored in a dictionary
		# the dictionary is of the form {client_id : conn}
		if words[0] == "Client":
			client_id = int(words[1])
			pidToSock[client_id] = conn

		else:
			recv_lamport_time = int(words[1])
			recv_pid = int(words[2])

			# user input is the string starting from words[3] until the end 
			# which is either an insert or lookup operation
			user_input = " ".join(words[3:])

			if words[0] == "request":
				print(f"Received request ({recv_lamport_time}, {recv_pid})")
				with muLock:
					heapq.heappush(queue, (recv_lamport_time, recv_pid, user_input))
				# send a reply to the process that sent the request
				conn.sendall(bytes(f"reply {recv_lamport_time} {recv_pid} {user_input}", "utf-8"))

				# Increment local lamport time based on the request's timestamp
				with muLock:
					local_lamport_time = max(local_lamport_time, recv_lamport_time) + 1

			elif words[0] == "reply":
				with muLock:
					reply_count[(recv_lamport_time, recv_pid)] = reply_count.setdefault((recv_lamport_time, recv_pid), 0) + 1

				print(f"Received reply for ({recv_lamport_time}, {recv_pid}), incrementing reply count to {reply_count[(recv_lamport_time, recv_pid)]}")

				with muLock:
					# If the number of replies equals n-1 and the head of the queue equals the received process
					if queue and reply_count.get((recv_lamport_time, recv_pid), 0) == len(pidToSock) and queue[0][:2] == (recv_lamport_time, recv_pid):
						# Execute the transaction
						execute_transaction()
						
			elif words[0] == "updated":
				# with muLock:
				update_count[(recv_lamport_time, recv_pid)] = update_count.setdefault((recv_lamport_time, recv_pid), 0) + 1
							
			elif words[0] == "update":
				print(f"Received new transaction corresponding to request ({recv_lamport_time}, {recv_pid}) for update")
				with muLock:
					# Update balance table and add the transaction to the blockchain
                    # words[1] is the balance table in string format
					src = int(user_input.split()[1])
					dest = int(user_input.split()[2])
					amount = float(user_input.split()[3])
					balance_table[src] -= amount
					balance_table[dest] += amount
					blockchain.add_block(user_input)
					# Send a message to the client that the balance table has been updated
					conn.sendall(bytes(f"updated {recv_lamport_time} {recv_pid}", "utf-8")) 

			elif words[0] == "release":

				with muLock:
					release_count[(recv_lamport_time, recv_pid)] = release_count.setdefault((recv_lamport_time, recv_pid), 0) + 1

				print(f"Received release for request ({recv_lamport_time}, {recv_pid})")
				
				with muLock:
					heapq.heappop(queue)

					if queue:
						top_lamport_time, top_pid, user_input = queue[0]
						if top_pid == process_id and reply_count.get((top_lamport_time, top_pid), 0) == len(pidToSock):
							# reset reply count to ensure another thread doesn't send the same insert to primary server
							reply_count[(top_lamport_time, top_pid)] = 0
							execute_transaction()
			
                

	# Printing out a backtrace here just to see what went wrong, as socket errors can be very vague
	except Exception as e:
		print(f"exception in sending to port: {e}", flush=True)
		traceback.print_exc()

# handle incoming messages from other clients
def respond(conn, addr):
	while True:
		try:
			data = conn.recv(1024)
		except:
			break
		if not data:
			conn.close()
			break
        # Spawn new thread for every msg to ensure IO is non-blocking
		threading.Thread(target=handle_client_msg, args=(conn, data)).start() 

def handle_conn_to_client(out_sock, IP, port, pid):
	connected = False
	while not connected:
		try:
			out_sock.connect((IP, port))
			connected = True
		except:
			pass
	
	# Allow the client to note this as a new client-client connection
	out_sock.sendall(bytes(f"Client {pid}", "utf-8"))
	client_id = 1 if port == CLIENT1_PORT else (2 if port == CLIENT2_PORT else 0) 
	pidToSock[client_id] = out_sock

	while True:
		try:
			data = out_sock.recv(1024)
		except Exception as e:
			print(f"Error receiving data: {e}")
			break
		if not data:
			try:
				# Before shutting down, check if the socket is connected
				if out_sock.fileno() != -1:
					out_sock.shutdown(socket.SHUT_RDWR)
					out_sock.close()
			except Exception as e:
				print(f"Error closing socket: {e}")
			finally:
				return  # Exit the function when the socket is closed
		threading.Thread(target=handle_client_msg, args=(out_sock, data)).start()

if __name__ == "__main__":

	pid = argv[1]
	start_ports = 9000

	# specify server's socket address so client can connect to it
	# since client and server are just different processes on the same machine
	# server's IP is just local machine's IP
	SERVER_IP = socket.gethostname()
	CLIENT1_PORT = start_ports 
	CLIENT2_PORT = start_ports + 1
	CLIENT3_PORT = start_ports + 2

	muLock = threading.Lock()

	threading.Thread(target=get_user_input).start()

	# Create in_sock to listen for incoming connections from other 2 clients
	in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	out_socks = []
	if pid == "1":
		in_sock.bind((SERVER_IP, CLIENT1_PORT))
	elif pid == "2":
		in_sock.bind((SERVER_IP, CLIENT2_PORT))
		# connect to client 1 in a separate thread
		out_client1_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		threading.Thread(target=handle_conn_to_client, args=(out_client1_sock, SERVER_IP, CLIENT1_PORT, pid)).start()
	elif pid == "3":
		in_sock.bind((SERVER_IP, CLIENT3_PORT))
		# connect to client 1 & 2 in a separate thread
		out_client1_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		threading.Thread(target=handle_conn_to_client, args=(out_client1_sock, SERVER_IP, CLIENT1_PORT, pid)).start()
		out_client2_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		threading.Thread(target=handle_conn_to_client, args=(out_client2_sock, SERVER_IP, CLIENT2_PORT, pid)).start()

	# Print the list of available commands in a pretty format
	print("Available commands:")
	print("1. balance <client_id>")
	print("2. transfer <src_client_id> <dest_client_id> <amount>")
	print("3. print balance table")
	print("4. print blockchain")
	print("5. help")

	in_sock.listen()

	# infinite loop to keep waiting for incoming connections from other clients
	while True:
		try:
			# accept incoming connection
			conn, addr = in_sock.accept()
		except:
			break
		out_socks.append((conn, addr))
		# Start a new thread to handle incoming connections from other clients
		threading.Thread(target=respond, args=(conn,addr)).start()