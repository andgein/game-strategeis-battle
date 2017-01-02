#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import collections
import enum
import multiprocessing.pool

__author__ = 'Andrew Gein <andgein@yandex.ru>'


class AbstractPlayer:
    def __init__(self, player_type):
        self.player_type = player_type

    def move(self, board):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()


class Bot(AbstractPlayer):
    NAME = 'UNKNOWN NAME'
    AUTHOR = 'UNKNOWN AUTHOR'

    def move(self, board):
        raise NotImplementedError()

    def __str__(self):
        return 'Бот %s (%s)' % (self.__class__.__name__, self.get_bot_name_and_author())

    @classmethod
    def get_bot_name_and_author(cls):
        return '%s, %s' % (cls.NAME, cls.AUTHOR)


class ConsolePlayer(AbstractPlayer):
    def move(self, board):
        print('Текущее состояние поля:')
        board.print()
        while True:
            print('Ходят %s' % (str(PlayerType(self.player_type)), ))
            print('Ваш ход? Введите два числа через пробел, номер строки и номер столбца.')
            try:
                move = list(map(int, input().split()))
            except ValueError:
                print('Неправильный формат. Введите два числа через пробел, номер строки и номер столбца.')
                continue
            if len(move) != 2:
                print('Неправильный формат. Введите два числа через пробел, номер строки и номер столбца.')
                continue
            return Move(move[0], move[1])

    def __str__(self):
        return 'Человек'


