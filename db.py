import MySQLdb



db = MySQLdb.connect(host="downtimetracker.calpfalrvyri.us-east-1.rds.amazonaws.com", user="Roadster",passwd="Roadster",db="Downtime")

def recordDown(reporter, feature, timestamp, reason):
    cur = db.cursor()
    try:
        cur.execute('''INSERT INTO FeatureList (Username, FeatureNumber, Down, Reason) values (%s, %s, %s, %s)''', (reporter, feature, timestamp, reason))
        db.commit()
        return True
    except:
        db.rollback()
        return False
    return status

def recordUp(outageid, timestamp):
    cur = db.cursor()
    try:
        cur.execute('''UPDATE FeatureList SET Up = %s WHERE ID = %s''', (timestamp, outageid))
        db.commit()
        return True
    except:
	db.rollback()
        return False

def recordUpdate(outageid, reason):
    cur = db.cursor()
    try:
        cur.execute('''UPDATE FeatureList SET Reason = %s WHERE ID = %s''', (reason, outageid))
        db.commit()
        return True
    except:
	db.rollback()
        return False

def recordReport(reporter, feature, startTime, endTime, reason):
    cur = db.cursor()
    try:
        cur.execute('''insert into FeatureList (Username, FeatureNumber, Down, Up, Reason) values (%s, %s, %s, %s, %s)''', (reporter, feature, startTime, endTime, reson))
        db.commit()
        print("success")
        return True
    except:
        print("fail")
        db.rollback()
        return False()


def getActiveDowns(feature):
    cur = db.cursor()
    #try:
    cur.execute('''SELECT FeatureNumber, Username, Reason, Down, ID FROM FeatureList WHERE FeatureNumber=%s AND Up IS NULL''', (feature))
    results = cur.fetchall()

    return results
    #except:
    #return ""
