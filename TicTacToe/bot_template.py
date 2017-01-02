#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tictactoe import Game, Bot, Move, ConsolePlayer

import logging
import sys


class MyBot(Bot):
    """
    Этот класс — в целом всё, что необходимо, чтобы создать своего бота.
    Во всех функциях этого класса доступна переменная self.player_type, которая равна 1,
    если ваш бот играет за крестики, и 2, если за нолики.
    """

    # Укажите здесь имя вашего бота
    NAME = 'Мой самый лучший бот'

    # Укажите здесь ваше имя
    AUTHOR = 'Иван Пупкин'

    def move(self, board):
        """
        Это самая главная функция бота.
        Она принимает на вход текущее поле (переменная board) и должна вернуть ход.

        Вот пример тела этой функции для бота, который всегда ходит в клетку с координатами (0, 0),
        даже если она уже занята:

        def move(self, board):
            return Move(0, 0)

        Как вы заметили, нужно всегда вернуть конструкцию Move(ROW, COLUMN), где (ROW, COLUMN) — координаты клетки,
        куда ваш бот хочет сходить.

        Чтобы узнать, чем занята та или иная ячейка поля, обратитесь к переменной board.
        Например, в board[1][1] лежит информация о центральной ячейке поля, потому что её координаты — (1, 1).
        Если в board[1][1] лежит значение 0, то она пустая. Если 1, то там находится крестик,
        а если 2, то нолик.

        Вот пример функции move, которая ищет первую свободную ячейку и ходит в неё:

        def move(self, board):
            for row in range(board.size):
                for column in range(board.size):
                     if board[row][column] == 0:
                          return Move(row, column)

        Внимательные заметили, что в этом примере мы использовали размер поля board.size. Он всегда равен 3.

        Чтобы узнать, стоит ли в клетки ваш значок или значок противника, можно просто сравнить board[row][column] и
        self.player_type (о нём см. выше) на равенство. Чтобы узнать, «принадлежит» ли вам клетка,
        используйте следующую конструкцию:

        if board[row][column] == self.player_type:
            print('Это моя клетка!')

        Функция move() ОБЯЗАТЕЛЬНО должна вернуть объект Move() с какими-нибудь параметрами.
        В противном случае ход не будет засчитан.

        Вы можете использовать и изменять board как угодно, это никак не отразится на состоянии поля в игре.
        Не изменяйте self.player_type, это ни на что не повлияет и только может запутать вашего же бота :-)

        Ограничение на время работы функции — 3 секунды.

        ==========================================================================================================

        Есть два способа создавать свои функции: вне класса вашего бота и внутри него.

        1. В первом случае определяйте функции вне класса как обычно в программах на питоне. Они могут использовать
        глобальные переменные из вашего файла и вообще работать как обычно. Если для работы этих функций нужны
        self.player_type или board из бота, то передайте их явно при работе функции move(). Например:

        def find_best_move(board, player_type):
           ... Здесь код, который находит лучший ход, он может использовать переданные ему переменные
           ... board и player_type
           return Move(ROW, COLUMN)

        class MyBot(Bot):
            def move(board):
                return find_best_move(board, self.player_type)

        2. Во втором случае создавайте функции прямо внутри класса бота. В этом случае ВСЕГДА добавляйте в качестве
        первого аргумента self, а для вызова используйте конструкцию self.<название_функции>(). Такие функции
        могут напрямую использовать self.player_type, так как находятся внутри бота, передавать эту переменную
        ещё раз не надо. Например:

        class MyBot(Bot):
            def find_best_move(self, board):
                ... Здесь код, который находит лучший ход, он может использовать переданные ему переменные
                ... board и self.player_type
                return Move(ROW, COLUMN)

            def move(self, board):
                # Обратите внимание на self перед названием функции и на отсутствие self в качестве первого аргумента
                # (он передаётся автоматически)
                return self.find_best_move(board)

        ============================================================================================================
        """
        pass


"""
Код ниже запускает игру между вашим ботом и человеком.
Его легко можно модифицировать, чтобы запустить игру между двумя людьми или двумя ботами.
"""
if __name__ == '__main__':
    # Следующая строка настраивает вывод информации об игре на стандартный поток вывода
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s [%(levelname)s] %(message)s')

    game = Game(MyBot, ConsolePlayer)

    # Если вы хотите сыграть за крестики вместо ноликов, поменяйте аргументы местами:
    # game = Game(ConsolePlayer, MyBot)

    # Если вы хотите запустить игру между двумя людьми, укажите два ConsolePlayer:
    # game = Game(ConsolePlayer, ConsolePlayer)

    # Если вы хотите запустить игру между двумя ботами, разместите их код в этом файле (не забудьте назвать классы
    # по-разному!), и укажите в следующей строке названия классов (обратите внимания, что названия классов надо
    # писать без скобок после них).
    # game = Game(MyBot1, MyBot2)

    game.play()

