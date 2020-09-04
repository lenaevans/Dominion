from __future__ import annotations

import random
import numpy as np
from copy import deepcopy
from typing import List, Tuple, Dict, Callable

import Game
from Card import Card, CardNameMap, Copper, Estate
from nn.network_definition import DominionNetwork
from utils import namesinlist, getcard


class Player:
    def __init__(self, name: str, order: int):
        self.name = name
        self.order = order
        self.hand: List[Card] = []
        self.deck: List[Card] = []
        self.deck += [Copper()] * 7
        self.deck += [Estate()] * 3
        random.shuffle(self.deck)
        self.played: List[Card] = []
        self.discard: List[Card] = []
        self.aside: List[Card] = []
        self.hold: List[Card] = []
        self.turns = 0
        self.type = "normal"
        self.our_turn = 0
        self.actions_played = 0
        self.treasures_played = 0
        self.cards_gained = 0
        self.cards_bought = 0
        self.current_game_hand_states: List[List[List[float]]] = []
        self.current_game_hand_one_hot: List[List[int]] = []
        self.current_game_kingdom_states: List[List[List[float]]] = []
        self.current_game_kingdom_one_hot: List[List[int]] = []
        self.current_game_opponent_states: List[List[List[float]]] = []
        self.current_game_states: List[List[float]] = []
        self.discount_factor = 0.99
        self.batch_size = 1
        for i in range(5):
            self.draw()

    def other(self) -> List[Card]:
        return self.played + self.discard + self.hold + self.aside

    def stack(self) -> List[Card]:
        return (
            self.deck + self.hand + self.played + self.discard + self.aside + self.hold
        )

    def draw(self, dest: List[Card] = None) -> Card:
        # defualt destination is player's hand
        if dest is None:
            dest = self.hand
        # Replenish deck if necessary.
        if len(self.deck) == 0:
            self.deck = self.discard
            self.discard = []
            random.shuffle(self.deck)
        # If deck has cards, add card to destination list
        if len(self.deck) > 0:
            c = self.deck.pop(0)
            dest.append(c)
            return c
        return None

    def start_turn(self):
        self.turns += 1
        self.actions = 1
        self.buys = 1
        self.purse = 0
        self.our_turn = 1

    def cleanup(self):
        self.discard = self.discard + self.played + self.hand + self.aside
        self.played = []
        self.hand = []
        self.aside = []
        self.our_turn = 0
        self.actions_played = 0
        self.treasures_played = 0
        self.cards_gained = 0
        self.cards_bought = 0
        for i in range(5):
            self.draw()

    def playcard(
        self,
        c: Card,
        game: Game.Game,
        network: DominionNetwork,
        draw: bool = True,
        mock: bool = False,
    ) -> int:
        self.actions -= 1
        c.use(self, game.trash)
        c.augment(self, draw)
        cards_from_deck = c.play(self, game, network, mock)
        return cards_from_deck + c.coins

    def choose_action(
        self,
        game: Game.Game,
        network: DominionNetwork,
        optional: bool = True,
        mock: bool = False,
    ) -> str:
        return str(
            input(
                "Which card would you like to play?  You have "
                + str(self.actions)
                + " action(s).\
                             \n-Hit enter for no play. --> "
            )
        )

    def choose_treasure(self, game: Game.Game, network: DominionNetwork) -> str:
        return str(
            input(
                "Which card would you like to play?  You have "
                + str(self.actions)
                + " action(s).\
                             \n-Hit enter for no play. --> "
            )
        )

    def yesnoinput(
        self,
        prompt: str,
        game: Game.Game,
        network: DominionNetwork,
        yesstring: str = "",
        nostring: str = "",
        callbacks: dict = None,
        applyto: Player = None,
        mock: bool = False,
    ) -> bool:
        return bool(input("Do you choose true or false"))

    def choose_buy(
        self,
        game: Game.Game,
        network: DominionNetwork,
        upto: int,
        exact: bool = False,
        optional: bool = False,
        gain: bool = False,
        mock: bool = False,
        constraint: str = None,
        destination: str = None,
    ) -> str:
        buy_string = (
            "Buying power is "
            + str(self.purse)
            + ".  You have "
            + str(self.buys)
            + " buy"
        )
        if self.buys > 1:
            buy_string += "s"
        buy_string += ". "
        purchase = input(
            buy_string
            + "What would you like to purchase?  \n-Hit enter for no purchase.-   --> "
        )
        return purchase

    def choose_discard(
        self,
        prompt: str,
        game: Game.Game,
        network: DominionNetwork,
        constraint: str = None,
        additional_draw: int = 0,
        optional: bool = False,
        trash_card: bool = False,
        ondeck: bool = False,
        mock: bool = False,
    ) -> str:
        return str(input(prompt))

    def hprint(self, string: str):
        print(string)

    def cprint(self, string: str):
        pass

    def show(self, lead: str = ""):
        print(lead + self.name)
        print("hand:", ", ".join(namesinlist(self.hand)))
        if len(self.deck) > 0:
            print(
                "deck (alphabetical order):", ", ".join(sorted(namesinlist(self.deck)))
            )
        if len(self.discard) > 0:
            print("discard:", ", ".join(sorted(namesinlist(self.discard))))
        if len(self.played) > 0:
            print("played:", ", ".join(sorted(namesinlist(self.played))))
        if len(self.aside) > 0:
            print("aside:", ", ".join(sorted(namesinlist(self.aside))))

    def cardsummary(self) -> Dict[str, float]:
        summary: Dict[str, float] = {}
        for c in self.stack():
            if c.name in summary:
                summary[c.name] += 1
            else:
                summary[c.name] = 1
        summary["Total cards"] = len(self.stack())
        summary["VICTORY POINTS"] = self.calcpoints()
        return summary

    def calcpoints(self) -> int:
        vp = 0
        for c in self.stack():
            if "victory" in c.categories or "curse" in c.categories:
                vp += c.get_points(self)
        return vp

    def gain_card(
        self,
        game: Game.Game,
        network: DominionNetwork,
        upto: int,
        exact: bool = False,
        optional: bool = False,
        mock: bool = False,
        constraint: str = None,
        destination: str = None,
    ) -> str:
        card = self.choose_buy(
            game,
            network,
            upto,
            exact=exact,
            optional=optional,
            gain=True,
            mock=mock,
            constraint=constraint,
            destination=destination,
        )
        if card:
            c = getcard(card, game.supply, upto=upto)
            if destination == "hand":
                self.hand.append(game.supply[card].pop())
            else:
                self.discard.append(game.supply[card].pop())
            self.cprint(self.name + " gained " + c.name + ". ")
            c.ongain(self, game, network, mock=False)
            self.cards_gained += 1
            return card
        return None

    def game_over(
        self, network: DominionNetwork, reward: float, point_difference: float
    ):
        print("Reward is " + str(reward))
        print("Point difference is " + str(point_difference))
        print(len(self.current_game_hand_states))

        train_batch_hand = []
        train_batch_hand_one_hot = []
        train_batch_kingdom = []
        train_batch_kingdom_one_hot = []
        train_batch_opponent = []
        train_batch_state = []
        train_batch_reward = []
        train_batch_point_difference = []

        for hand, hand_one_hot, kingdom, kingdom_one_hot, opponent, state in zip(
            reversed(self.current_game_hand_states),
            reversed(self.current_game_hand_one_hot),
            reversed(self.current_game_kingdom_states),
            reversed(self.current_game_kingdom_one_hot),
            reversed(self.current_game_opponent_states),
            reversed(self.current_game_states),
        ):
            train_batch_hand.append(hand)
            train_batch_hand_one_hot.append(hand_one_hot)
            train_batch_kingdom.append(kingdom)
            train_batch_kingdom_one_hot.append(kingdom_one_hot)
            train_batch_opponent.append(opponent)
            train_batch_state.append(state)
            train_batch_reward.append(reward)
            train_batch_point_difference.append(point_difference)

            reward *= self.discount_factor
            point_difference *= self.discount_factor

            if len(train_batch_reward) >= self.batch_size:
                network.update(
                    train_batch_hand,
                    train_batch_hand_one_hot,
                    train_batch_kingdom,
                    train_batch_kingdom_one_hot,
                    train_batch_opponent,
                    train_batch_state,
                    train_batch_reward,
                    train_batch_point_difference,
                )
                train_batch_hand = []
                train_batch_hand_one_hot = []
                train_batch_kingdom = []
                train_batch_kingdom_one_hot = []
                train_batch_opponent = []
                train_batch_state = []
                train_batch_reward = []
                train_batch_point_difference = []

        self.current_game_hand_states = []
        self.current_game_hand_one_hot = []
        self.current_game_kingdom_states = []
        self.current_game_kingdom_one_hot = []
        self.current_game_opponent_states = []
        self.current_game_states = []
        network.get_summary()
        network.save()


