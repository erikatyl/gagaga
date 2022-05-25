import os
import socket
import asyncio
import websockets
import threading
import sys
import errno

HOST = '127.0.0.1'
PORT = 6969

if len(sys.argv) == 1:
  print("require websocket url")
  os._exit()

wsaddr = sys.argv[1]

async def ws_send(websocket, data):
  await websocket.send(data)

def receive(s, websocket):
  global event_loop
  while not websocket.closed:
    data = s.recv(1024)
    
    if not data:
      break
    
    print(websocket.closed, "RECV |", data)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(ws_send(websocket, data.decode("utf-8")))
  
  print("receive(): connection closed")
  
  os._exit(1)

async def listen():
  async with websockets.connect(wsaddr) as websocket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    
    s.listen()
    
    conn, addr = s.accept()
    
    loop = threading.Thread(target=receive, args=(conn, websocket))
    loop.start()
    
    while not websocket.closed:
      try:
        message = await websocket.recv()
        print(websocket.closed, "SEND |", message)
        conn.sendall(str.encode(message))
      except Exception as e:
        break
    
    print("listen(): connection closed")
    os._exit(1)

event_loop = asyncio.get_event_loop().run_until_complete(listen())
import os
import time
import socket
import threading
import websocket
import _thread
import time
import rel
import sys
from threading import Lock

if len(sys.argv) == 1:
  print("usage: {} [websocket url]".format(sys.argv[0]))
  os._exit(0)

HOST = '127.0.0.1'
PORT = 6969

receive_thread = None
current_conn = None
is_ws_connected = False
ws = None

lock = Lock()

rel.safe_read()

def on_message(ws, message):
  with lock:
    if current_conn:
      current_conn.send(str.encode(message))

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")
    
    with lock:
      global is_ws_connected
      is_ws_connected = False

def on_open(ws):
    print("Opened connection")
    
    with lock:
      global is_ws_connected
      is_ws_connected = True

def socket_receive(ws):
  global is_ws_connected
  global current_conn
  
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  s.bind((HOST, PORT))
  
  s.listen()
  
  while True:
    conn, addr = s.accept()
    
    with lock:
      current_conn = conn
    
    data = conn.recv(4096)
    while data:
      with lock:
        if is_ws_connected:
          ws.send(data)
      
      data = conn.recv(4096)
    
    with lock:
      current_conn = None

websocket.enableTrace(True)

with lock:
  ws = websocket.WebSocketApp(sys.argv[1],
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
  
receive_thread = threading.Thread(target=socket_receive, args=(ws,))
receive_thread.start()

while True:
  try:
    ws.run_forever()
    print("OKAY")
  except Exception as e:
    print(e)
  
  ws.close()
  print("client.py: connection closed unexpectedly; reconnecting in 5s...")
  
  time.sleep(5)