class BoardCell(enum.Enum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2

    def inverse(self):
        return BoardCell(3 - self.value)

    def __str__(self):
        if self == BoardCell.BLACK:
            return '\u25C9'
        elif self == BoardCell.WHITE:
            return '\u25CE'
        elif self == BoardCell.EMPTY:
            return ' '


class PlayerType(enum.Enum):
    BLACK = 1
    WHITE = 2

    def inverse(self):
        return PlayerType(3 - self.value)

    def __str__(self):
        if self == PlayerType.BLACK:
            return 'чёрные'
        if self == PlayerType.WHITE:
            return 'белые'


class Winner(enum.Enum):
    BLACK = 1
    WHITE = 2
    DRAW = 3


class IncorrectMove(Exception):
    pass


class GameBoard:
    def __init__(self):
        self.size = 8
        self.board = [[BoardCell.EMPTY] * self.size for _ in range(self.size)]
        self.board[3][4] = self.board[4][3] = BoardCell.BLACK
        self.board[3][3] = self.board[4][4] = BoardCell.WHITE

    def apply_move(self, player_type, move):
        if not self._is_valid_coordinates(move.row, move.column):
            raise IncorrectMove(
                'Клетка (%d, %d) имеет неправильные координаты. Все координаты должны быть от 0 до %d' % (
                    move.row, move.column, self.size - 1
                ))
        if self.board[move.row][move.column] != BoardCell.EMPTY:
            raise IncorrectMove('Клетка (%d, %d) не пуста' % (move.row, move.column))

        new_cell = BoardCell(player_type.value)

        if not self._is_valid_move(move.row, move.column, new_cell):
            raise IncorrectMove('Неправильный ход, ни одна фишка не перевернётся')

        self.board[move.row][move.column] = new_cell

        flipped_cells = self._get_flipped_cells_for_move(move.row, move.column, new_cell)
        for flipped_x, flipped_y in flipped_cells:
            self.board[flipped_x][flipped_y] = self.board[flipped_x][flipped_y].inverse()

    def _is_valid_coordinates(self, row, column):
        return 0 <= row < self.size and 0 <= column < self.size

    def _get_flipped_cells_for_move(self, row, column, board_cell):
        flipped_cells = []

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for direction_x, direction_y in directions:
            flipped_in_direction = []

            x, y = row + direction_x, column + direction_y
            if not self._is_valid_coordinates(x, y) \
                    or self.board[x][y] == BoardCell.EMPTY or self.board[x][y] == board_cell:
                continue

            while self._is_valid_coordinates(x, y):
                if self.board[x][y] == board_cell:
                    flipped_cells.extend(flipped_in_direction)
                    break
                flipped_in_direction.append((x, y))
                x, y = x + direction_x, y + direction_y

        return flipped_cells

    def _is_valid_move(self, row, column, board_cell):
        return len(self._get_flipped_cells_for_move(row, column, board_cell)) > 0

    def has_anybody_correct_move(self):
        return self.has_player_correct_move(PlayerType.BLACK) or self.has_player_correct_move(PlayerType.WHITE)

    def has_player_correct_move(self, current_move):
        new_cell = BoardCell(current_move.value)
        for row in range(self.size):
            for column in range(self.size):
                if self.board[row][column] != BoardCell.EMPTY:
                    continue

                if self._is_valid_move(row, column, new_cell):
                    return True

        return False

    def get_winner(self):
        if self.has_anybody_correct_move():
            return False

        all_cells = [cell for row in self.board for cell in row]
        black_count = all_cells.count(BoardCell.BLACK)
        white_count = all_cells.count(BoardCell.WHITE)

        if black_count > white_count:
            return Winner.BLACK
        if white_count > black_count:
            return Winner.WHITE

        return Winner.DRAW

    def is_full(self):
        for row in range(self.size):
            for column in range(self.size):
                if self.board[row][column] == BoardCell.EMPTY:
                    return False
        return True

    def create_copy_for_player(self):
        board_copy = GameBoard()
        board_copy.board = [[cell.value for cell in row] for row in self.board]
        return board_copy

    def __getitem__(self, item):
        return self.board[item]

    def print(self):
        print(' ', *range(self.size))
        for row in range(self.size):
            print(row, *map(BoardCell, self.board[row]))


class Move(collections.namedtuple('Move', ('row', 'column'))):
    pass


class Game:
    INCORRECT_MOVE_TRIES_LIMIT = 5
    BOT_MOVE_TIMEOUT = 3  # в секундах

    def __init__(self, black_player_factory: callable, white_player_factory: callable):
        self.black_player = black_player_factory(PlayerType.BLACK.value)
        self.white_player = white_player_factory(PlayerType.WHITE.value)
        self._init_game()

    @staticmethod
    def _safe_run(timeout, function, args, kwargs):
        """ Запускает функцию function с таймаутом на выполнение """
        try:
            pool = multiprocessing.pool.ThreadPool(processes=1)
            async_result = pool.apply_async(function, args, kwargs)
            # Кидает исключение TimeoutError если исполнение превысило timeout секунд
            return async_result.get(timeout)
        except multiprocessing.context.TimeoutError:
            logging.info('Превышено время ожидания ответа: %d секунд' % (timeout,))
            return None

    def _make_one_move(self):
        current_player = self.black_player if self.current_move == PlayerType.BLACK else self.white_player
        if self.current_move == PlayerType.BLACK:
            self.move_counter += 1

        logging.info("Ход №%d игрока «%s» за %s:" % (self.move_counter, current_player, self.current_move))
        
        if not self.board.has_player_correct_move(self.current_move):
            logging.info('У игрока нет ни одного хода, передаю ход другому игроку')
            self.current_move = self.current_move.inverse()
            return
        
        # Несколько раз пытаемся узнать ход, пока пользователь или бот не сделает корректный ход
        try_index = 1
        while try_index < self.INCORRECT_MOVE_TRIES_LIMIT:
            try:
                if isinstance(current_player, Bot):
                    timeout = self.BOT_MOVE_TIMEOUT
                else:
                    timeout = None

                board_copy = self.board.create_copy_for_player()
                try:
                    move = self._safe_run(timeout, current_player.move, (board_copy,), {})
                    logging.info(move)
                except Exception as e:
                    logging.error('Произошла ошибка при попытке сделать ход: %s' % e)
                    logging.exception(e)
                    raise IncorrectMove('Произошла ошибка при попытке сделать ход: %s' % e)

                if not isinstance(move, Move):
                    raise IncorrectMove('Игрок вернул объект не типа Move. Используйте констукцию '
                                        'return Move(row, column) в ваших ботах')
                self.board.apply_move(self.current_move, move)
            except IncorrectMove as e:
                logging.info('Неправильный ход. %s' % e)
            else:
                break

            try_index += 1
            logging.info('Пытаюсь получить ход ещё раз. Попытка №%d:' % (try_index,))
        else:
            logging.info('Не удалось получить нормальный ход за %d попыток от игрока %s' % (
                self.INCORRECT_MOVE_TRIES_LIMIT,
                current_player
            ))
            logging.info('Засчитываю автоматический проигрыш')
            self.winner = Winner(self.current_move.inverse().value)
            return

        self.current_move = self.current_move.inverse()

    def _init_game(self):
        self.board = GameBoard()
        self.current_move = PlayerType.BLACK
        self.move_counter = 0
        self.winner = None

    def _is_game_finished(self):
        return self.winner is not None

    def _check_for_winner(self):
        winner = self.board.get_winner()
        if winner:
            self.winner = winner

    def _show_finish_game_message(self):
        if self.winner != Winner.DRAW:
            finish_message = 'Победили %s!' % (str(PlayerType(self.winner.value)),)
        else:
            finish_message = 'Ничья!'
        logging.info('*** %s ***' % (finish_message,))

        if any(not isinstance(p, Bot) for p in self.players):
            self.board.print()

    @property
    def players(self):
        return [self.black_player, self.white_player]

    def play(self):
        self._init_game()

        while not self._is_game_finished():
            self._make_one_move()
            self._check_for_winner()

        self._show_finish_game_message()

        return self.winner


if __name__ == '__main__':
    import sys


    class StupidBot(Bot):
        NAME = 'Глупый бот'
        AUTHOR = 'Андрей Гейн'

        def move(self, board):
            for row in range(board.size):
                for column in range(board.size):
                    if board[row][column] == BoardCell.EMPTY.value:
                        return Move(row, column)


    class StupidPrinterBot(StupidBot):
        def move(self, board):
            for row in range(board.size):
                for column in range(board.size):
                    if board[row][column] == self.player_type:
                        print('Нашёл свою клетку: %d, %d' % (row, column))
            return super().move(board)


    class SlowBot(Bot):
        NAME = 'Медленный бот'
        AUTHOR = 'Андрей Гейн'

        def move(self, board):
            import time
            time.sleep(5)


    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format='%(asctime)s [%(levelname)s] %(message)s')
    game = Game(ConsolePlayer, ConsolePlayer)
    game.play()
