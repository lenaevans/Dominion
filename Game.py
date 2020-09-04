from __future__ import annotations
import random
import pandas
import numpy as np
from collections import defaultdict
from typing import Dict, List, DefaultDict, Tuple

import Player
import Card
from utils import players_around, getcard
from nn.network_definition import DominionNetwork


class Game:
    def __init__(self, players: List[Player.Player], verbose: bool = True):
        self.players = players
        self.trash: List[Card.Card] = []
        self.supply = self.setup_supply()
        self.supply_order: Dict[int, List[str]] = {}
        self.verbose = verbose

        for card_name in Card.CardNameMap:
            card = Card.CardNameMap[card_name]
            if card.cost in self.supply_order:
                self.supply_order[card.cost].append(card_name)
            else:
                self.supply_order[card.cost] = [card_name]

        self.turns = 0

    def setup_supply(self) -> DefaultDict[str, List[Card.Card]]:
        if len(self.players) > 2:
            nV = 12
        else:
            nV = 8
        nC = -10 + 10 * len(self.players)

        # Define box
        box: Dict[str, List[Card.Card]] = {}
        box["Woodcutter"] = [Card.Woodcutter()] * 10
        box["Smithy"] = [Card.Smithy()] * 10
        box["Laboratory"] = [Card.Laboratory()] * 10
        box["Village"] = [Card.Village()] * 10
        box["Festival"] = [Card.Festival()] * 10
        box["Market"] = [Card.Market()] * 10
        box["Chancellor"] = [Card.Chancellor()] * 10
        box["Workshop"] = [Card.Workshop()] * 10
        box["Moneylender"] = [Card.Moneylender()] * 10
        box["Chapel"] = [Card.Chapel()] * 10
        box["Cellar"] = [Card.Cellar()] * 10
        box["Remodel"] = [Card.Remodel()] * 10
        box["Adventurer"] = [Card.Adventurer()] * 10
        box["Feast"] = [Card.Feast()] * 10
        box["Mine"] = [Card.Mine()] * 10
        box["Library"] = [Card.Library()] * 10
        box["Gardens"] = [Card.Gardens()] * nV
        box["Moat"] = [Card.Moat()] * 10
        box["Council Room"] = [Card.Council_Room()] * 10
        box["Witch"] = [Card.Witch()] * 10
        box["Bureaucrat"] = [Card.Bureaucrat()] * 10
        box["Militia"] = [Card.Militia()] * 10
        box["Spy"] = [Card.Spy()] * 10
        # box["Thief"] = [Card.Thief()] * 10
        box["Throne Room"] = [Card.Throne_Room()] * 10
        box["Duke"] = [Card.Duke()] * nV
        box["Poacher"] = [Card.Poacher()] * 10
        box["Vassal"] = [Card.Vassal()] * 10
        box["Artisan"] = [Card.Artisan()] * 10
        box["Courtyard"] = [Card.Courtyard()] * 10
        box["Shanty Town"] = [Card.Shanty_Town()] * 10
        box["Baron"] = [Card.Baron()] * 10
        box["Ill-Gotten Gains"] = [Card.IllGottenGains()] * 10
        box["Treasure Trove"] = [Card.Treasure_Trove()] * 10
        box["Cache"] = [Card.Cache()] * 10
        box["Harem"] = [Card.Harem()] * nV
        box["Feodum"] = [Card.Feodum()] * nV
        box["Tunnel"] = [Card.Tunnel()] * nV
        box["Silk Road"] = [Card.Silk_Road()] * nV
        box["Fairgrounds"] = [Card.Fairgrounds()] * nV
        box["Farmland"] = [Card.Farmland()] * nV
        box["Great Hall"] = [Card.Great_Hall()] * nV
        box["Mill"] = [Card.Mill()] * nV
        box["Bank"] = [Card.Bank()] * 10
        box["Conspirator"] = [Card.Conspirator()] * 10
        box["Ironworks"] = [Card.Ironworks()] * 10
        box["Mining Village"] = [Card.Mining_Village()] * 10
        box["Nobles"] = [Card.Nobles()] * nV
        box["Upgrade"] = [Card.Upgrade()] * 10
        box["Trading Post"] = [Card.Trading_Post()] * 10

        supply_order: Dict[int, List[str]] = {}

        for card_name in Card.CardNameMap:
            card = Card.CardNameMap[card_name]
            if card.cost in supply_order:
                supply_order[card.cost].append(card_name)
            else:
                supply_order[card.cost] = [card_name]

        # Pick 10 cards from box to be in the supply.
        boxlist = [k for k in box]
        random.shuffle(boxlist)
        random10 = boxlist[:10]
        supply = defaultdict(list, [(k, box[k]) for k in random10])

        # The supply always has these cards
        supply["Copper"] = [Card.Copper()] * (60 - len(self.players) * 7)
        supply["Silver"] = [Card.Silver()] * 40
        supply["Gold"] = [Card.Gold()] * 30
        supply["Estate"] = [Card.Estate()] * nV
        supply["Duchy"] = [Card.Duchy()] * nV
        supply["Province"] = [Card.Province()] * nV
        supply["Curse"] = [Card.Curse()] * nC

        return supply

    @staticmethod
    def count_cards_in_pile(card_name: str, pile: List[Card.Card]) -> int:
        count = 0
        for card in pile:
            if card.name == card_name:
                count += 1
        return count

    @staticmethod
    def gameover(supply: DefaultDict[str, List[Card.Card]]):
        if len(supply["Province"]) == 0:
            return True
        out = 0
        for stack in supply:
            if len(supply[stack]) == 0:
                out += 1
                print(str(stack) + " is out!")
        if out >= 3:
            return True
        return False

    @staticmethod
    def cardsummaries(players: List[Player.Player]) -> pandas.DataFrame:
        cardsums = {}
        for player in players:
            cardsums[player.name] = player.cardsummary()
        return pandas.DataFrame(cardsums).fillna(0).astype(int)

    def get_card_features(self, card_name: str, player: Player.Player,) -> List[float]:

        card = Card.CardNameMap[card_name]

        cost = float(card.cost) / 8
        vpoints = float(card.get_points(player)) / 6
        is_victory = float("victory" in card.categories)
        is_action = float("action" in card.categories)
        is_coin = float("coin" in card.categories)
        is_attack = float("attack" in card.categories)
        is_reaction = float("reaction" in card.categories)
        is_duration = float("duration" in card.categories)

        supply_left = float(len(self.supply[card_name])) / 10
        player_deck_count = float(Game.count_cards_in_pile(card_name, player.deck)) / 10
        player_discard_count = (
            float(Game.count_cards_in_pile(card_name, player.discard)) / 10
        )

        opponent_discards = [0.0, 0.0, 0.0]
        opponent_decks = [0.0, 0.0, 0.0]
        for idx, opponent in enumerate(
            players_around(self.players, player, inclusive=False)
        ):
            opponent_discards[idx] = (
                float(Game.count_cards_in_pile(card_name, opponent.discard)) / 10
            )
            opponent_decks[idx] = (
                float(Game.count_cards_in_pile(card_name, opponent.stack())) / 10
            )

        player_hand_count = float(Game.count_cards_in_pile(card_name, player.hand)) / 10
        trash_count = float(Game.count_cards_in_pile(card_name, self.trash)) / 10

        return [
            cost,
            vpoints,
            is_victory,
            is_action,
            is_coin,
            is_attack,
            is_reaction,
            is_duration,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            supply_left,
            player_deck_count,
            player_discard_count,
            player_hand_count,
            opponent_discards[0],
            opponent_discards[1],
            opponent_discards[2],
            opponent_decks[0],
            opponent_decks[1],
            opponent_decks[2],
            trash_count,
        ]

    def get_game_state(
        self, player: Player.Player, cards_to_draw: int = 0,
    ) -> Tuple[
        List[List[float]],
        List[int],
        List[List[float]],
        List[int],
        List[List[float]],
        List[float],
    ]:

        opponent_states: List[List[float]] = []

        for opponent in players_around(self.players, player, inclusive=False):
            opponent_states.append(
                [
                    float(len(opponent.deck)) / 40,
                    float(len(opponent.discard)) / 40,
                    float(len(opponent.hand)) / 5,
                    float(opponent.calcpoints()) / 30,
                    float(opponent.our_turn),
                ]
            )

        hand_state: List[List[float]] = []
        hand_one_hot: List[int] = []

        for card in player.hand:
            hand_state.append(self.get_card_features(card.name, player))
            hand_one_hot.append(Card.CardIndexMap[card.name])

        kingdom_state: List[List[float]] = []
        kingdom_one_hot: List[int] = []

        for card_name in self.supply:
            kingdom_state.append(self.get_card_features(card_name, player))
            kingdom_one_hot.append(Card.CardIndexMap[card_name])

        game_state = [
            float(player.actions),
            float(player.buys),
            float(self.turns) / 20,
            float(cards_to_draw) / 5,
            float(player.purse) / 8,
            float(player.our_turn),
            float(len(player.deck)) / 40,
            float(len(player.discard)) / 40,
            float(len(player.hand)) / 5,
            float(player.calcpoints()) / 30,
        ]

        return (
            hand_state,
            hand_one_hot,
            kingdom_state,
            kingdom_one_hot,
            opponent_states,
            game_state,
        )

    def take_turn(self, player: Player.Player, network: DominionNetwork):
        player.start_turn()

        print(player.name + "'s turn")

        print("Starting hand")
        for c in player.hand:
            print(c.name)

        # Action phase
        while player.actions > 0:
            move_to_play = player.choose_action(self, network)
            if move_to_play:
                print("Playing " + move_to_play)
                c = getcard(
                    move_to_play, self.supply, player.hand, "your hand", ["action"]
                )
                player.playcard(c, self, network)
                player.actions_played += 1
                if player.type != "neural_network":
                    board_state = self.get_game_state(player)
                    hand = board_state[0]
                    if len(hand) == 0:
                        print("Empty hand")
                        hand = np.zeros((1, 33))

                    hand_one_hot = board_state[1]
                    if len(hand_one_hot) == 0:
                        hand_one_hot = [0]

                    player.current_game_hand_states.append(hand)
                    player.current_game_hand_one_hot.append(hand_one_hot)
                    player.current_game_kingdom_states.append(board_state[2])
                    player.current_game_kingdom_one_hot.append(board_state[3])
                    player.current_game_opponent_states.append(board_state[4])
                    player.current_game_states.append(board_state[5])
            else:
                player.actions = 0
                if player.type != "neural_network":
                    board_state = self.get_game_state(player)
                    hand = board_state[0]
                    if len(hand) == 0:
                        print("Empty hand")
                        hand = np.zeros((1, 33))

                    hand_one_hot = board_state[1]
                    if len(hand_one_hot) == 0:
                        hand_one_hot = [0]

                    player.current_game_hand_states.append(hand)
                    player.current_game_hand_one_hot.append(hand_one_hot)
                    player.current_game_kingdom_states.append(board_state[2])
                    player.current_game_kingdom_one_hot.append(board_state[3])
                    player.current_game_opponent_states.append(board_state[4])
                    player.current_game_states.append(board_state[5])
                break

        print("Hand after playing actions")
        for c in player.hand:
            print(c.name)

        # Play treasures
        while len(player.hand) > 0:
            to_play = player.choose_treasure(self, network)
            if to_play:
                print("Using " + to_play)
                c = getcard(to_play, self.supply, player.hand, "your hand", ["coin"])
                c.onuse(player, self, network, mock=False)
                player.hand.remove(c)
                player.played.append(c)
                player.treasures_played += 1

                if player.type != "neural_network":
                    board_state = self.get_game_state(player)
                    hand = board_state[0]
                    if len(hand) == 0:
                        print("Empty hand")
                        hand = np.zeros((1, 33))

                    hand_one_hot = board_state[1]
                    if len(hand_one_hot) == 0:
                        hand_one_hot = [0]

                    player.current_game_hand_states.append(hand)
                    player.current_game_hand_one_hot.append(hand_one_hot)
                    player.current_game_kingdom_states.append(board_state[2])
                    player.current_game_kingdom_one_hot.append(board_state[3])
                    player.current_game_opponent_states.append(board_state[4])
                    player.current_game_states.append(board_state[5])
            else:
                if player.type != "neural_network":
                    board_state = self.get_game_state(player)
                    hand = board_state[0]
                    if len(hand) == 0:
                        print("Empty hand")
                        hand = np.zeros((1, 33))

                    hand_one_hot = board_state[1]
                    if len(hand_one_hot) == 0:
                        hand_one_hot = [0]

                    player.current_game_hand_states.append(hand)
                    player.current_game_hand_one_hot.append(hand_one_hot)
                    player.current_game_kingdom_states.append(board_state[2])
                    player.current_game_kingdom_one_hot.append(board_state[3])
                    player.current_game_opponent_states.append(board_state[4])
                    player.current_game_states.append(board_state[5])
                break

        print("Hand after playing treasures")
        for c in player.hand:
            print(c.name)

        # Buy phase
        print("Total coins: " + str(player.purse))
        while player.buys > 0:
            purchase = player.choose_buy(
                self, network, upto=player.purse, optional=True
            )

            if purchase:
                c = getcard(purchase, self.supply, upto=player.purse)
                print("Purchased " + purchase)
                player.discard.append(self.supply[purchase].pop())
                player.buys = player.buys - 1
                player.purse = player.purse - c.cost
                player.cprint(player.name + " bought " + c.name + ". ")
                c.ongain(player, self, network, mock=False)
                c.onbuy(player, self, network, mock=False)
                player.cards_bought += 1

                if player.type != "neural_network":
                    board_state = self.get_game_state(player)
                    hand = board_state[0]
                    if len(hand) == 0:
                        print("Empty hand")
                        hand = np.zeros((1, 33))

                    hand_one_hot = board_state[1]
                    if len(hand_one_hot) == 0:
                        hand_one_hot = [0]

                    player.current_game_hand_states.append(hand)
                    player.current_game_hand_one_hot.append(hand_one_hot)
                    player.current_game_kingdom_states.append(board_state[2])
                    player.current_game_kingdom_one_hot.append(board_state[3])
                    player.current_game_opponent_states.append(board_state[4])
                    player.current_game_states.append(board_state[5])
            else:
                player.buys = 0
                if player.type != "neural_network":
                    board_state = self.get_game_state(player)
                    hand = board_state[0]
                    if len(hand) == 0:
                        print("Empty hand")
                        hand = np.zeros((1, 33))

                    hand_one_hot = board_state[1]
                    if len(hand_one_hot) == 0:
                        hand_one_hot = [0]

                    player.current_game_hand_states.append(hand)
                    player.current_game_hand_one_hot.append(hand_one_hot)
                    player.current_game_kingdom_states.append(board_state[2])
                    player.current_game_kingdom_one_hot.append(board_state[3])
                    player.current_game_opponent_states.append(board_state[4])
                    player.current_game_states.append(board_state[5])

        player.cleanup()

    def play_game(self, networks=Dict[str, DominionNetwork]) -> List[str]:
        turn = 0
        while not Game.gameover(self.supply) and turn <= 75:
            turn += 1
            print("turn " + str(turn))
            name_list = []
            cost_list = []
            quantity_list = []
            for value in self.supply_order:
                for stack in self.supply_order[value]:
                    if stack in self.supply:
                        name_list.append(stack)
                        cost_list.append(value)
                        quantity_list.append(len(self.supply[stack]))
            supplydf = pandas.DataFrame(
                data={"Cost": cost_list, "Remaining": quantity_list}, index=name_list
            )
            if self.verbose:
                print("\n\nSUPPLY")
                print(supplydf)
                print("\r")
                print(
                    Game.cardsummaries(self.players).loc[
                        ["Total cards", "VICTORY POINTS"]
                    ]
                )
                print("\nStart of turn " + str(turn))
            for player in self.players:
                if not Game.gameover(self.supply):
                    self.take_turn(player, networks[player.name])
                    last_turn = player.order
                else:
                    break

        # Final scores and winners
        dcs = Game.cardsummaries(self.players)
        vp = dcs.loc["VICTORY POINTS"]
        vpmax = vp.max()
        high_scores2 = []
        high_scores1 = []
        winners = []
        for player in self.players:
            if vp.loc[player.name] == vpmax:
                if player.order > last_turn:
                    high_scores2.append(player.name)
                else:
                    high_scores1.append(player.name)

        if len(high_scores2) > 0:
            winners = high_scores2
        else:
            winners = high_scores1

        if len(winners) > 1:
            winstring = " and ".join(winners) + " win!"
        else:
            winstring = " ".join([winners[0], "wins!"])

        for player in self.players:
            if (player.calcpoints() == vpmax) and (turn <= 75):
                print(player.calcpoints())
                if len(high_scores2) + len(high_scores1) == 1:
                    player.game_over(
                        networks[player.name], 1.0, float(max(vp) - min(vp)) / 10.0
                    )
                else:
                    player.game_over(
                        networks[player.name], 0.0, float(max(vp) - min(vp)) / 10.0
                    )
            else:
                player.game_over(
                    networks[player.name], -1.0, float(min(vp) - max(vp)) / 10.0
                )

        if not self.verbose:
            print("\n\nGAME OVER!!!   " + winstring + "\n")
        return winners
