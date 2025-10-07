import random

class EnhancedMatchScenarios:
    """Realistic match scenarios based on position and game state"""
    
    @staticmethod
    def get_scenario(position, minute, team_possession=True):
        """Get contextual scenario based on position and game state"""
        
        scenarios = {
            'ST': {
                'attacking': [
                    ("Through on goal! Only the keeper to beat!", ['shoot', 'round_keeper', 'chip'], 'GK'),
                    ("Ball drops in the box after a scramble!", ['shoot', 'control_shoot'], 'CB'),
                    ("Crosses coming in from the wing!", ['header', 'volley'], 'CB'),
                    ("1v1 with the defender at the edge of the box!", ['dribble', 'shoot', 'pass'], 'CB'),
                    ("Quick counter-attack, 2v1 situation!", ['shoot', 'pass_to_teammate'], None),
                ],
                'defending': [
                    ("Pressing the defender high up!", ['press_defender', 'anticipate_pass'], 'CB'),
                    ("Corner kick, need to win the header!", ['defensive_header'], 'CB'),
                ]
            },
            'W': {
                'attacking': [
                    ("Racing down the wing with space!", ['cross', 'cut_inside', 'take_on_fullback'], 'FB'),
                    ("Isolated 1v1 with the fullback!", ['dribble', 'pace_burst', 'cross'], 'FB'),
                    ("Cutting inside on your stronger foot!", ['shoot', 'through_ball', 'dribble'], 'CDM'),
                    ("Counter-attack, lots of space ahead!", ['sprint', 'cross_early', 'drive_inside'], None),
                ],
                'defending': [
                    ("Tracking back to help defend!", ['track_runner', 'tactical_foul', 'stay_with_man'], 'W'),
                    ("Opposition counter, need to slow them down!", ['tactical_foul', 'guide_outside'], None),
                ]
            },
            'CAM': {
                'attacking': [
                    ("Space opens up outside the box!", ['shoot', 'through_ball', 'dribble'], 'CDM'),
                    ("Quick one-two opportunity!", ['quick_pass', 'run_into_box'], 'CM'),
                    ("Striker making a run!", ['through_ball', 'hold_ball', 'shoot'], 'CB'),
                    ("Free kick just outside the box!", ['shoot', 'cross', 'pass_short'], 'GK'),
                ],
                'defending': [
                    ("Need to press their playmaker!", ['press', 'cut_passing_lane'], 'CAM'),
                    ("Dropping deep to help defend!", ['interception', 'track_runner'], 'CM'),
                ]
            },
            'CM': {
                'attacking': [
                    ("Building up play from midfield!", ['pass', 'through_ball', 'switch_play'], 'CM'),
                    ("Late run into the box!", ['shoot', 'header', 'cut_back'], 'CDM'),
                    ("Space to drive forward!", ['dribble', 'pass', 'long_shot'], 'CM'),
                ],
                'defending': [
                    ("Breaking up their attack!", ['tackle', 'interception', 'tactical_foul'], 'CAM'),
                    ("Covering the defense!", ['track_runner', 'block', 'clearance'], 'W'),
                ]
            },
            'CDM': {
                'attacking': [
                    ("Starting the attack from deep!", ['pass', 'long_ball', 'drive_forward'], 'CAM'),
                    ("Set piece opportunity!", ['header', 'get_in_position'], 'CB'),
                ],
                'defending': [
                    ("They're breaking through the middle!", ['tackle', 'block', 'tactical_foul'], 'CAM'),
                    ("Protecting the back four!", ['interception', 'cover', 'clear'], 'ST'),
                    ("Dangerous counter-attack incoming!", ['tactical_foul', 'sprint_back', 'position'], 'W'),
                ]
            },
            'FB': {
                'attacking': [
                    ("Overlapping run down the flank!", ['cross', 'cut_back', 'shoot'], 'W'),
                    ("Space to get forward!", ['cross', 'pass_inside', 'take_on'], 'W'),
                ],
                'defending': [
                    ("Winger running at you!", ['tackle', 'show_outside', 'stay_on_feet'], 'W'),
                    ("2v1 overload against you!", ['delay', 'force_wide', 'tactical_foul'], 'W'),
                    ("Cross coming in!", ['block', 'header', 'track_runner'], None),
                ]
            },
            'CB': {
                'attacking': [
                    ("Corner kick opportunity!", ['header', 'get_in_box', 'near_post_run'], 'CB'),
                    ("Building from the back!", ['pass', 'long_ball', 'carry_forward'], None),
                ],
                'defending': [
                    ("Striker through on goal!", ['tackle', 'block', 'shepherd_wide'], 'ST'),
                    ("High ball into the box!", ['header', 'clearance', 'control'], 'ST'),
                    ("1v1 with the striker!", ['stand_ground', 'tackle', 'force_wide'], 'ST'),
                    ("Dangerous through ball!", ['intercept', 'recover', 'foul'], 'CAM'),
                ]
            },
            'GK': {
                'attacking': [
                    ("Quick counter opportunity!", ['throw', 'kick_long', 'play_short'], None),
                    ("Building from the back!", ['pass_to_cb', 'play_to_fb'], None),
                ],
                'defending': [
                    ("1v1 with the striker!", ['stay_big', 'rush_out', 'stay_on_line'], 'ST'),
                    ("Shot from distance!", ['dive', 'parry', 'catch'], 'CAM'),
                    ("Cross into the box!", ['claim', 'punch', 'stay_on_line'], None),
                    ("Free kick!", ['position_wall', 'anticipate', 'react'], None),
                ]
            }
        }
        
        # Get scenarios for position
        pos_scenarios = scenarios.get(position, scenarios['CM'])
        
        # Choose attacking or defending based on possession
        scenario_type = 'attacking' if team_possession else 'defending'
        available = pos_scenarios.get(scenario_type, pos_scenarios['attacking'])
        
        # Add time-based urgency
        if minute > 85:
            if team_possession:
                available.append(("Last chance to score!", ['shoot', 'risky_pass', 'dribble'], None))
            else:
                available.append(("Defending the lead!", ['clear', 'time_waste', 'foul'], None))
        
        return random.choice(available) if available else ("Standard play", ['pass', 'dribble', 'shoot'], None)

    @staticmethod
    def get_follow_up_description(action, success, position):
        """Get narrative follow-up after an action"""
        
        follow_ups = {
            'shoot': {
                True: [
                    "The ball flies towards goal!",
                    "What a strike!",
                    "He's hit it sweetly!",
                    "Powerful shot!"
                ],
                False: [
                    "Wide of the target!",
                    "Over the bar!",
                    "Weak effort saved easily.",
                    "Blocked by the defender!"
                ]
            },
            'dribble': {
                True: [
                    "Beats his man brilliantly!",
                    "Excellent skill to get past!",
                    "He's through!",
                    "Fantastic footwork!"
                ],
                False: [
                    "Dispossessed!",
                    "Good defending!",
                    "Loses the ball!",
                    "Tackled cleanly!"
                ]
            },
            'pass': {
                True: [
                    "Perfect weight on the pass!",
                    "Finds his teammate!",
                    "Excellent vision!",
                    "Splits the defense!"
                ],
                False: [
                    "Intercepted!",
                    "Poor pass!",
                    "Straight to the opponent!",
                    "Overhit!"
                ]
            },
            'tackle': {
                True: [
                    "Excellent tackle!",
                    "Wins the ball cleanly!",
                    "Perfectly timed!",
                    "Strong challenge!"
                ],
                False: [
                    "Mistimed!",
                    "The attacker skips past!",
                    "Foul given!",
                    "Beaten easily!"
                ]
            }
        }
        
        action_results = follow_ups.get(action, follow_ups['pass'])
        return random.choice(action_results[success])
