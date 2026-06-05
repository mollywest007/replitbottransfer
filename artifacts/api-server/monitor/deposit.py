from solana_client.wallet import get_wallet_address, get_wallet_balance
from utils.logger import logger


class DepositMonitor:
    def __init__(self):
        self._last_balance: float | None = None
        self._subscribers: set[int] = set()

    def subscribe(self, chat_id: int) -> None:
        self._subscribers.add(chat_id)
        logger.info(f"Deposit monitor: subscribed chat {chat_id} (total: {len(self._subscribers)})")

    def unsubscribe(self, chat_id: int) -> None:
        self._subscribers.discard(chat_id)

    async def poll(self, bot) -> None:
        if not self._subscribers:
            return

        wallet = get_wallet_address()
        if not wallet:
            return

        try:
            current_balance = await get_wallet_balance(wallet)
        except Exception as e:
            logger.warning(f"Deposit monitor: RPC error — {e}")
            return

        if self._last_balance is None:
            self._last_balance = current_balance
            return

        deposited = current_balance - self._last_balance
        if deposited >= 0.001:
            logger.info(f"Deposit detected: +{deposited:.4f} SOL (new balance: {current_balance:.4f} SOL)")
            from bot.messages import deposit_notification_message
            text = deposit_notification_message(deposited, current_balance, wallet)
            for chat_id in list(self._subscribers):
                try:
                    await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
                except Exception as e:
                    logger.warning(f"Deposit monitor: failed to notify {chat_id}: {e}")

        self._last_balance = current_balance


deposit_monitor = DepositMonitor()
