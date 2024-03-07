import pyrebase

firebaseConfig = {
                'apiKey': "",
                'authDomain': "",
                'databaseURL': "",
                'projectId': "",
                'storageBucket': "",
                'messagingSenderId': "",
                'appId': "",
                'measurementId': ""
}

firebase = pyrebase.initialize_app(firebaseConfig)

email = "adm@adm.com"
password = "adm2326"

auth = firebase.auth()

user = auth.sign_in_with_email_and_password(email, password)

db = firebase.database()

#data = {
#    "nickname": "Mortimer 'Morty' Smit"
#}

#results = db.child("users").child(user['localId']).set(data)

all_users = db.child("users").get()

class NicknameDuplicadoException(Exception):
    pass

def is_nickname_duplicate(nickname_to_check):
    all_users = db.child("users").get()
    for user in all_users.each():
        user_data = user.val()
        if 'nickname' in user_data and user_data['nickname'] == nickname_to_check:
            return True
    return False

def get_nickname_by_email(email_to_find):
    all_users = db.child("users").get()
    for user in all_users.each():
        user_data = user.val()
        if 'email' in user_data and user_data['email'] == email_to_find:
            return user_data.get('nickname')
    return None

def get_nickname_by_login(login):
    user = db.child("users").child(login['localId']).get().val()
    return user['nickname']

# Exemplo de uso da função
#nickname_to_check = input("Digite o nickname que deseja verificar: ")

#if is_nickname_duplicate(nickname_to_check):
#    print("Já existe um usuário com este nickname.")
#else:
 #   print("Nickname disponível.")


