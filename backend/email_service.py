import smtplib
import os
from email.mime.text import MIMEText


def send_email(subject, body):
    sender = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    receiver = "balispandan26@gmail.com"

    # Safety check
    if not sender or not password:
        print("Missing EMAIL or PASSWORD environment variables")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")

    except Exception as e:
        print("Error sending email:", e)


# 👇 This part is for CI/CD (GitHub Actions)
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("No status provided")
        exit()

    status = sys.argv[1]

    if status == "success":
        send_email(
            "✅ CI/CD Success",
            "Your AutoQuery pipeline ran successfully!"
        )

    else:
        send_email(
            "❌ CI/CD Failed",
            "Your AutoQuery pipeline failed. Check GitHub Actions logs."
        )