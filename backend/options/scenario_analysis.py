"""
Scenario Analysis Engine
Test portfolio performance under different price/IV scenarios
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ScenarioAnalysisEngine:
    """
    Analyze portfolio performance across multiple scenarios
    """
    
    def __init__(self):
        self.scenarios = []
    
    def create_price_scenarios(self, current_price: float, 
                              changes_pct: List[float]) -> List[float]:
        """Generate price scenarios"""
        return [current_price * (1 + pct/100) for pct in changes_pct]
    
    def create_iv_scenarios(self, current_iv: float,
                           changes_pct: List[float]) -> List[float]:
        """Generate IV scenarios"""
        return [current_iv * (1 + pct/100) for pct in changes_pct]
    
    def calculate_portfolio_value(self, positions: List[Dict],
                                  spot_price: float, iv_level: float,
                                  greeks_calculator) -> Dict[str, float]:
        """
        Calculate portfolio value and Greeks at given spot/IV
        """
        total_value = 0
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        
        for pos in positions:
            qty = pos.get('qty', 1)
            
            # Recalculate option value with new spot/IV
            greeks = greeks_calculator.calculate_all_greeks(
                S=spot_price,
                K=pos['strike_price'],
                T=pos['time_to_expiry'],
                r=pos.get('risk_free_rate', 0.05),
                sigma=iv_level,
                option_type=pos['option_type']
            )
            
            option_value = greeks['theoretical_price']
            total_value += option_value * qty
            total_delta += greeks['delta'] * qty
            total_gamma += greeks['gamma'] * qty
            total_theta += greeks['theta'] * qty
            total_vega += greeks['vega'] * qty
        
        return {
            'portfolio_value': total_value,
            'delta': total_delta,
            'gamma': total_gamma,
            'theta': total_theta,
            'vega': total_vega
        }
    
    def run_scenario_analysis(self, positions: List[Dict],
                             current_spot: float,
                             current_iv: float,
                             price_changes: List[float] = [-10, -5, 0, 5, 10],
                             iv_changes: List[float] = [-50, -20, 0, 20, 50],
                             greeks_calculator=None) -> Dict[str, Any]:
        """
        Run comprehensive scenario analysis
        
        Returns:
            P&L matrix, Greeks sensitivity, risk metrics
        """
        try:
            from backend.engine_c.src.options_analytics import get_greeks_calculator
            if not greeks_calculator:
                greeks_calculator = get_greeks_calculator()
            
            # Calculate base value
            base_value = self.calculate_portfolio_value(
                positions, current_spot, current_iv, greeks_calculator
            )
            
            # Generate scenarios
            price_scenarios = self.create_price_scenarios(current_spot, price_changes)
            iv_scenarios = self.create_iv_scenarios(current_iv, iv_changes)
            
            # P&L matrix
            pnl_matrix = []
            greeks_matrix = []
            
            for price_change in price_changes:
                pnl_row = []
                greeks_row = []
                
                for iv_change in iv_changes:
                    new_spot = current_spot * (1 + price_change/100)
                    new_iv = current_iv * (1 + iv_change/100)
                    
                    scenario_result = self.calculate_portfolio_value(
                        positions, new_spot, new_iv, greeks_calculator
                    )
                    
                    pnl = scenario_result['portfolio_value'] - base_value['portfolio_value']
                    pnl_row.append(pnl)
                    greeks_row.append(scenario_result)
                
                pnl_matrix.append(pnl_row)
                greeks_matrix.append(greeks_row)
            
            # Find best/worst scenarios
            pnl_flat = [pnl for row in pnl_matrix for pnl in row]
            max_gain = max(pnl_flat)
            max_loss = min(pnl_flat)
            
            # Risk metrics
            positive_scenarios = len([x for x in pnl_flat if x > 0])
            total_scenarios = len(pnl_flat)
            
            return {
                'base_value': base_value['portfolio_value'],
                'price_changes': price_changes,
                'iv_changes': iv_changes,
                'pnl_matrix': pnl_matrix,
                'greeks_matrix': greeks_matrix,
                'max_gain': max_gain,
                'max_loss': max_loss,
                'max_gain_scenario': self._find_scenario(pnl_matrix, max_gain, price_changes, iv_changes),
                'max_loss_scenario': self._find_scenario(pnl_matrix, max_loss, price_changes, iv_changes),
                'win_probability': (positive_scenarios / total_scenarios) * 100,
                'calculated_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Scenario analysis error: {e}")
            return {}
    
    def _find_scenario(self, matrix, target_value, price_changes, iv_changes):
        """Find which scenario produced the target value"""
        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                if val == target_value:
                    return {
                        'price_change': price_changes[i],
                        'iv_change': iv_changes[j]
                    }
        return None
    
    def generate_heatmap_data(self, pnl_matrix, price_changes, iv_changes):
        """Format data for heatmap visualization"""
        return {
            'x_labels': [f"{iv:+.0f}%" for iv in iv_changes],
            'y_labels': [f"{price:+.0f}%" for price in price_changes],
            'values': pnl_matrix,
            'title': 'P&L Heatmap'
        }


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("  SCENARIO ANALYSIS ENGINE")
    print("=" * 80)
    
    engine = ScenarioAnalysisEngine()
    
    print("\n[INFO] Scenario Analysis Features:")
    print("  - Price scenarios (±10%)")
    print("  - IV scenarios (±50%)")
    print("  - P&L matrix generation")
    print("  - Greeks sensitivity")
    print("  - Best/worst scenario identification")
    print("  - Win probability calculation")
    
    print("\n[INFO] Output Format:")
    print("  - Heatmap data (price × IV)")
    print("  - Risk metrics")
    print("  - Scenario details")
    
    print("\n" + "=" * 80)
    print("  SCENARIO ANALYSIS READY")
    print("=" * 80)
