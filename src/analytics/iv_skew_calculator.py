"""
Enhanced IV skew analysis across strikes and pockets
"""
import numpy as np
from typing import Dict, List, Tuple

class IVSkewEnhanced:
    def __init__(self):
        self.iv_cache = {}
        
    def analyze_skew_pockets(self, chain_data: Dict, spot_price: float, 
                            magnet_strikes: List[float]) -> Dict:
        """Analyze IV skew patterns and pockets"""
        atm_strike = self._find_atm_strike(chain_data, spot_price)
        
        return {
            'iv_gradient': self._calculate_iv_gradient(chain_data, atm_strike),
            'magnet_skew': self._analyze_magnet_skew(chain_data, magnet_strikes),
            'one_sided_skew': self._analyze_one_sided_skew(chain_data, atm_strike),
            'iv_crush_pockets': self._find_iv_crush_pockets(chain_data),
            'fear_zones': self._identify_fear_zones(chain_data, spot_price)
        }
    
    def _calculate_iv_gradient(self, chain_data: Dict, atm_strike: float) -> Dict:
        """Calculate IV gradient away from ATM"""
        strikes = sorted(chain_data.keys())
        atm_idx = strikes.index(atm_strike)
        
        # Get IVs for ±5 strikes
        left_strikes = strikes[max(0, atm_idx-5):atm_idx]
        right_strikes = strikes[atm_idx+1:min(len(strikes), atm_idx+6)]
        
        left_ivs = []
        right_ivs = []
        
        for strike in left_strikes:
            if 'CE' in chain_data[strike]:
                left_ivs.append(chain_data[strike]['CE'].get('IV', 0))
        
        for strike in right_strikes:
            if 'PE' in chain_data[strike]:
                right_ivs.append(chain_data[strike]['PE'].get('IV', 0))
        
        left_gradient = np.gradient(left_ivs) if left_ivs else [0]
        right_gradient = np.gradient(right_ivs) if right_ivs else [0]
        
        return {
            'left_steepness': np.mean(left_gradient) if left_gradient else 0,
            'right_steepness': np.mean(right_gradient) if right_gradient else 0,
            'asymmetry': abs(np.mean(left_ivs) - np.mean(right_ivs)) if left_ivs and right_ivs else 0
        }
    
    def _analyze_magnet_skew(self, chain_data: Dict, magnet_strikes: List[float]) -> Dict:
        """Analyze IV at magnet strikes vs surrounding"""
        magnet_skew = {}
        
        for magnet in magnet_strikes:
            if magnet in chain_data:
                # Get IV at magnet
                magnet_ce_iv = chain_data[magnet].get('CE', {}).get('IV', 0)
                magnet_pe_iv = chain_data[magnet].get('PE', {}).get('IV', 0)
                
                # Get IV at surrounding strikes (±2)
                surrounding_strikes = []
                strikes = sorted(chain_data.keys())
                magnet_idx = strikes.index(magnet)
                
                for idx in range(max(0, magnet_idx-2), min(len(strikes), magnet_idx+3)):
                    if idx != magnet_idx:
                        surrounding_strikes.append(strikes[idx])
                
                # Calculate average IV around magnet
                surrounding_ce_iv = []
                surrounding_pe_iv = []
                
                for strike in surrounding_strikes:
                    if 'CE' in chain_data[strike]:
                        surrounding_ce_iv.append(chain_data[strike]['CE'].get('IV', 0))
                    if 'PE' in chain_data[strike]:
                        surrounding_pe_iv.append(chain_data[strike]['PE'].get('IV', 0))
                
                avg_surrounding_ce = np.mean(surrounding_ce_iv) if surrounding_ce_iv else 0
                avg_surrounding_pe = np.mean(surrounding_pe_iv) if surrounding_pe_iv else 0
                
                magnet_skew[magnet] = {
                    'ce_iv_ratio': magnet_ce_iv / avg_surrounding_ce if avg_surrounding_ce > 0 else 1,
                    'pe_iv_ratio': magnet_pe_iv / avg_surrounding_pe if avg_surrounding_pe > 0 else 1,
                    'iv_stability': 'STABLE' if (magnet_ce_iv < avg_surrounding_ce * 0.9 and 
                                                magnet_pe_iv < avg_surrounding_pe * 0.9) else 'VOLATILE'
                }
        
        return magnet_skew
    
    def _analyze_one_sided_skew(self, chain_data: Dict, atm_strike: float) -> Dict:
        """Analyze CE vs PE IV at same strike"""
        skew_data = {}
        
        # Analyze 3 strikes around ATM
        strikes = sorted(chain_data.keys())
        atm_idx = strikes.index(atm_strike)
        
        for idx in range(max(0, atm_idx-1), min(len(strikes), atm_idx+2)):
            strike = strikes[idx]
            ce_iv = chain_data[strike].get('CE', {}).get('IV', 0)
            pe_iv = chain_data[strike].get('PE', {}).get('IV', 0)
            
            if ce_iv > 0 and pe_iv > 0:
                skew_ratio = ce_iv / pe_iv
                
                if skew_ratio > 1.2:
                    skew_type = 'CE_FEAR'  # Upside fear
                elif skew_ratio < 0.8:
                    skew_type = 'PE_FEAR'  # Downside fear
                else:
                    skew_type = 'BALANCED'
                
                skew_data[strike] = {
                    'ce_iv': ce_iv,
                    'pe_iv': pe_iv,
                    'skew_ratio': skew_ratio,
                    'skew_type': skew_type,
                    'fear_strength': abs(skew_ratio - 1)
                }
        
        return skew_data
    
    def _find_iv_crush_pockets(self, chain_data: Dict) -> List[Dict]:
        """Find strikes with unusually low IV (crush pockets)"""
        pockets = []
        strikes = sorted(chain_data.keys())
        
        for i in range(2, len(strikes)-2):
            # Get IV window around strike
            window_strikes = strikes[i-2:i+3]
            window_ivs = []
            
            for strike in window_strikes:
                ce_iv = chain_data[strike].get('CE', {}).get('IV', 0)
                pe_iv = chain_data[strike].get('PE', {}).get('IV', 0)
                if ce_iv > 0:
                    window_ivs.append(ce_iv)
                if pe_iv > 0:
                    window_ivs.append(pe_iv)
            
            if window_ivs:
                current_ce_iv = chain_data[strikes[i]].get('CE', {}).get('IV', 0)
                current_pe_iv = chain_data[strikes[i]].get('PE', {}).get('IV', 0)
                window_avg = np.mean(window_ivs)
                window_std = np.std(window_ivs)
                
                # Check if current IV is significantly lower
                iv_crush = (current_ce_iv < window_avg - window_std and 
                           current_pe_iv < window_avg - window_std)
                
                if iv_crush:
                    pockets.append({
                        'strike': strikes[i],
                        'ce_iv': current_ce_iv,
                        'pe_iv': current_pe_iv,
                        'window_avg': window_avg,
                        'z_score': (current_ce_iv - window_avg) / window_std if window_std > 0 else 0,
                        'crush_strength': (window_avg - current_ce_iv) / window_avg
                    })
        
        return pockets
    
    def _identify_fear_zones(self, chain_data: Dict, spot_price: float) -> Dict:
        """Identify zones with spike in IV (fear zones)"""
        fear_zones = {'above': [], 'below': []}
        strikes = sorted(chain_data.keys())
        
        # Find ATM index
        atm_strike = min(strikes, key=lambda x: abs(x - spot_price))
        atm_idx = strikes.index(atm_strike)
        
        # Check ±5 strikes for IV spikes
        for i in range(max(0, atm_idx-5), min(len(strikes), atm_idx+6)):
            strike = strikes[i]
            ce_iv = chain_data[strike].get('CE', {}).get('IV', 0)
            pe_iv = chain_data[strike].get('PE', {}).get('IV', 0)
            
            # Get local average (excluding current)
            local_strikes = []
            for j in range(max(0, i-2), min(len(strikes), i+3)):
                if j != i:
                    local_strikes.append(strikes[j])
            
            local_ce_ivs = []
            local_pe_ivs = []
            
            for s in local_strikes:
                local_ce = chain_data[s].get('CE', {}).get('IV', 0)
                local_pe = chain_data[s].get('PE', {}).get('IV', 0)
                if local_ce > 0:
                    local_ce_ivs.append(local_ce)
                if local_pe > 0:
                    local_pe_ivs.append(local_pe)
            
            if local_ce_ivs and local_pe_ivs:
                avg_local_ce = np.mean(local_ce_ivs)
                avg_local_pe = np.mean(local_pe_ivs)
                
                # Check for IV spike
                if ce_iv > avg_local_ce * 1.3:
                    fear_type = 'CE_FEAR'
                    strength = (ce_iv - avg_local_ce) / avg_local_ce
                elif pe_iv > avg_local_pe * 1.3:
                    fear_type = 'PE_FEAR'
                    strength = (pe_iv - avg_local_pe) / avg_local_pe
                else:
                    continue
                
                zone = {
                    'strike': strike,
                    'fear_type': fear_type,
                    'strength': strength,
                    'current_iv': max(ce_iv, pe_iv),
                    'local_avg': max(avg_local_ce, avg_local_pe)
                }
                
                if strike > spot_price:
                    fear_zones['above'].append(zone)
                else:
                    fear_zones['below'].append(zone)
        
        return fear_zones
