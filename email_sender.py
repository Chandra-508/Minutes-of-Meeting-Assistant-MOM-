import os
import base64

from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


def get_gmail_service():

    creds = None


    if os.path.exists("token.json"):

        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )


    if not creds or not creds.valid:


        if creds and creds.expired and creds.refresh_token:

            creds.refresh(Request())


        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )


        with open("token.json", "w") as token:

            token.write(
                creds.to_json()
            )


    return build(
        "gmail",
        "v1",
        credentials=creds
    )



def send_email(receiver, subject, body):

    service = get_gmail_service()


    message = MIMEText(
        body,
        "html"
    )


    message["To"] = receiver
    message["Subject"] = subject


    raw = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()


    service.users().messages().send(
        userId="me",
        body={
            "raw": raw
        }
    ).execute()



def extract_emails(attendees):

    emails = []


    for attendee in attendees:

        if isinstance(attendee, dict):

            email = attendee.get(
                "email"
            )

            if email:
                emails.append(email)


        elif isinstance(attendee, str):

            emails.append(attendee)


    return emails



def send_meeting_report(result):


    attendees = result.get(
        "attendees",
        []
    )


    emails = extract_emails(
        attendees
    )


    if not emails:

        raise ValueError(
            "No attendee email addresses found"
        )


    body = f"""
<html>

<body>

<h2>📝 AI Meeting Summary</h2>


<h3>Summary</h3>

<p>
{result.get("summary","")}
</p>


<h3>✅ Decisions</h3>

<ul>
"""


    for item in result.get("decisions", []):

        body += f"<li>{item}</li>"


    body += """
</ul>


<h3>📋 Action Items</h3>

<ul>
"""


    for item in result.get("action_items", []):

        body += f"""
<li>
<b>Owner:</b> {item.get('owner')}<br>
<b>Task:</b> {item.get('task')}<br>
<b>Deadline:</b> {item.get('deadline')}
</li>
"""


    body += """
</ul>


<h3>⚠️ Risks</h3>

<ul>
"""


    for item in result.get("risks", []):

        body += f"<li>{item}</li>"


    body += """
</ul>


<h3>🔓 Open Items</h3>

<ul>
"""


    for item in result.get("open_items", []):

        body += f"<li>{item}</li>"


    body += """
</ul>


<p>
Regards,<br>
<b>AI Meeting Assistant</b>
</p>


</body>

</html>
"""


    send_email(
        ", ".join(emails),
        "AI Meeting Summary",
        body
    )