class NNPlayer(Player):
    def __init__(
        self,
        name: str,
        order: int,
        initial_exploration_temperature: float = 0.001,
        game_index: int = 1,
    ):
        Player.__init__(self, name, order)

        self.initial_exploration_temperature = initial_exploration_temperature
        self.type = "neural_network"
        self.game_index = game_index

    def get_exploration_factor(self) -> float:
        return self.initial_exploration_temperature * np.power(
            1 - 0.0002, self.game_index
        )

    def play_action_and_get_game_state(
        self, game: Game.Game, action: Card, network: DominionNetwork,
    ) -> Tuple[
        List[List[float]],
        List[int],
        List[List[float]],
        List[int],
        List[List[float]],
        List[float],
    ]:

        game_copy = deepcopy(game)
        self_copy = deepcopy(self)

        if action:
            c = getcard(
                action.name, game_copy.supply, self_copy.hand, "your hand", ["action"]
            )
            self_copy.cprint(self_copy.name + " thought about playing " + c.name + ". ")

            cards_from_deck = self_copy.playcard(
                c, game_copy, network, draw=False, mock=True,
            )
        else:
            self_copy.cprint(self_copy.name + " thought about playing nothing. ")
            self_copy.actions = 0
            cards_from_deck = 0

        game_state = game_copy.get_game_state(self_copy, cards_from_deck)
        self_copy = None
        game_copy = None

        return game_state

    def buy_card_and_get_game_state(
        self,
        game: Game.Game,
        buy: Card,
        network: DominionNetwork,
        gain: bool = False,
        destination: str = None,
    ) -> Tuple[
        List[List[float]],
        List[int],
        List[List[float]],
        List[int],
        List[List[float]],
        List[float],
    ]:

        game_copy = deepcopy(game)
        self_copy = deepcopy(self)

        if buy:
            c = getcard(buy.name, game_copy.supply)
            if c:
                if destination == "hand":
                    self_copy.hand.append(game_copy.supply[buy.name].pop())
                else:
                    self_copy.discard.append(game_copy.supply[buy.name].pop())
                if not gain:
                    self_copy.buys = self_copy.buys - 1
                    self_copy.purse = self_copy.purse - c.cost
                    if self_copy.purse < 0:
                        raise ValueError
                    c.onbuy(self_copy, game_copy, network, mock=True)
                c.ongain(self_copy, game_copy, network, mock=True)
                self_copy.cprint(
                    self_copy.name + " thought about buying " + c.name + ". "
                )
        else:
            self_copy.cprint(self_copy.name + " thought about buying nothing. ")
            if not gain:
                self_copy.buys = 0

        game_state = game_copy.get_game_state(self_copy)
        game_copy = None
        self_copy = None

        return game_state

    def play_treasure_and_get_game_state(
        self, game: Game.Game, treasure: Card, network: DominionNetwork,
    ) -> Tuple[
        List[List[float]],
        List[int],
        List[List[float]],
        List[int],
        List[List[float]],
        List[float],
    ]:

        game_copy = deepcopy(game)
        self_copy = deepcopy(self)

        if treasure is not None:
            c = getcard(
                treasure.name, game_copy.supply, self_copy.hand, "your hand", ["coin"]
            )
            c.onuse(self_copy, game_copy, network, mock=True)
            self_copy.hand.remove(c)
            self_copy.played.append(c)
            self_copy.treasures_played += 1

            self_copy.cprint(self_copy.name + " thought about playing " + c.name + ". ")
        else:
            self_copy.cprint(self_copy.name + " thought about playing nothing. ")

        game_state = game_copy.get_game_state(self_copy)

        game_copy = None
        self_copy = None
        return game_state

    def discard_and_get_game_state(
        self,
        game: Game.Game,
        discard: Card,
        network: DominionNetwork,
        additional_draw: int = 0,
        ondeck: bool = False,
        trash_card: bool = False,
    ) -> Tuple[
        List[List[float]],
        List[int],
        List[List[float]],
        List[int],
        List[List[float]],
        List[float],
    ]:

        game_copy = deepcopy(game)
        self_copy = deepcopy(self)

        if discard:
            c = getcard(discard.name, game_copy.supply, self_copy.hand, "your hand")
            self_copy.hand.remove(c)

            if ondeck:
                self_copy.deck.insert(0, c)
            elif trash_card:
                game_copy.trash.append(c)
                c.ontrash(self_copy, game_copy, network, mock=True)
            else:
                self_copy.discard.append(c)
                c.ondiscard(self_copy, game_copy, network, mock=True)

        game_state = game_copy.get_game_state(self_copy, additional_draw)

        game_copy = None
        self_copy = None
        return game_state

    @staticmethod
    def random_index(scores: List[float], temperature: float) -> int:
        max_score = max(scores)
        weights = [np.exp((x - max_score) / temperature) for x in scores]
        prob: List[float] = weights / sum(weights)

        total = 0.0
        rand = np.random.random()

        for idx, p in enumerate(prob):
            total += p
            if rand <= total:
                return idx
        return -1

    def trycallback(
        self,
        callback: Callable[[Player, Game.Game, DominionNetwork, bool], int],
        game: Game.Game,
        network: DominionNetwork,
        applyto: Player = None,
    ) -> Tuple[
        List[List[float]],
        List[int],
        List[List[float]],
        List[int],
        List[List[float]],
        List[float],
    ]:
        game_copy = deepcopy(game)
        self_copy = deepcopy(self)

        if applyto:
            applyto_copy = deepcopy(applyto)

        if applyto:
            callback(applyto_copy, game_copy, network, True)
        else:
            callback(self_copy, game_copy, network, True)

        # TODO: Should add in draw cards context here
        game_state = game_copy.get_game_state(self_copy)

        game_copy = None
        self_copy = None
        if applyto:
            applyto_copy = None

        return game_state

    def choose_action(
        self,
        game: Game.Game,
        network: DominionNetwork,
        optional: bool = True,
        mock: bool = False,
    ) -> str:

        # Can draw more actions so need to always check for available actions
        potential_actions: List[Card] = []
        if optional:
            potential_actions.append(None)

        for card in self.hand:
            if "action" in card.categories:
                potential_actions.append(card)

        print(potential_actions)

        if len(potential_actions) == 0:
            return None

        scores: List[float] = []
        states: List[
            Tuple[
                List[List[float]],
                List[int],
                List[List[float]],
                List[int],
                List[List[float]],
                List[float],
            ]
        ] = []

        for action in potential_actions:
            board_state = self.play_action_and_get_game_state(game, action, network)
            score = network.eval_position(board_state)
            print(score)
            if action:
                scores.append(score)
            else:
                scores.append(score-0.1)
            states.append(board_state)

        chosen_index = NNPlayer.random_index(scores, self.get_exploration_factor())
        best_state = states[chosen_index]
        best_action = potential_actions[chosen_index]

        if not mock:
            hand = best_state[0]
            if len(hand) == 0:
                print("Empty hand")
                hand = np.zeros((1, 33))

            hand_one_hot = best_state[1]
            if len(hand_one_hot) == 0:
                hand_one_hot = [0]

            self.current_game_hand_states.append(hand)
            self.current_game_hand_one_hot.append(hand_one_hot)
            self.current_game_kingdom_states.append(best_state[2])
            self.current_game_kingdom_one_hot.append(best_state[3])
            self.current_game_opponent_states.append(best_state[4])
            self.current_game_states.append(best_state[5])
        if best_action:
            return best_action.name
        return None

    def choose_buy(
        self,
        game: Game.Game,
        network: DominionNetwork,
        upto: int,
        exact: bool = False,
        optional: bool = False,
        gain: bool = False,
        mock: bool = False,
        constraint: str = None,
        destination: str = None,
    ) -> str:

        potential_buys: List[Card] = []

        for card in game.supply:
            if (
                (CardNameMap[card].cost <= upto)
                and len(game.supply[card])
                and (not exact or (CardNameMap[card].cost == upto))
                and (
                    (constraint is None) or (constraint in CardNameMap[card].categories)
                )
                > 0
            ):
                potential_buys.append(CardNameMap[card])

        if optional:
            potential_buys.append(None)

        print(potential_buys)

        if len(potential_buys) == 0:
            return None

        scores: List[float] = []
        states: List[
            Tuple[
                List[List[float]],
                List[int],
                List[List[float]],
                List[int],
                List[List[float]],
                List[float],
            ]
        ] = []

        for buy in potential_buys:
            board_state = self.buy_card_and_get_game_state(
                game, buy, network, gain=gain, destination=destination
            )
            score = network.eval_position(board_state)
            print(score)
            if buy:
                scores.append(score)
            else:
                scores.append(score)
            states.append(board_state)

        chosen_index = NNPlayer.random_index(scores, self.get_exploration_factor())
        best_state = states[chosen_index]
        best_buy = potential_buys[chosen_index]

        if not mock:
            hand = best_state[0]
            if len(hand) == 0:
                print("Empty hand")
                hand = np.zeros((1, 33))

            hand_one_hot = best_state[1]
            if len(hand_one_hot) == 0:
                hand_one_hot = [0]

            self.current_game_hand_states.append(hand)
            self.current_game_hand_one_hot.append(hand_one_hot)
            self.current_game_kingdom_states.append(best_state[2])
            self.current_game_kingdom_one_hot.append(best_state[3])
            self.current_game_opponent_states.append(best_state[4])
            self.current_game_states.append(best_state[5])
        if best_buy:
            return best_buy.name
        return None

    def choose_treasure(
        self, game: Game.Game, network: DominionNetwork, mock: bool = False,
    ) -> str:

        potential_treasures: List[Card] = [None]

        for card in self.hand:
            if "coin" in card.categories:
                potential_treasures.append(card)

        scores: List[float] = []
        states: List[
            Tuple[
                List[List[float]],
                List[int],
                List[List[float]],
                List[int],
                List[List[float]],
                List[float],
            ]
        ] = []

        for treasure in potential_treasures:
            board_state = self.play_treasure_and_get_game_state(game, treasure, network)
            score = network.eval_position(board_state)
            print(score)
            if treasure:
                scores.append(score)
            else:
                scores.append(score-0.1)
            states.append(board_state)

        chosen_index = NNPlayer.random_index(scores, self.get_exploration_factor())
        best_state = states[chosen_index]
        best_play = potential_treasures[chosen_index]

        if not mock:
            hand = best_state[0]
            if len(hand) == 0:
                print("Empty hand")
                hand = np.zeros((1, 33))

            hand_one_hot = best_state[1]
            if len(hand_one_hot) == 0:
                hand_one_hot = [0]

            self.current_game_hand_states.append(hand)
            self.current_game_hand_one_hot.append(hand_one_hot)
            self.current_game_kingdom_states.append(best_state[2])
            self.current_game_kingdom_one_hot.append(best_state[3])
            self.current_game_opponent_states.append(best_state[4])
            self.current_game_states.append(best_state[5])
        if best_play:
            return best_play.name
        return None

    def choose_discard(
        self,
        prompt: str,
        game: Game.Game,
        network: DominionNetwork,
        constraint: str = None,
        additional_draw: int = 0,
        optional: bool = False,
        trash_card: bool = False,
        ondeck: bool = False,
        mock: bool = False,
    ) -> str:

        candidates: List[Card] = []

        if optional:
            candidates.append(None)

        for card in self.hand:
            if (constraint in card.categories) or (constraint is None):
                candidates.append(card)

        if len(candidates) == 1:
            if candidates[0]:
                return candidates[0].name
            else:
                return None

        scores: List[float] = []
        states: List[
            Tuple[
                List[List[float]],
                List[int],
                List[List[float]],
                List[int],
                List[List[float]],
                List[float],
            ]
        ] = []

        for candidate in candidates:
            if candidate:
                print("Thought about discarding " + candidate.name)
            else:
                print("Thought about discarding nothing")
            board_state = self.discard_and_get_game_state(
                game,
                candidate,
                network,
                additional_draw=additional_draw,
                ondeck=ondeck,
                trash_card=trash_card,
            )
            score = network.eval_position(board_state)
            print(score)

            scores.append(score)
            states.append(board_state)

        chosen_index = NNPlayer.random_index(scores, self.get_exploration_factor())
        best_state = states[chosen_index]
        best_discard = candidates[chosen_index]

        if not mock:
            hand = best_state[0]
            if len(hand) == 0:
                print("Empty hand")
                hand = np.zeros((1, 33))

            hand_one_hot = best_state[1]
            if len(hand_one_hot) == 0:
                hand_one_hot = [0]

            self.current_game_hand_states.append(hand)
            self.current_game_hand_one_hot.append(hand_one_hot)
            self.current_game_kingdom_states.append(best_state[2])
            self.current_game_kingdom_one_hot.append(best_state[3])
            self.current_game_opponent_states.append(best_state[4])
            self.current_game_states.append(best_state[5])
        if best_discard:
            return best_discard.name
        return None

    def yesnoinput(
        self,
        prompt: str,
        game: Game.Game,
        network: DominionNetwork,
        yesstring: str = "",
        nostring: str = "",
        callbacks: Dict[
            bool, Callable[[Player, Game.Game, DominionNetwork, bool], int]
        ] = None,
        applyto: Player = None,
        mock: bool = False,
    ) -> bool:
        if callbacks:

            scores: List[float] = []
            states: List[
                Tuple[
                    List[List[float]],
                    List[int],
                    List[List[float]],
                    List[int],
                    List[List[float]],
                    List[float],
                ]
            ] = []
            candidates: List[bool] = []
            for response in callbacks:

                board_state = self.trycallback(
                    callbacks[response], game, network, applyto=applyto,
                )
                score = network.eval_position(board_state)
                print("Option " + str(response) + " score: " + str(score))
                scores.append(score)
                states.append(board_state)
                candidates.append(response)

            chosen_index = NNPlayer.random_index(scores, self.get_exploration_factor())
            best_state = states[chosen_index]
            best_response = candidates[chosen_index]

            if not mock:
                hand = best_state[0]
                if len(hand) == 0:
                    print("Empty hand")
                    hand = np.zeros((1, 33))

                hand_one_hot = best_state[1]
                if len(hand_one_hot) == 0:
                    hand_one_hot = [0]

                self.current_game_hand_states.append(hand)
                self.current_game_hand_one_hot.append(hand_one_hot)
                self.current_game_kingdom_states.append(best_state[2])
                self.current_game_kingdom_one_hot.append(best_state[3])
                self.current_game_opponent_states.append(best_state[4])
                self.current_game_states.append(best_state[5])
            return best_response
        return True

    def hprint(self, string):
        pass

    def cprint(self, string):
        print(string)

    def show(self, lead=""):
        pass


