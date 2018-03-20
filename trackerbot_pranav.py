import os
import datetime
import time
import re
import random
import db
import traceback
from slackclient import SlackClient


# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
#EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

COMMAND_RECORD_DOWN = "down"
COMMAND_RECORD_UP = "up"
COMMAND_RECORD_SHOW = "show"
COMMAND_RECORD_REPORT = "report"
COMMAND_RECORD_UPDATE = "update"

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"], event["user"]
    return None, None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel, sender):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    #default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Grab user details
    userInfo = slack_client.api_call(
         "users.info",
         user=sender
    )

    if userInfo["ok"] == True:
        userDisplayName = userInfo["user"]["profile"]["display_name"] or userInfo["user"]["name"] or "Unknown Sender"
        userTimezoneOffset = userInfo["user"]["tz_offset"] or 36000
        userTimezoneName = userInfo["user"]["tz_label"] or "Australian Eastern Standard Time"
    else:
        userDisplayName = "Unknown Sender"
        userTimezoneOffset = 36000
        userTimezoneName = "Australian Eastern Standard Time"

    # Get current timestamp for db and display uses
    currentUTCTime, displayTime = getCurrentTime(userTimezoneOffset)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!

    try:
        commandWord = command.lower().split(' ', 1)[0]
        # For command = down
        if commandWord == COMMAND_RECORD_DOWN:
            splittedMessage = command.split(' ', 2)
            feature = splittedMessage[1].upper()
            reason = splittedMessage[2]

            activeDowns = db.getActiveDowns(feature)

            if (len(activeDowns) > 0):
                response = userDisplayName + ", *" + feature + "* is already down since *" + getCurrentTime(userTimezoneOffset, activeDowns[0][3])[1] + "* (" + userTimezoneName + ") by *" + activeDowns[0][1] + "* due to *" + activeDowns[0][2] + "*"
            else:
                db.recordDown(userDisplayName, feature, currentUTCTime, reason)
                response = userDisplayName + " declared *" + feature + "* as *DOWN* as of " + displayTime + " " + userTimezoneName + " due to *" + reason + "*.\n" + makeRandomAnnouncement(COMMAND_RECORD_DOWN)

        # For command = up
        elif commandWord == COMMAND_RECORD_UP:
            splittedMessage = command.split(' ', 2)
            feature = splittedMessage[1].upper()

            activeDowns = db.getActiveDowns(feature)

            if (len(activeDowns) == 0):
                response = userDisplayName + ", *" + feature + "* is not down. It needs to be down first."
            elif(len(activeDowns) != 1):
                response = userDisplayName + ", *" + feature + "* has multiple active outages. This shouldn't have happened :( please let Pranav know."
            else:
                outageid = activeDowns[0][4]
                db.recordUp(outageid, currentUTCTime)
                response = userDisplayName + " declared *" + feature + "* as *UP* as of " + displayTime + " " + userTimezoneName + ".\n" + makeRandomAnnouncement(COMMAND_RECORD_UP)

        # For command = update
        elif commandWord == COMMAND_RECORD_UPDATE:
            splittedMessage = command.split(' ', 2)
            feature = splittedMessage[1].upper()
            reason = splittedMessage[2]

            activeDowns = db.getActiveDowns(feature)

            if (len(activeDowns) == 0):
                response = userDisplayName + ", *" + feature + "* is not down. It needs to be down first."
            elif(len(activeDowns) != 1):
                response = userDisplayName + ", *" + feature + "* has multiple active outages. This shouldn't have happened :( please let Pranav know."
            else:
                outageid = activeDowns[0][4]
                db.recordUpdate(outageid, reason)
                response = userDisplayName + " updated the reason of *" + feature + "*: " + reason 
        
        # For command = report
        elif commandWord == COMMAND_RECORD_REPORT:
            splittedMessage = command.split(' ', 4)
            feature = splittedMessage[1].upper()
            startTime = splittedMessage[2] + " " + splittedMessage[3]
            endTime = splittedMessage[4] + " " + splittedMessage[5]
            reason = splittedMessage[6]

            activeDowns = db.getActiveDowns(feature)
        
            if(len(activeDowns) > 0):
                response = userDisplayName + ", *" + feature + "* is already down since *" + getCurrentTime(userTimezoneOffset, activeDowns[0][3])[1] + "* (" + userTimezoneName + ") by *" + activeDowns[0][1] + "* due to *" + activeDowns[0][2] + "*"
            else:
                db.recordReport(userDisplayName, feature, getUTCTime(userTimezoneOffset, startTime)[1], getUTCTime(UserTimezoneOffset, endTime)[1],reason)
                response = userDisplayName + " recorded *" + feature + "* as down from *" + startTime + "* to *" + endTime + "* due to *" + reason + "*.\n" + makeRandomAnnouncement(COMMAND_RECORD_REPORT)
            print (response)

            # response = userDisplayName + " reported *" + feature + "* as down from *" + startTime + "* to *" + endTime + "* due to " + reason + ". However, I haven't been trained on how to take a report yet. "

        elif commandWord == COMMAND_RECORD_SHOW:
            splittedMessage = command.split(' ', 2)
            feature = splittedMessage[1].upper()

            response = userDisplayName + ", I understand you want data for " + feature + ", but I don't know how to show anything yet."

    except Exception as inst:
         response = userDisplayName + ", your command is incorrect."


    #if command.startswith(EXAMPLE_COMMAND):
    #    response = "Sure Pranav...write some more code then I can do that!"

    # Sends the response back to the channel
    sendMessage(response, channel)

def sendMessage(message, channel):
    default_response = "What do you mean?"

    return slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=message or default_response
    )

def validateInput(input):
    return ""

def outputReason(input):
    return "This is due to " + input

def getCurrentTime(displayOffset, inputTime = datetime.datetime.utcnow()):
    inputTime = inputTime.replace(microsecond=0)
    displayTime = inputTime + datetime.timedelta(seconds=displayOffset)
    return inputTime, str(displayTime.year).zfill(4) + "/" + str(displayTime.month).zfill(2) + "/" + str(displayTime.day).zfill(2) + " " + str(displayTime.hour).zfill(2) + ":" + str(displayTime.minute).zfill(2)

def getUTCTime ( displayOffset, inputTime):
    inputTime = inputTime.replace(mirosecond=0)
    UTCTime = inputTime - datetime.timedelta(seconds=displayOffset)
    return inputTime, str(UTCTime.year).zfill(4) + "/" + str(UTCTime.month).zfill(2) + "/" + str(UTCTime.day).zfill(2) + " " + str(UTCTime.hour).zfill(2) + ":" + str(UTCTime.minute).zfill(2)

def makeRandomAnnouncement(status):
    if (status == COMMAND_RECORD_DOWN):
	list = [
		"Please remain calm and listen to instructions from the crew.",
		"Time to panic."
    	]
    elif (status == COMMAND_RECORD_UP):
        list = [
                "Time for some beers.",
                "Time to celebrate.",
                "Woohoo! Congratulations on fixing the issue."
        ]
    elif (status == COMMAND_RECORD_UPDATE):
       list = [
                "Please keep me updated on any further changes.",
                "Let me know if I need to ask Karthick to escalate"
        ]
    else:
       list = [
		"Okay."
	]

    return random.choice(list)

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel, sender = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel, sender)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
