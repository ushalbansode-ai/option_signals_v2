"""
Analyzes intraday migration of max OI strikes
"""
import numpy as np
from typing import Dict, List

class OIMigrationAnalyzer:
    def __init__(self, track_period: int = 30):
        self.track_period = track_period  # minutes
        self.migration_history = []
        
    def analyze_migration(self, chain_data: Dict, spot_price: float) -> Dict:
        """Analyze OI migration patterns"""
        current_max = self._get_max_oi_strikes(chain_data)
        
        # Track migration
        migration_trend = self._track_migration_trend(current_max)
        
        return {
            'current_max_oi': current_max,
            'migration_trend': migration_trend,
            'exhaustion_signals': self._detect_exhaustion(current_max, migration_trend),
            'trend_strength': self._assess_trend_strength(migration_trend),
            'next_potential_level': self._predict_next_level(current_max, migration_trend)
        }
    
    def _get_max_oi_strikes(self, chain_data: Dict) -> Dict:
        """Get strikes with maximum OI"""
        max_ce_oi = 0
        max_ce_strike = None
        max_pe_oi = 0
        max_pe_strike = None
        
        for strike, data in chain_data.items():
            ce_oi = data.get('CE', {}).get('open_interest', 0)
            pe_oi = data.get('PE', {}).get('open_interest', 0)
            
            if ce_oi > max_ce_oi:
                max_ce_oi = ce_oi
                max_ce_strike = strike
            
            if pe_oi > max_pe_oi:
                max_pe_oi = pe_oi
                max_pe_strike = strike
        
        return {
            'max_ce': {'strike': max_ce_strike, 'oi': max_ce_oi},
            'max_pe': {'strike': max_pe_strike, 'oi': max_pe_oi},
            'distance': abs(max_ce_strike - max_pe_strike) if max_ce_strike and max_pe_strike else 0
        }
    
    def _track_migration_trend(self, current_max: Dict) -> Dict:
        """Track migration trend of max OI strikes"""
        self.migration_history.append(current_max)
        
        if len(self.migration_history) > self.track_period:
            self.migration_history.pop(0)
        
        if len(self.migration_history) < 3:
            return {'ce_trend': 'NEUTRAL', 'pe_trend': 'NEUTRAL', 'velocity': 0}
        
        # Calculate trend for CE max OI
        ce_strikes = [m['max_ce']['strike'] for m in self.migration_history if m['max_ce']['strike']]
        if len(ce_strikes) >= 3:
            ce_slope = self._calculate_slope(ce_strikes)
            ce_trend = 'UP' if ce_slope > 0.5 else 'DOWN' if ce_slope < -0.5 else 'FLAT'
        else:
            ce_trend = 'NEUTRAL'
        
        # Calculate trend for PE max OI
        pe_strikes = [m['max_pe']['strike'] for m in self.migration_history if m['max_pe']['strike']]
        if len(pe_strikes) >= 3:
            pe_slope = self._calculate_slope(pe_strikes)
            pe_trend = 'UP' if pe_slope > 0.5 else 'DOWN' if pe_slope < -0.5 else 'FLAT'
        else:
            pe_trend = 'NEUTRAL'
        
        # Overall trend
        if ce_trend == 'DOWN' and pe_trend == 'UP':
            overall = 'BULLISH'  # Call writers covering, put writers chasing up
        elif ce_trend == 'UP' and pe_trend == 'DOWN':
            overall = 'BEARISH'  # Put writers covering, call writers chasing down
        elif ce_trend == 'UP' and pe_trend == 'UP':
            overall = 'CONSOLIDATION'  # Both moving together
        else:
            overall = 'NEUTRAL'
        
        return {
            'ce_trend': ce_trend,
            'pe_trend': pe_trend,
            'overall': overall,
            'ce_slope': ce_slope if 'ce_slope' in locals() else 0,
            'pe_slope': pe_slope if 'pe_slope' in locals() else 0,
            'divergence': abs(ce_slope - pe_slope) if 'ce_slope' in locals() and 'pe_slope' in locals() else 0
        }
    
    def _detect_exhaustion(self, current_max: Dict, migration_trend: Dict) -> List[str]:
        """Detect trend exhaustion signals"""
        exhaustion_signals = []
        
        # Check if one side's migration has stalled
        if migration_trend['ce_trend'] == 'FLAT' and migration_trend['pe_trend'] != 'FLAT':
            exhaustion_signals.append('CE_MIGRATION_STALL')
        
        if migration_trend['pe_trend'] == 'FLAT' and migration_trend['ce_trend'] != 'FLAT':
            exhaustion_signals.append('PE_MIGRATION_STALL')
        
        # Check for divergence
        if migration_trend['divergence'] > 1.0:
            exhaustion_signals.append('HIGH_DIVERGENCE')
        
        # Check if max OI strikes are too close (pinning)
        if current_max['distance'] < 100:
            exhaustion_signals.append('TIGHT_PINNING')
        
        return exhaustion_signals
    
    def _assess_trend_strength(self, migration_trend: Dict) -> float:
        """Assess strength of migration trend"""
        strength = 0
        
        if migration_trend['overall'] == 'BULLISH':
            strength = abs(migration_trend['ce_slope']) + abs(migration_trend['pe_slope'])
        elif migration_trend['overall'] == 'BEARISH':
            strength = abs(migration_trend['ce_slope']) + abs(migration_trend['pe_slope'])
        elif migration_trend['overall'] == 'CONSOLIDATION':
            strength = min(abs(migration_trend['ce_slope']), abs(migration_trend['pe_slope']))
        
        return min(strength / 2, 1.0)  # Normalize to 0-1
    
    def _predict_next_level(self, current_max: Dict, migration_trend: Dict) -> Dict:
        """Predict next potential level based on migration"""
        next_levels = {}
        
        if migration_trend['ce_trend'] == 'DOWN':
            # CE max OI moving down
            next_ce = current_max['max_ce']['strike'] - 50  # Assuming 50 point increments
            next_levels['ce'] = {
                'strike': next_ce,
                'direction': 'DOWN',
                'confidence': abs(migration_trend['ce_slope'])
            }
        
        if migration_trend['pe_trend'] == 'UP':
            # PE max OI moving up
            next_pe = current_max['max_pe']['strike'] + 50
            next_levels['pe'] = {
                'strike': next_pe,
                'direction': 'UP',
                'confidence': abs(migration_trend['pe_slope'])
            }
        
        return next_levels
    
    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate slope of values over time"""
        if len(values) < 2:
            return 0
        
        x = list(range(len(values)))
        y = values
        
        # Simple linear regression
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x_i ** 2 for x_i in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        return slope
