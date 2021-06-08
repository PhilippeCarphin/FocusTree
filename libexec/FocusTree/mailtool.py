#!/usr/bin/env python3
import smtplib
from email.message import EmailMessage
import getpass
import sys
import mimetypes

def add_attachment(m, attachment):
    ctype, encoding = mimetypes.guess_type(attachment)
    if ctype is None or encoding is not None:
        # No guess could be made, or the file is encoded (compressed), so
        # use a generic bag-of-bits type.
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    with open(attachment, 'rb') as f:
        m.add_attachment(f.read(),
                         maintype=maintype,
                         subtype=subtype,
                         filename=attachment)

def make_message_object(origin, destination, subject, content, attachment=None):
    m = EmailMessage()
    m.set_content(content)
    m['Subject'] = subject
    m['From'] = origin
    m['To'] = destination
    if attachment:
        add_attachment(m, attachment)
    return m

def make_hotmail_connection():
    from_smtp = 'smtp-mail.outlook.com'
    from_address = 'phil103@hotmail.com'
    password = getpass.getpass('Say password for user {} : '.format(from_address))

    s = smtplib.SMTP(from_smtp, 587 )
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(from_address, password)
    return s

def send_mail(origin, destination, subject, content, attachment=None):
    hc = make_hotmail_connection()
    send_mail_connected(origin, destination, subject, content, hc, attachment)
    hc.quit()

def send_mail_connected(origin, destination, subject, content, connection, attachment=None):
    message = make_message_object(origin, destination, subject, content, attachment)
    connection.send_message(message, origin, destination)

def test_send_mail():
    send_mail("phil103@hotmail.com", "pcarphin@gmail.com", "el subjecto", "el contento")


def send_cmc_command():
    import sys
    usage = "Fist argument : subject\nSecondArgument : content\n\n Message will be sent to my CMC address from my hotmail address"
    subject = ""
    content = ""
    try:
        subject = sys.argv[1]
    except IndexError:
        print("send_mail ERROR: Missing argument\n\n" + usage)
        quit()

    try:
        content = sys.argv[2]
    except IndexError:
        print("send_mail ERROR: Missing argument\n\n" + usage)
        quit()

    send_mail(
        "phil103@hotmail.com",
        "philippe.carphin2@canada.ca",
        subject, content)

def test_send_attachment():
    subject = 'Test of attachment'
    content = 'This message should have mailtool.py as an attachmetn'
    hotmail = make_hotmail_connection()
    send_mail_connected(
        "phil103@hotmail.com",
        "pcarphin@gmail.com",
        subject, content, hotmail, 'mailtool.py')
    hotmail.quit()

def resolve_nicknames(potential_nickname):
    if potential_nickname in addresses:
        return addresses[potential_nickname]

addresses = {
    "cmc": "philippe.carphin2@canada.ca",
    "hotmail": "phil103@hotmail.com",
    "poly": "philippe.carphin@polymtl.ca"
    }
def test_send_cmc_command():
    send_cmc_command()
if __name__ == "__main__":
    # test_send_mail()
    # test_send_cmc_command()
    # send_cmc_command()
    test_send_attachment()
