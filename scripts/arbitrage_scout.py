from decimal import Decimal

from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.utils.trading_pair_fetcher import TradingPairFetcher

s_decimal_0 = Decimal(0)


class ArbitrageScout(ScriptStrategyBase):
    """
    ArbitrageScout is a meta-strategy that algorithmically searches for arbitrage strategies for you across two exchanges that you insert.
    Params:
    Two exchange names
    min_profitability
    Algo automatically finds the intersectional sets of tokens that are listed in both markets. Then, every second it iterates through all these markets to find profitable pairs. If profit is more than your min_profitability parameter, it will notify you on telegram.
    You can then execute a manual arbitrage by buying said token at the cheaper exchange, withdrawing it to the premium exchange, and selling it there.
    Free money. You're welcome.
    """
    # The exchanges you want to scout.
    arbitrage_markets = ["gate_io_paper_trade", "ascend_ex_paper_trade"]
    # Min profitability before it alerts you.
    min_profitability = Decimal('0.007')

    trading_pair_fetcher: TradingPairFetcher = TradingPairFetcher.get_instance()
    if trading_pair_fetcher.ready:
        trading_pairs_1 = trading_pair_fetcher.trading_pairs.get(arbitrage_markets[0], [])
        trading_pairs_2 = trading_pair_fetcher.trading_pairs.get(arbitrage_markets[1], [])

    # It takes a long time to start up the market pairs if you search through all the markets.
    # A speedier startup would search through only a splice of the markets.
    trading_pairs_set = list(set(trading_pairs_1).intersection(trading_pairs_2))
    trading_pairs_set = trading_pairs_set[:]

    markets = {arbitrage_markets[0]: trading_pairs_set, arbitrage_markets[1]: trading_pairs_set}

    def on_tick(self):
        self.logger().info(f"Set of Trading Pairs {self.trading_pairs_set}")
        self.notify_hb_app_with_timestamp(f"Exchange_1: {self.arbitrage_markets[0]}; Exchange_2: {self.arbitrage_markets[1]}")
        for pair in self.trading_pairs_set:
            try:
                market_1_bid = self.connectors[self.arbitrage_markets[0]].get_price(pair, False)
                market_1_ask = self.connectors[self.arbitrage_markets[0]].get_price(pair, True)
                market_2_bid = self.connectors[self.arbitrage_markets[1]].get_price(pair, False)
                market_2_ask = self.connectors[self.arbitrage_markets[1]].get_price(pair, True)
                profitability_buy_2_sell_1 = market_1_bid / market_2_ask - 1
                profitability_buy_1_sell_2 = market_2_bid / market_1_ask - 1

                if profitability_buy_1_sell_2 > self.min_profitability:
                    self.notify_hb_app_with_timestamp(f"{pair}: Buy@1 & Sell@2: {profitability_buy_1_sell_2:.5f}")
                if profitability_buy_2_sell_1 > self.min_profitability:
                    self.notify_hb_app_with_timestamp(f"{pair}: Buy@2 & Sell@1: {profitability_buy_2_sell_1:.5f}")
            except BaseException:
                self.logger().info(f"{pair} has no bid or ask order book")
