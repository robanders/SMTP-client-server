import socket
import sys

def mail_from_cmd(user_in):
    mail = user_in[0:4]
    if mail != "MAIL":
        return "500"

    from_index = user_in.find("FROM:")

    if from_index == -1:
        return "500"

    sp = user_in[4:from_index]
    rp = user_in[from_index + 5:]
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
        return "500"


def path(r_path):
    if len(r_path) == 0:
        return "501"
    first_char = r_path[0]
    last_char = r_path[-1]
    if first_char != "<":
        return "501"
    if last_char != ">":
        return "501"
    mb = r_path[1:-1]
    # print("mailbox: " + mb)

    error = mailbox(mb)
    if error != None:
        return error

    global confirmed_path
    confirmed_path = r_path
    return None


def mailbox(path):
    at = path.find("@")
    if at == -1:
        return "501"
    lp = path[0:at]
    dm = path[at + 1:]

    error = string(lp)
    if error != None:
        return error

    error = domain(dm)
    if error != None:
        return error

    return None


def string(local_part):
    for c in local_part:
        if c == "<" or c == ">" or c == "(" or c == ")" or c == "[" \
                or c == "]" or c == "\\" or c == "." or c == "," \
                or c == ";" or c == ":" or c == "@" or c == '"' or c == " " or c == "\t":
            return "501"

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
        return "501"
    error = element(elmt)
    if error != None:
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
        return "501"


def let_dig_str(name):
    if name.isalnum():
        return None
    else:
        return "501"


def rcpt_to_cmd(user_in):
    rcpt = user_in[0:4]
    if rcpt != "RCPT":
        return "500"

    to_index = user_in.find("TO:")

    if to_index == -1:
        return "500"

    sp = user_in[4:to_index]
    fp = user_in[to_index + 3:]
    fp = fp.strip()

    error = space(sp)
    if error != None:
        return error

    error = path(fp)
    if error != None:
        return error

    return None


def data_cmd(user_in):
    data = user_in[0:4]
    if user_in.strip() == data:
        return None
    else:
        return "500"

def get_recv(client_sock,rest):

    str1 =''
    loop = True
    while loop:
        nl_index = rest.find('\n')
        if nl_index != -1:
            if nl_index == 0:
                str1 = rest[0]
            else:
                str1 = rest[0:nl_index]
            if len(rest)> nl_index+1:
                rest = rest[nl_index+1:]
            else:
                 rest = ''
            return None, str1, rest
        else:
            try:
                recv_data = client_sock.recv(1024)
                #print "receiving " + user_in
                rest = rest + recv_data
            except socket.error, e:
                print 'Failed to receive data from client. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
                return "recv_error", '',rest

    return None,str1, rest

def send_msg(msg, client_sock):
    try:
        client_sock.send(msg)
        #print "sending " + msg
    except socket.error, e:
        print 'Failed to process message. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
        client_sock.close()
        return "send_error"
    return

