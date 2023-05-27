# bimaru.py: Template para implementação do projeto de Inteligência Artificial 2022/2023.
# Devem alterar as classes e funções neste ficheiro de acordo com as instruções do enunciado.
# Além das funções e classes já definidas, podem acrescentar outras que considerem pertinentes.

# Grupo 25:
# 102571 Francisco Gouveia
# 103155 Rui Amaral

import sys
import numpy as np
from search import (
    Problem,
    Node,
    astar_search,
    breadth_first_tree_search,
    depth_first_tree_search,
    greedy_search,
    recursive_best_first_search,
)

water_pos = {
                'T': [(-1, 0), (0, 1), (0, -1)],
                'B': [(1, 0), (0, 1), (0, -1)],
                'R': [(-1, 0), (0, 1), (1, 0)],
                'L': [(-1, 0), (0, -1), (1, 0)],
                'C': [(-1, 0), (0, 1), (0, -1), (1, 0)],
                'M': []
            }

class BimaruState:
    state_id = 0

    def __init__(self, board):
        self.board = board
        self.id = BimaruState.state_id
        BimaruState.state_id += 1

    def __lt__(self, other):
        return self.id < other.id
    
    def actions(self):
        return self.board.get_actions()

    # TODO: outros metodos da classe


class Board:
    """Representação interna de um tabuleiro de Bimaru."""
    def __init__(self, matrix, rows, columns, hints):
        """Construtor para o tabuleiro e informação necessária
            -> '.' = water
            -> 't' = top
            -> 'b' = bottom
            -> 'l' = left
            -> 'r' = right
            -> 'm' = middle
            -> 'c' = circle
            -> 'None' = none (a.k.a. empty)
            Se algum dos símbolos for upper_case então é de uma hint.
        """
        self.board = matrix
        self.rows = rows
        self.columns = columns
        self.my_rows = [0] * 10
        self.my_columns = [0] * 10
        self.incomplete_hints = 0
        self.remaining_ships = [-1, 4, 3, 2, 1]
        self.hints = hints;

    def get_value(self, row: int, col: int) -> str:
        """Devolve o valor na respetiva posição do tabuleiro."""
        return self.board[row, col]

    def adjacent_vertical_values(self, row: int, col: int) -> (str, str):
        """Devolve os valores imediatamente acima e abaixo,
        respectivamente."""
        if row == 0:
            return (None, self.board[row+1, col])
        elif row == 9:
            return (self.board[row-1, col], None)
        else:
            return (self.board[row-1, col], self.board[row+1, col])

    def adjacent_horizontal_values(self, row: int, col: int) -> (str, str):
        """Devolve os valores imediatamente à esquerda e à direita,
        respectivamente."""
        if col == 0:
            return (None, self.board[row, col+1])
        elif col == 9:
            return (self.board[row, col-1], None)
        else:
            return (self.board[row, col-1], self.board[row, col+1])

    #def use_hints(self, hints):
        """Completa o tabuleiro com as informações dadas nas pistas."""
        num_hints = len(hints)
        # Sorts the hints by row and column
        hints.sort(key=lambda hint: hint[0] * 10 + hint[1])

        for i in range(num_hints):
            row = hints[i][0]
            column = hints[i][1]
            letter = hints[i][2]

            if letter in ('T', 'B', 'L', 'R', 'M', 'C'):
                self.board[row, column] = letter
                self.my_rows[row] += 1
                self.my_columns[column] += 1
                self.incomplete_hints += 1
                self.fill_surrounding_water(row, column, letter)

                if letter == 'C':
                    self.remaining_ships[1] -= 1
                    self.incomplete_hints -= 1

                # Checks whether we have completed a ship horizontally
                elif letter == 'R':
                    length = 1
                    while letter in ('R', 'L', 'M'):
                        if (column - length <= 0): break

                        letter = self.board[row, column - length]

                        if letter == 'L':
                            self.remaining_ships[length] -= 1
                            self.incomplete_hints -= length
                            break
                        length += 1

                # Checks whether we have completed a ship vertically
                elif letter == 'B':
                    length = 1
                    while letter in ('B', 'T', 'M'):
                        if (row - length <= 0): break

                        letter = self.board[row - length, column]

                        if letter == 'T':
                            self.remaining_ships[length] -= 1
                            self.incomplete_hints -= length
                            break
                        length += 1
   
    def use_hints(self):
        """Places waters from the hints. Does not place down any ship parts."""
        for hint in self.hints:
            letter = hint[2]
            if (letter == 'W'):
                self.try_place('W', hint[0], hint[1])
            else:
                #self.try_place(letter, hint[0], hint[1])
                self.fill_surrounding_water(hint[0], hint[1], letter)

    def fill_surrounding_water(self, row, column, letter):
        """Fills in the squares around a given ship part with water"""
        # Get all the water positions for the ship part
        pos_offsets = water_pos[letter] + [(1, 1), (-1, -1), (-1, 1), (1, -1)]
        positions = [(row + v_off, column + h_off) for (v_off, h_off) in pos_offsets]

        for pos in positions:
            if (Board.is_valid_position(pos)):
                self.try_place('.', *pos)

    def get_num_ships_in_row(self, row: int) -> int:
        """Retorna o número de navios numa determinada linha."""
        return self.my_rows[row]
            
    def get_num_ships_in_column(self, column: int) -> int:
        """Retorna o número de navios numa determinada coluna."""
        return self.my_columns[column]
        
    def complete_row_with_water(self, row: int):
        """Completa uma linha do tabuleiro com zeros onde estaria None."""
        for i in range(10):
            self.try_place('.', row, i)
    
    def complete_column_with_water(self, column: int):
        """Completa uma coluna do tabuleiro com zeros onde estaria None."""
        for i in range(10):
            self.try_place('.', i, column)

    def try_place(self, letter, row, column):
        """Places a water tile on the given position."""
        if (self.board[row, column] is None):
            self.board[row, column] = letter;

    def complete_board_after_hints(self):
        """Completa o tabuleiro a partir de conclusões que pode tirar
        através das listas rows e columns, e das hints dadas."""
        # Itera sobre linhas
        for i in range(10):
            if self.get_num_ships_in_row(i) == self.rows[i]:
                self.complete_row_with_water(i)
        # Itera sobre colunas
        for i in range(10):
            if self.get_num_ships_in_column(i) == self.columns[i]:
                self.complete_column_with_water(i)
        # Bloqueia espaço ao lado dos barcos
    
    def get_actions(self):
        """Finds all possible actions for the current board."""
        actions = [];
        """for row in range(self.rows.size()):
            parts = self.rows[row] - self.my_rows[row];
            if (parts <= 0): continue
            for col in range(self.columns.size()):
                remaining = parts
                size = 1
                letter = self.board[row][col]
                if (letter in ['W', '.', 'R', 'M']): continue
                if (self.board[row][col - 2] is 'L'
                        or self.board[row][col - 1] is 'M'
                        or self.board[row][col - 2] is 'M'
                        and self.board[row][col - 3] in ['M', 'L']): continue
                if (letter is 'L') {
                    size = 2
                }"""
                    
    def print(self):
        for i in range(10):
            for j in range(10):
                if self.board[i,j] is not None:
                    print(self.board[i,j], end='')
                else:
                    print('*', end='')
            print()

    @staticmethod
    def is_valid_position(pos):
        return pos[0] in range(0, 10) and pos[1] in range(0, 10)

    @staticmethod
    def parse_instance():
        rows, columns, hints = [], [], []
        row_input = input()
        row_ptr = 4
        for i in range(10):
            rows.append(int(row_input[row_ptr]))
            row_ptr += 2
        column_input = input()
        col_init = 7
        for i in range(10):
            columns.append(int(column_input[col_init]))
            col_init += 2
        num_hints = int(input())
        for i in range(num_hints):
            new_hint = input()
            new_hint = (int(new_hint[5]), int(new_hint[7]), new_hint[9])
            hints.append(new_hint)
        # Create a matrix to represent the board and return a Board object
        matrix = np.full((10,10), None)
        my_board = Board(matrix, rows, columns, hints)
        my_board.use_hints()
        return my_board


