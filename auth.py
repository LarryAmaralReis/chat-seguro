import smtplib
from email.mime.text import MIMEText
from functions import *

def enviar_email(email):
    servidor_email = smtplib.SMTP('smtp.gmail.com', 587)

    servidor_email.starttls()

    servidor_email.login('mycriptochat@gmail.com', 'nilekatwwvwlskbw')

    remetente = 'mycriptochat@gmail.com'
    destinatarios = [email]
    assunto = 'CriptoChat - Código de Autenticação'

    # Gerando um número
    private, public, p = generate_dh_key_pair()

    # Criando o corpo do email
    mensagem = MIMEText(f"Seu código de autenticação é: {private}")
    mensagem['Subject'] = assunto
    mensagem['From'] = remetente
    mensagem['To'] = ', '.join(destinatarios)

    # Convertendo a mensagem para string
    mensagem_str = mensagem.as_string()

    servidor_email.sendmail(remetente, destinatarios, mensagem_str)

    servidor_email.quit()

    return private
