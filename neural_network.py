'''
Created on Feb 29, 2016
@author: hanhanwu
'''
from sqlite3 import dbapi2 as sqlite
from sets import Set


class onehidden_nn:
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)
        
        
    def __del__(self):
        self.con.close()
        
        
    def create_tables(self):
        self.con.execute('drop table if exists hidden_node')
        self.con.execute('drop table if exists input_hidden')
        self.con.execute('drop table if exists hidden_output')
        
        self.con.execute('create table hidden_node(create_key)')
        self.con.execute('create table input_hidden(fromid, toid, strength)')
        self.con.execute('create table hidden_output(fromid, toid, strength)')
        
        self.con.execute('create index if not exists hidden_nodeidx on hidden_node(create_key)')
        self.con.execute('create index if not exists ih_fromidx on input_hidden(fromid)')
        self.con.execute('create index if not exists ih_toidx on input_hidden(toid)')
        self.con.execute('create index if not exists ho_fromidx on hidden_output(fromid)')
        self.con.execute('create index if not exists ho_toidx on hidden_output(toid)')
        self.con.commit()
        
    
    # get the strength of a connection in input_hidden table or hidden_output table
    def get_strength(self, fromid, toid, layer):
        if layer == 0: tb = 'input_hidden'
        else: tb = 'hidden_output'
        
        cur = self.con.execute("""
        select strength from %s where fromid=%d and toid=%d
        """ % (tb, fromid, toid)).fetchone()
        if cur == None:
            if layer == 0: return -0.2
            elif layer == 1: return 0
        return cur[0]
    
    
    # if the connection exists, update the strength, otherwise insert a new connection with the strength value
    def set_strength(self, fromid, toid, layer, new_strength):
        if layer == 0: tb = 'input_hidden'
        else: tb = 'hidden_output'
        
        cur = self.con.execute("""
        select strength from %s where fromid=%d and toid=%d
        """ % (tb, fromid, toid)).fetchone()
        if cur == None:
            self.con.execute("""
            insert into %s (fromid, toid, strength) values (%d,%d,%f)
            """ % (tb, fromid, toid, new_strength))
        else:
            self.con.execute("""
            update %s set strength=%f where rowid=%d
            """ % (tb, new_strength, cur[0]))
        self.con.commit()
        
        
    def create_hidden_node(self, words, urls):
        if len(words) > 3: return
        create_key = '_'.join(sorted([str(wid) for wid in words]))
        cur = self.con.execute("""
        select rowid from hidden_node where create_key='%s'
        """ % create_key).fetchone()
        
        if cur == None:
            cur = self.con.execute("""
            insert into hidden_node (create_key) values ('%s')
            """ % create_key)
            hidden_id = cur.lastrowid
        else:
            hidden_id = cur[0]
        for wid in words:
            self.set_strength(wid, hidden_id, 0, 1.0/len(words))
        for uid in urls:
            self.set_strength(hidden_id, uid, 1, 0.1)
        self.con.commit()
        
    
    # using the input or output ids to find the hidden nodes    
    def find_hidden_nodes(self, words, urls):
        hidden_nodes = Set()
        for wid in words:
            for (hidden_node,) in self.con.execute('select toid from input_hidden where fromid=%d' % wid):
                hidden_nodes.add(hidden_node)
        for uid in urls:
            for (hidden_node,) in self.con.execute('select fromid from hidden_output where toid=%d' % uid):
                hidden_nodes.add(hidden_node)
        return list(hidden_nodes)
    
    
    # setup neural network
    def setup_nn(self, words, urls):
        self.words = words
        self.urls = urls
        self.hidden_nodes = self.find_hidden_nodes(words, urls)
        
        self.li = [1.0]*len(self.words)
        self.lo = [1.0]*len(self.urls)
        self.lh = [1.0]*len(self.hidden_nodes)
        
        # build the weight matrix for input_hidden and hidden_output
        self.w_ih = [[self.get_strength(wid, hid, 0) for hid in self.hidden_nodes] for wid in self.words]
        self.w_ho = [[self.get_strength(hid, uid, 1) for uid in self.urls] for hid in self.hidden_nodes]
            


def main():
    dbname = 'neural_network.db'
    my_nn = onehidden_nn(dbname)
    my_nn.create_tables()
    
    wApple, wPhone, wRose = 101, 102, 103
    wApplePhone, wRoseGold, wPhone, wBanana = 201, 202, 203, 204
    
    my_nn.create_hidden_node([wApple, wPhone], [wApplePhone, wRoseGold, wPhone, wBanana])
    print 'input_hidden:'
    for cont in my_nn.con.execute('select * from input_hidden'):
        print cont
    print 'hidden_output:'
    for cont in my_nn.con.execute('select * from hidden_output'):
        print cont
    
if __name__ == '__main__':
    main()
