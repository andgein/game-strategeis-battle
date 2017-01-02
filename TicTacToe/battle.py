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

from tictactoe import Game, Bot, Winner

BOTS_FOLDER = 'bots'
LOGS_FOLDER = 'logs'


class Battle:
    def __init__(self, players):
        self.players = players
        self.scores = [0] * len(self.players)
        self.round_number = 0

        self._ensure_folder_exists(LOGS_FOLDER)
        self.logs_folder = os.path.join(LOGS_FOLDER, datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S'))

    def _play_game(self, player1_idx, player2_idx):
        player1 = self.players[player1_idx]
        player2 = self.players[player2_idx]

        logging.info('%s VS %s' % (player1.get_bot_name_and_author(), player2.get_bot_name_and_author()))

        game = Game(player1, player2)
        game.play()
        if game.winner == Winner.X:
            self.scores[player1_idx] += 2
        elif game.winner == Winner.O:
            self.scores[player2_idx] += 2
        elif game.winner == Winner.DRAW:
            self.scores[player1_idx] += 1
            self.scores[player2_idx] += 1

        logging.info('Итоговое поле:')
        game.board.print(via_logging=True)

    def play_round(self):
        self.round_number += 1
        logging.info('Играю раунд %d на %d игроков' % (self.round_number, len(self.players)))
        round_logs_folder = os.path.join(self.logs_folder, 'Раунд %d' % (self.round_number, ))
        logging.info('Логи раунда хранятся в папке %s' % (round_logs_folder, ))
        self._ensure_folder_exists(round_logs_folder)

        for player1_idx, player1 in enumerate(self.players):
            for player2_idx, player2 in enumerate(self.players):
                if player1_idx == player2_idx:
                    continue

                logging.info('Играет %s против %s' % (
                    player1.get_bot_name_and_author(),
                    player2.get_bot_name_and_author()
                ))

                log_file_name = os.path.join(round_logs_folder, self._safe_filename('%s VS %s.log' % (
                    player1.get_bot_name_and_author(),
                    player2.get_bot_name_and_author()
                )))
                clear_logging_root_handlers()
                logging.basicConfig(level=logging.INFO, filename=log_file_name,
                                    format='%(asctime)s [%(levelname)s] %(message)s')
                self._play_game(player1_idx, player2_idx)

        clear_logging_root_handlers()
        logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                            format='%(asctime)s [%(levelname)s] %(message)s')

    def fight(self, rounds):
        logging.info('Логи баттла хранятся в папке %s' % (self.logs_folder, ))
        self._ensure_folder_exists(self.logs_folder)
        for _ in range(rounds):
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
    ROUNDS = 10

    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(asctime)s [%(levelname)s] %(message)s')

    bots = BotLoader(BOTS_FOLDER).load()
    Battle(bots).fight(ROUNDS)
