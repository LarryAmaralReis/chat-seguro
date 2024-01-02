from entry import *
from chat import *

if __name__ == "__main__":
    nickname_root = tk.Tk()
    nickname_app = NicknameEntry(nickname_root, ChatApp)
    nickname_root.mainloop()