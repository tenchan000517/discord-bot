from typing import Optional, List, Dict
from datetime import datetime
import traceback
import json
from web3 import Web3
from models.rewards import Reward
from services.coupon_service import CouponService
from services.nft_service import NFTService
from services.token_service import TokenService

class RewardManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.coupon_service = CouponService()
        self.nft_service = NFTService()
        self.token_service = TokenService()

    async def _get_server_reward_settings(self, server_id: str) -> Dict:
        """サーバーごとの報酬設定を取得"""
        settings = await self.bot.get_server_settings(server_id)
        if not settings or 'feature_settings' not in settings or 'rewards' not in settings['feature_settings']:
            raise ValueError("報酬設定が見つかりません")
        return settings['feature_settings']['rewards']

    async def _initialize_web3(self, settings: Dict):
        """Web3接続を初期化"""
        web3_settings = settings['web3']
        w3 = Web3(Web3.HTTPProvider(web3_settings['rpc_url']))
        
        # NFTコントラクト
        with open('contracts/nft_abi.json', 'r') as f:
            nft_contract = w3.eth.contract(
                address=web3_settings['nft_contract_address'],
                abi=json.load(f)['abi']
            )
            
        # トークンコントラクト
        with open('contracts/token_abi.json', 'r') as f:
            token_contract = w3.eth.contract(
                address=web3_settings['token_contract_address'],
                abi=json.load(f)['abi']
            )
            
        return w3, nft_contract, token_contract, web3_settings['private_key']

    async def _save_reward(self, reward: Reward) -> bool:
        """報酬データをDBに保存"""
        try:
            return await self.db.save_reward(reward.to_dict())
        except Exception as e:
            print(f"Error saving reward: {e}")
            print(traceback.format_exc())
            return False

    async def _mint_nft(self, w3: Web3, contract, private_key: str, user_id: str) -> str:
        """NFTを発行"""
        # トランザクションの構築
        nonce = w3.eth.get_transaction_count(w3.eth.account.from_key(private_key).address)
        
        txn = contract.functions.mint(
            user_id,
            {}  # metadata
        ).build_transaction({
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price
        })
        
        # トランザクションの署名と送信
        signed_txn = w3.eth.account.sign_transaction(txn, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # トランザクションの完了を待機
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt.transactionHash.hex()

    async def _transfer_tokens(self, w3: Web3, contract, private_key: str, user_id: str, amount: float) -> str:
        """トークンを転送"""
        # Wei単位に変換（18桁）
        amount_in_wei = int(amount * 10**18)
        
        # トランザクションの構築
        nonce = w3.eth.get_transaction_count(w3.eth.account.from_key(private_key).address)
        
        txn = contract.functions.transfer(
            user_id,
            amount_in_wei
        ).build_transaction({
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price
        })
        
        # トランザクションの署名と送信
        signed_txn = w3.eth.account.sign_transaction(txn, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # トランザクションの完了を待機
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt.transactionHash.hex()

    async def claim_reward(
        self, 
        user_id: str, 
        server_id: str, 
        reward_type: str, 
        points: int
    ) -> Optional[Reward]:
        """報酬を請求"""
        try:
            # サーバー設定を取得
            settings = await self._get_server_reward_settings(server_id)
            
            # ポイント制限のチェック
            limits = settings['limits']
            if reward_type == 'COUPON':
                if points < limits['min_points_coupon'] or points > limits['max_points_coupon']:
                    raise ValueError(f"クーポン交換には{limits['min_points_coupon']}から{limits['max_points_coupon']}ポイントが必要です")
            elif reward_type == 'NFT':
                if points < limits['min_points_nft']:
                    raise ValueError(f"NFT発行には{limits['min_points_nft']}ポイント以上が必要です")
            elif reward_type == 'TOKEN':
                if points < limits['min_points_token']:
                    raise ValueError(f"トークン交換には{limits['min_points_token']}ポイント以上が必要です")

            # ポイント残高チェック
            current_points = await self.bot.point_manager.get_points(user_id, server_id)
            if current_points < points:
                raise ValueError("ポイントが不足しています")

            # 報酬インスタンスの作成
            reward = Reward.create(user_id, server_id, points, reward_type)

            # 報酬タイプに応じた処理
            try:
                if reward_type == 'COUPON':
                    # クーポンAPI用の設定
                    api_settings = settings['coupon_api']
                    coupon_service = CouponService(api_settings['api_key'], api_settings['api_url'])
                    claim_code = await coupon_service.generate_coupon(points)
                elif reward_type in ['NFT', 'TOKEN']:
                    # Web3接続の初期化
                    w3, nft_contract, token_contract, private_key = await self._initialize_web3(settings)
                    
                    if reward_type == 'NFT':
                        claim_code = await self._mint_nft(w3, nft_contract, private_key, user_id)
                    else:  # TOKEN
                        token_amount = points * settings['limits']['token_conversion_rate']
                        claim_code = await self._transfer_tokens(w3, token_contract, private_key, user_id, token_amount)
                else:
                    raise ValueError(f"不正な報酬タイプ: {reward_type}")

                reward.claim_code = claim_code
            except Exception as e:
                reward.status = "FAILED"
                reward.metadata["error"] = str(e)
                await self._save_reward(reward)
                raise

            # ポイントの消費
            success = await self.bot.point_manager.remove_points(
                user_id, 
                server_id, 
                "rewards", 
                points,
                {"reward_id": reward.id}
            )
            if not success:
                raise ValueError("ポイントの消費に失敗しました")

            # 報酬の状態を完了に更新
            reward.status = "COMPLETED"
            reward.claimed_at = datetime.now()
            await self._save_reward(reward)

            return reward

        except Exception as e:
            print(f"Error claiming reward: {e}")
            print(traceback.format_exc())
            return None

    async def get_user_rewards(
        self, 
        user_id: str,
        server_id: str,
        status: Optional[str] = None
    ) -> List[Reward]:
        """ユーザーの報酬履歴を取得"""
        try:
            rewards_data = await self.db.get_user_rewards(user_id, server_id, status)
            return [Reward.from_dict(data) for data in rewards_data]
        except Exception as e:
            print(f"Error getting user rewards: {e}")
            print(traceback.format_exc())
            return []

    async def get_pending_rewards(self, server_id: Optional[str] = None) -> List[Reward]:
        """処理待ちの報酬を取得"""
        try:
            rewards_data = await self.db.get_rewards_by_status('PENDING', server_id)
            return [Reward.from_dict(data) for data in rewards_data]
        except Exception as e:
            print(f"Error getting pending rewards: {e}")
            print(traceback.format_exc())
            return []

    async def retry_failed_reward(self, reward_id: str) -> Optional[Reward]:
        """失敗した報酬の再処理"""
        try:
            reward = await self.get_reward_by_id(reward_id)
            if not reward or reward.status != 'FAILED':
                return None

            # 再処理ロジック
            reward.status = 'PENDING'
            await self._save_reward(reward)
            return await self.process_reward(reward)

        except Exception as e:
            print(f"Error retrying failed reward: {e}")
            print(traceback.format_exc())
            return None