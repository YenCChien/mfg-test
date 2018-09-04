from pymongo import MongoClient
from bson.objectid import ObjectId

class Mongodb:
    def __init__(self, ip, port):
        self.conn = MongoClient("{0}:{1}".format(ip,port))
        try:
            info = self.conn.server_info()
        except Exception as err:
            raise Exception(err)
        else:
            for msg in info:
                print('{0}:{1}'.format(msg,info[msg]))
    def login_db(self, name):
        self.db = eval('self.conn.'+name)
        print(self.db)
    def logout_db(self):
        self.db.logout()
    def collection(self, name):
        self.tb = eval('self.db.'+name)
    def find(self, key=None, value=None):
        return self.tb.find_one({key: value})
    def insert(self, dic):
        if self.find('_id',dic['_id']):
            i = 0
            while True:
                i+=1
                if not self.find('_id',dic['_id']+'-{}'.format(i)):
                    dic['_id'] = dic['_id']+'-{}'.format(i)
                    self.tb.insert_one(dict([(k,dic[k]) for k in sorted(dic.keys())]))
                    break
        else:
            self.tb.insert_one(dict([(k,dic[k]) for k in sorted(dic.keys())]))
    def close(self):
        self.conn.close()

def saveDB(db, table, data, server, port=27017):
    c = Mongodb(server,port)
    c.login_db(db)
    c.collection(table)
    c.insert(data)
    c.close
    # x = {
    #     "_id" : "F81D0FDA6863",
    #     "Band" : "1,5-85",
    #     "5" : "28",
    #     "10" : "28",
    #     "20" : "29",
    #     "30" : "30",
    #     "40" : "30",
    #     "50" : "30",
    #     "60" : "30",
    #     "70" : "30",
    #     "80" : "30"
    # }