def process_msg(client_sock):
    state = "mail wait"
    rcpt_list = []
    data_list = []
    mail_command = ""
    global confirmed_path
    confirmed_path = ""
    rest = ''
    loop = True
    while loop:
        try:
            recv_err, user_in, rest = get_recv(client_sock, rest)
            if recv_err != None:
                return recv_err
            #print "receiving " + user_in
        except socket.error, e:
            print 'Failed to receive data from client. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
            return "recv_error"
        #print(user_in)
        text_start = user_in[0:4]
        if text_start == "QUIT":
            return "QUIT"
        if state != "process":  # processing is taking in data
            if text_start == "MAIL":
                error = mail_from_cmd(user_in)
                if error == None:
                    if state == "mail wait":
                        state = "rcpt wait"
                        mail_command = confirmed_path  # saves valid mail command
                        del rcpt_list[:]
                    else:
                        error = "503"
                elif error == "501" and state != "mail wait":
                    error = "503"
            elif text_start == "RCPT":
                error = rcpt_to_cmd(user_in)
                if error == None:
                    if state == "rcpt wait" or state == "rcpt wait 2":
                        state = "rcpt wait 2"
                        rcpt_list.append(confirmed_path)
                    else:
                        error = "503"
                elif error == "501" and state != "rcpt wait" and state != "rcpt wait 2":
                    error = "503"
            elif text_start == "DATA":
                error = data_cmd(user_in)
                if error == None:
                    if state == "rcpt wait 2":
                        state = "process"
                        error = "354"
                        del data_list[:]
                    else:
                        error = "503"
                elif error == "501" and state != "rcpt wait 2":
                    error = "503"
            else:
                error = "500"
        else:
            # print("processing")
            if user_in == ".":
                state = "mail wait"
                error = None
                domain_list = build_domain_list(rcpt_list)
                for c in domain_list:
                    file = open("forward/" + c, 'a+')
                    file.write("From: " + mail_command + "\n")
                    for i in rcpt_list:
                        file.write("To: " + i + "\n")
                    for d in data_list:
                        if d == "\n":
                            file.write(d)
                        else:
                            file.write(d + "\n")
                    file.close()
                loop = False
            else:
                data_list.append(user_in)
                #print 'd = (' + user_in + ')'
                error = "9000"  # made up error so it doesn't print 250 OK after each DATA input

        # error processing
        if error == "500":
            send_err = send_msg("500 Syntax error: command unrecognized", client_sock)
            if(send_err != None):
                return send_err
        elif error == "501":
            send_err = send_msg("501 Syntax error in parameters or arguments", client_sock)
            if (send_err != None):
                return send_err
        elif error == "503":
            send_err = send_msg("503 Bad sequence of commands", client_sock)
            if (send_err != None):
                return send_err
        elif error == "354":
            send_err = send_msg("354 Start mail input; end with <CRLF>.<CRLF>", client_sock)
            if (send_err != None):
                return send_err
        elif error == "9000":
            pass
        else:
            send_err = send_msg("250 OK", client_sock)
            if (send_err != None):
                return send_err
    return None

def build_domain_list(rcpt_list):
    domain_list = []
    for c in rcpt_list:
        at = c.find('@')
        dom = c[at+1:-1]
        domain_list.append(dom)
    domain_list = set(domain_list)
    return domain_list

# "Main Code"
if len(sys.argv) != 2:
    print "invalid parameters, enter a port number."
    exit()
try:
    port = int(sys.argv[1])
except ValueError:
    print "port must be an integer"
    exit()
confirmed_path = ""
try:
    sock = socket.socket()
except socket.error, e:
    print 'Failed to create socket. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
    exit(1)

try:
    host = socket.gethostname()
except socket.error, e:
    print 'Failed to get host. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
    exit(1)

try:
    sock.bind((host, port))
except socket.error, e:
    print 'Failed to bind socket. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
    exit(1)

try:
    sock.listen(1)
except socket.error, e:
    print 'Failed to listen. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
    exit(1)

looping = True
while looping:
    try:
        client_sock, addr = sock.accept()
    except socket.error, e:
        print 'Failed to accept. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
        exit(1)
    try:
        client_sock.send('220 ' + host)
    except socket.error, e:
        print 'Failed to send 220 greeting. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
        client_sock.close()
        continue
    try:
        ack = client_sock.recv(1024)
    except socket.error, e:
        print 'Failed to receive acknowledgement. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
        client_sock.close()
        continue

    #print ack
    if(ack[0:4] == 'HELO'):
        try:
            client_sock.send('250 ' + ack + ' pleased to meet you.')
        except socket.error, e:
            print 'Failed to send 250 message. Error code: ' + str(e[0]) + ' , Error message : ' + e[1]
            client_sock.close()
            continue
        error = process_msg(client_sock)
        if error != None:
            client_sock.close()
            continue
    else:
        print "invalid HELO message"
    client_sock.close()
    #looping = False
sock.close()