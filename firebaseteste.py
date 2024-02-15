import pyrebase

firebaseConfig = {
                'apiKey': "AIzaSyA25NeC-hSwceoYeEKyXVR7Pa8QlsNm5KE",
                'authDomain': "criptochat-ba4da.firebaseapp.com",
                'databaseURL': "https://criptochat-ba4da-default-rtdb.firebaseio.com",
                'projectId': "criptochat-ba4da",
                'storageBucket': "criptochat-ba4da.appspot.com",
                'messagingSenderId': "394191700396",
                'appId': "1:394191700396:web:f4d3374f4aefdc01c2ba09",
                'measurementId': "G-LVD9LXKGHW"
}

firebase = pyrebase.initialize_app(firebaseConfig)

email = "adm@adm.com"
password = "adm2326"

auth = firebase.auth()

user = auth.sign_in_with_email_and_password(email, password)

db = firebase.database()

def get_nickname_by_email(email_to_find):
    all_users = db.child("users").get()
    for user in all_users.each():
        user_data = user.val()
        if 'email' in user_data and user_data['email'] == email_to_find:
            return user_data.get('nickname')
    return None

teste = db.child("users").child(user['localId']).get()
teste = teste.val()
print(teste['nickname'])

