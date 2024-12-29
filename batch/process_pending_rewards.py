import asyncio
import os
from dotenv import load_dotenv
import sys
import traceback

# プロジェクトのルートディレクトリをPYTHONPATHに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import GachaBot

async def process_pending_rewards():
    """未処理の報酬を処理"""
    try:
        # Botインスタンスの初期化（トークンなしで）
        bot = GachaBot()
        
        # 未処理の報酬を取得
        pending_rewards = await bot.reward_manager.get_pending_rewards()
        if not pending_rewards:
            print("未処理の報酬はありません")
            return

        print(f"{len(pending_rewards)}件の未処理報酬を処理します...")
        
        # 各報酬を処理
        for reward in pending_rewards:
            try:
                await bot.reward_manager.process_reward(reward)
                print(f"報酬ID {reward.id} の処理が完了しました")
            except Exception as e:
                print(f"報酬ID {reward.id} の処理中にエラーが発生: {e}")
                print(traceback.format_exc())
                continue

    except Exception as e:
        print(f"バッチ処理中にエラーが発生: {e}")
        print(traceback.format_exc())
    finally:
        # 必要に応じてクリーンアップ処理
        if hasattr(bot, 'db') and bot.db:
            print("データベース接続をクローズ")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(process_pending_rewards())