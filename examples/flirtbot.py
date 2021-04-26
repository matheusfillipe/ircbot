from IrcBot.bot import IrcBot, utils, persistentData, tempData, Message, ReplyIntent, log
import logging
import os

##################################################
# SETTINGS                                       #
##################################################

LOGFILE = None
LEVEL = logging.DEBUG
HOST = 'irc.freenode.org'
PORT = 6666
NICK = 'flirtbot'
PASSWORD = ''
USERNAME = 'flirtbot'
REALNAME = 'flirtbot'
FREENODE_AUTH = True
SINGLE_CHAN = True
CHANNELS = ["#bottest"]
ACCEPT_PRIVATE_MESSAGES = True
DBFILEPATH = NICK+".db"


# Flirtbot Options
USE_NICK = False   # Useful for testing (If set to False)
PRIVATEONLY_SHOW = False # Show command only gets replied on private chat
PRIVATEONLY_FIND = False # Find command only gets replied on private chat (Can be spammy if set to False)
MAX_FIND_N_RESULTS = 15 # Number of results to show on find command


utils.setParseOrderTopBottom()
# Registration validation
class VALIDATE:
    min_name_len = 3
    min_description_len = 5 #characters count
    sex = ["f", "m"]
    orientation = ["s", "l", "g", "b", "t"]

# Translate the commands here:
class CMDS:
    prefix = "!" 
    regex = "^%s%s\s*$"
    
    # Command names:
    include = "include"
    delete = "delete"
    find = "find (.*)"
    show = "show (.*)"


INFO_CMDS = {
    r"^!help\s*$": [
        CMDS.include+": Use this to register on the bot",
        CMDS.delete+": Deletes your registration allowing you to recreate it",
        CMDS.find+": Find someone on certain city, with certain or gender or sexual orientation",
        CMDS.show+": Find out about some user",
    ],
}

# Translate bot messages here
class MSGS:
    include_name = "Hello! tell me your name"
    include_name_alert = f"Invalid name! Enter at least {VALIDATE.min_name_len} characters"
    already_registered_error = "You are already registered!"
    include_age = "Tell me your age"
    age_error = "Please, just type a number. Try again"
    include_sex = "Now tell me your biological gender, either m for male or f for female."
    include_orientation = "What is your sexual orientation?"
    include_city = "Tell us where you live (Use one word)"
    sex_error = "Please enter one of " + ", ".join(VALIDATE.sex)
    orientation_error = "Please enter one of " + ", ".join(VALIDATE.orientation)
    include_description = "Describe yourself"
    description_error = "Please fill more than " + str(VALIDATE.min_description_len) + " characters for the description"
    on_accepted = "Welcome to the club! Good luck"
    nick_not_registerd_error = "User not registered!"
    on_deleted = "Removed!"

    help = {CMDS.include: "Add yourself to the bot",
            CMDS.find.replace(" (.*)",""): "Use search queries like: !find f g 3-30 genova. The order of the parameters doesn't matter",
            CMDS.show.replace(" (.*)",""): "Pass in a nick and find info",
            }
   

# Useful if connecting to freenode from a blacklisted ip that will require SASL
USE_SASL = False

# Uncoment to use password from environment PW variable, like if you run:
# `PASSWORD=mypw python bot.py`

# PASSWORD=os.environ['PASSWORD']

table_columns=["nick", "age", "sexo", "orientation", "city", "description", "timestamp"]


##################################################
# BOT COMMANDS DEFINITIONS                       #
##################################################
import datetime

users = persistentData(NICK+".db", "users" , table_columns)
temp_users = tempData()

getcmd = lambda cmd: CMDS.regex % (CMDS.prefix, cmd)

for r in INFO_CMDS:
    @utils.regex_cmd(r, ACCEPT_PRIVATE_MESSAGES)
    def info_cmd(m, regexp=r):
        return INFO_CMDS[regexp]

@utils.regex_cmd("^!help (.*)$", ACCEPT_PRIVATE_MESSAGES)
def include(m):
    hlp = m.group(1)
    if hlp in MSGS.help:
        return MSGS.help[hlp]
    return "Not a valid command, use one of: " + ", ".join([k for k in MSGS.help])

# Registration
def finalizeInclude(msg):
    users.push(temp_users.get(msg))
    return MSGS.on_accepted+" "+temp_users.get(msg)[table_columns[0]]

def getDescription(msg):
    if len(msg.text)<VALIDATE.min_description_len:
        return ReplyIntent(MSGS.description_error, getDescription)
    temp_users.get(msg)[table_columns[5]] = msg.text
    return finalizeInclude(msg)

def getCity(msg):
    city = msg.text.split()
    temp_users.get(msg)[table_columns[4]] = city[0] if city else ""
    return ReplyIntent(MSGS.include_description, getDescription)

def getOrientation(msg):
    if msg.text not in VALIDATE.orientation:
        return ReplyIntent(MSGS.orientation_error, getOrientation)
    temp_users.get(msg)[table_columns[3]] = msg.text.upper()
    return ReplyIntent(MSGS.include_city, getCity)

def getSex(msg):
    if msg.text not in VALIDATE.sex:
        return ReplyIntent(MSGS.sex_error, getSex)
    temp_users.get(msg)[table_columns[2]] = msg.text.upper()
    return ReplyIntent(MSGS.include_orientation, getOrientation)

