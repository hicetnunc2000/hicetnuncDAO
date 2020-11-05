
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
            time_lock = sp.TTimestamp,
            oracle_staking_rights = sp.TBool
            ))
        self.init(
            achieved = sp.tez(0), 
            goal = sp.tez(0),
            meta = 'QmcBXzLWiBGpQtiZRtK4D486xkEpdCXc4QDoX3WMGARmG1',
            protocol = sp.address('tz1'),
            admin = sp.address('tz1'),
            oracle = sp.address('tz1'),
            token_id = sp.nat(1),
            time_lock = sp.timestamp(0),
            oracle_staking_rights = True
            )    


    @sp.entry_point
    def contribute(self, params):
        sp.verify(sp.amount > sp.tez(1))
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
        sp.verify(((sp.sender == self.data.oracle) | (sp.sender == self.data.admin)) & (self.data.oracle_staking_rights == False))
        self.data.oracle = params

    @sp.entry_point
    def update_meta(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.meta = params
        
    #oracle/admin staking
    @sp.entry_point
    def set_baker(self, params):
        sp.verify(((sp.sender == self.data.oracle) & (self.data.oracle_staking_rights == True)) | (sp.sender == self.data.admin))

        sp.set_delegate(sp.some(params))
        
        sp.if (sp.sender == self.data.admin):
            self.data.oracle_staking_rights = False
        
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
        self.init(
            fa2 = fa2,
            oracle = oracle,
            hicetnuncDAOs = sp.big_map(tkey=sp.TAddress, tvalue=sp.TNat),
            tk_counter = sp.nat(1)
            )
            
    @sp.entry_point
    def originate_hicetnuncDAO(self, params):
        
        sp.verify(sp.tez(params.goal) > sp.tez(20))
        
        tk = sp.local('', self.data.tk_counter)
        
        self.kt = sp.some(
            sp.create_contract(
                storage = sp.record(
                    achieved = sp.tez(0), 
                    goal = sp.tez(params.goal),
                    meta = params.meta,
                    protocol = sp.to_address(sp.self),
                    admin = params.address,
                    oracle = self.data.oracle,
                    token_id = tk.value,
                    time_lock = (sp.now).add_days(38),
                    oracle_staking_rights = True
                    ), contract = self.created)).open_some()
                    
        #there is the possibility of setting randomly the baker also at the creation of the contract such module is being developed and should be known as random bridge
        
        self.data.hicetnuncDAOs[self.kt] = tk.value
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


# https://www.smartpy.io/dev/index.html?code=eJy1WXtv2zYQ_9@fgrOBWUINN3bSoSjgdWm7dkDXDu0CtFhRCLRE24IlURDppA724Xd8SaRMySqaCcjD4pH3vvsdPZqg33ZpTHhxKOLlxcUFqj@9uv5rNErzklYcsRxXvDwizBArR6@vl2gF_8zVasRJXmaYk2AMK_PyOA5HozjDjDmHBbDhJS14hWMePhsheBKyQVGUFimPooCRbKPfi0d8nMslfiyJ2HzzkcS0SoKaRDw43qXkliRKoJt3B07uZw5FTjjWq3_zKi227nJZUU5jmmmS6ySpCGMuDU7ytOgjoKBURvooON2TIkqNnO8xd9e3FGfdOvA0J1FG470muYHPjOO89IkRwcoe9IyqdLvjTG95QWnmEIfhqa37bAtCBRfhDHWIrZd9pp9@yOMXn@___JS@eFN@4Ok_H_nbq1dXT3_5tv@9TF5@jq8@vKKfLz@9e3P9MX@zmPY5CCvjBlN@v5iGnW7qI7Od1UfnuqzAPFi0KVy3cOOVE0N0OeamOhDXKeLXaCTf_QZHEsiXY1TStOB1xsQiidI1RInMmRkqcYVzZudOOb8lVbo5irTBOT0UHP1qnLSwHW8TMlIkpEI_rVQ8JJjjuTRpQ@9GjKIwQfJIGVRyO92gpZA0YDGcBePxTHzYMC6YkyS9baSVK_lBizunJTiC0ZwEoSV8rE6LdU3pLhHKx6vu9JY8V968NEFgVl1vzSxDmDidIctpIOIYLMgjuxKOHY1sZ4AiBduQSuhS9auivOVVRP2Z3@LsQLq0qcU2r04UMw4QOR8rKeWvCeRYjBlBfEfq5Hz@WIX4c5QydCjhZIgIs6MrkBVdpHaej@XACtKVHaTqgBD9i7ooVBiH6GcUtLedJOUKvcYZI@3yaG0Bpyox@_NUqyeK4KBE7RbcI4kurVoOs64cpKR8rMqhVq9XUkZ4tMZ7EXc_7IRhJhaFLxzgsZEtghAzIRnZCqwhPov80bL6ahQAlM0ZBs@csD8ruAoNl1WXUe9SvksqfPeDvkcTKPh5DhzQhlaIQ4cx7jw5paB3os43uW3604BThATamKYrGqHrogztjeGtiP_3tCCNyScelkCkRQrFeVGCjyy4emL5qQURI1NLhgDFGdrg5Uz31TZqjCsi68_KxZ@tNNpzHwQ4h4mALWwTzP2YQv3jLtpSaDi2TrdRjsuA78nRaUyIy7Jt2k0bcOyjWLhChEoDStzS7XzqjVAKYZ0Woka5ON0fr_6QEx1CR4nAgmGDM5YXvqTkexsDTKd2B22060Icxmcy893ULbXboxoPOOuShoN3thr5@dqreQYAX_O4ANi2xMxL79RtWcX9dC7q5TQyYSpTFSYl_zYDgVuJ7KVtcHCr7PnJLTjM9z5wURP2loDLpx2iD8bI5hG4RPvaKKEzP_QDLPtpahfAmIoI2CLxDGUsXadZyo@IysYo6iQCWJbQPDtKGtkpETQCijCXbyTblBZii_xsxGKHeIdymhwyyWFNxGEJhFYG8iUITkVsRw9ZAktoD4YqxIituKF1lSZb0pEJ0l1OYfmiM@Sr5SDPHquEAGJfDOtlJxD2e4pEl7im630VbU8HrAkyq_GrRG1XDc25cxhoF4f_fzJwV9kxX9Ns1dw6tPF1B_CQbc1Z80wTHQNE2wH1NNE2Rt9o0Vc5tDlcVOA3SsufXuNM7YCY9hvInkacldij_0RBb11SHnIG6Qe_QyaGNuoxnIdgnjZm7cAop5Bq@N2J_OsBFEOMKPc@_Kjj9rRBM5fuJQ2ifBiZfDcONXDz1LnIeyewGjtSDrgNUIL7Z_KzzqmHu0EF_CFM8pYc_8BsV48PNt@WJWrhBlthLsn77idU14V2iyEcthVO8DoztWCG7kAaWIUGWCTQ8ynaEl53XHE0kxOSi9nFLNcPUEYwao7NRTgbo4JyYAIJXGBAQ9Gz2kUCCInxKxALoqC7N0O12ySN7ZiYFLhKqQGbjEfmVWB1S_tyUxLhWLb7YHppDTcHRqqFj@iJTVX_o4YecbkPP4H4S4rbtKKFGCgF4N6k2yA045ipM2LohDHRIBxdkwU@EufJOEoZeBdQuTT5t@M9mAAlhzw_usujUys8kkPYqajxwh77mgoAxM1Y25JzoI3bVPPdIvB5z6EB5e@CL4rh19CvSNygsIn7fu62J4@kiqxjkjM93dV3JoeQ1XffystZZ3V1Ec6rgyjzojas2p1v0vKQvLRxnBmAvMbyg0@CPSmEHCe1TjKET1UaKGbDBYmyw@ihionMOYaO9IDyA@PmxuQxWFPfnYjqJOcCUyWbuFv2XDfYiiw7FFwaX9chO9BO_rh8WX9JMO4h1ZytbxQ8rGYWDO4e7B3un_TdF1TUDBdgWaWbJ0HaiRxfOvmrA_9swgo9Ljtezzs6oHwllNqTY7SDhtVmM3McuoqXpwK0fdgEU9RcqipGrcOHh_5yXl8ldiW066Cr8HtO70q4bh1lsQmsFEJnr0wmyHqarwWtr_ocCgu3NlnQQWvgYcsmfuLWPd1ZaqGpucsQfd4CzTaldTfS2M0hgdL_H3S@Htc-
