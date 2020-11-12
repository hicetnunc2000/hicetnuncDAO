
# @hicetnunc2000 hicetnuncDAO

import smartpy as sp
FA2 = sp.import_template("FA2.py")

class hicetnuncDAO(sp.Contract):
    def __init__(self):
        self.init_type(sp.TRecord(
            achieved = sp.TMutez,
            meta = sp.TString,
            protocol = sp.TAddress,
            admin = sp.TAddress,
            oracle = sp.TAddress,
            token_id = sp.TNat,
            goal = sp.TMutez,
            time_lock = sp.TTimestamp
            ))
        self.init(
            achieved = sp.tez(0), 
            goal = sp.tez(0),
            meta = 'QmcBXzLWiBGpQtiZRtK4D486xkEpdCXc4QDoX3WMGARmG1',
            protocol = sp.address('tz1'),
            admin = sp.address('tz1'),
            oracle = sp.address('tz1'),
            token_id = sp.nat(1),
            time_lock = sp.timestamp(0)
            )    

    @sp.entry_point
    def contribute(self, params):
        sp.verify(sp.amount > sp.tez(1)) # minimal contribution
        sp.verify(sp.sender != self.data.admin)
        
        self.data.achieved += sp.amount
        
        amount = sp.local("", sp.fst(sp.ediv(sp.amount, sp.mutez(1)).open_some()))
        c = sp.contract(sp.TRecord(
            address=sp.TAddress,
            amount=sp.TNat,
            token_id=sp.TNat
            ), self.data.protocol, entry_point = "mint_hicetnuncDAO").open_some()
        sp.transfer(sp.record(
            address=sp.sender,
            amount=amount.value,
            token_id=self.data.token_id
            ), sp.mutez(0), c)
    
    #in case the protocol?/oracle? is updated    
    @sp.entry_point
    def update_oracle(self, params):
        sp.verify((sp.sender == self.data.oracle) | (sp.sender == self.data.admin))
        self.data.oracle = params

    @sp.entry_point
    def update_meta(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.meta = params
        
    #oracle/admin staking
    @sp.entry_point
    def set_baker(self, params):
        sp.verify((sp.sender == self.data.oracle) | (sp.sender == self.data.admin))

        sp.set_delegate(sp.some(params))
        
        
    @sp.entry_point
    def withdraw(self, params):
        sp.verify(sp.sender == self.data.admin) # comment for testing
        sp.verify(sp.now > self.data.time_lock) # comment for testing
        sp.send(params.address, params.amount, message = None)
        #self.data.time_lock = (sp.now).add_days(45)
        
class hicetnunc_protocol(sp.Contract):
    def __init__(self, fa2, oracle):
        self.created = hicetnuncDAO()
        self.kt = sp.address('tz1')
        self.tk = 0
        self.init(
            fa2 = fa2,
            oracle = oracle,
            hicetnuncDAOs = sp.big_map(tkey=sp.TAddress, tvalue=sp.TNat),
            tk_counter = sp.nat(1)
            )
            
    @sp.entry_point
    def originate_hicetnuncDAO(self, params):
        
        sp.verify(sp.tez(params.goal) > sp.tez(20))
        
        self.tk = self.data.tk_counter
        
        self.kt = sp.some(
            sp.create_contract(
                storage = sp.record(
                    achieved = sp.tez(0), 
                    goal = sp.tez(params.goal),
                    meta = params.meta,
                    protocol = sp.to_address(sp.self),
                    admin = params.address,
                    oracle = self.data.oracle,
                    token_id = self.tk,
                    time_lock = (sp.now).add_days(40)
                    ), contract = self.created)).open_some()
                    
        #there is the possibility of setting randomly the baker also at the creation of the contract such module is being developed and should be known as random bridge
        
        self.data.hicetnuncDAOs[self.kt] = self.tk
        self.data.tk_counter += 1
        
    @sp.entry_point
    def mint_hicetnuncDAO(self, params):
        
        sp.verify(self.data.hicetnuncDAOs[sp.sender] == params.token_id)

        record = sp.local('', params)
        c = sp.contract(
            sp.TRecord(
            address=sp.TAddress,
            amount=sp.TNat,
            token_id=sp.TNat,
            symbol=sp.TString
            ), 
            self.data.fa2, 
            entry_point = "mint").open_some()
            
        sp.transfer(
            sp.record(
            address=params.address,
            amount=params.amount,
            token_id=params.token_id,
            symbol='hicetnuncDAO'
            ), 
            sp.mutez(0), 
            c)
            
    #update oracle
    @sp.entry_point
    def update_oracle(self, params):
        sp.verify(sp.sender == self.data.oracle)
        self.data.oracle = params

class hicetnunc_oracle(sp.Contract):
    def __init__(self, admin):
        self.init(
            hicetnunc_protocol = sp.address('tz1'),
            admin = admin
            )
    
    @sp.entry_point
    def update_admin(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.admin = params

    @sp.entry_point
    def update_oracle_protocol(self, params):
        sp.verify(sp.sender == self.data.admin)
        c = sp.contract(sp.TAddress, self.data.hicetnunc_protocol, entry_point="update_oracle").open_some()
        sp.transfer(params, sp.mutez(0), c)
        
    @sp.entry_point
    def set_baker_hicetnuncDAO(self, params):
        sp.verify(sp.sender == self.data.admin)
        c = sp.contract(sp.TKeyHash, params.hicetnuncDAO, entry_point="set_baker").open_some()
        sp.transfer(params.baker, sp.mutez(0), c)
    
    # such is a upgradable oracle, which intends to get random bakers for hicetnuncDAOs with oracle_staking_rights = True
    