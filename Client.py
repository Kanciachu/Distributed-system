import NodeClient
import time

client1 = NodeClient.NodeClient("Client1", "127.0.0.1", 5000)
client1.start()

time.sleep(2)
print("\nHello! This is Music Streaming service")
while True:
    time.sleep(2)
    userinput = input(
        "Enter [/auth] to authenticate your client  \n"
        "Enter [/list]      to get list of songs         \n"
        "Enter specific file name in [filename.wav] manner to play a song\n")
    client1.postMessage(userinput)