#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import operator
import re
import sys
import glob
import inspect
import os
import os.path
import importlib.util
import datetime
import gc

from kirzhanovsky import Game, Bot

BOTS_FOLDER = 'bots'
LOGS_FOLDER = 'logs'


class Battle:
    def __init__(self, players):
        self.players = players
        self.scores = [0] * len(self.players)
        self.round_number = 0

        self._ensure_folder_exists(LOGS_FOLDER)
        self.logs_folder = os.path.join(LOGS_FOLDER, datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S'))

    def _play_game(self):
        game = Game(self.players)
        game.play()
        for player_id, player_score in enumerate(game.scores):
            self.scores[player_id] += player_score

    def play_round(self):
        self.round_number += 1
        logging.info('Играю раунд %d на %d игроков' % (self.round_number, len(self.players)))

        log_file_name = os.path.join(self.logs_folder, 'Игра %d.log' % self.round_number)
        clear_logging_root_handlers()
        logging.basicConfig(level=logging.INFO, filename=log_file_name,
                            format='%(asctime)s [%(levelname)s] %(message)s')
        self._play_game()
        gc.collect()

        clear_logging_root_handlers()
        logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                            format='%(asctime)s [%(levelname)s] %(message)s')

    def fight(self, games):
        logging.info('Логи баттла хранятся в папке %s' % (self.logs_folder, ))
        self._ensure_folder_exists(self.logs_folder)
        for _ in range(games):
            self.play_round()
            logging.info('Таблица результатов после раунда %d:' % (self.round_number, ))
            self.print_scores_table()

    def print_scores_table(self):
        players_with_scores = list(zip(self.players, self.scores))
        players_with_scores = sorted(players_with_scores, key=operator.itemgetter(1), reverse=True)
        for player, score in players_with_scores:
            logging.info('%s: %d' % (player.get_bot_name_and_author(), score))

    @staticmethod
    def _ensure_folder_exists(folder):
        if os.path.exists(folder):
            if not os.path.isdir(folder):
                raise Exception('Не могу создать папку %s' % (folder,))
        else:
            try:
                os.mkdir(folder)
            except Exception as e:
                logging.error('Не могу создать папку %s: %s' % (folder, e))
                raise

    @staticmethod
    def _safe_filename(filename):
        return re.sub(r'[\[\]/\\;,><&*:%=+@!#^()|?]', '', filename)


class BotLoader:
    def __init__(self, bots_folder):
        self.bots_folder = bots_folder

    def load(self):
        logging.info('Загружаю ботов из папки %s' % (self.bots_folder, ))
        bot_files = glob.glob(os.path.join(self.bots_folder, '*.py'))
        bots = []
        for bot_file in bot_files:
            logging.info('Загружаю ботов из файла %s' % (bot_file, ))
            try:
                bots.extend(self._load_bots_from_file(bot_file))
            except Exception as e:
                logging.error('Не могу загрузить бота из файла %s: %s' % (bot_file, e))
                raise

        logging.info('Найдено %d бота(ов): %s' % (
            len(bots),
            '; '.join(b.get_bot_name_and_author() for b in bots)
        ))
        return bots

    def _load_bots_from_file(self, bot_file):
        module = self._import_module_from_file(bot_file)
        # Берём всё, что импортирует модуль
        classes = [getattr(module, x) for x in dir(module)]
        # Ищем классы-наследники Bot'а
        classes = list(filter(lambda c: inspect.isclass(c) and issubclass(c, Bot) and c != Bot, classes))

        if len(classes) == 0:
            raise ValueError('в файле не найдено ни одного бота')

        logging.info('Из файла %s загрузил ботов: %s' % (
            bot_file,
            '; '.join(b.get_bot_name_and_author() for b in classes)
        ))

        return classes

    @staticmethod
    def _import_module_from_file(bot_file):
        spec = importlib.util.spec_from_file_location('bot', bot_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def clear_logging_root_handlers():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

if __name__ == '__main__':
    GAMES_RATIO = 10

    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(asctime)s [%(levelname)s] %(message)s')

    bots = BotLoader(BOTS_FOLDER).load()
    Battle(bots).fight(GAMES_RATIO * len(bots))