class ComputerPlayer(Player):
    def __init__(self, name: str, order: int, sp: bool = True):
        Player.__init__(self, name, order)
        # beginning and middle of game
        self.buygaintable1 = [
            "Province",
            "Gold",
            "Laboratory",
            "Festival",
            "Witch",
            "Council Room",
            "Market",
            "Militia",
            "Adventurer",
            "Smithy",
            "Bureaucrat",
            "Silver",
            "Moat",
            "",
        ]
        # end of game
        self.buygaintable2 = [
            "Province",
            "Gardens",
            "Duchy",
            "Estate",
            "Gold",
            "Silver",
            "",
        ]
        # beginning and middle of the game, too many action cards
        self.buygaintable3 = [
            "Province",
            "Gold",
            "Festival",
            "Laboratory",
            "Market",
            "Village",
            "Silver",
            "",
        ]
        self.playtable1 = [
            "Village",
            "Festival",
            "Market",
            "Laboratory",
            "Witch",
            "Council Room",
            "Militia",
            "Adventurer",
            "Smithy",
            "Bureaucrat",
            "Moat",
        ][::-1]
        self.discardtable1 = [
            "Gardens",
            "Duchy",
            "Province",
            "Estate",
            "Curse",
            "Copper",
            "Village",
            "Bureaucrat",
            "Silver",
            "Militia",
            "Smithy",
            "Council Room",
            "Witch",
            "Festival",
            "Market",
            "Adventurer",
            "Laboratory",
            "Gold",
            "Moat",
        ]
        self.sp = sp

    @staticmethod
    def totalbuypower(cardlist: List[Card]):
        TBP = 0
        for c in cardlist:
            TBP += c.buypower
            if "action" in c.categories:
                TBP += c.coins
        return TBP

    @staticmethod
    def Findex(item: str, playtable: List[str]):
        try:
            return playtable.index(item)
        except:
            return -1

    def action_balance(self):
        balance = 0
        for c in self.stack():
            if "action" in c.categories:
                balance = balance - 1 + c.actions
        return 70 * balance / len(self.stack())

    def choose_action(
        self,
        game: Game.Game,
        network: DominionNetwork,
        optional: bool = True,
        mock: bool = False,
    ) -> str:
        self.hand.sort(key=lambda x: ComputerPlayer.Findex(x.name, self.playtable1))
        for card in reversed(self.hand):
            if "action" in card.categories:
                return card.name
        return None

    def choose_buy(
        self,
        game: Game.Game,
        network: DominionNetwork,
        upto: int,
        exact: bool = False,
        optional: bool = False,
        gain: bool = False,
        mock: bool = False,
        constraint: str = None,
        destination: str = None,
    ) -> str:
        if (
            len(game.supply["Province"])
            > len(game.players) + ComputerPlayer.totalbuypower(self.deck) / 8
        ):
            if self.action_balance() < -10:
                bgt = self.buygaintable3
            else:
                bgt = self.buygaintable1
        else:
            bgt = self.buygaintable2

        for c in bgt:
            if (
                c in game.supply
                and len(game.supply[c]) > 0
                and game.supply[c][0].cost <= upto
            ):
                return c
        return None

    def choose_discard(
        self,
        prompt: str,
        game: Game.Game,
        network: DominionNetwork,
        constraint: str = None,
        additional_draw: int = 0,
        optional: bool = False,
        trash_card: bool = False,
        ondeck: bool = False,
        mock: bool = False,
    ) -> str:

        self.hand.sort(key=lambda x: ComputerPlayer.Findex(x.name, self.discardtable1))
        return self.hand[0].name

    def choose_treasure(self, game: Game.Game, network: DominionNetwork) -> str:
        for card in self.hand:
            if "coin" in card.categories:
                return card.name

        return None

    def yesnoinput(
        self,
        prompt: str,
        game: Game.Game,
        network: DominionNetwork,
        yesstring: str = "",
        nostring: str = "",
        callbacks: dict = None,
        applyto: Player = None,
        mock: bool = False,
    ) -> bool:
        return True

    def hprint(self, string: str):
        pass

    def cprint(self, string: str):
        if not self.sp:
            print(string)

    def show(self, lead: str = ""):
        pass


