import pandas as pd

from gk_scouting.similarity_engine import find_similar_goalkeepers


def make_table():
    return pd.DataFrame(
        {
            "minutes": [900, 900, 900, 120],
            "sweeper_actions_p90": [2.0, 2.1, 5.0, 2.0],
            "avg_distance_from_goal": [12.0, 12.2, 20.0, 12.0],
            "save_pct": [75.0, 74.5, 50.0, 75.0],
            "pass_success_pct": [85.0, 84.0, 60.0, 85.0],
            "avg_pass_length": [35.0, 35.5, 50.0, 35.0],
            "long_ball_pct": [30.0, 31.0, 60.0, 30.0],
        },
        index=["Target Keeper", "Similar Keeper", "Different Keeper", "Too Few Minutes"],
    )


def test_similarity_excludes_target_and_low_minute_players():
    result = find_similar_goalkeepers(
        make_table(),
        "Target Keeper",
        top_n=5,
        min_minutes=180,
    )

    assert "Target Keeper" not in result.index
    assert "Too Few Minutes" not in result.index
    assert result.index[0] == "Similar Keeper"


def test_similarity_returns_percentage_between_zero_and_hundred():
    result = find_similar_goalkeepers(
        make_table(),
        "Target Keeper",
        top_n=2,
    )

    assert result["similarity_pct"].between(0, 100).all()
    assert result["similarity"].between(0, 1).all()
