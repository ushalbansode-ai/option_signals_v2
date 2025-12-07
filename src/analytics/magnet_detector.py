"""
Detects magnet strikes and low-OI gaps
"""
import numpy as np
from scipy import stats

class MagnetDetector:
    def __init__(self, window_size: int = 5):
        self.window_size = window_size  # Neighbor strikes to compare
        
    def find_magnets_and_gaps(self, chain_data: Dict, spot_price: float) -> Dict:
        """Identify magnet strikes and low-OI gaps"""
        strikes = sorted(chain_data.keys())
        
        # Calculate total OI per strike
        total_oi = []
        for strike in strikes:
            ce_oi = chain_data[strike].get('CE', {}).get('open_interest', 0)
            pe_oi = chain_data[strike].get('PE', {}).get('open_interest', 0)
            total_oi.append(ce_oi + pe_oi)
        
        # Find magnet strikes (local maxima in OI)
        magnets = self._find_local_maxima(strikes, total_oi)
        
        # Find low-OI gaps between magnets
        gaps = self._find_low_oi_gaps(strikes, total_oi, magnets, spot_price)
        
        return {
            'magnets': magnets,
            'gaps': gaps,
            'spot_in_gap': self._is_spot_in_gap(spot_price, gaps),
            'nearest_magnet': self._find_nearest_magnet(spot_price, magnets)
        }
    
    def _find_local_maxima(self, strikes: List[float], total_oi: List[int]) -> List[Dict]:
        """Find strikes with unusually high total OI compared to neighbors"""
        magnets = []
        
        for i in range(self.window_size, len(strikes) - self.window_size):
            window_oi = total_oi[i-self.window_size:i+self.window_size+1]
            current_oi = total_oi[i]
            window_mean = np.mean(window_oi)
            window_std = np.std(window_oi)
            
            # Magnet condition: OI > mean + 2*std
            if current_oi > window_mean + 2 * window_std:
                z_score = (current_oi - window_mean) / window_std if window_std > 0 else 0
                
                magnets.append({
                    'strike': strikes[i],
                    'total_oi': current_oi,
                    'z_score': z_score,
                    'relative_strength': current_oi / window_mean if window_mean > 0 else 1
                })
        
        return sorted(magnets, key=lambda x: x['z_score'], reverse=True)[:5]
    
    def _find_low_oi_gaps(self, strikes: List[float], total_oi: List[int], 
                          magnets: List[Dict], spot_price: float) -> List[Dict]:
        """Find zones between magnets with low OI"""
        gaps = []
        
        # Sort magnets by strike
        sorted_magnets = sorted(magnets, key=lambda x: x['strike'])
        
        for i in range(len(sorted_magnets) - 1):
            mag1 = sorted_magnets[i]
            mag2 = sorted_magnets[i + 1]
            
            # Find indices of these strikes
            idx1 = strikes.index(mag1['strike'])
            idx2 = strikes.index(mag2['strike'])
            
            # Get OI values in between
            gap_oi_values = total_oi[idx1+1:idx2]
            gap_strikes = strikes[idx1+1:idx2]
            
            if gap_oi_values:
                avg_gap_oi = np.mean(gap_oi_values)
                avg_magnet_oi = (mag1['total_oi'] + mag2['total_oi']) / 2
                
                # Gap condition: average gap OI < 30% of average magnet OI
                if avg_gap_oi < 0.3 * avg_magnet_oi:
                    gaps.append({
                        'from_strike': mag1['strike'],
                        'to_strike': mag2['strike'],
                        'avg_oi': avg_gap_oi,
                        'oi_ratio': avg_gap_oi / avg_magnet_oi,
                        'strikes_in_gap': len(gap_strikes)
                    })
        
        return gaps
