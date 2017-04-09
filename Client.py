import sys
import socket
import os

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

def send_msg(msg,sock):
    try:
        if msg[-1] == '\n':
            sock.send(msg)
        else:
            sock.send(msg + '\n')
        #print "sending " + msg
    except socket.error, e:
        print 'Failed to send message. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
        sock.close()
        exit(1)
    return

def get_response(sock):
    try:
        smtp_response = sock.recv(1024)
        print "receiving " + smtp_response
    except socket.error, e:
        print 'Failed to receive response. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
        sock.close()
        exit(1)
    #smtp_response = raw_input()
    if(len(smtp_response) < 3):
        smtp_code = smtp_response
    if(len(smtp_response) > 3):
        smtp_code = smtp_response[0:4].rstrip()
    else:
        smtp_code = smtp_response[0:3]
    return (smtp_code,smtp_response)

def process_msg(email_msg, sock):
    ###State Machine Code###
    state = "from_wait"
    smtp_response = ""
    for raw_line in email_msg:
        if raw_line == '':
            line = '\n'
        elif len(raw_line) > 1:
            if (raw_line[-1] == "\n"):
                line = raw_line[0:-1]
            else:
                line = raw_line
        else:
            line = raw_line
        if(state == "from_wait"): #waiting for the sender of the message
            if (line[0:5] == "From:"):
                send_msg("MAIL FROM:" + line[5:],sock)
                state = "to_wait"
                smtp_code,smtp_response = get_response(sock)
                if (smtp_code == "250"):
                    pass
                    #sys.stderr.write(smtp_response + "\n")
                else:
                    #sys.stderr.write(smtp_response + "\n")
                    send_msg("QUIT", sock)
                    sock.close()
                    exit()
            else:
                #sys.stderr.write(smtp_response + "\n")
                send_msg("QUIT", sock)
                sock.close()
                exit()
        elif(state == "to_wait"): #waiting for the first recipient
            if(line[0:3] == "To:"):
                send_msg("RCPT TO:" + line[3:], sock)
                state = "to_wait2"
                smtp_code,smtp_response = get_response(sock)
                if (smtp_code == "250"):
                    pass
                    #sys.stderr.write(smtp_response + "\n")
                else:
                    #sys.stderr.write(smtp_response + "\n")
                    send_msg("QUIT", sock)
                    sock.close()
                    exit()
            else:
                #sys.stderr.write(smtp_response + "\n")
                send_msg("QUIT", sock)
                sock.close()
                exit()
        elif(state == "to_wait2"): #waiting for a second or more possible recipient
            if (line[0:3] == "To:"):
                send_msg("RCPT TO:" + line[3:], sock)
                state = "to_wait2"
                smtp_code,smtp_response = get_response(sock)
                if (smtp_code == "250"):
                    pass
                    #sys.stderr.write(smtp_response + "\n")
                else:
                    #sys.stderr.write(smtp_response + "\n")
                    send_msg("QUIT", sock)
                    sock.close()
                    exit()
            else:  # assume valid message--should be DATA
                send_msg("DATA", sock)
                smtp_code,smtp_response = get_response(sock)
                if (smtp_code == "354"):
                    pass
                    #sys.stderr.write(smtp_response + "\n")
                else:
                    #sys.stderr.write(smtp_response + "\n")
                    send_msg("QUIT", sock)
                    sock.close()
                    exit()
                state = "processing"
                send_msg(line, sock)
        elif(state == "processing"): #processing DATA state
            if(line[0:5] == "From:"):
                send_msg(".", sock) #closes old msg
                smtp_code,smtp_response = get_response(sock)
                if (smtp_code == "250"):
                    pass
                    #sys.stderr.write(smtp_response + "\n")
                else:
                    #sys.stderr.write(smtp_response + "\n")
                    send_msg("QUIT", sock)
                    sock.close()
                    exit()
                send_msg("MAIL FROM:" + line[5:], sock)
                state = "to_wait"
                smtp_code,smtp_response = get_response(sock)
                if (smtp_code == "250"):
                    pass
                    #sys.stderr.write(smtp_response + "\n")
                else:
                    #sys.stderr.write(smtp_response + "\n")
                    send_msg("QUIT", sock)
                    sock.close()
                    exit()
            else: #this should be normal data
                send_msg(line, sock)
    if state == "to_wait" or state == "from_wait": #making sure the file is correctly formatted
        send_msg("QUIT", sock)
        sock.close()
        exit()
    elif state == "to_wait2": #handling condition of empty data
        send_msg("DATA", sock)
        smtp_code,smtp_response = get_response(sock)
        if (smtp_code == "354"):
            pass
            #sys.stderr.write(smtp_response + "\n")
        else:
            #sys.stderr.write(smtp_response + "\n")
            send_msg("QUIT", sock)
            sock.close()
            exit()
        state = "processing"

    send_msg(".", sock)  # closes old msg
    smtp_code,smtp_response = get_response(sock)
    if (smtp_code == "250"):
        pass
        #sys.stderr.write(smtp_response + "\n")
    else:
        #sys.stderr.write(smtp_response + "\n")
        send_msg("QUIT", sock)
        sock.close()
        exit()
    send_msg("QUIT", sock)
    return None

