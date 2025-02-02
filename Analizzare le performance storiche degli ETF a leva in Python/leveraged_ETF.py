import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
import datetime

def returns(prices):
    """
    Calcola la crescita di 1 dollaro investito in un titolo con determinati prezzi
    """
    return (1 + prices.pct_change(1)).cumprod()

def drawdown(prices):
    """
    Calcola il drawdown di un titolo con determinati prezzi
    """
    rets = returns(prices)
    return (rets.div(rets.cummax()) - 1) * 100

def cagr(prices):
    """
    Calcola il Compound Annual Growth Rate (CAGR) di un titolo con determinati prezzi
    """
    delta = (prices.index[-1] - prices.index[0]).days / 365.25
    return ((prices[-1] / prices[0]) ** (1 / delta) - 1) * 100


start = "2009-01-01"
end = "2020-01-01"

spy = yf.download("SPY", start, end)["Adj Close"]
upro = yf.download("UPRO", start, end)["Adj Close"]

spy_returns = returns(spy).rename("SPY")
upro_returns = returns(upro).rename("UPRO")

spy_returns.plot(title="Growth of $1: SPY vs UPRO", legend=True, figsize=(10,6))
upro_returns.plot(legend=True)
plt.show()

print("CAGRs")
print(f"SPY: {cagr(spy):.2f}%")
print(f"UPRO: {cagr(upro):.2f}%")

spy_drawdown = drawdown(spy)
upro_drawdown = drawdown(upro)
print("Max Drawdown")
print(f"SPY: {spy_drawdown.idxmin()} {spy_drawdown.min():.2f}%")
print(f"UPRO: {upro_drawdown.idxmin()} {upro_drawdown.min():.2f}%")
upro_drawdown.plot.area(color="red", title="UPRO drawdown", figsize=(10,6))
plt.show()

def sim_leverage(proxy, leverage=1, expense_ratio = 0.0, initial_value=1.0):
    pct_change = proxy.pct_change(1)
    pct_change = (pct_change - expense_ratio / 252) * leverage
    sim = (1 + pct_change).cumprod() * initial_value
    sim[0] = initial_value
    return sim

vfinx = yf.download("VFINX", start, end)["Adj Close"]
upro_sim = sim_leverage(vfinx, leverage=3, expense_ratio=0.0092).rename("UPRO Sim")
upro_sim.plot(title="Growth of $1: UPRO vs UPRO Sim", legend=True, figsize=(10,6))
upro_returns.plot(legend=True)
plt.show()

start = '1976-08-31'
vfinx = yf.download("VFINX", start, end)["Adj Close"]
upro_sim = sim_leverage(vfinx, leverage=3, expense_ratio=0.0092).rename("UPRO Sim")
upro_sim.plot(title="Growth of $1: VFINX vs UPRO Sim", legend=True, figsize=(10,6))

vfinx_returns = returns(vfinx).rename("VFINX")
vfinx_returns.plot(legend=True)
plt.show()
print("CAGRs")
print(f"VFINX: {cagr(vfinx):.2f}%")
print(f"UPRO Sim: {cagr(upro_sim):.2f}%")

upro_sim_drawdown = drawdown(upro_sim)
vfinx_drawdown = drawdown(vfinx)

print("Max Drawdown")
print(f"VFINX: {vfinx_drawdown.idxmin()} {vfinx_drawdown.min():.2f}%")
print(f"UPRO Sim: {upro_sim_drawdown.idxmin()} {upro_sim_drawdown.min():.2f}%")
upro_sim_drawdown.plot.area(color="red", title="UPRO Sim drawdown", figsize=(10,6))
plt.show()

print("")

