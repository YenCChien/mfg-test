from pymongo import MongoClient
from bson.objectid import ObjectId

conn = MongoClient("192.168.12.90:27017")

db = conn.config
collection = db.Cal_US

collection.stats

cursor = collection.find({})
data = [d for d in cursor]
print(data)


collection.insert_one({"_id":"999","value":"8888"})
collection.insert_one({"_id":"777","value":"8888"})

{
    "_id" : "6863",
    "MAC" : "F81D0FDA6863",
    "Band" : "1,5-85",
    "5" : "28",
    "10" : "28",
    "20" : "29",
    "30" : "30",
    "40" : "30",
    "50" : "30",
    "60" : "30",
    "70" : "30",
    "80" : "30"
}


i = 2
x['_id'] += '-{}'.format(i)
collection.insert_one()

cursor = collection.find({})
data = [d for d in cursor]

data

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

from pymongo import MongoClient
from bson.objectid import ObjectId

c = Mongodb('192.168.12.90','27017')
c.login_db('AFI')
c.collection('Cal_US')
x = {
    "_id" : "F81D0FDA6863",
    "Band" : "1,5-85",
    "5" : "28",
    "10" : "28",
    "20" : "29",
    "30" : "30",
    "40" : "30",
    "50" : "30",
    "60" : "30",
    "70" : "30",
    "80" : "30"
}