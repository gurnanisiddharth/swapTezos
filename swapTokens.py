import smartpy as sp


class ContractLibrary(sp.Contract):

    def TransferTokens(sender, reciever, amount, tokenAddress, id):

        arg = [
            sp.record(
                from_=sender,
                txs=[
                    sp.record(
                        to_=reciever,
                        token_id=id,
                        amount=amount
                    )
                ]
            )
        ]

        transferHandle = sp.contract(
            sp.TList(sp.TRecord(from_=sp.TAddress, txs=sp.TList(sp.TRecord(
                amount=sp.TNat, to_=sp.TAddress, token_id=sp.TNat).layout(("to_", ("token_id", "amount")))))),
            tokenAddress,
            entry_point='transfer').open_some()

        sp.transfer(arg, sp.mutez(0), transferHandle)
    
    def Mint(amount, reciever, tokenAddress, id):

        arg = sp.variant('mint_tokens', [sp.record(
            owner=reciever, amount=amount, token_id=id)])

        transferHandle = sp.contract(
            sp.TVariant(
                burn_tokens=sp.TList(sp.TRecord(owner=sp.TAddress, token_id=sp.TNat, amount=sp.TNat).layout(
                    ("owner", ("token_id", "amount")))),
                mint_tokens=sp.TList(sp.TRecord(owner=sp.TAddress, token_id=sp.TNat, amount=sp.TNat).layout(
                    ("owner", ("token_id", "amount"))))
            ),
            tokenAddress,
            entry_point='tokens').open_some()

        sp.transfer(arg, sp.mutez(0), transferHandle)
    

class Bridge(sp.Contract):
    def __init__(self, _oldTokenAddress, _newTokenAddress, admin, _tokenMapping=sp.map(l={}, tkey=sp.TNat, tvalue=sp.TNat)):
        self.init(
            admin=admin,
            oldTokenAddress=_oldTokenAddress,
            newTokenAddress=_newTokenAddress,
            tokenMapping=_tokenMapping,
            locked=False
        )

    @sp.entry_point
    def swapTokens(self, params):
        sp.set_type(params, sp.TRecord(tokenId=sp.TNat, amount=sp.TNat))
        sp.verify(self.data.tokenMapping.contains(
            params.tokenId), "ErrorMessage.token Not Swapable")
        newTokenId = sp.local(
            'newTokenId', self.data.tokenMapping[params.tokenId])
        ContractLibrary.TransferTokens(
            sp.sender, sp.self_address, params.amount, self.data.oldTokenAddress, params.tokenId)
        ContractLibrary.Mint(params.amount, sp.sender,
                             self.data.newTokenAddress, newTokenId.value)

    @sp.entry_point
    def setAddress(self, params):
        sp.set_type(params, sp.TRecord(
            oldTokenAddress=sp.TAddress, newTokenAddress=sp.TAddress))
        sp.verify(sp.sender == self.data.admin,
                  message="ErrorMessage. Not Admin")
        sp.verify(~self.data.locked, message="ErrorMessage. Already Set")
        self.data.locked = True
        self.data.oldTokenAddress = params.oldTokenAddress
        self.data.newTokenAddress = params.newTokenAddress

    @sp.entry_point
    def addMapping(self, oldTokenId, newTokenId):
        sp.set_type(oldTokenId, sp.TNat)
        sp.set_type(newTokenId, sp.TNat)
        sp.verify(sp.sender == self.data.admin,
                  message="ErrorMessage. Not Admin")
        sp.for x in self.data.tokenMapping.values():
            sp.verify(x != newTokenId,
                      message="ErrorMessage.TokenAlreadyExists")
        sp.verify(~self.data.tokenMapping.contains(oldTokenId),
                  message="ErrorMessage.MappingAlreadyExists")
        self.data.tokenMapping[oldTokenId] = newTokenId
