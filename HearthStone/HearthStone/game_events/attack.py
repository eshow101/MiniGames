#! /usr/bin/python
# -*- encoding: utf-8 -*-

from .base import GameEvent
from .damage import Damage
from ..utils.debug import verbose

__author__ = 'fyabc'


class Attack(GameEvent):
    def __init__(self, game, source, target):
        super(Attack, self).__init__(game)
        self.source = source
        self.target = target

    def __str__(self):
        return '{}({}=>{})'.format(super(Attack, self).__str__(), self.source, self.target)

    def _happen(self):
        self._message()

        self.source.remain_attack_number -= 1
        if self.source.stealth:
            self.source.stealth = False

        # [NOTE] Should this change to insert?

        src_atk = self.source.attack
        if src_atk > 0:
            self.game.add_event_quick(Damage, self.source, self.target, src_atk)

        tar_atk = self.target.attack
        if tar_atk > 0:
            self.game.add_event_quick(Damage, self.target, self.source, tar_atk)

    def _message(self):
        verbose('{} attack {}!'.format(self.source, self.target))


__all__ = [
    'Attack',
]
