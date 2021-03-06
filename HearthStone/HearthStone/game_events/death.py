#! /usr/bin/python
# -*- encoding: utf-8 -*-

"""Events about death of minion and hero.

[Dependency] .(base, basic), {utils.debug, constants}
"""

from .base import GameEvent
from .basic import GameEnd
from ..utils.debug import verbose
from ..constants import card as cc

__author__ = 'fyabc'


class Death(GameEvent):
    def __init__(self, game, entity):
        super().__init__(game)
        self.entity = entity

    def __str__(self):
        return '{}({})'.format(super().__str__(), self.entity)

    def _happen(self):
        raise NotImplementedError()

    def _message(self):
        verbose('{} died!'.format(self.entity))


class MinionDeath(Death):
    def __init__(self, game, minion):
        super().__init__(game, minion)

        # [NOTE] Get player id now, because the minion may be removed and cannot find its player.
        self.player_id = self.minion.player_id

    @property
    def minion(self):
        return self.entity

    def _happen(self):
        if self.minion.location != cc.Location_DESK:
            # Only minions in desk can death.
            self.disable()
            return

        self._message()

        desk = self.game.players[self.player_id].desk
        assert self.minion in desk, 'The minion must in the desk'

        index = desk.index(self.minion)
        desk.remove(self.minion)

        self.minion.change_location(cc.Location_CEMETERY)

        self.minion.run_death_rattle(self.player_id, index)


class HeroDeath(Death):
    def __init__(self, game, player):
        super().__init__(game, player)
        self.player_id = player.player_id

    @property
    def player(self):
        return self.entity

    def _happen(self):
        self._message()

        # [NOTE] Should this change to insert?
        self.game.add_event_quick(GameEnd, self.player_id)

    def __str__(self):
        return '{}(P{})'.format(super().__str__(), self.player_id)


__all__ = [
    'Death',
    'MinionDeath',
    'HeroDeath',
]
