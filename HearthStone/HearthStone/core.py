#! /usr/bin/python
# -*- coding: utf-8 -*-

import json

from .constants import game as gc
from .game_data.card_data import get_card_type
from .event_framework import EventEngine
from .game_entities.player import Player
from .game_events.basic import GameEnd
from .game_exception import GameEndException
from .game_handlers.basic import CreateCoinHandler, TurnBeginDrawCardHandler, ComboHandler

__author__ = 'fyabc'


class AuraManager:
    """The class of an aura manager of minions and other.
    Some minions and card
    """

    def __init__(self, game):
        self.game = game

    def clear(self):
        pass


class HistoryManager:
    def __init__(self, game):
        self.game = game

    def clear(self):
        pass


class Game:
    """The class of the game.

    This class contains:
        an event engine
        an aura(光环) manager
        some game data
            turns
            minions
            cards
            heroes
        cemetery
        a history manager
            ...
    """

    # Constants.
    TotalPlayerNumber = gc.TotalPlayerNumber
    MaxDeckNumber = gc.MaxDeckNumber
    MaxHandNumber = gc.MaxHandNumber
    MaxDeskNumber = gc.MaxDeskNumber
    MaxCrystal = gc.MaxCrystal

    def __init__(self, game_filename=None, **kwargs):
        # Event engine.
        engine_kwargs = {}
        if 'logging_filename' in kwargs:
            engine_kwargs['logging_filename'] = kwargs.pop('logging_filename')

        self.engine = EventEngine(**engine_kwargs)
        self.engine.add_terminate_event_type(GameEnd)

        # Game data.
        self.game_filename = game_filename
        self.players = self.load_game(game_filename)
        self.current_player_id = 0

        # Some counters.
        self.turn_number = 0
        self.summon_number = 0

        # Aura manager.
        self.aura_manager = AuraManager(self)

        # History manager.
        self.history = HistoryManager(self)

        self.init_handlers()

    # Properties.
    @property
    def current_player(self):
        return self.players[self.current_player_id]

    @property
    def opponent_player(self):
        return self.players[1 - self.current_player_id]

    @property
    def opponent_player_id(self):
        return 1 - self.current_player_id

    # Events and handlers.
    def create_event(self, event_type, *args, **kwargs):
        return event_type(self, *args, **kwargs)

    def add_event(self, event):
        self.engine.add_event(event)

    def add_event_quick(self, event_type, *args, **kwargs):
        self.engine.add_event(event_type(self, *args, **kwargs))

    def prepend_event(self, event):
        self.engine.prepend_event(event)

    def prepend_event_quick(self, event_type, *args, **kwargs):
        self.engine.prepend_event(event_type(self, *args, **kwargs))

    def insert_event(self, event):
        self.engine.insert_event(event)

    def insert_event_quick(self, event_type, *args, **kwargs):
        self.engine.insert_event(event_type(self, *args, **kwargs))

    def dispatch_event(self, event):
        return self.engine.dispatch_event(event)

    def dispatch_event_quick(self, event_type, *args, **kwargs):
        return self.engine.dispatch_event(event_type(self, *args, **kwargs))

    def create_handler(self, handler_type, *args, **kwargs):
        return handler_type(self, *args, **kwargs)

    def add_handler(self, handler):
        self.engine.add_handler(handler)

    def add_handler_quick(self, handler_type, *args, **kwargs):
        self.engine.add_handler(handler_type(self, *args, **kwargs))

    # Game operations.
    def load_game(self, game_filename=None):
        if game_filename is None:
            return [Player(self, player_id=i) for i in range(gc.TotalPlayerNumber)]
        with open(game_filename, 'r', encoding='utf-8') as f:
            return [Player.load_from_dict(self, data, player_id=i) for i, data in enumerate(json.load(f))]

    def init_handlers(self):
        self.add_handler_quick(TurnBeginDrawCardHandler)
        self.add_handler_quick(CreateCoinHandler)
        self.add_handler_quick(ComboHandler)

    def restart_game(self):
        self.aura_manager.clear()
        self.history.clear()

        self.engine.start(clear_handlers=True)

        self.current_player_id = 0
        self.turn_number = 0

        self.players = self.load_game(self.game_filename)
        self.init_handlers()

    def run_test(self, events):
        try:
            for event in events:
                self.engine.dispatch_event(event)
        except GameEndException as e:
            print('Game end at P{}!'.format(e.current_player_id))

    def next_turn(self):
        self.current_player_id = (self.current_player_id + 1) % gc.TotalPlayerNumber
        self.turn_number += 1

    def range(self, player_id=None, **kwargs):
        """Method to get 'where' functions, which return a list of entities, used in random target events, etc.
        
        :param player_id: 0, 1 or None (default), None means both
        :param kwargs:
            exclude_minion: Minion
                The minion that to be excluded (usually the source)
            exclude_dead: Bool, default is False
                Exclude dead minions
            exclude_hero: Bool, default is False
                Exclude hero
        :return: A function that return
        """

        exclude_minion = kwargs.pop('exclude_minion', None)
        exclude_dead = kwargs.pop('exclude_dead', False)
        exclude_hero = kwargs.pop('exclude_hero', False)

        def where():
            if player_id is None:
                candidates = self.players[0].desk + self.players[1].desk
                if not exclude_hero:
                    candidates += self.players
            else:
                player = self.players[player_id]
                candidates = player.desk.copy()
                if not exclude_hero:
                    candidates += [player]

            if exclude_minion is not None:
                candidates.remove(exclude_minion)

            if exclude_dead:
                candidates = [entity for entity in candidates if entity.alive]

            return candidates

        return where

    # Other utilities.
    def create_card(self, card_id_or_name, player_id=None):
        return get_card_type(card_id_or_name)(self, player_id=player_id)

    def log(self, *args, **kwargs):
        """Logging something (maybe events?) into the history manager."""
        pass

    def run_tk(self, **kwargs):
        """Run tkinter game."""

        size = kwargs.pop('size', '1500x600')

        import tkinter as tk
        from .gui_tools.tkgui.game_window import GameWindow

        root = tk.Tk(className='HearthStone')
        root.geometry(size)

        app = GameWindow(self, root)

        app.mainloop()
