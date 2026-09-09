import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm

import matplotlib.pyplot as plt
from enum import Enum

class Mode(Enum):
    VALS= "vals"
    PLOTS= "plots"





def calculate_all_volatilities(df, mode : Mode, window =30):
    N = len(df)
    
    # 1. Close-to-Close
    log_returns = np.log(df['Close'] / df['Close'].shift(1)).dropna()
    
    # 2. Parkinson
    parkinson_terms = (np.log(df['High'] / df['Low']))**2 / (4 * np.log(2))
    
    # 3. Garman-Klass
    log_hl = np.log(df['High'] / df['Low'])
    log_co = np.log(df['Close'] / df['Open'])
    gk_terms = 0.5 * (log_hl**2) - (2 * np.log(2) - 1) * (log_co**2)
    
    # 4. Yang-Zhang
    log_ho = np.log(df['High'] / df['Open'])
    log_lo = np.log(df['Low'] / df['Open'])
    
    # Rogers-Satchell term
    rs_terms = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
    
    # Overnight and Open-to-Close variance
    log_overnight = np.log(df['Open'] / df['Close'].shift(1)).dropna()
    
    


    if mode == Mode.VALS:

        #c2c
        close_vol = log_returns.std() * np.sqrt(252)

        #Parkinson
        parkinson_vol = np.sqrt(parkinson_terms.mean() * 252)

        #Garman-Klass
        gk_vol = np.sqrt(gk_terms.mean() * 252)

        ## Yang-Zhang
        k = 0.34 / (1.34 + (N + 1) / (N - 1))

        rs_var = rs_terms.mean()
        overnight_var = log_overnight.var()
        open_to_close_var = log_co.var()
        yz_var = overnight_var + k * open_to_close_var + (1 - k) * rs_var
        yz_vol = np.sqrt(yz_var * 252)


        return {
        "Close-to-Close": close_vol,
        "Parkinson": parkinson_vol,
        "Garman-Klass": gk_vol,
        "Yang-Zhang": yz_vol
        }



    elif mode == Mode.PLOTS:

        #Rolling Close-to-Close
        c2c_rolling = log_returns.rolling(window=window).std() * np.sqrt(252)

        # Rolling Parkinson
        parkinson_rolling = np.sqrt(parkinson_terms.rolling(window=window).mean() * 252)

        # Rolling Garman-Klass
        gk_rolling = np.sqrt(gk_terms.rolling(window=window).mean() * 252)

        #Rolling Yang-Zhang
        k = 0.34 / (1.34 + (window + 1) / (window - 1))

        overnight_var = log_overnight.rolling(window=window).var()
        open_to_close_var = log_co.rolling(window=window).var()
        rs_var = rs_terms.rolling(window=window).mean()
        
        yz_var = overnight_var + k * open_to_close_var + (1 - k) * rs_var
        yz_rolling = np.sqrt(yz_var * 252)


        return {
            "Close-to-Close": c2c_rolling,
            "Parkinson": parkinson_rolling,
            "Garman-Klass": gk_rolling,
            "Yang-Zhang": yz_rolling
        }

def plot_rolling_estimators(df, window=30):
    N = len(df)
    
    dit = calculate_all_volatilities(df,mode=Mode.PLOTS, window=window)

    #Rollings
    c2c_rolling = dit["Close-to-Close"]
    parkinson_rolling = dit["Parkinson"]
    gk_rolling = dit["Garman-Klass"]
    yz_rolling= dit[ "Yang-Zhang"]                   


    # Plotting
    plt.figure(figsize=(12, 6))
    plt.plot(c2c_rolling, label="Close-to-Close", color="navy", linewidth=1.5)
    plt.plot(parkinson_rolling, label="Parkinson", color="darkorange", linestyle="--")
    plt.plot(gk_rolling, label="Garman-Klass", color="green", linestyle="-.")
    plt.plot(yz_rolling, label="Yang-Zhang", color="crimson", linewidth=1.8)
    
    plt.title(f"AAPL {window}-Day Rolling Historical Volatility Estimators")
    plt.xlabel("Date")
    plt.ylabel("Annualized Volatility")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()


########################### TO NOT SAVE THE PLOT -> COMMENT THE NEXT LINE ############################
    plt.savefig("aapl_estimator_comparison.png", dpi=150)


    plt.show()

    
# Test on AAPL
if __name__ == "__main__":
    data = yf.download("AAPL", period="1y")
    data.columns = data.columns.get_level_values(0)
    
    results = calculate_all_volatilities(data,mode=Mode.VALS)
    print (results)
    
    plot_rolling_estimators(data)