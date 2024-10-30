from typing import List, Dict

k = 32


def get_expectation(rating_1: int, rating_2: int) -> float:
        """compute the probability that a team with rating_1 elo
        value has to win againts a team with rating_2 elo value.

        Args:
            elo_win (int): elo rating of first team
            elo_lose (int): elo rating of second team

        Returns:
            float: win probability of the first team against the second team.
        """
        return (1.0 / (1.0 + pow(10, ((rating_2 - rating_1) / 1000))))


def modify_rating(old_reating: int, expected: float, result: float, kFactor: float) -> int:
        """Compute the elo rating of a player based on the outcome of a game

        Args:
            old_reating (int): _description_
            expected (float): _description_
            result (float): _description_
            kFactor (float): _description_

        Returns:
            int: _description_
        """
        return (old_reating + kFactor * (result - expected))


def compute_ratings(elo_data: dict) -> dict:
        """Calculate new Elo ratings for each player based on game results.
    
        Args:
                elo_data (dict): Dictionary containing 'winners' and 'losers' keys with lists of player Elo values.
        
        Returns:
                dict: Updated Elo ratings in the same structure as input.
        """
        # Calculate average Elo for each team
        winners_avg_elo = sum(elo_data['winners']) / len(elo_data['winners'])
        losers_avg_elo = sum(elo_data['losers']) / len(elo_data['losers'])
        
        # Calculate expectations
        winners_expectation = get_expectation(winners_avg_elo, losers_avg_elo)
        losers_expectation = get_expectation(losers_avg_elo, winners_avg_elo)
        
        # Compute new Elo ratings for each player
        updated_elos = {
                'winners': [
                        modify_rating(elo_data['winners'][0], winners_expectation, 1.0, k),
                        modify_rating(elo_data['winners'][1], winners_expectation, 1.0, k)
                ],
                'losers': [
                        modify_rating(elo_data['losers'][0], losers_expectation, 0.0, k),
                        modify_rating(elo_data['losers'][1], losers_expectation, 0.0, k)
                ]
        }
        
        return updated_elos


def calculate_gain_percentage(elo_history: List[int]) -> float:
    """Calculate gain/loss percentage based on Elo history of the last 10 games."""
    if len(elo_history) < 2:
        return 0.0  # Not enough data
    start_elo, end_elo = elo_history[-10], elo_history[-1]
    return ((end_elo - start_elo) / start_elo) * 100 if start_elo else 0.0