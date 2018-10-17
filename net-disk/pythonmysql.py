import pymysql as pm

class MysqlPython(object):

    def __init__(self, database, host='localhost', user='root'
                 , password='123456', port=3306, charset='utf8'):
        # 连接数据库需要的属性
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.charset = charset
        self.database = database
        # self.db = pm.connect(host=self.host, user=self.user, port=self.port, database=self.database,
        #                      password=self.password, charset=self.charset)
        # self.cur = self.db.cursor()

    def open(self):
        self.db = pm.connect(host=self.host, user=self.user, port=self.port, database=
        self.database, password=self.password, charset=self.charset)
        self.cur = self.db.cursor()

    def close(self):
        self.cur.close()
        self.db.close()

    def zhixing(self, sql, L = None):
        try:
            self.open()
            self.cur.execute(sql, L)
            self.db.commit()
            print('ok')
        except Exception as e:
            self.db.rollback()
            print("Error", e)
        self.close()

    def select_all(self, sql, L=None):
        try:
            self.open()
            self.cur.execute(sql, L)
            result = self.cur.fetchall()
            return result
        except Exception as e:
            print("ERROR", e)
        self.close()

