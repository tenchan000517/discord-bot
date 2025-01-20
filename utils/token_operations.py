from typing import Optional, Dict, Any
import json
import logging
from web3 import Web3
from eth_account.messages import encode_defunct
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger(__name__)

class TokenOperations:
    def __init__(self, dynamodb=None):
        """
        トークン操作のユーティリティクラス
        Args:
            dynamodb: boto3のDynamoDBリソース（テスト用にモック可能）
        """
        if dynamodb is None:
            self.dynamodb = boto3.resource('dynamodb')
        else:
            self.dynamodb = dynamodb
        
        self.settings_table = self.dynamodb.Table('ServerSettings')
        self._load_contract_abi()

    def _load_contract_abi(self) -> None:
        """コントラクトABIの読み込み"""
        try:
            with open('contracts/token_abi.json', 'r') as f:
                self.token_abi = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load token ABI: {str(e)}")
            raise

    async def get_token_settings(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        サーバーのトークン設定を取得
        Args:
            server_id: DiscordサーバーID
        Returns:
            Optional[Dict[str, Any]]: トークン設定または None
        """
        try:
            response = self.settings_table.get_item(
                Key={
                    'serverId': server_id,
                    'type': 'token_settings'
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Failed to get token settings: {str(e)}")
            return None

    async def update_token_settings(
        self, 
        server_id: str, 
        network_id: int,
        contract_address: str,
        token_symbol: str,
        decimals: int
    ) -> bool:
        """
        トークン設定の更新
        Args:
            server_id: DiscordサーバーID
            network_id: ネットワークID
            contract_address: トークンコントラクトアドレス
            token_symbol: トークンシンボル
            decimals: デシマル数
        Returns:
            bool: 更新成功したかどうか
        """
        try:
            self.settings_table.put_item(
                Item={
                    'serverId': server_id,
                    'type': 'token_settings',
                    'networkId': network_id,
                    'contractAddress': Web3.to_checksum_address(contract_address),
                    'tokenSymbol': token_symbol,
                    'decimals': decimals,
                    'enabled': True
                }
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to update token settings: {str(e)}")
            return False

    def create_contract(self, web3: Web3, contract_address: str):
        """
        コントラクトインスタンスの作成
        Args:
            web3: Web3インスタンス
            contract_address: コントラクトアドレス
        Returns:
            Contract: コントラクトインスタンス
        """
        return web3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=self.token_abi
        )

    async def get_balance(
        self, 
        web3: Web3,
        contract_address: str,
        wallet_address: str
    ) -> Optional[Decimal]:
        """
        トークン残高の取得
        Args:
            web3: Web3インスタンス
            contract_address: コントラクトアドレス
            wallet_address: ウォレットアドレス
        Returns:
            Optional[Decimal]: トークン残高
        """
        try:
            contract = self.create_contract(web3, contract_address)
            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(wallet_address)
            ).call()
            decimals = contract.functions.decimals().call()
            return Decimal(balance) / Decimal(10 ** decimals)
        except Exception as e:
            logger.error(f"Failed to get token balance: {str(e)}")
            return None

    async def transfer_tokens(
        self,
        web3: Web3,
        contract_address: str,
        from_address: str,
        to_address: str,
        amount: Decimal,
        private_key: str
    ) -> Optional[str]:
        """
        トークンの転送
        Args:
            web3: Web3インスタンス
            contract_address: コントラクトアドレス
            from_address: 送信元アドレス
            to_address: 送信先アドレス
            amount: 送信量
            private_key: 秘密鍵
        Returns:
            Optional[str]: トランザクションハッシュ
        """
        try:
            contract = self.create_contract(web3, contract_address)
            decimals = contract.functions.decimals().call()
            amount_wei = int(amount * (10 ** decimals))

            # トランザクションの構築
            nonce = web3.eth.get_transaction_count(from_address)
            tx = contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                'chainId': web3.eth.chain_id,
                'gas': 100000,  # ガス制限は適宜調整
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
            })

            # 署名と送信
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return web3.to_hex(tx_hash)

        except Exception as e:
            logger.error(f"Failed to transfer tokens: {str(e)}")
            return None

    async def verify_signature(
        self,
        web3: Web3,
        message: str,
        signature: str,
        expected_address: str
    ) -> bool:
        """
        署名の検証
        Args:
            web3: Web3インスタンス
            message: 署名されたメッセージ
            signature: 署名
            expected_address: 期待されるアドレス
        Returns:
            bool: 署名が有効かどうか
        """
        try:
            message_hash = encode_defunct(text=message)
            recovered_address = web3.eth.account.recover_message(
                message_hash,
                signature=signature
            )
            return recovered_address.lower() == expected_address.lower()
        except Exception as e:
            logger.error(f"Failed to verify signature: {str(e)}")
            return False