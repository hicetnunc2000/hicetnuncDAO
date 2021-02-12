import smartpy as sp

class hDAO(sp.Contract):
    def __init__(self, objkt, ung, manager, metadata):
        self.init(
            swaps = sp.big_map(tkey=sp.TNat, tvalue=sp.TRecord(issuer=sp.TAddress, ung_per_objkt=sp.TNat, objkt_id=sp.TNat, objkt_amount=sp.TNat)),
            swap_id = 0,
            objkt_id = 0,
            objkt = objkt,
            ung = ung,
            manager = manager,
            balance = sp.tez(0),
            metadata = metadata
            )
        
    @sp.entry_point
    def default(self, params):
        pass
    
    @sp.entry_point
    def swap(self, params):
        sp.verify(params.objkt_amount > 0)
        self.fa2_transfer(self.data.objkt, sp.sender, sp.to_address(sp.self), params.objkt_id, params.objkt_amount)
        self.data.swaps[self.data.swap_id] = sp.record(issuer=sp.sender, objkt_id=params.objkt_id, objkt_amount=params.objkt_amount, ung_per_objkt=params.ung_per_objkt)
        self.data.swap_id += 1
        
    @sp.entry_point
    def collect(self, params):
        sp.verify(params.objkt_amount > 0)
        self.fa2_transfer(self.data.ung, sp.sender, self.data.swaps[params.swap_id].issuer, 1, self.data.swaps[params.swap_id].ung_per_objkt * params.objkt_amount)
        self.fa2_transfer(self.data.objkt, sp.to_address(sp.self), sp.sender, self.data.swaps[params.swap_id].objkt_id, params.objkt_amount)
        self.data.swaps[params.swap_id].objkt_id = abs(self.data.swaps[params.swap_id].objkt_id - params.objkt_amount)
        
        sp.if (self.data.swaps[params.swap_id].objkt_amount == 0):
            del self.data.swaps[params.swap_id]
        
    @sp.entry_point
    def cancel_swap(self, params):
        sp.verify(sp.sender == self.data.swaps[params].issuer)
        self.fa2_transfer(self.data.objkt, sp.to_address(sp.self), sp.sender, self.data.swaps[params].objkt_id, self.data.swaps[params].objkt_amount)
        del self.data.swaps[params]
    
    @sp.entry_point
    def set_baker(self, params):
        sp.verify((sp.sender == self.data.manager))
        sp.set_delegate(sp.some(params))
        
    @sp.entry_point
    def management_rewards(self, params):
        sp.verify(sp.sender == self.data.manager)
        sp.send(sp.sender, sp.balance - self.data.balance)
        
    @sp.entry_point
    def mint_OBJKT(self, params):
        sp.verify(params.amount > 0)
        sp.set_type(params, sp.TRecord(address=sp.TAddress, amount=sp.TNat, metadata=sp.TMap(sp.TString, sp.TBytes)))
        c = sp.contract(
            sp.TRecord(
            address=sp.TAddress,
            amount=sp.TNat,
            token_id=sp.TNat,
            token_info=sp.TMap(sp.TString, sp.TBytes)
            ), 
            self.data.objkt, 
            entry_point = "mint").open_some()
            
        sp.transfer(
            sp.record(
            address=params.address,
            amount=params.amount,
            token_id=self.data.objkt_id,
            token_info=params.metadata
            ), 
            sp.mutez(0), 
            c)
        
        self.data.objkt_id += 1
    
    @sp.entry_point
    def join_hDAO(self, params):
        sp.verify((sp.amount > sp.mutez(0)) & (sp.balance < sp.tez(730000)))
        
        c = sp.contract(
            sp.TRecord(
            address=sp.TAddress,
            amount=sp.TNat,
            token_id=sp.TNat,
            token_info=sp.TMap(sp.TString, sp.TBytes)
            ), 
            self.data.ung, 
            entry_point = "mint").open_some()
            
        sp.transfer(
            sp.record(
            address=sp.sender,
            amount=sp.fst(sp.ediv(sp.amount, sp.mutez(1)).open_some()),
            token_id=1,
            token_info={"": sp.pack("ipfs://QmS87PA42aKj6WgPM1vQMHxyavKJkswa5ycgAn1wbSrNgi")}
            ), 
            sp.mutez(0), 
            c)
        
        self.data.balance += sp.amount
    
    @sp.entry_point
    def leave_hDAO(self, params):
        #sp.verify( self.data.auth.get(sp.sender, False ) )
        self.fa2_transfer(self.data.ung, sp.sender, sp.to_address(sp.self), 1, params)
        sp.send(sp.sender, sp.mutez(params))
        self.data.balance -= sp.mutez(params) 

    def fa2_transfer(self, fa2, from_, to_, objkt_id, objkt_amount):
        c = sp.contract(sp.TList(sp.TRecord(from_=sp.TAddress, txs=sp.TList(sp.TRecord(amount=sp.TNat, to_=sp.TAddress, token_id=sp.TNat).layout(("to_", ("token_id", "amount")))))), fa2, entry_point='transfer').open_some()
        sp.transfer(sp.list([sp.record(from_=from_, txs=sp.list([sp.record(amount=objkt_amount, to_=to_, token_id=objkt_id)]))]), sp.mutez(0), c)
