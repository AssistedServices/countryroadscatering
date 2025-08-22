from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, EmailStr
import subprocess
import html

app = FastAPI()

RECIPIENT = "hello@countryroadscatering.co.uk"   # <-- where notifications go
SENDER    = "no-reply@countryroadscatering.co.uk"  # must exist/relay via postfix

class MenuRequest(BaseModel):
    email: EmailStr
    consent: bool | None = None
    source: str | None = "menu_request"

def send_mail(subject: str, body: str):
    # use local MTA via sendmail for reliability
    p = subprocess.Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=subprocess.PIPE, text=True)
    msg = f"""From: {SENDER}
To: {RECIPIENT}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

{body}
"""
    p.communicate(msg)
    if p.returncode != 0:
        raise RuntimeError("sendmail failed")

@app.post("/api/menu-request")
async def menu_request(payload: MenuRequest, request: Request):
    try:
        ip = request.client.host if request.client else "unknown"
        email = str(payload.email)
        consent = "yes" if payload.consent else "no"
        subject = "CRC: Menu PDF requested"
        body = (
            f"Email: {email}\n"
            f"Consent: {consent}\n"
            f"Source: {payload.source}\n"
            f"IP: {ip}\n"
        )
        send_mail(subject, body)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
