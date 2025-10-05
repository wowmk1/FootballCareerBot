import random
import config

class DiceRoller:
    """Handles all DnD-style dice rolling for match events"""
    
    @staticmethod
    def roll_d20():
        """Roll a d20 (1-20)"""
        return random.randint(1, 20)
    
    @staticmethod
    def calculate_modifier(stat_value):
        """Convert stat (0-99) to d20 modifier
        
        60-69 = +6 modifier
        70-79 = +7 modifier  
        80-89 = +8 modifier
        90-99 = +9 modifier
        
        Formula: stat // 10
        """
        return stat_value // 10
    
    @staticmethod
    def make_check(stat_value, difficulty_class, advantage=False, disadvantage=False):
        """Make a d20 ability check
        
        Args:
            stat_value: Player's stat (0-99)
            difficulty_class: DC to beat
            advantage: Roll twice, take higher
            disadvantage: Roll twice, take lower
            
        Returns:
            dict with roll details and success boolean
        """
        modifier = DiceRoller.calculate_modifier(stat_value)
        
        if advantage:
            roll1 = DiceRoller.roll_d20()
            roll2 = DiceRoller.roll_d20()
            dice_roll = max(roll1, roll2)
            roll_type = "advantage"
            rolls_made = [roll1, roll2]
        elif disadvantage:
            roll1 = DiceRoller.roll_d20()
            roll2 = DiceRoller.roll_d20()
            dice_roll = min(roll1, roll2)
            roll_type = "disadvantage"
            rolls_made = [roll1, roll2]
        else:
            dice_roll = DiceRoller.roll_d20()
            roll_type = "normal"
            rolls_made = [dice_roll]
        
        total = dice_roll + modifier
        success = total >= difficulty_class
        
        critical_success = dice_roll == 20
        critical_failure = dice_roll == 1
        
        return {
            'dice_roll': dice_roll,
            'modifier': modifier,
            'total': total,
            'difficulty_class': difficulty_class,
            'success': success,
            'critical_success': critical_success,
            'critical_failure': critical_failure,
            'roll_type': roll_type,
            'rolls_made': rolls_made,
            'stat_value': stat_value
        }
    
    @staticmethod
    def determine_difficulty(action_type, game_situation):
        """Determine DC based on action and situation
        
        Args:
            action_type: 'shoot', 'pass', 'dribble', 'defend', 'save'
            game_situation: dict with context (position, defenders, etc.)
            
        Returns:
            int: Difficulty Class (DC)
        """
        base_dc = config.DC_MEDIUM  # 15
        
        if action_type == config.ACTION_SHOOT:
            if game_situation.get('in_box'):
                base_dc = config.DC_EASY  # 10
            if game_situation.get('one_on_one'):
                base_dc = config.DC_EASY  # 10
            if game_situation.get('crowded'):
                base_dc = config.DC_HARD  # 20
                
        elif action_type == config.ACTION_PASS:
            if game_situation.get('under_pressure'):
                base_dc = config.DC_HARD  # 20
            else:
                base_dc = config.DC_EASY  # 10
                
        elif action_type == config.ACTION_DRIBBLE:
            defenders = game_situation.get('defenders', 1)
            base_dc = config.DC_MEDIUM + (defenders * 2)
            
        elif action_type == config.ACTION_DEFEND:
            if game_situation.get('attacker_pace') > 85:
                base_dc = config.DC_HARD  # 20
            else:
                base_dc = config.DC_MEDIUM  # 15
                
        elif action_type == config.ACTION_SAVE:
            if game_situation.get('shot_power') > 85:
                base_dc = config.DC_HARD  # 20
            else:
                base_dc = config.DC_MEDIUM  # 15
        
        return min(base_dc, config.DC_VERY_HARD)
    
    @staticmethod
    def format_roll_result(roll_result, action_description):
        """Format roll result into readable text
        
        Returns:
            str: Formatted text for Discord
        """
        emoji_map = {
            'critical_success': '🌟',
            'success': '✅',
            'failure': '❌',
            'critical_failure': '💥'
        }
        
        if roll_result['critical_success']:
            outcome = emoji_map['critical_success']
            result_text = "**CRITICAL SUCCESS!**"
        elif roll_result['critical_failure']:
            outcome = emoji_map['critical_failure']
            result_text = "**CRITICAL FAILURE!**"
        elif roll_result['success']:
            outcome = emoji_map['success']
            result_text = "**SUCCESS!**"
        else:
            outcome = emoji_map['failure']
            result_text = "**FAILED!**"
        
        if roll_result['roll_type'] == 'advantage':
            roll_text = f"🎲 Rolls: {roll_result['rolls_made'][0]}, {roll_result['rolls_made'][1]} (advantage) → {roll_result['dice_roll']}"
        elif roll_result['roll_type'] == 'disadvantage':
            roll_text = f"🎲 Rolls: {roll_result['rolls_made'][0]}, {roll_result['rolls_made'][1]} (disadvantage) → {roll_result['dice_roll']}"
        else:
            roll_text = f"🎲 Roll: {roll_result['dice_roll']}"
        
        formatted = (
            f"{outcome} {result_text}\n"
            f"{roll_text}\n"
            f"➕ Modifier: +{roll_result['modifier']}\n"
            f"🎯 Total: **{roll_result['total']}** vs DC {roll_result['difficulty_class']}\n"
        )
        
        return formatted

# Global dice roller instance
dice_roller = DiceRoller()
