from server import ChatServer
from channels import ChatChannels

if __name__ == "__main__":
    chat_server = ChatServer()
    chat_channels = ChatChannels()
    chat_channels.start_channels()