def getAge(msg):
    if not msg.text.isdigit():
        return ReplyIntent(MSGS.age_error, getAge)
    temp_users.get(msg)[table_columns[1]] = msg.text
    return ReplyIntent(MSGS.include_sex, getSex)

def getName(msg):
    if len(msg.text) < VALIDATE.min_name_len:
        return ReplyIntent(MSGS.include_name_alert, getName)
    temp_users.push(msg, {table_columns[0]: msg.txt, table_columns[-1]:  str(datetime.datetime.now())[:-7]})
    return ReplyIntent(MSGS.include_age, getAge)

@utils.regex_cmd_with_messsage(getcmd(CMDS.include), ACCEPT_PRIVATE_MESSAGES)
def include(m, message):
    nick = message.sender_nick
    for user in users.data:
        if nick == user[table_columns[0]]:
            return MSGS.already_registered_error
    temp_users.push(message, {table_columns[0]: message.sender_nick, table_columns[-1]:  str(datetime.datetime.now())[:-7]})
    if USE_NICK:
        return ReplyIntent(Message(channel=message.sender_nick, sender_nick=message.sender_nick, message=MSGS.include_age), getAge)
    else:
        return ReplyIntent(Message(channel=message.sender_nick, sender_nick=message.sender_nick, message=MSGS.include_name), getName)

####################################################################################################


import re, time
@utils.regex_cmd_with_messsage(getcmd(CMDS.find), ACCEPT_PRIVATE_MESSAGES)
def find(m, message):
    log(str(users.data))
    query = m.group(1)
    args = m.group(1).split(" ")
    msg="Searching for: "
    age_min=None
    age_max=None
    sex=None
    orientation=None
    r=re.match(r"^\D*([0-9]+)-([0-9]+).*$", query)
    if r:
        msg+="age in range: "
        if r.group(1) and r.group(2):
            age_min = r.group(1)
            age_max = r.group(2)
            msg+=f"from {age_min} to {age_max}; "
        else:
            msg+="Age range in wrong format (Correct eg. 20-35); "

    for sex_ in VALIDATE.sex:
        if sex_ in args:
            msg+="Biological sex: "+sex_+"; "
            sex=sex_
            break

    for orientation_ in VALIDATE.orientation:
        if orientation_ in args:
            msg+="Orientation: "+orientation_+"; "
            orientation=orientation_
            break
    
    words=[]
    for word in args:
        if not "-" in word and len(word)>1:
            words.append(word)
    if words:
        msg+=" words: "+", ".join(words)

    results=[]
    for user in users.data:
        mask=[False, False, False, False]
        i=0
        if not age_min is None and not age_max is None:
            if int(age_min)<=int(user[table_columns[1]])<=int(age_max):
                mask[i]=1
        else:
            mask[i]=1
        i=1
        if not sex is None:
            if sex.upper()==user[table_columns[2]]:
                mask[i]=1
        else:
            mask[i]=1
        i=2
        if not orientation is None:
            if orientation.upper()==user[table_columns[3]]:
                mask[i]=1
        else:
            mask[i]=1
        i=3
        if words:
            for word in words:
                if word in user[table_columns[0]] or word in user[table_columns[4]] or word in user[table_columns[5]]:
                    mask[i]=1
                    break
        else:
            mask[i]=1
        if mask==[1,1,1,1]:
            results.append(user)
        if len(results) >= MAX_FIND_N_RESULTS:
            break
    # Sort by timestamp
    # results.sort(key=lambda user: time.mktime(time.strptime(user[table_columns[6]], '%Y-%m-%d %H:%M:%S')))
    results.reverse()
    if PRIVATEONLY_FIND:
        return [Message(channel=message.sender_nick, sender_nick=message.sender_nick, message=m) for m in [msg] + list([", ".join([f"{u}: {user[u]}" for u in user if not "id" in u]) for user in results] if results else ["No results"])]
    else:
        return [msg] + list([", ".join([f"{u}: {user[u]}" for u in user if not "id" in u]) for user in results] if results else ["No results"])

@utils.regex_cmd_with_messsage(getcmd(CMDS.show), ACCEPT_PRIVATE_MESSAGES)
def show(m, message):
    search_nick = m.group(1)
    return_value=""
    if search_nick == "me":
        search_nick = message.sender_nick
    for user in users.data:
        if search_nick == user[table_columns[0]]:
            return_value = ", ".join([f"{u}: {user[u]}" for u in user if not "id" in u])
            break
    return_value = MSGS.nick_not_registerd_error if not return_value else return_value
    return Message(channel=message.sender_nick, sender_nick=message.sender_nick, message=return_value) if PRIVATEONLY_SHOW else return_value

@utils.regex_cmd_with_messsage(getcmd(CMDS.delete), ACCEPT_PRIVATE_MESSAGES)
def delete(m, message):
    nick = message.sender_nick
    for user in users.data:
        if nick == user[table_columns[0]]:
            users.pop(user["id"])
            return MSGS.on_deleted
    return MSGS.nick_not_registerd_error
    
##################################################
# RUNNING THE BOT                                #
##################################################

if __name__ == "__main__":
    utils.setLogging(LEVEL, LOGFILE)
    bot = IrcBot(HOST, PORT, NICK, CHANNELS, PASSWORD, tables=[users])
    bot.run()
