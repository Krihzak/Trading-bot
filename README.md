# Trading-bot
A small Python CLI that places **MARKET**, **LIMIT**, and **STOP_LIMIT** (bonus) orders on the [Binance USDT-M Futures Testnet](https://testnet.binancefuture.com). The code is split into a thin client wrapper, an order service, input validators, and a CLI layer so each piece can be re-used or unit-tested in isolation.
