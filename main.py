from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import instaloader
import os
import datetime
import hashlib
import pymongo

client = pymongo.MongoClient("your mongo database token")
db = client.grammer # choose your database name instead of grammer
collection = db["users"] # choose your database document instead of users
limits = 12
loader = instaloader.Instaloader()
data = {"limits":str(limits),"time":str(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")),"logged":False}


def tolist(s:str):
    if s:
        ts=s.replace("[","").replace("]","").replace("'","").replace(" ","").split(",")
    else:
        ts = list()
    return ts 

# function to handle the /start command

def logout(update,context):
    global limits
    # Set  values in data to default
    data["logged"] = False
    data.pop("username")
    data["limits"] = 12
    data.pop("history")
    data.pop("id")
    limits = 12
    update.message.reply_text("Logged out successfly")
    print("Logged out")
    
def start(update, context):
    update.message.reply_text('Hi,use /help for instructions')

# function to handle the /help command
def help(update, context):
    helpmessage = """Just write a instagram username and I'll send you its latest posts,
and to set the maximum limits use '/limits [number]' , but if you want no limits just set it to -1,
you can also use multiline support and get posts of many users by sending one message
    for example :
        dog
        cat
        lizzard
You can get a value by using the '/get' command.
use '/get values' to see  available values.
You can also an account '/create [username] [password]'.
and login '/login [username] [password]'.
"""

    update.message.reply_text(helpmessage)

# function to handle errors occured in the dispatcher 
def error(update, context):
    # raise an error if found
    update.message.reply_text('an error occured')
    if context.error == IndexError:
        update.message.reply_text("/limits [number]")
    raise context.error

# Login
def login(update,context):
    global limits

    try:
        # Get user and password from message if they're not available see 'except' block
        username = update.message.text.split(" ")[1]
        password = update.message.text.split(" ")[2]
        print(username,password)
        # Get username from DB
        q =collection.find_one({"username":username})
        if not data["logged"]:
            # Check if the user is not logged
            if q:
                # Check hash of password 
                if q["password"] == hashlib.sha1(password.encode()).hexdigest():
                    # Set values to the user data
                    data["logged"] = True
                    data["username"] = username
                    data["id"] = q["_id"]
                    data["history"] = tolist(q["history"])
                    limits = int(q["limits"])
                    data["limits"] = limits
                    update.message.reply_text("Logged in successfly")
                    print(username,"Logged in")
                else:
                    update.message.reply_text("Incorrect Password or Username")
                    print(username,"Tried to login , but it failed due to IPU")
            else:
                update.message.reply_text("No account with this username") 
                print(username,"Tried to login , but it failed due to NAU")
        else:
            print(username,"Tried to login , but it failed due to ALI")
            update.message.reply_text("You're logged in")
    except IndexError:
        # Return an instruction message 
        update.message.reply_text("/login [username] [password]")
def create(update,context):
    try:
        # Get the user auths from message
        username = update.message.text.split(" ")[1]
        password = update.message.text.split(" ")[2]
        # Hash the pwd
        enc_pwd = hashlib.sha1(password.encode()).hexdigest()
        print(username, password)
        # Check if user is not on database
        if not collection.find_one({"username":username}):
            # Add user
            collection.insert_one({"username":username,"password":enc_pwd,"limits":limits,"history":""})
            update.message.reply_text("Done , now you can log in")
            print(username,"Created an account")
        else:
            # Return an UAE error
            update.message.reply_text("Username already exists")
            print(username,"Tried to make an already existing account")
    except IndexError:
        # Return instruction msg
        update.message.reply_text("/create [username] [password]")
    
def text(update, context):
    global limits
    global DB
    try:
        if("/limits" in update.message.text):
            try:
                # Set limits to what comes in msg
                limits = int(update.message.text.split(" ")[1])
                if data["logged"]:
                    # If the user is logged in update the one in account too // Not working currently and idk why
                    collection.update_one({"_id":data["id"]},{"$set":{"limits":limits}})
                print("Limit setted to "+str(limits))
                update.message.reply_text("Limit updated to "+str(limits))
                data["limits"] = str(limits)
            except IndexError:
                update.message.reply_text("/limits [number]")
        elif("/get" in update.message.text):
            # Get value command
            try:
                # Get the command
                req = update.message.text.split(" ")[1]
                #Update time on data
                data["time"] =str(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")) 
                if req in data:
                    #return value if it's in data
                    if req == "history":
                        update.message.reply_text(str(data[req]).replace("[","").replace("]","").replace("'","").replace(",","\n"))
                    else:
                        update.message.reply_text(str(data[req]))
                elif req == "values": # If the user asked for '/get values' return  values in data
                    update.message.reply_text(str(list(data.keys())).replace("[","").replace("]","").replace("'",""))
                else: # If not found return instruction msg
                    update.message.reply_text("Invalid key , use '/get values'")
            except IndexError:
                # Return instruction msg
                update.message.reply_text("/get [value]")
        else:
            # if the user sent no command , that means send user posts
            username = update.message.text.split("\n")
            for i in username: # Multiline support
                i = i.strip()
                update.message.reply_text(i)
                profile = instaloader.Profile.from_username(loader.context,i)
                a = 0 # Very basic ik
                if data["logged"]:
                    # Update history if user is logged
                    history = collection.find_one({"_id":data["id"]})["history"]
                    print(history)
                    history = tolist(str(history))
                    
                    if i in history:
                        # If value in history change its position to be the latest by removing it and appending it again
                        history.remove(i)
                        history.append(i)
                    else:# If not just append it
                        history.append(i)
                    q = {"history":str(history)}
                    
                    collection.update_one({"_id":data["id"]},{"$set":q})
                    data["history"] = q["history"]
                for post in profile.get_posts(): # Loop to get posts
                    print("post number : "+str(a)+" from profile : "+str(i))
                    update.message.reply_text(str(post.url)) # Sending image url
                    if(a == limits-1):
                        break
                    a += 1
    except instaloader.exceptions.ProfileNotExistsException:
        # Profile does not exist exception handler
        update.message.reply_text("This profile does not exists")
        print("Username does not exist")
    except instaloader.exceptions.ProfileHasNoPicsException:
        # Profile Has no pics exception handler
        print("Username does not have pictures")
        update.message.reply_text("This profile does not have any picture")
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        print("Username is a private account")
        update.message.reply_text("This is a private account")
    except Exception:
        raise Exception
def main():
    global DB
    TOKEN = "your telegram bot token"
    PORT = int(os.environ["PORT"]) # !!!!!!!!!!!!!! IF YOU DON'T WANT TO USE HEROKU REMOVE THIS LINE !!!!!!!!!!!!!!!!!!!


    username = "your IG username" # Instagram credentials to avoid redirection to login page problem
    password = "your IG password" 
    loader.login(username,password)
    # create the updater, that will automaticy create also a dispatcher and a queue to 
    # make them dialoge
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # add handlers for start and help commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("create",create))
    dispatcher.add_handler(CommandHandler("login",login))
    dispatcher.add_handler(CommandHandler("logout",logout))
    # add an handler for normal text (not commands)
    dispatcher.add_handler(MessageHandler(Filters.text, text))

    # add an handler for errors
    dispatcher.add_error_handler(error)

    # start your shiny new bot
    #updater.start_webhook(listen="0.0.0.0",port=PORT,
                        url_path=TOKEN,webhook_url="your heroku app URL"+TOKEN,
                        force_event_loop=True) # LEAVE THIS LINE COMMENTED IF YOU ARE NOT ANTENDING TO HEROKU AS A HOSTING PROVIDER
    updater.start_polling() # IF YOU WANT TO LOCALLY HOST THE BOT & COMMENT IT IF THE ABOVE IS YES!!!!!!!!!!!!!!!!!!!!!!
    # run the bot until Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