class QvistPlayer(Player):
    def __init__(self, name: str, order: int, sp: bool = True):
        Player.__init__(self, name, order)
        # beginning and middle of game
        self.buygaintable1 = [
            "Colony",
            "Platinum",
            "Province",
            "Bank" "Artisan" "Nobles",
            "Gold",
            "Fairgrounds",
            "Farmland" "Harem" "Adventurer",
            "Witch",
            "Upgrade",
            "Laboratory",
            "Council Room",
            "Festival",
            "Market",
            "Ill-Gotten Gains",
            "Trading Post",
            "Treasure Trove",
            "Library",
            "Bandit",
            "Duke",
            "Mine",
            "Cache",
            "Throne Room",
            "Ironmonger",
            "Militia",
            "Moneylender",
            "Smithy",
            "Conspirator",
            "Ironworks",
            "Mining Village",
            "Mill",
            "Remodel",
            "Poacher",
            "Baron",
            "Gardens",
            "Silk Road",
            "Feodum",
            "Bureaucrat",
            "Spy",
            "Feast",
            "Thief",
            "Swindler",
            "Village",
            "Silver",
            "Shanty Town",
            "Workshop",
            "Vassal",
            "Tunnel",
            "Woodcutter",
            "Great Hall",
            "Chancellor",
            "Chapel",
            "Courtyard",
            "Cellar",
            "Moat",
            "Estate",
            "",
        ]
        # end of game
        self.buygaintable2 = [
            "Colony",
            "Platinum",
            "Province",
            "Nobles",
            "Gold",
            "Fairgrounds",
            "Farmland",
            "Harem",
            "Duchy",
            "Duke",
            "Mill",
            "Gardens",
            "Silk Road",
            "Feodum",
            "Silver",
            "Tunnel",
            "Great Hall",
            "Estate",
            "",
        ]

        self.discardtable1 = [
            "Colony",
            "Province",
            "Fairgrounds",
            "Farmland",
            "Duchy",
            "Duke",
            "Gardens",
            "Silk Road",
            "Feodum",
            "Silver",
            "Tunnel",
            "Great Hall",
            "Estate",
            "Gardens",
            "Duchy",
            "Province",
            "Estate",
            "Curse",
            "Copper",
            "Village",
            "Bureaucrat",
            "Silver",
            "Militia",
            "Smithy",
            "Council Room",
            "Witch",
            "Festival",
            "Market",
            "Adventurer",
            "Laboratory",
            "Gold",
            "Mill",
            "Harem",
            "Moat",
            "Nobles",
        ] + reversed(self.buygaintable1)
        self.sp = sp

    @staticmethod
    def totalbuypower(cardlist: List[Card]):
        TBP = 0
        for c in cardlist:
            TBP += c.buypower
            if "action" in c.categories:
                TBP += c.coins
        return TBP

    @staticmethod
    def Findex(item: str, playtable: List[str]):
        try:
            return playtable.index(item)
        except:
            return -1

    def action_balance(self):
        balance = 0
        for c in self.stack():
            if "action" in c.categories:
                balance = balance - 1 + c.actions
        return 70 * balance / len(self.stack())

    def choose_action(
        self,
        game: Game.Game,
        network: DominionNetwork,
        optional: bool = True,
        mock: bool = False,
    ) -> str:
        self.hand.sort(key=lambda x: ComputerPlayer.Findex(x.name, self.playtable1))
        for card in reversed(self.hand):
            if "action" in card.categories:
                return card.name
        return None

    def choose_buy(
        self,
        game: Game.Game,
        network: DominionNetwork,
        upto: int,
        exact: bool = False,
        optional: bool = False,
        gain: bool = False,
        mock: bool = False,
        constraint: str = None,
        destination: str = None,
    ) -> str:
        if (
            len(game.supply["Province"])
            > len(game.players) + ComputerPlayer.totalbuypower(self.deck) / 8
        ):
            bgt = self.buygaintable1
        else:
            bgt = self.buygaintable2

        for c in bgt:
            if (
                c in game.supply
                and len(game.supply[c]) > 0
                and game.supply[c][0].cost <= upto
            ):
                return c
        return None

    def choose_discard(
        self,
        prompt: str,
        game: Game.Game,
        network: DominionNetwork,
        constraint: str = None,
        additional_draw: int = 0,
        optional: bool = False,
        trash_card: bool = False,
        ondeck: bool = False,
        mock: bool = False,
    ) -> str:

        self.hand.sort(key=lambda x: ComputerPlayer.Findex(x.name, self.discardtable1))
        return self.hand[0].name

    def choose_treasure(self, game: Game.Game, network: DominionNetwork) -> str:
        for card in self.hand:
            if "coin" in card.categories:
                return card.name

        return None

    def yesnoinput(
        self,
        prompt: str,
        game: Game.Game,
        network: DominionNetwork,
        yesstring: str = "",
        nostring: str = "",
        callbacks: dict = None,
        applyto: Player = None,
        mock: bool = False,
    ) -> bool:
        return True

    def hprint(self, string: str):
        pass

    def cprint(self, string: str):
        if not self.sp:
            print(string)

    def show(self, lead: str = ""):
        pass