def mail_from_cmd(user_in):
    mail = user_in[0:4]
    if mail != "MAIL":
        return "mail-from-cmd"

    from_index = user_in.find("FROM:")
    #new_line_index = user_in.find("\n")

    if from_index == -1: #or new_line_index == -1:
        return "mail-from-cmd"

    sp = user_in[4:from_index]
    rp = user_in[from_index + 5:] #had new_line_index in second slot
    rp = rp.strip()

    error = space(sp)
    if error != None:
        return error

    error = path(rp)
    if error != None:
        return error

    return None

def space(name):
    if name.isspace():
        return None
    elif name == '\t':
        return None
    else:
        return "sp"

def path(r_path):
    if len(r_path) == 0:
        return "path"
    first_char = r_path[0]
    last_char = r_path[-1]
    if first_char != "<":
        return "path"
    if last_char != ">":
        return "path"
    mb = r_path[1:-1]
    #print("mailbox: " + mb)

    error = mailbox(mb)
    if error != None:
        return error

    return None

def mailbox(path):
    at = path.find("@")
    if at == -1:
        return "invalid mail address"
    lp = path[0:at]
    dm = path[at + 1:]

    error = string(lp)
    if error != None:
        return error

    error = domain(dm)
    if error!= None:
        return error

    return None

def string(local_part):
    for c in local_part:
        if c == "<" or c == ">"or c == "(" or c == ")" or c == "[" \
                or c == "]" or c == "\\" or c == "." or c == "," \
                or c == ";"or c == ":" or c == "@" or c == '"' or c == " " or c == "\t":
            return "local part"

    return None

def domain(mb_name):
    dot = mb_name.find(".")
    if dot != -1:
        elmt = mb_name[0:dot]
        dm = mb_name[dot + 1:]
        error = domain(dm)
        if error != None:
            return error
    else:
        elmt = mb_name

    if len(elmt) == 0:
        return "domain"
    error = element(elmt)
    if error!= None:
        return error
    return None

def element(name):
    a = name[0]
    lds = name[1:]

    error = alpha(a)
    if error != None:
        return error


    error = let_dig_str(lds)
    if error != None:
        return error

    return None

def alpha(char):
    if char.isalpha():
        return None
    else:
        return "name"

def let_dig_str(name):
    if name.isalnum():
        return None
    else:
        return "name"

def get_email_msg():
    user_in = ''
    print("Enter From address in the following example format: test@live.com")
    while True:
        try:
            user_in = raw_input()
        except EOFError:
            break
        error = mailbox(user_in.strip())
        if error != None:
            print("ERROR -- " + error)
            print("Please enter a valid From address in the following format: test@live.com")
        else:
            break
    from_address = user_in.strip()
    print("Enter one or more valid To addresses separated by commas\nexample: test@example.com,test2@exmaple.com")
    to_list = []
    ask_again = True
    while ask_again: #Have to deal with multiple To's
        to_list = []
        try:
            user_in = raw_input()
        except EOFError:
            break
        remainder = user_in.strip()
        looping = True
        while looping:
            comma_index = remainder.find(",")
            if(comma_index != -1):
                first_address = remainder[0:comma_index].strip()
                remainder = remainder[comma_index + 1:]
            else:
                first_address = remainder.strip()
                looping = False
                ask_again = False
            error = mailbox(first_address)
            if error != None:
                print("ERROR -- " + error)
                print("Please re-enter your To address.")
                print("If you have multiple to addresses, re-enter all of them.")
                looping = False
                ask_again = True
            else:
                to_list.append(first_address)
    print("Enter the subject of your mail message.")
    user_in = raw_input()
    subject = user_in
    print("Provide the body of your message content. Terminate with a period on a line by itself.")
    message_list = []
    while True:
        try:
            user_in = raw_input()
        except EOFError:
            break
        #print "body (" + user_in + ")"
        if(user_in == "."):
            break
        message_list.append(user_in)

    to_string = ''
    for c in reversed(to_list):
        to_string = '<' + c + '>,' + to_string
    to_string = to_string[0:-1]

    email_msg = []
    email_msg.append("From: <" + from_address + ">")
    for c in to_list:
        email_msg.append("To: <" + c + ">")
    email_msg.append("From: <" + from_address + ">")
    email_msg.append("To: " + to_string) #fix stuff here
    email_msg.append("Subject: " + subject)
    email_msg.append("\n")
    for c in message_list:
        email_msg.append(c)

    error = None
    return error, email_msg

#Main Program
if len(sys.argv) != 3:
    print "invalid parameters, enter hostname followed by port number."
    exit()
host = sys.argv[1]
try:
    port = int(sys.argv[2])
except ValueError:
    print "port must be an integer"
    exit()
error,email_msg = get_email_msg()
if error != None:
    exit()
try:
    sock = socket.socket()
except socket.error, e:
    print 'Failed to create socket. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
    exit(1)
try:
    sock.connect((host, port))
except socket.error, e:
    print 'Failed to connect. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
    exit(1)
try:
    msg = sock.recv(1024)
except socket.error, e:
    print 'Failed to receive message. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
    sock.close()
    exit(1)

if msg[0:3] == '220':
    try:
        sock.send('HELO ' + host)
    except socket.error, e:
        print 'Failed to send HELO message. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
        sock.close()
        exit(1)
    try:
        msg2 = sock.recv(1024)
    except socket.error, e:
        print 'Failed to receive message. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
        sock.close()
        exit(1)
else:
    print "invalid Server greeting"
    exit(1)
#exit()

process_msg(email_msg, sock)