"""
Analyzes time-decay pressure and seller comfort windows
"""
from datetime import datetime, time
from typing import Dict, List

class TimeDecayAnalyzer:
    def __init__(self, market_open: time = time(9, 15), market_close: time = time(15, 30)):
        self.market_open = market_open
        self.market_close = market_close
        
    def analyze_time_pressure(self, chain_data: Dict, spot_price: float, 
                             current_time: datetime) -> Dict:
        """Analyze time-decay effects and seller comfort"""
        current_time_only = current_time.time()
        time_into_session = self._get_time_into_session(current_time_only)
        
        return {
            'time_phase': self._get_time_phase(current_time_only),
            'seller_aggression': self._assess_seller_aggression(chain_data, time_into_session),
            'pinning_pressure': self._calculate_pinning_pressure(chain_data, spot_price, time_into_session),
            'breakout_probability': self._get_breakout_probability(time_into_session),
            'gamma_risk': self._assess_gamma_risk(current_time_only)
        }
    
    def _get_time_phase(self, current_time: time) -> str:
        """Determine current market phase"""
        if time(9, 15) <= current_time < time(10, 30):
            return 'OPENING_PHASE'
        elif time(10, 30) <= current_time < time(11, 30):
            return 'MID_MORNING'
        elif time(11, 30) <= current_time < time(13, 30):
            return 'SELLER_COMFORT_WINDOW'  # Intraday writers settle
        elif time(13, 30) <= current_time < time(14, 30):
            return 'POST_LUNCH'
        elif time(14, 30) <= current_time <= time(15, 30):
            return 'GAMMA_GAME_PHASE'  # Late-day gamma games
        else:
            return 'CLOSED'
    
    def _assess_seller_aggression(self, chain_data: Dict, time_into_session: float) -> float:
        """Assess how aggressive option sellers are based on time"""
        # Seller aggression increases in comfort windows
        if 0.4 <= time_into_session <= 0.7:  # 11:30-13:30
            return 0.8
        elif time_into_session > 0.8:  # After 14:30
            return 0.9
        else:
            return 0.5
    
    def _calculate_pinning_pressure(self, chain_data: Dict, spot_price: float, 
                                   time_into_session: float) -> Dict:
        """Calculate pinning pressure near high OI strikes"""
        if time_into_session < 0.8:
            return {'pressure': 0.3, 'target_strikes': []}
        
        # Find high OI strikes near spot
        nearby_strikes = []
        for strike in chain_data.keys():
            if abs(strike - spot_price) < 100:  # Within 100 points
                ce_oi = chain_data[strike].get('CE', {}).get('open_interest', 0)
                pe_oi = chain_data[strike].get('PE', {}).get('open_interest', 0)
                total_oi = ce_oi + pe_oi
                
                if total_oi > 1000000:  # High OI threshold
                    nearby_strikes.append({
                        'strike': strike,
                        'total_oi': total_oi,
                        'distance': abs(strike - spot_price)
                    })
        
        # Sort by distance
        nearby_strikes.sort(key=lambda x: x['distance'])
        
        if nearby_strikes:
            pressure = min(0.3 + (time_into_session - 0.8) * 2, 0.9)
            return {
                'pressure': pressure,
                'target_strikes': [s['strike'] for s in nearby_strikes[:3]],
                'strong_pin': len(nearby_strikes) >= 2
            }
        
        return {'pressure': 0.2, 'target_strikes': []}
    
    def _get_breakout_probability(self, time_into_session: float) -> float:
        """Get probability of valid breakout based on time"""
        # Early in session: higher breakout probability
        if time_into_session < 0.3:
            return 0.8
        # Seller comfort window: lower breakout probability
        elif 0.4 <= time_into_session <= 0.7:
            return 0.4
        # Gamma game phase: volatile, can break either way
        elif time_into_session > 0.8:
            return 0.6
        else:
            return 0.5
    
    def _assess_gamma_risk(self, current_time: time) -> float:
        """Assess gamma risk (squeeze potential)"""
        if time(14, 30) <= current_time <= time(15, 30):
            return 0.8  # High gamma risk
        elif time(9, 15) <= current_time < time(10, 30):
            return 0.7  # Opening gamma
        else:
            return 0.4
    
    def _get_time_into_session(self, current_time: time) -> float:
        """Get normalized time into session (0 to 1)"""
        session_length = 6.25 * 60 * 60  # 6 hours 15 minutes in seconds
        current_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        open_seconds = self.market_open.hour * 3600 + self.market_open.minute * 60
        
        time_elapsed = max(0, current_seconds - open_seconds)
        return min(1.0, time_elapsed / session_length)
