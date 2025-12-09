"""Futures Data Analysis"""
import pandas as pd

class FuturesAnalyzer:
    def __init__(self, data):
        self.data = data
        self.futures_data = data[data['INSTRUMENT'].isin(['FUTSTK', 'FUTIDX'])]
    
    def find_buildup_signals(self):
        signals = []
        
        for symbol in self.futures_data['SYMBOL'].unique():
            symbol_data = self.futures_data[self.futures_data['SYMBOL'] == symbol]
            
            oi_change = symbol_data['CHG_IN_OI'].sum()
            price_change = symbol_data['CHG'].sum()
            
            signal = self._interpret_buildup(oi_change, price_change)
            
            if signal != "Neutral":
                signals.append({
                    'symbol': symbol,
                    'signal': signal,
                    'oi_change': oi_change,
                    'price_change': price_change
                })
        
        return pd.DataFrame(signals)
    
    def _interpret_buildup(self, oi_change, price_change):
        if oi_change > 0 and price_change > 0:
            return "Long Buildup"
        elif oi_change > 0 and price_change < 0:
            return "Short Buildup"
        elif oi_change < 0 and price_change > 0:
            return "Short Covering"
        elif oi_change < 0 and price_change < 0:
            return "Long Unwinding"
        return "Neutral"
