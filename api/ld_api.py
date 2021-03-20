import secrets

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

import compute.middle_layer as cml
from utils.env import API_USER, API_PASS

app = FastAPI()

security = HTTPBasic()


class DiscordUser(BaseModel):
    discord_user_id: int
    discord_user_name: str
    # is_player: Optional[bool] = None


class Player(BaseModel):
    ingame_player_name: str
    discord_user_id: int
    discord_user_name: str


class Score(BaseModel):
    discord_user_id: int
    discord_user_name: str
    proof: str
    difficulty: str
    score: str
    misses: str
    perfects_percent: str
    triggers: str
    map_uuid: str


def check_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, API_USER)
    correct_password = secrets.compare_digest(credentials.password, API_PASS)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


# GETS


@app.get("/topplayers")
def top(nb_to_show: Optional[int] = 10, credentials=Depends(check_credentials)):
    return cml.get_top_players(nb_to_show, format=False)


@app.get("/topmap/{map_name}")
def top_map(map_name: str, nb_to_show: Optional[int] = 10, credentials=Depends(check_credentials)):
    return cml.get_top_players_on_specific_map(map_name, nb_to_show, format=False)


@app.get("/playerstats_by_name/{ingame_player_name}")
def playerstats_by_name(ingame_player_name: str, credentials=Depends(check_credentials)):
    return cml.get_player_stats(0, ingame_player_name, format=False)


@app.get("/playerstats_by_discord_id/{discord_id}")
def playerstats_by_discord_id(discord_id: int, credentials=Depends(check_credentials)):
    return cml.get_player_stats(discord_id, "", format=False)


@app.get("/search_player/{ingame_player_name}")
def search_player(ingame_player_name: str, credentials=Depends(check_credentials)):
    return cml.search_players_names_by_name_pattern(ingame_player_name, format=False)


@app.get("/submissions")
def submissions(credentials=Depends(check_credentials)):
    return cml.get_pending_subs_player(format=False)


# @app.get("/submissions/{discord_user_id}")
# def submissions_by_discord_id(discord_user_id: int, credentials = Depends(check_credentials)):
#    return cml.get_pendings_submissions(discord_user_id)

# PUTS


@app.put("/register")
def register(player: Player, credentials=Depends(check_credentials)):
    # return cml.registering_player(player.discord_user_id, player.discord_user_name, player.ingame_player_name)
    return cml.registering_player(
        player.discord_user_id, player.discord_user_name, player.ingame_player_name
    )


@app.put("/unregister/{confirm_string}")
def unregister(
    discord_user: DiscordUser, confirm_string: str, credentials=Depends(check_credentials)
):
    return cml.unregistering_player(
        discord_user.discord_user_id, discord_user.discord_user_name, confirm_string
    )


@app.put("/rename/{new_ingame_name}")
def rename(discord_user: DiscordUser, new_ingame_name: str, credentials=Depends(check_credentials)):
    return cml.rename_player(discord_user.discord_user_id, new_ingame_name)


@app.put("/submit_score")
def submit(score: Score, credentials=Depends(check_credentials)):
    return cml.handle_player_submission(
        score.discord_user_id,
        score.discord_user_name,
        score.proof,
        score.difficulty,
        score.score,
        score.misses,
        score.perfects_percent,
        score.triggers,
        "",
        "",
        "",
        score.map_uuid,
    )


@app.put("/cancel_submission/{submission_id}")
def cancel_submission(submission_id: int, credentials=Depends(check_credentials)):
    return cml.cancel_submission_of_player(0, submission_id, api_call=True)


@app.put("/validate_submission/{submission_id}")
def validate_submission(submission_id: int, credentials=Depends(check_credentials)):
    return cml.validate_submission(submission_id, api_call=True)