class Bimaru(Problem):
    def __init__(self, board: Board):
        """O construtor especifica o estado inicial."""
        # É preciso incluir: binaruState, o board, e o id
        # TODO
        pass

    def actions(self, state: BimaruState):
        """Retorna uma lista de ações que podem ser executadas a
        partir do estado passado como argumento."""

        pass

    def result(self, state: BimaruState, action):
        """Retorna o estado resultante de executar a 'action' sobre
        'state' passado como argumento. A ação a executar deve ser uma
        das presentes na lista obtida pela execução de
        self.actions(state)."""
        # TODO
        pass

    def goal_test(self, state: BimaruState):
        """Retorna True se e só se o estado passado como argumento é
        um estado objetivo. Deve verificar se todas as posições do tabuleiro
        estão preenchidas de acordo com as regras do problema."""
        # TODO
        pass

    def h(self, node: Node):
        """Função heuristica utilizada para a procura A*."""
        # TODO
        pass
    
    # TODO: outros metodos da classe

if __name__ == "__main__":
    my_board = Board.parse_instance()
    my_board.complete_board_after_hints()
    my_board.print()
    # TODO:
    # Ler o ficheiro do standard input,
    # Usar uma técnica de procura para resolver a instância,
    # Retirar a solução a partir do nó resultante,
    # Imprimir para o standard output no formato indicado.
