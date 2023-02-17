import smtplib

if __name__=='__main__':
    smtp_username = 'corpora-admin@digitalcorpora.org'
    smtp_password = 'N!zsa9Bk'
    smtp_server = 'smtp.dreamhost.com'
    from_addr = 'simsong@acm.org'
    to_addrs = ['12023228411@tmomail.net']
    msg = 'to: simsons-pager\n\nHey man\n'
    debug = False
    with smtplib.SMTP(smtp_server,587) as smtp:
        if debug:
            smtp.set_debuglevel(1)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(smtp_username, smtp_password)
        smtp.sendmail(from_addr,to_addrs,msg.encode('utf8'))
        if debug:
            print("Sent mail to ",to_addrs," from ",from_addr," with SMTP . message length:",len(msg),file=sys.stderr)
