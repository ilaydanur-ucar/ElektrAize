import smtplib
import os
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()
FIREBASE_API_KEY= os.getenv("FIREBASE_API_KEY")

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
    
    def send_reset_email(self, recipient_email: str, reset_token: str):
        try:
            subject = "ElektrAize - Şifre Sıfırlama"
            body = f"""
            Merhaba,

            ElektrAize hesabınız için şifre sıfırlama talebinde bulundunuz.

            Şifrenizi sıfırlamak için aşağıdaki linke tıklayın:
            http://localhost:8000/reset-password?token={reset_token}

            Bu link 1 saat boyunca geçerlidir.

            Eğer bu talebi siz yapmadıysanız, bu emaili görmezden gelebilirsiniz.

            Saygılarımızla,
            ElektrAize Ekibi
            """
            
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                
            return True
            
        except Exception as e:
            print(f"Email gönderim hatası: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail="Email gönderilemedi. Lütfen daha sonra tekrar deneyin."
            )
    
    def send_welcome_email(self, recipient_email: str, full_name: str):
        try:
            subject = "ElektrAize - Hoş Geldiniz!"
            body = f"""
            Sayın {full_name},

            ElektrAize enerji anomali tespit sistemine hoş geldiniz!

            Artık aşağıdaki özelliklere erişebilirsiniz:
            • Enerji tüketim anomalilerini görüntüleme
            • Şehir bazlı detaylı analizler
            • Otomatik PDF rapor oluşturma
            • Gerçek zamanlı bildirimler

            Sistemimizle ilgili sorularınız için bizimle iletişime geçebilirsiniz.

            Saygılarımızla,
            ElektrAize Ekibi
            """
            
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                
            return True
            
        except Exception as e:
            print(f"Hoş geldin emaili gönderim hatası: {str(e)}")
            # Kritik değil, devam et

email_service = EmailService()
def send_verification_email(id_token: str):
    """
    Firebase üzerinden kullanıcıya doğrulama maili gönderir.
    """
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
        payload = {
            "requestType": "VERIFY_EMAIL",
            "idToken": id_token
        }

        response = requests.post(url, json=payload)
        data = response.json()
        print("Firebase doğrulama maili sonucu:", data)

        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"]["message"])
        return {"message": "Doğrulama maili gönderildi"}
    except Exception as e:
        print("Doğrulama maili hatası:", e)
        raise HTTPException(status_code=500, detail="Firebase doğrulama maili gönderilemedi.")