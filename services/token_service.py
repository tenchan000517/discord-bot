# services/token_service.py
from web3 import Web3
from decimal import Decimal
import json
import os

class TokenService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_RPC_URL')))
        self.contract_address = os.getenv('TOKEN_CONTRACT_ADDRESS')
        self.private_key = os.getenv('WEB3_PRIVATE_KEY')
        
        # コントラクトABIの読み込み
        with open('contracts/token_abi.json', 'r') as f:
            self.contract_abi = json.load(f)
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
        
        self.conversion_rate = Decimal('0.1')  # 1ポイント = 0.1トークン

    async def transfer_tokens(self, recipient: str, points: int) -> str:
        """トークンを転送"""
        # ポイントからトークン量を計算
        token_amount = Decimal(str(points)) * self.conversion_rate
        
        # Wei単位に変換（18桁）
        amount_in_wei = int(token_amount * Decimal('1e18'))
        
        # トランザクションの構築
        nonce = self.w3.eth.get_transaction_count(self.w3.eth.account.from_key(self.private_key).address)
        
        txn = self.contract.functions.transfer(
            recipient,
            amount_in_wei
        ).build_transaction({
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # トランザクションの署名と送信
        signed_txn = self.w3.eth.account.sign_transaction(txn, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # トランザクションの完了を待機
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt.transactionHash.hex()