"""
Analyzes alignment between near-term and further-dated expiries
"""
import numpy as np
from typing import Dict, List

class ExpiryAlignmentAnalyzer:
    def __init__(self):
        self.expiry_data = {}
    
    def analyze_alignment(self, current_expiry_data: Dict, 
                         next_expiry_data: Dict) -> Dict:
        """Analyze alignment between expiries"""
        return {
            'support_alignment': self._analyze_support_alignment(
                current_expiry_data, next_expiry_data
            ),
            'resistance_alignment': self._analyze_resistance_alignment(
                current_expiry_data, next_expiry_data
            ),
            'magnet_alignment': self._analyze_magnet_alignment(
                current_expiry_data, next_expiry_data
            ),
            'overall_alignment_score': self._calculate_alignment_score(
                current_expiry_data, next_expiry_data
            ),
            'gamma_vs_swing': self._assess_gamma_vs_swing(
                current_expiry_data, next_expiry_data
            )
        }
    
    def _analyze_support_alignment(self, current: Dict, next_exp: Dict) -> Dict:
        """Analyze if supports align across expiries"""
        current_supports = self._identify_supports(current)
        next_supports = self._identify_supports(next_exp)
        
        aligned_supports = []
        for cs in current_supports:
            for ns in next_supports:
                if abs(cs['strike'] - ns['strike']) <= 50:  # Within 50 points
                    aligned_supports.append({
                        'strike': cs['strike'],
                        'current_strength': cs['strength'],
                        'next_strength': ns['strength'],
                        'alignment_score': min(cs['strength'], ns['strength']),
                        'type': 'SWING_ANCHOR' if ns['strength'] > 0.7 else 'GAMMA_ONLY'
                    })
        
        return {
            'aligned_supports': aligned_supports,
            'alignment_count': len(aligned_supports),
            'strong_anchor_count': len([s for s in aligned_supports if s['type'] == 'SWING_ANCHOR'])
        }
    
    def _analyze_resistance_alignment(self, current: Dict, next_exp: Dict) -> Dict:
        """Analyze if resistances align across expiries"""
        current_resistances = self._identify_resistances(current)
        next_resistances = self._identify_resistances(next_exp)
        
        aligned_resistances = []
        for cr in current_resistances:
            for nr in next_resistances:
                if abs(cr['strike'] - nr['strike']) <= 50:
                    aligned_resistances.append({
                        'strike': cr['strike'],
                        'current_strength': cr['strength'],
                        'next_strength': nr['strength'],
                        'alignment_score': min(cr['strength'], nr['strength']),
                        'type': 'SWING_ANCHOR' if nr['strength'] > 0.7 else 'GAMMA_ONLY'
                    })
        
        return {
            'aligned_resistances': aligned_resistances,
            'alignment_count': len(aligned_resistances),
            'strong_anchor_count': len([r for r in aligned_resistances if r['type'] == 'SWING_ANCHOR'])
        }
    
    def _analyze_magnet_alignment(self, current: Dict, next_exp: Dict) -> Dict:
        """Analyze if magnet strikes align across expiries"""
        current_magnets = self._identify_magnets(current)
        next_magnets = self._identify_magnets(next_exp)
        
        aligned_magnets = []
        for cm in current_magnets:
            for nm in next_magnets:
                if abs(cm['strike'] - nm['strike']) <= 50:
                    aligned_magnets.append({
                        'strike': cm['strike'],
                        'current_strength': cm['total_oi'],
                        'next_strength': nm['total_oi'],
                        'alignment_ratio': min(cm['total_oi'], nm['total_oi']) / max(cm['total_oi'], nm['total_oi']),
                        'confidence': min(cm['confidence'], nm['confidence'])
                    })
        
        return {
            'aligned_magnets': aligned_magnets,
            'alignment_count': len(aligned_magnets),
            'average_alignment_ratio': np.mean([m['alignment_ratio'] for m in aligned_magnets]) if aligned_magnets else 0
        }
    
    def _calculate_alignment_score(self, current: Dict, next_exp: Dict) -> float:
        """Calculate overall alignment score"""
        support_alignment = self._analyze_support_alignment(current, next_exp)
        resistance_alignment = self._analyze_resistance_alignment(current, next_exp)
        magnet_alignment = self._analyze_magnet_alignment(current, next_exp)
        
        scores = []
        
        # Support alignment component
        if support_alignment['aligned_supports']:
            sup_score = (support_alignment['strong_anchor_count'] / 
                        max(len(support_alignment['aligned_supports']), 1))
            scores.append(sup_score)
        
        # Resistance alignment component
        if resistance_alignment['aligned_resistances']:
            res_score = (resistance_alignment['strong_anchor_count'] / 
                        max(len(resistance_alignment['aligned_resistances']), 1))
            scores.append(res_score)
        
        # Magnet alignment component
        if magnet_alignment['aligned_magnets']:
            mag_score = magnet_alignment['average_alignment_ratio']
            scores.append(mag_score)
        
        if scores:
            return np.mean(scores)
        return 0
    
    def _assess_gamma_vs_swing(self, current: Dict, next_exp: Dict) -> Dict:
        """Assess if current levels are gamma games or swing anchors"""
        current_supports = self._identify_supports(current)
        next_supports = self._identify_supports(next_exp)
        
        gamma_only = []
        swing_anchors = []
        
        for cs in current_supports:
            # Check if support exists in next expiry
            exists_in_next = any(abs(cs['strike'] - ns['strike']) <= 50 for ns in next_supports)
            
            if exists_in_next:
                swing_anchors.append({
                    'strike': cs['strike'],
                    'strength': cs['strength'],
                    'type': 'SWING_ANCHOR'
                })
            else:
                gamma_only.append({
                    'strike': cs['strike'],
                    'strength': cs['strength'],
                    'type': 'GAMMA_GAME'
                })
        
        return {
            'gamma_only_levels': gamma_only,
            'swing_anchor_levels': swing_anchors,
            'gamma_game_ratio': len(gamma_only) / max(len(current_supports), 1),
            'swing_anchor_ratio': len(swing_anchors) / max(len(current_supports), 1),
            'trading_implication': 'TRUST_LEVELS' if len(swing_anchors) > len(gamma_only) else 'FADE_LEVELS'
        }
    
    def _identify_supports(self, chain_data: Dict) -> List[Dict]:
        """Identify support strikes"""
        supports = []
        
        for strike, data in chain_data.items():
            pe_oi = data.get('PE', {}).get('open_interest', 0)
            ce_oi = data.get('CE', {}).get('open_interest', 0)
            
            if pe_oi > ce_oi * 1.5 and pe_oi > 100000:
                supports.append({
                    'strike': strike,
                    'strength': min(pe_oi / (ce_oi + 1), 5) / 5,  # Normalized 0-1
                    'pe_oi': pe_oi,
                    'ce_oi': ce_oi
                })
        
        return sorted(supports, key=lambda x: x['strength'], reverse=True)[:5]
    
    def _identify_resistances(self, chain_data: Dict) -> List[Dict]:
        """Identify resistance strikes"""
        resistances = []
        
        for strike, data in chain_data.items():
            ce_oi = data.get('CE', {}).get('open_interest', 0)
            pe_oi = data.get('PE', {}).get('open_interest', 0)
            
            if ce_oi > pe_oi * 1.5 and ce_oi > 100000:
                resistances.append({
                    'strike': strike,
                    'strength': min(ce_oi / (pe_oi + 1), 5) / 5,
                    'ce_oi': ce_oi,
                    'pe_oi': pe_oi
                })
        
        return sorted(resistances, key=lambda x: x['strength'], reverse=True)[:5]
    
    def _identify_magnets(self, chain_data: Dict) -> List[Dict]:
        """Identify magnet strikes"""
        magnets = []
        
        for strike, data in chain_data.items():
            total_oi = (data.get('CE', {}).get('open_interest', 0) + 
                       data.get('PE', {}).get('open_interest', 0))
            
            if total_oi > 2000000:  # High OI threshold
                magnets.append({
                    'strike': strike,
                    'total_oi': total_oi,
                    'confidence': min(total_oi / 5000000, 1.0)  # Normalized
                })
        
        return sorted(magnets, key=lambda x: x['total_oi'], reverse=True)[:3]
