from __future__ import annotations
import random
from typing import List, Dict

import Game
import Player
from nn.network import Network
from nn.network_definition import DominionNetwork
from nn.network_definition_no_rnn import DominionNetworkNoRecurrent


if __name__ == "__main__":
    network = DominionNetwork()

    for idx in range(10000):
        print("Game number " + str(idx))

        names = random.choice(
            [["*Alex", "*Ben"], ["*Alex", "+Ben"], ["+Alex", "*Ben"]]
        )

        players: List[Player.Player] = []
        networks: Dict[str, Network] = {}

        for play_order, name in enumerate(names):
            if name[0] == "*":
                players.append(Player.ComputerPlayer(name[1:], play_order))
            elif name[0] == "^":
                players.append(Player.QvistPlayer(name[1:], play_order))
            elif name[0] == "+":
                players.append(Player.NNPlayer(name[1:], play_order, game_index=idx))
            else:
                players.append(Player.Player(name, play_order))
            networks[name[1:]] = random.choice([network])

        game = Game.Game(players)
        game.play_game(networks)
