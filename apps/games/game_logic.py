"""
Lógica de juegos para el casino online
Implementa la mecánica de cada juego
"""

import math
import random
from decimal import Decimal
from typing import Dict, Any


class GameLogic:
    """Lógica base para todos los juegos"""

    @staticmethod
    def calculate_payout(bet: Decimal, multiplier: float) -> Decimal:
        """Calcula el payout basado en la apuesta y multiplicador"""
        return Decimal(str(multiplier)) * bet

    @staticmethod
    def calculate_profit(payout: Decimal, bet: Decimal) -> Decimal:
        """Calcula la ganancia (payout - apuesta)"""
        return payout - bet


class SlotsGame:
    """
    Lógica del juego Neon Slots: grid 3x3 (3 rodillos x 3 símbolos), líneas ganadoras y jackpot.

    Diseño de RTP (Return to Player) calibrado por simulación Monte Carlo (400k tiradas) para
    imitar el rango real de los casinos online (92%-97% RTP, es decir 3%-8% de margen de casa,
    según datos de la industria). El jackpot progresivo se financia con un pequeño porcentaje de
    TODAS las apuestas (ganen o pierdan) tal como funcionan los progresivos reales, no solo con
    las apuestas perdedoras: así la casa nunca queda expuesta a pagar más de lo que el propio
    juego recauda a largo plazo.
    """

    SYMBOLS = ['cherry', 'lemon', 'orange', 'watermelon', 'diamond', 'seven']
    WEIGHTS = [30, 25, 20, 15, 7, 3]

    # Multiplicador por línea de 3 símbolos iguales (el símbolo 'seven' no paga aquí: dispara el jackpot)
    LINE_MULTIPLIERS = {
        'cherry': 2.5,
        'lemon': 2.5,
        'orange': 4,
        'watermelon': 6,
        'diamond': 12,
    }

    JACKPOT_SYMBOL = 'seven'
    JACKPOT_BASE_AMOUNT = Decimal('400.00')
    JACKPOT_CONTRIBUTION_RATE = Decimal('0.015')  # 1.5% de CADA apuesta (gane o pierda) alimenta el jackpot

    # 3+ diamantes en cualquier posición del grid (sin necesidad de línea) otorgan giros gratis
    FREE_SPINS_SYMBOL = 'diamond'
    FREE_SPINS_TRIGGER_COUNT = 3
    FREE_SPINS_AWARD = 3

    # Líneas de pago sobre el grid[fila][columna]: 3 filas + 2 diagonales
    LINES = [
        ('row0', [(0, 0), (0, 1), (0, 2)]),
        ('row1', [(1, 0), (1, 1), (1, 2)]),
        ('row2', [(2, 0), (2, 1), (2, 2)]),
        ('diag1', [(0, 0), (1, 1), (2, 2)]),
        ('diag2', [(0, 2), (1, 1), (2, 0)]),
    ]

    @staticmethod
    def spin(bet: Decimal, jackpot_pool: Decimal) -> Dict[str, Any]:
        """Ejecuta una tirada de slots sobre un grid 3x3"""

        grid = [
            [random.choices(SlotsGame.SYMBOLS, weights=SlotsGame.WEIGHTS)[0] for _ in range(3)]
            for _ in range(3)
        ]

        winning_lines = []
        total_multiplier = 0
        jackpot_won = False

        for name, cells in SlotsGame.LINES:
            symbols_in_line = [grid[r][c] for r, c in cells]
            if symbols_in_line[0] == symbols_in_line[1] == symbols_in_line[2]:
                symbol = symbols_in_line[0]
                if symbol == SlotsGame.JACKPOT_SYMBOL:
                    jackpot_won = True
                    winning_lines.append({'line': name, 'symbol': symbol, 'cells': cells, 'jackpot': True})
                else:
                    mult = SlotsGame.LINE_MULTIPLIERS[symbol]
                    total_multiplier += mult
                    winning_lines.append({'line': name, 'symbol': symbol, 'cells': cells, 'multiplier': mult})

        # El pool crece con cada tirada (como los progresivos reales), gane o pierda esa tirada
        jackpot_pool += bet * SlotsGame.JACKPOT_CONTRIBUTION_RATE

        if jackpot_won:
            payout = jackpot_pool
            new_jackpot_pool = SlotsGame.JACKPOT_BASE_AMOUNT
        elif total_multiplier > 0:
            payout = GameLogic.calculate_payout(bet, total_multiplier)
            new_jackpot_pool = jackpot_pool
        else:
            payout = Decimal('0')
            new_jackpot_pool = jackpot_pool

        profit_loss = GameLogic.calculate_profit(payout, bet)

        diamond_count = sum(row.count(SlotsGame.FREE_SPINS_SYMBOL) for row in grid)
        free_spins_awarded = SlotsGame.FREE_SPINS_AWARD if diamond_count >= SlotsGame.FREE_SPINS_TRIGGER_COUNT else 0

        return {
            'grid': grid,
            'winning_lines': winning_lines,
            'multiplier': total_multiplier,
            'payout': float(payout),
            'profit_loss': float(profit_loss),
            'jackpot_won': jackpot_won,
            'jackpot_pool': float(new_jackpot_pool),
            'free_spins_awarded': free_spins_awarded,
            'result': {
                'won': len(winning_lines) > 0
            }
        }


class FarmFestGame:
    """
    Lógica del juego Farm Fest Slots: grid 5x3 (5 rodillos x 3 símbolos), 5 líneas de pago,
    comodín (WILD), símbolo de dispersión (SCATTER) que activa giros gratis, y más figuras
    que Neon Slots (12 símbolos vs 6).

    A diferencia de Neon Slots (líneas de 3 iguales en cualquier posición), aquí se usa el
    estándar real de tragamonedas de 5 rodillos: la línea paga si hay 3, 4 o 5 símbolos
    iguales CONSECUTIVOS empezando desde el rodillo más a la izquierda (igual que Book of Ra,
    Starburst, etc. en casinos reales), con el comodín sustituyendo a cualquier símbolo excepto
    el scatter.

    RTP calibrado por simulación Monte Carlo (5 millones de tiradas) en 96.7% (margen de casa
    ≈3.3%), dentro del mismo rango real de casinos online (92%-97%) usado en Neon Slots.
    """

    SYMBOLS = ['cabbage', 'corn', 'tomato', 'pepper', 'eggplant', 'carrot',
               'chicken', 'sheep', 'pig', 'farmer', 'wild', 'scatter']
    WEIGHTS = [20, 18, 16, 14, 12, 10, 6, 5, 4, 3, 3, 2]

    LOW_TIER = {'cabbage', 'corn', 'tomato', 'pepper', 'eggplant', 'carrot'}
    MID_TIER = {'chicken', 'sheep', 'pig', 'farmer'}

    LOW_PAYTABLE = {3: 4, 4: 13, 5: 42}
    MID_PAYTABLE = {3: 9, 4: 33, 5: 125}
    WILD_PAYTABLE = {3: 16, 4: 67, 5: 250}
    SCATTER_PAYTABLE = {3: 5, 4: 16, 5: 83}

    WILD_SYMBOL = 'wild'
    SCATTER_SYMBOL = 'scatter'
    FREE_SPINS_TRIGGER_COUNT = 3
    FREE_SPINS_AWARD = 10

    COLS = 5
    ROWS = 3

    # 3 líneas horizontales + 2 líneas en zigzag (V e inverse-V), igual que las tragamonedas
    # reales de 5 rodillos que combinan filas rectas con patrones en zigzag
    LINES = [
        ('row0', [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]),
        ('row1', [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4)]),
        ('row2', [(2, 0), (2, 1), (2, 2), (2, 3), (2, 4)]),
        ('v_shape', [(0, 0), (1, 1), (2, 2), (1, 3), (0, 4)]),
        ('inv_v_shape', [(2, 0), (1, 1), (0, 2), (1, 3), (2, 4)]),
    ]

    @staticmethod
    def _evaluate_line(grid, cells):
        """Evalúa cuántos símbolos iguales consecutivos hay desde el rodillo 0 (con comodín)"""
        symbols = [grid[r][c] for r, c in cells]
        first = symbols[0]
        if first == FarmFestGame.SCATTER_SYMBOL:
            return None, 0

        target = first
        if target == FarmFestGame.WILD_SYMBOL:
            for s in symbols[1:]:
                if s != FarmFestGame.WILD_SYMBOL:
                    target = s
                    break

        count = 0
        for s in symbols:
            if s == target or s == FarmFestGame.WILD_SYMBOL:
                count += 1
            else:
                break

        if count < 3:
            return None, 0
        return target, count

    @staticmethod
    def _payout_for(target, count):
        if target == FarmFestGame.WILD_SYMBOL:
            return FarmFestGame.WILD_PAYTABLE.get(count, 0)
        if target in FarmFestGame.LOW_TIER:
            return FarmFestGame.LOW_PAYTABLE.get(count, 0)
        if target in FarmFestGame.MID_TIER:
            return FarmFestGame.MID_PAYTABLE.get(count, 0)
        return 0

    @staticmethod
    def spin(bet: Decimal) -> Dict[str, Any]:
        """Ejecuta una tirada de Farm Fest Slots sobre un grid 5x3"""

        grid = [
            [random.choices(FarmFestGame.SYMBOLS, weights=FarmFestGame.WEIGHTS)[0] for _ in range(FarmFestGame.COLS)]
            for _ in range(FarmFestGame.ROWS)
        ]

        winning_lines = []
        total_multiplier = 0

        for name, cells in FarmFestGame.LINES:
            target, count = FarmFestGame._evaluate_line(grid, cells)
            if target is None:
                continue
            mult = FarmFestGame._payout_for(target, count)
            if mult > 0:
                total_multiplier += mult
                winning_lines.append({
                    'line': name, 'symbol': target, 'count': count, 'cells': cells[:count], 'multiplier': mult
                })

        scatter_count = sum(row.count(FarmFestGame.SCATTER_SYMBOL) for row in grid)
        scatter_win = False
        if scatter_count >= FarmFestGame.FREE_SPINS_TRIGGER_COUNT:
            scatter_mult = FarmFestGame.SCATTER_PAYTABLE.get(scatter_count, FarmFestGame.SCATTER_PAYTABLE[5])
            total_multiplier += scatter_mult
            scatter_win = True

        payout = GameLogic.calculate_payout(bet, total_multiplier) if total_multiplier > 0 else Decimal('0')
        profit_loss = GameLogic.calculate_profit(payout, bet)

        free_spins_awarded = FarmFestGame.FREE_SPINS_AWARD if scatter_win else 0

        return {
            'grid': grid,
            'winning_lines': winning_lines,
            'multiplier': total_multiplier,
            'payout': float(payout),
            'profit_loss': float(profit_loss),
            'scatter_count': scatter_count,
            'scatter_win': scatter_win,
            'free_spins_awarded': free_spins_awarded,
            'result': {
                'won': len(winning_lines) > 0 or scatter_win
            }
        }


class DragonFruitGame:
    """
    Lógica del juego Dragon Fruit Bonanza: grid 6x6 (36 celdas), sin líneas de pago fijas.

    Sigue la variante de "cluster pays" usada por Sweet Bonanza (Pragmatic Play), adaptada
    al grid real de 6x6 de este juego: 10 o más símbolos iguales EN CUALQUIER POSICIÓN del
    grid ganan (el umbral real de Sweet Bonanza es 8, pero ahí el grid es de 30 celdas;
    aquí se sube a 10 para mantener la misma frecuencia de combos con 36 celdas), sin
    necesitar adyacencia entre ellos. Tras
    cada victoria, los símbolos ganadores se eliminan, los símbolos restantes de cada columna
    caen por gravedad, se rellenan los huecos superiores con símbolos nuevos, y el grid se
    vuelve a evaluar (tumble) hasta que no queden más combinaciones nuevas en esa tirada.

    El símbolo scatter (huevo1) activa giros gratis con 4+ apariciones en cualquier lugar
    del grid (incluidas nuevas apariciones durante los propios tumbles de la misma tirada,
    ya que un scatter nunca forma parte de un cluster ganador y por tanto nunca se elimina:
    contar los scatters en el grid final tras todos los tumbles equivale a contar todos los
    que aparecieron en la tirada completa). El símbolo bomba multiplicador (huevo2) solo
    aparece durante los giros gratis, lleva un valor aleatorio (2x-100x), y TODOS los valores
    de bomba vistos durante la tirada completa (incluidos sus tumbles) se SUMAN y ese total
    se aplica como multiplicador a la ganancia acumulada de toda la tirada al final — igual
    que el mecanismo real de Sweet Bonanza durante su bonus de giros gratis.

    RTP calibrado por simulación Monte Carlo (10 millones de tiradas, ver scratchpad
    dragon_fruit_sim.py) en ~95% (margen de casa ≈5%), dentro del mismo rango real de
    casinos online (92%-97%) usado en el resto de juegos de este proyecto.
    """

    COLS = 6
    ROWS = 6
    CELLS = COLS * ROWS
    MIN_CLUSTER = 10  # con 36 celdas, un umbral de 8 (el de Sweet Bonanza a 30 celdas) dispara demasiado seguido

    LOW_TIER = ['lemon', 'strawberry', 'orange', 'watermelon', 'grapes']
    MID_TIER = ['dragon_fruit']
    HIGH_TIER = ['dragon_verde', 'dragon_rojo', 'dragon_de_oro']
    SCATTER_SYMBOL = 'huevo1'
    BOMB_SYMBOL = 'huevo2'

    BASE_SYMBOLS = LOW_TIER + MID_TIER + HIGH_TIER + [SCATTER_SYMBOL]
    BASE_WEIGHTS = [26, 26, 26, 26, 26, 13, 6, 4, 2, 2]

    FREE_SYMBOLS = BASE_SYMBOLS + [BOMB_SYMBOL]
    FREE_WEIGHTS = BASE_WEIGHTS + [4]

    PAYTABLE = {
        'lemon':         {'10-11': 0.84,  '12-14': 3.52,  '15-19': 7.55,  '20-24': 18.46,  '25+': 71.3},
        'strawberry':    {'10-11': 0.84,  '12-14': 3.52,  '15-19': 7.55,  '20-24': 18.46,  '25+': 71.3},
        'orange':        {'10-11': 0.84,  '12-14': 3.52,  '15-19': 7.55,  '20-24': 18.46,  '25+': 71.3},
        'watermelon':    {'10-11': 0.84,  '12-14': 3.52,  '15-19': 7.55,  '20-24': 18.46,  '25+': 71.3},
        'grapes':        {'10-11': 0.84,  '12-14': 3.52,  '15-19': 7.55,  '20-24': 18.46,  '25+': 71.3},
        'dragon_fruit':  {'10-11': 2.18,  '12-14': 7.55,  '15-19': 16.78, '20-24': 42.0,   '25+': 142.6},
        'dragon_verde':  {'10-11': 4.45,  '12-14': 16.78, '15-19': 36.9,  '20-24': 83.9,   '25+': 214.0},
        'dragon_rojo':   {'10-11': 6.71,  '12-14': 25.2,  '15-19': 51.2,  '20-24': 112.4,  '25+': 285.3},
        'dragon_de_oro': {'10-11': 11.75, '12-14': 57.05, '15-19': 83.9,  '20-24': 167.8,  '25+': 428.0},
    }

    SCATTER_TRIGGER = 4
    FREE_SPINS_AWARD = 10
    RETRIGGER_AWARD = 5

    BOMB_VALUES = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100]
    BOMB_WEIGHTS = [30, 20, 15, 10, 8, 6, 4, 3, 2, 1, 0.6, 0.3, 0.1]

    @staticmethod
    def _paybucket(count):
        if count >= 25:
            return '25+'
        if count >= 20:
            return '20-24'
        if count >= 15:
            return '15-19'
        if count >= 12:
            return '12-14'
        return '10-11'  # count siempre es >= MIN_CLUSTER (10) cuando se llama esto

    @staticmethod
    def _draw_symbol(free_mode):
        symbols, weights = (DragonFruitGame.FREE_SYMBOLS, DragonFruitGame.FREE_WEIGHTS) if free_mode \
            else (DragonFruitGame.BASE_SYMBOLS, DragonFruitGame.BASE_WEIGHTS)
        return random.choices(symbols, weights=weights)[0]

    @staticmethod
    def _new_grid(free_mode):
        return [
            [DragonFruitGame._draw_symbol(free_mode) for _ in range(DragonFruitGame.COLS)]
            for _ in range(DragonFruitGame.ROWS)
        ]

    @staticmethod
    def _refill(grid, cleared, free_mode):
        """Aplica gravedad por columna y rellena los huecos superiores con símbolos nuevos"""
        for col in range(DragonFruitGame.COLS):
            survivors = [grid[row][col] for row in range(DragonFruitGame.ROWS) if not cleared[row][col]]
            missing = DragonFruitGame.ROWS - len(survivors)
            new_col = [DragonFruitGame._draw_symbol(free_mode) for _ in range(missing)] + survivors
            for row in range(DragonFruitGame.ROWS):
                grid[row][col] = new_col[row]
        return grid

    @staticmethod
    def spin(bet: Decimal, free_mode: bool = False) -> Dict[str, Any]:
        """Ejecuta una tirada completa (con todos sus tumbles en cascada) de Dragon Fruit Bonanza"""

        grid = DragonFruitGame._new_grid(free_mode)
        initial_grid = [row[:] for row in grid]
        bomb_values = {}  # (row, col) -> valor asignado, persiste mientras la bomba no sea eliminada

        def assign_bomb_values():
            if not free_mode:
                return
            for r in range(DragonFruitGame.ROWS):
                for c in range(DragonFruitGame.COLS):
                    if grid[r][c] == DragonFruitGame.BOMB_SYMBOL and (r, c) not in bomb_values:
                        bomb_values[(r, c)] = random.choices(
                            DragonFruitGame.BOMB_VALUES, weights=DragonFruitGame.BOMB_WEIGHTS
                        )[0]

        assign_bomb_values()

        tumbles = []
        total_win = Decimal('0')

        while True:
            counts = {}
            for r in range(DragonFruitGame.ROWS):
                for c in range(DragonFruitGame.COLS):
                    s = grid[r][c]
                    if s in (DragonFruitGame.SCATTER_SYMBOL, DragonFruitGame.BOMB_SYMBOL):
                        continue
                    counts[s] = counts.get(s, 0) + 1

            winners = {s: c for s, c in counts.items() if c >= DragonFruitGame.MIN_CLUSTER}
            if not winners:
                break

            winner_details = []
            for s, c in winners.items():
                bucket = DragonFruitGame._paybucket(c)
                mult = DragonFruitGame.PAYTABLE[s][bucket]
                amt = bet * Decimal(str(mult))
                total_win += amt
                winner_details.append({'symbol': s, 'count': c, 'multiplier': mult, 'payout': float(amt)})

            cleared = [[grid[r][c] in winners for c in range(DragonFruitGame.COLS)] for r in range(DragonFruitGame.ROWS)]
            cleared_cells = [
                {'row': r, 'col': c} for r in range(DragonFruitGame.ROWS) for c in range(DragonFruitGame.COLS) if cleared[r][c]
            ]

            grid = DragonFruitGame._refill(grid, cleared, free_mode)
            assign_bomb_values()

            tumbles.append({
                'winners': winner_details,
                'cleared_cells': cleared_cells,
                'grid_after': [row[:] for row in grid],
            })

        scatter_count = sum(1 for r in range(DragonFruitGame.ROWS) for c in range(DragonFruitGame.COLS)
                             if grid[r][c] == DragonFruitGame.SCATTER_SYMBOL)

        bomb_list = [{'row': r, 'col': c, 'value': v} for (r, c), v in bomb_values.items()]
        bomb_multiplier_sum = sum(bomb_values.values())

        base_win = total_win
        if free_mode and bomb_multiplier_sum > 0:
            total_win = total_win * bomb_multiplier_sum

        free_spins_triggered = scatter_count >= DragonFruitGame.SCATTER_TRIGGER
        free_spins_awarded = 0
        if free_spins_triggered:
            free_spins_awarded = DragonFruitGame.RETRIGGER_AWARD if free_mode else DragonFruitGame.FREE_SPINS_AWARD

        profit_loss = GameLogic.calculate_profit(total_win, bet)
        total_multiplier = float(total_win / bet) if bet > 0 else 0.0

        return {
            'initial_grid': initial_grid,
            'cols': DragonFruitGame.COLS,
            'rows': DragonFruitGame.ROWS,
            'tumbles': tumbles,
            'final_grid': [row[:] for row in grid],
            'scatter_count': scatter_count,
            'free_spins_triggered': free_spins_triggered,
            'free_spins_awarded': free_spins_awarded,
            'bomb_values': bomb_list,
            'bomb_multiplier_sum': bomb_multiplier_sum,
            'base_win': float(base_win),
            'multiplier': total_multiplier,
            'payout': float(total_win),
            'profit_loss': float(profit_loss),
            'is_free_spin': free_mode,
            'result': {
                'won': total_win > 0
            }
        }


class TotemFallsGame:
    """
    Lógica del juego Totem Falls Bonanza: grid 4x6 (24 celdas), cluster pays + tumble
    (misma metodología que Dragon Fruit Bonanza) con multiplicador de avalancha al
    estilo Gonzo's Quest (NetEnt): cada cascada consecutiva dentro de la misma tirada
    usa un multiplicador mayor de una escalera fija (1x, 2x, 3x, 5x, con tope en 5x),
    aplicado solo a la ganancia de ese paso.

    El comodín (totem_wild) sustituye a cualquier símbolo regular al contar clusters
    (se asigna al símbolo que maximice la ganancia). El scatter (totem_scatter) activa
    giros gratis con 3+ apariciones en cualquier lugar del grid. La ficha multiplicadora
    (totem_multiplicador, "X2") no forma sus propios clusters: cada instancia presente
    en un paso ganador SUMA +2x al multiplicador de avalancha de ese paso (no multiplica,
    para evitar que la combinación con la escalera de avalancha dispare el RTP).

    RTP calibrado por simulación Monte Carlo (ver scratchpad totem_falls_sim.py) en
    ~93%, dentro del rango real de casinos online (92%-97%) usado en el resto de
    juegos de este proyecto. Nota de diseño: con solo 24 celdas y 6 símbolos regulares,
    el umbral mínimo de cluster tuvo que subirse a 8 (más alto que el 8/30celdas de
    Sweet Bonanza o el 10/36celdas de Dragon Fruit) porque una malla tan pequeña con
    pocos tipos de símbolo hace que cualquier umbral bajo dispare cascadas descontroladas.
    """

    COLS = 4
    ROWS = 6
    CELLS = COLS * ROWS
    MIN_CLUSTER = 8

    LOW_TIER = ['totem_3', 'totem_5', 'totem_2']
    MID_TIER = ['totem_4', 'totem_1']
    HIGH_TIER = ['totem_6']
    WILD_SYMBOL = 'totem_wild'
    SCATTER_SYMBOL = 'totem_scatter'
    MULT_SYMBOL = 'totem_multiplicador'

    REGULAR_SYMBOLS = LOW_TIER + MID_TIER + HIGH_TIER
    BASE_SYMBOLS = REGULAR_SYMBOLS + [WILD_SYMBOL, SCATTER_SYMBOL, MULT_SYMBOL]
    BASE_WEIGHTS = [16, 16, 16, 13, 13, 10, 2, 1.0, 4]

    AVALANCHE_LADDER = [1, 2, 3, 5]

    PAYTABLE = {
        'totem_3': {'8-9': 0.41, '10-11': 1.36, '12-15': 4.08,  '16+': 13.6},
        'totem_5': {'8-9': 0.41, '10-11': 1.36, '12-15': 4.08,  '16+': 13.6},
        'totem_2': {'8-9': 0.54, '10-11': 1.77, '12-15': 5.44,  '16+': 17.68},
        'totem_4': {'8-9': 1.09, '10-11': 3.4,  '12-15': 10.88, '16+': 38.08},
        'totem_1': {'8-9': 1.36, '10-11': 4.35, '12-15': 13.6,  '16+': 47.6},
        'totem_6': {'8-9': 2.72, '10-11': 9.52, '12-15': 29.92, '16+': 102.0},
    }

    SCATTER_TRIGGER = 3
    FREE_SPINS_AWARD = 8
    RETRIGGER_AWARD = 4

    @staticmethod
    def _paybucket(count):
        if count >= 16:
            return '16+'
        if count >= 12:
            return '12-15'
        if count >= 10:
            return '10-11'
        return '8-9'

    @staticmethod
    def _avalanche_mult(step_index):
        ladder = TotemFallsGame.AVALANCHE_LADDER
        return ladder[min(step_index, len(ladder) - 1)]

    @staticmethod
    def _draw_symbol():
        return random.choices(TotemFallsGame.BASE_SYMBOLS, weights=TotemFallsGame.BASE_WEIGHTS)[0]

    @staticmethod
    def _new_grid():
        return [[TotemFallsGame._draw_symbol() for _ in range(TotemFallsGame.COLS)] for _ in range(TotemFallsGame.ROWS)]

    @staticmethod
    def _refill(grid, cleared):
        for col in range(TotemFallsGame.COLS):
            survivors = [grid[row][col] for row in range(TotemFallsGame.ROWS) if not cleared[row][col]]
            missing = TotemFallsGame.ROWS - len(survivors)
            new_col = [TotemFallsGame._draw_symbol() for _ in range(missing)] + survivors
            for row in range(TotemFallsGame.ROWS):
                grid[row][col] = new_col[row]
        return grid

    @staticmethod
    def spin(bet: Decimal) -> Dict[str, Any]:
        """Ejecuta una tirada completa (con toda su cascada de avalanchas) de Totem Falls Bonanza"""

        grid = TotemFallsGame._new_grid()
        initial_grid = [row[:] for row in grid]

        tumbles = []
        total_win = Decimal('0')
        step_index = 0

        while True:
            counts = {}
            wild_count = 0
            mult_count = 0
            for r in range(TotemFallsGame.ROWS):
                for c in range(TotemFallsGame.COLS):
                    s = grid[r][c]
                    if s == TotemFallsGame.SCATTER_SYMBOL:
                        continue
                    if s == TotemFallsGame.WILD_SYMBOL:
                        wild_count += 1
                        continue
                    if s == TotemFallsGame.MULT_SYMBOL:
                        mult_count += 1
                        continue
                    counts[s] = counts.get(s, 0) + 1

            wild_target = None
            if wild_count:
                best_gain = -1
                for s, c in counts.items():
                    gain = (TotemFallsGame.PAYTABLE[s][TotemFallsGame._paybucket(c + wild_count)]
                            - TotemFallsGame.PAYTABLE[s][TotemFallsGame._paybucket(c)])
                    if gain > best_gain:
                        best_gain, wild_target = gain, s
                if wild_target is not None and (counts.get(wild_target, 0) + wild_count) >= TotemFallsGame.MIN_CLUSTER:
                    counts[wild_target] = counts.get(wild_target, 0) + wild_count
                else:
                    wild_target = None

            winners = {s: c for s, c in counts.items() if c >= TotemFallsGame.MIN_CLUSTER}
            if not winners:
                break

            step_mult = TotemFallsGame._avalanche_mult(step_index)
            if mult_count:
                step_mult += 2 * mult_count

            winner_details = []
            step_base_win = Decimal('0')
            for s, c in winners.items():
                bucket = TotemFallsGame._paybucket(c)
                mult = TotemFallsGame.PAYTABLE[s][bucket]
                amt = bet * Decimal(str(mult))
                step_base_win += amt
                winner_details.append({
                    'symbol': s, 'count': c, 'multiplier': mult, 'payout': float(amt),
                    'used_wild': s == wild_target
                })

            step_win = step_base_win * Decimal(str(step_mult))
            total_win += step_win

            winner_syms = set(winners.keys())
            cleared = [[grid[r][c] in winner_syms for c in range(TotemFallsGame.COLS)] for r in range(TotemFallsGame.ROWS)]
            if wild_target is not None:
                for r in range(TotemFallsGame.ROWS):
                    for c in range(TotemFallsGame.COLS):
                        if grid[r][c] == TotemFallsGame.WILD_SYMBOL:
                            cleared[r][c] = True

            cleared_cells = [
                {'row': r, 'col': c} for r in range(TotemFallsGame.ROWS) for c in range(TotemFallsGame.COLS) if cleared[r][c]
            ]

            grid = TotemFallsGame._refill(grid, cleared)

            tumbles.append({
                'winners': winner_details,
                'cleared_cells': cleared_cells,
                'grid_after': [row[:] for row in grid],
                'avalanche_multiplier': step_mult,
                'step_win': float(step_win),
            })
            step_index += 1

        scatter_count = sum(1 for r in range(TotemFallsGame.ROWS) for c in range(TotemFallsGame.COLS)
                             if grid[r][c] == TotemFallsGame.SCATTER_SYMBOL)

        free_spins_triggered = scatter_count >= TotemFallsGame.SCATTER_TRIGGER
        free_spins_awarded = TotemFallsGame.FREE_SPINS_AWARD if free_spins_triggered else 0

        profit_loss = GameLogic.calculate_profit(total_win, bet)
        total_multiplier = float(total_win / bet) if bet > 0 else 0.0

        return {
            'initial_grid': initial_grid,
            'cols': TotemFallsGame.COLS,
            'rows': TotemFallsGame.ROWS,
            'tumbles': tumbles,
            'final_grid': [row[:] for row in grid],
            'max_avalanche': tumbles[-1]['avalanche_multiplier'] if tumbles else 0,
            'scatter_count': scatter_count,
            'free_spins_triggered': free_spins_triggered,
            'free_spins_awarded': free_spins_awarded,
            'multiplier': total_multiplier,
            'payout': float(total_win),
            'profit_loss': float(profit_loss),
            'result': {
                'won': total_win > 0
            }
        }


class FrozenAgeGame:
    """
    Lógica del juego Frozen Age: grid 5x5 (25 celdas), cluster pays + tumble
    (misma metodología que Totem Falls Bonanza) con multiplicador de avalancha al
    estilo Gonzo's Quest (NetEnt): cada cascada consecutiva dentro de la misma tirada
    usa un multiplicador mayor de una escalera fija (1x, 2x, 3x, 5x, con tope en 5x),
    aplicado solo a la ganancia de ese paso.

    El comodín (frozen_wild) sustituye a cualquier símbolo regular al contar clusters
    (se asigna al símbolo que maximice la ganancia). El scatter (frozen_egg_gold) activa
    giros gratis con 3+ apariciones en cualquier lugar del grid. La ficha multiplicadora
    (frozen_egg_purple) no forma sus propios clusters: cada instancia presente en un paso
    ganador SUMA +2x al multiplicador de avalancha de ese paso (no multiplica, para evitar
    que la combinación con la escalera de avalancha dispare el RTP).

    RTP calibrado por simulación Monte Carlo (ver scratchpad frozen_age_sim.py, 500k
    tiradas) en ~93%, dentro del rango real de casinos online (92%-97%) usado en el
    resto de juegos de este proyecto. Nota de diseño: con 25 celdas repartidas entre 10
    símbolos regulares (más que Totem Falls, que solo usa 6), el promedio de apariciones
    por símbolo es más bajo, así que el umbral mínimo de cluster se bajó a 6 (vs. 8 en
    Totem Falls) para que los clusters sigan siendo alcanzables sin diluirse demasiado.
    """

    COLS = 5
    ROWS = 5
    CELLS = COLS * ROWS
    MIN_CLUSTER = 6

    LOW_TIER = ['frozen_k', 'frozen_q', 'frozen_j', 'frozen_a']
    MID_TIER = ['frozen_dino_1', 'frozen_dino_2', 'frozen_dino_3', 'frozen_dino_4']
    HIGH_TIER = ['frozen_dino_5', 'frozen_dino_6']
    WILD_SYMBOL = 'frozen_wild'
    SCATTER_SYMBOL = 'frozen_egg_gold'
    MULT_SYMBOL = 'frozen_egg_purple'

    REGULAR_SYMBOLS = LOW_TIER + MID_TIER + HIGH_TIER
    BASE_SYMBOLS = REGULAR_SYMBOLS + [WILD_SYMBOL, SCATTER_SYMBOL, MULT_SYMBOL]
    BASE_WEIGHTS = [18, 18, 18, 18, 10, 10, 10, 10, 5, 4, 2.5, 1.2, 3.5]

    AVALANCHE_LADDER = [1, 2, 3, 5]

    PAYTABLE = {
        'frozen_k': {'6-8': 0.18, '9-13': 0.46, '14-18': 1.4, '19+': 3.7},
        'frozen_q': {'6-8': 0.18, '9-13': 0.46, '14-18': 1.4, '19+': 3.7},
        'frozen_j': {'6-8': 0.23, '9-13': 0.56, '14-18': 1.65, '19+': 4.6},
        'frozen_a': {'6-8': 0.23, '9-13': 0.56, '14-18': 1.65, '19+': 4.6},
        'frozen_dino_1': {'6-8': 0.32, '9-13': 0.83, '14-18': 2.3, '19+': 6.5},
        'frozen_dino_2': {'6-8': 0.32, '9-13': 0.83, '14-18': 2.3, '19+': 6.5},
        'frozen_dino_3': {'6-8': 0.42, '9-13': 1.1, '14-18': 3.0, '19+': 8.3},
        'frozen_dino_4': {'6-8': 0.42, '9-13': 1.1, '14-18': 3.0, '19+': 8.3},
        'frozen_dino_5': {'6-8': 0.74, '9-13': 2.0, '14-18': 5.5, '19+': 14.8},
        'frozen_dino_6': {'6-8': 1.3, '9-13': 3.7, '14-18': 10.2, '19+': 28.0},
    }

    SCATTER_TRIGGER = 3
    FREE_SPINS_AWARD = 8
    RETRIGGER_AWARD = 4

    @staticmethod
    def _paybucket(count):
        if count >= 19:
            return '19+'
        if count >= 14:
            return '14-18'
        if count >= 9:
            return '9-13'
        return '6-8'

    @staticmethod
    def _avalanche_mult(step_index):
        ladder = FrozenAgeGame.AVALANCHE_LADDER
        return ladder[min(step_index, len(ladder) - 1)]

    @staticmethod
    def _draw_symbol():
        return random.choices(FrozenAgeGame.BASE_SYMBOLS, weights=FrozenAgeGame.BASE_WEIGHTS)[0]

    @staticmethod
    def _new_grid():
        return [[FrozenAgeGame._draw_symbol() for _ in range(FrozenAgeGame.COLS)] for _ in range(FrozenAgeGame.ROWS)]

    @staticmethod
    def _refill(grid, cleared):
        for col in range(FrozenAgeGame.COLS):
            survivors = [grid[row][col] for row in range(FrozenAgeGame.ROWS) if not cleared[row][col]]
            missing = FrozenAgeGame.ROWS - len(survivors)
            new_col = [FrozenAgeGame._draw_symbol() for _ in range(missing)] + survivors
            for row in range(FrozenAgeGame.ROWS):
                grid[row][col] = new_col[row]
        return grid

    @staticmethod
    def spin(bet: Decimal) -> Dict[str, Any]:
        """Ejecuta una tirada completa (con toda su cascada de avalanchas) de Frozen Age"""

        grid = FrozenAgeGame._new_grid()
        initial_grid = [row[:] for row in grid]

        tumbles = []
        total_win = Decimal('0')
        step_index = 0

        while True:
            counts = {}
            wild_count = 0
            mult_count = 0
            for r in range(FrozenAgeGame.ROWS):
                for c in range(FrozenAgeGame.COLS):
                    s = grid[r][c]
                    if s == FrozenAgeGame.SCATTER_SYMBOL:
                        continue
                    if s == FrozenAgeGame.WILD_SYMBOL:
                        wild_count += 1
                        continue
                    if s == FrozenAgeGame.MULT_SYMBOL:
                        mult_count += 1
                        continue
                    counts[s] = counts.get(s, 0) + 1

            wild_target = None
            if wild_count:
                best_gain = -1
                for s, c in counts.items():
                    gain = (FrozenAgeGame.PAYTABLE[s][FrozenAgeGame._paybucket(c + wild_count)]
                            - FrozenAgeGame.PAYTABLE[s][FrozenAgeGame._paybucket(c)])
                    if gain > best_gain:
                        best_gain, wild_target = gain, s
                if wild_target is not None and (counts.get(wild_target, 0) + wild_count) >= FrozenAgeGame.MIN_CLUSTER:
                    counts[wild_target] = counts.get(wild_target, 0) + wild_count
                else:
                    wild_target = None

            winners = {s: c for s, c in counts.items() if c >= FrozenAgeGame.MIN_CLUSTER}
            if not winners:
                break

            step_mult = FrozenAgeGame._avalanche_mult(step_index)
            if mult_count:
                step_mult += 2 * mult_count

            winner_details = []
            step_base_win = Decimal('0')
            for s, c in winners.items():
                bucket = FrozenAgeGame._paybucket(c)
                mult = FrozenAgeGame.PAYTABLE[s][bucket]
                amt = bet * Decimal(str(mult))
                step_base_win += amt
                winner_details.append({
                    'symbol': s, 'count': c, 'multiplier': mult, 'payout': float(amt),
                    'used_wild': s == wild_target
                })

            step_win = step_base_win * Decimal(str(step_mult))
            total_win += step_win

            winner_syms = set(winners.keys())
            cleared = [[grid[r][c] in winner_syms for c in range(FrozenAgeGame.COLS)] for r in range(FrozenAgeGame.ROWS)]
            if wild_target is not None:
                for r in range(FrozenAgeGame.ROWS):
                    for c in range(FrozenAgeGame.COLS):
                        if grid[r][c] == FrozenAgeGame.WILD_SYMBOL:
                            cleared[r][c] = True

            cleared_cells = [
                {'row': r, 'col': c} for r in range(FrozenAgeGame.ROWS) for c in range(FrozenAgeGame.COLS) if cleared[r][c]
            ]

            grid = FrozenAgeGame._refill(grid, cleared)

            tumbles.append({
                'winners': winner_details,
                'cleared_cells': cleared_cells,
                'grid_after': [row[:] for row in grid],
                'avalanche_multiplier': step_mult,
                'step_win': float(step_win),
            })
            step_index += 1

        scatter_count = sum(1 for r in range(FrozenAgeGame.ROWS) for c in range(FrozenAgeGame.COLS)
                             if grid[r][c] == FrozenAgeGame.SCATTER_SYMBOL)

        free_spins_triggered = scatter_count >= FrozenAgeGame.SCATTER_TRIGGER
        free_spins_awarded = FrozenAgeGame.FREE_SPINS_AWARD if free_spins_triggered else 0

        profit_loss = GameLogic.calculate_profit(total_win, bet)
        total_multiplier = float(total_win / bet) if bet > 0 else 0.0

        return {
            'initial_grid': initial_grid,
            'cols': FrozenAgeGame.COLS,
            'rows': FrozenAgeGame.ROWS,
            'tumbles': tumbles,
            'final_grid': [row[:] for row in grid],
            'max_avalanche': tumbles[-1]['avalanche_multiplier'] if tumbles else 0,
            'scatter_count': scatter_count,
            'free_spins_triggered': free_spins_triggered,
            'free_spins_awarded': free_spins_awarded,
            'multiplier': total_multiplier,
            'payout': float(total_win),
            'profit_loss': float(profit_loss),
            'result': {
                'won': total_win > 0
            }
        }


class PandaMinesGame:
    """
    Lógica del juego Panda Mines (grid 5x5 = 25 celdas, cantidad de minas configurable).

    Usa la misma fórmula combinatoria que los juegos "Mines" reales de casinos online
    (Stake Originals, BC.Game, etc.): el multiplicador en cada punto de cobro es el inverso
    exacto de la probabilidad de haber revelado esa cantidad de celdas seguras sin tocar
    una mina, multiplicado por (1 - margen de casa). Como la probabilidad de supervivencia
    ya es matemáticamente exacta, el RTP resultante es EXACTAMENTE (1 - HOUSE_EDGE) sin
    importar cuántas celdas revele el jugador ni cuándo decida retirarse — así la casa
    siempre mantiene su margen garantizado, jugada tras jugada.
    """

    GRID_SIZE = 5  # 5x5 = 25 celdas
    TOTAL_CELLS = GRID_SIZE ** 2
    HOUSE_EDGE = Decimal('0.04')  # 4% de margen -> 96% RTP, estándar de la industria
    MIN_MINES = 1
    MAX_MINES = TOTAL_CELLS - 1

    # Una celda segura al azar (nunca una mina) es el "diamante": si el jugador la revela,
    # duplica el multiplicador de esa partida en adelante (si iba a ganar 2x, gana 4x).
    #
    # OJO: duplicar directamente el multiplicador de odds-exactas rompe la equidad del juego,
    # porque revelar más celdas hace más probable encontrar el diamante Y a la vez ya paga más
    # por sí solo — combinados, el premio se dispara sin límite (verificado por simulación: el
    # RTP se disparaba a 130-140%, insostenible para la casa). Para que el bono sea seguro sin
    # importar cuántas celdas revele el jugador, se reparte el mismo "pozo justo" (fair_multiplier
    # * (1-margen)) entre el caso con diamante y sin diamante, ponderado por la probabilidad real
    # de que el diamante ya haya aparecido entre las celdas reveladas. Así el valor esperado total
    # en cualquier punto de cobro sigue siendo EXACTAMENTE (1 - HOUSE_EDGE), con o sin diamante.
    DIAMOND_MULTIPLIER = Decimal('2')

    @staticmethod
    def generate_grid(mine_count: int) -> Dict[str, Any]:
        """Genera un grid con minas escondidas y una celda diamante (bono x2) entre las seguras"""
        mine_count = max(PandaMinesGame.MIN_MINES, min(int(mine_count), PandaMinesGame.MAX_MINES))
        all_cells = list(range(PandaMinesGame.TOTAL_CELLS))
        mines = random.sample(all_cells, mine_count)
        safe_cells = [c for c in all_cells if c not in mines]
        diamond_cell = random.choice(safe_cells)
        return {
            'mines': mines,
            'mine_count': mine_count,
            'diamond_cell': diamond_cell,
            'diamond_found': False,
            'revealed': []
        }

    @staticmethod
    def calculate_multiplier(mine_count: int, cells_revealed: int, diamond_found: bool = False) -> Decimal:
        """Multiplicador justo (odds exactas de supervivencia) menos el margen de la casa"""
        if cells_revealed <= 0:
            return Decimal('1.0')

        safe_cells = PandaMinesGame.TOTAL_CELLS - mine_count
        cells_revealed = min(cells_revealed, safe_cells)

        fair_multiplier = (
            Decimal(math.comb(PandaMinesGame.TOTAL_CELLS, cells_revealed))
            / Decimal(math.comb(safe_cells, cells_revealed))
        )
        fair_pool = fair_multiplier * (Decimal('1') - PandaMinesGame.HOUSE_EDGE)

        # Probabilidad real de que el diamante ya esté entre las celdas reveladas
        p_diamond = Decimal(cells_revealed) / Decimal(safe_cells) if safe_cells > 0 else Decimal('0')
        base_multiplier = fair_pool / (Decimal('1') + p_diamond)

        if diamond_found:
            return base_multiplier * PandaMinesGame.DIAMOND_MULTIPLIER
        return base_multiplier

    @staticmethod
    def reveal_cell(grid: Dict, cell_id: int) -> Dict[str, Any]:
        """Revela una celda. No paga nada todavía: el pago solo ocurre al cobrar (cash_out)"""

        if cell_id in grid['mines']:
            return {
                'hit_mine': True,
                'mines': grid['mines'],
                'game_over': True
            }

        is_diamond = (cell_id == grid['diamond_cell'])
        if cell_id not in grid['revealed']:
            grid['revealed'].append(cell_id)
        if is_diamond:
            grid['diamond_found'] = True

        cells_revealed = len(grid['revealed'])
        safe_cells = PandaMinesGame.TOTAL_CELLS - grid['mine_count']
        multiplier = PandaMinesGame.calculate_multiplier(grid['mine_count'], cells_revealed, grid['diamond_found'])
        all_safe_found = cells_revealed >= safe_cells

        next_multiplier = None
        if not all_safe_found:
            next_multiplier = float(round(
                PandaMinesGame.calculate_multiplier(grid['mine_count'], cells_revealed + 1, grid['diamond_found']), 4
            ))

        return {
            'hit_mine': False,
            'cell_id': cell_id,
            'is_diamond': is_diamond,
            'cells_revealed': cells_revealed,
            'multiplier': float(round(multiplier, 4)),
            'next_multiplier': next_multiplier,
            'game_over': all_safe_found,
            'auto_cashout': all_safe_found
        }

    @staticmethod
    def cash_out(grid: Dict, bet: Decimal) -> Dict[str, Any]:
        """Cobra la apuesta al multiplicador actual (único momento en que se paga)"""
        cells_revealed = len(grid['revealed'])
        multiplier = PandaMinesGame.calculate_multiplier(
            grid['mine_count'], cells_revealed, grid.get('diamond_found', False)
        )
        payout = GameLogic.calculate_payout(bet, float(multiplier)) if cells_revealed > 0 else Decimal('0')
        profit_loss = GameLogic.calculate_profit(payout, bet)

        return {
            'cells_revealed': cells_revealed,
            'multiplier': float(round(multiplier, 4)),
            'payout': float(payout),
            'profit_loss': float(profit_loss)
        }


class DuckRushGame:
    """
    Lógica de Duck Rush: el jugador dispara a patos que aparecen en pantalla, acumulando
    un multiplicador con cada acierto, y puede retirar su premio en cualquier momento después
    del primer acierto. Cada ronda comienza con 3 tiros; un pato bonus otorga +1 tiro extra o
    duplica la ganancia del siguiente acierto. Un pato trampa (o fallar el tiro) termina la
    ronda de inmediato con pago 0.

    RTP calibrado por simulación Monte Carlo (5 millones de tiradas): la estrategia MÁS SEGURA
    posible para el jugador (retirar justo después del primer acierto) da un RTP de ≈94.2%
    (margen de casa ≈5.8%), y CUALQUIER estrategia más arriesgada (seguir disparando) tiene un
    RTP progresivamente menor (verificado por simulación: ≈75% reteniendo hasta 2 aciertos,
    ≈46% hasta 3, ≈45% agotando también los tiros extra de bonus) — es decir, ninguna estrategia
    posible del jugador supera nunca el 100% de RTP, así la casa nunca puede quedar expuesta a
    perder dinero sin importar cómo juegue el usuario. El riesgo de fallo (pato trampa) crece en
    cada tiro sucesivo (17% -> 30% -> 47% -> 65%), lo que premia matemáticamente a quien decide
    retirarse a tiempo, tal como pide el diseño original del juego.
    """

    BASE_SHOTS = 3
    MAX_MULTIPLIER = Decimal('250')

    DUCK_MULTIPLIERS = {
        'comun': Decimal('1.03'),
        'veloz': Decimal('1.20'),
        'dorado': Decimal('1.80'),
        'bonus': Decimal('1.15'),
    }

    # Probabilidades por tiro (el riesgo de trampa/fallo crece con cada tiro sucesivo).
    # A partir del 4to tiro se reutiliza la última etapa.
    STAGES = [
        {'comun': 0.56, 'veloz': 0.17, 'dorado': 0.07, 'bonus': 0.03, 'trampa': 0.17},
        {'comun': 0.45, 'veloz': 0.17, 'dorado': 0.06, 'bonus': 0.02, 'trampa': 0.30},
        {'comun': 0.32, 'veloz': 0.14, 'dorado': 0.05, 'bonus': 0.02, 'trampa': 0.47},
        {'comun': 0.20, 'veloz': 0.10, 'dorado': 0.04, 'bonus': 0.01, 'trampa': 0.65},
    ]

    @staticmethod
    def start_round(bet: Decimal) -> Dict[str, Any]:
        """Crea el estado inicial de una ronda (se guarda en sesión, como Panda Mines)"""
        return {
            'bet_amount': str(bet),
            'multiplier': '1.0',
            'shots_taken': 0,
            'shots_allowed': DuckRushGame.BASE_SHOTS,
            'hits': 0,
            'duplicator_next': False,
        }

    @staticmethod
    def _stage_for(shot_index: int) -> Dict[str, float]:
        return DuckRushGame.STAGES[min(shot_index, len(DuckRushGame.STAGES) - 1)]

    @staticmethod
    def _pick_outcome(stage: Dict[str, float]) -> str:
        r = random.random()
        cumulative = 0.0
        for outcome, prob in stage.items():
            cumulative += prob
            if r < cumulative:
                return outcome
        return 'trampa'

    @staticmethod
    def shoot(round_state: Dict) -> Dict[str, Any]:
        """Ejecuta un disparo sobre la ronda activa. Modifica round_state in-place."""
        shots_taken = round_state['shots_taken']
        shots_allowed = round_state['shots_allowed']

        if shots_taken >= shots_allowed:
            return {'error': 'no_shots_left'}

        stage = DuckRushGame._stage_for(shots_taken)
        outcome = DuckRushGame._pick_outcome(stage)
        round_state['shots_taken'] += 1

        if outcome == 'trampa':
            return {
                'duck': 'trampa',
                'hit': False,
                'game_over': True,
                'multiplier': float(Decimal(round_state['multiplier'])),
                'payout': 0.0,
            }

        multiplier = Decimal(round_state['multiplier'])
        gain = DuckRushGame.DUCK_MULTIPLIERS[outcome] - Decimal('1')
        if round_state['duplicator_next']:
            gain *= 2
            round_state['duplicator_next'] = False

        multiplier = min(multiplier * (Decimal('1') + gain), DuckRushGame.MAX_MULTIPLIER)
        round_state['multiplier'] = str(multiplier)
        round_state['hits'] += 1

        bonus_effect = None
        if outcome == 'bonus':
            if random.random() < 0.5:
                round_state['shots_allowed'] += 1
                bonus_effect = 'extra_shot'
            else:
                round_state['duplicator_next'] = True
                bonus_effect = 'duplicator'

        bet = Decimal(round_state['bet_amount'])
        potential_payout = GameLogic.calculate_payout(bet, float(multiplier))
        shots_remaining = round_state['shots_allowed'] - round_state['shots_taken']

        return {
            'duck': outcome,
            'hit': True,
            'game_over': False,
            'bonus_effect': bonus_effect,
            'multiplier': float(round(multiplier, 4)),
            'potential_payout': float(potential_payout),
            'shots_remaining': shots_remaining,
            'can_cash_out': round_state['hits'] > 0,
        }

    @staticmethod
    def cash_out(round_state: Dict) -> Dict[str, Any]:
        """Cobra la apuesta al multiplicador actual (0 si aún no hubo ningún acierto)"""
        bet = Decimal(round_state['bet_amount'])
        multiplier = Decimal(round_state['multiplier'])
        payout = GameLogic.calculate_payout(bet, float(multiplier)) if round_state['hits'] > 0 else Decimal('0')
        profit_loss = GameLogic.calculate_profit(payout, bet)
        return {
            'multiplier': float(round(multiplier, 4)),
            'payout': float(payout),
            'profit_loss': float(profit_loss),
            'hits': round_state['hits'],
        }


class GoldenSlingRushGame:
    """
    Lógica de Golden Sling Rush: el jugador apuesta y lanza pájaros con una resortera contra
    una torre de bloques. Cada lanzamiento exitoso sube un multiplicador acumulado y el jugador
    elige COBRAR (banca la ganancia actual) o LANZAR DE NUEVO (arriesga todo por más). Un bloque
    trampa (fallo) termina la ronda de inmediato con pago 0. Misma familia de mecánica "apuesta y
    sigue" que DuckRushGame en este mismo archivo.

    Probabilidades por lanzamiento tal como se especificó (el riesgo de fallo crece con cada
    lanzamiento sucesivo; a partir del 4to se reutiliza la última etapa):
      lanzamiento 1: común 60%, cristal 20%, cofre 8%, pájaro dorado 5%, fallo 7%
      lanzamiento 2: común 45%, cristal 20%, cofre 7%, pájaro dorado 4%, fallo 24%
      lanzamiento 3: común 32%, cristal 17%, cofre 6%, pájaro dorado 3%, fallo 42%
      lanzamiento 4+: común 22%, cristal 12%, cofre 4%, pájaro dorado 2%, fallo 60%

    Diseño de RTP (misma filosofía que DuckRushGame, verificada por simulación Monte Carlo en
    scratchpad golden_sling_sim.py, 2M tiradas x 3 semillas): se usan ganancias FIJAS por tipo de
    bloque (no escaladas para volverse invariantes a la estrategia), así que como el riesgo de
    fallo crece más rápido de lo que compensa la ganancia, la ESTRATEGIA MÁS SEGURA posible
    (cobrar justo después del primer acierto) da un RTP de ≈95.4% (dentro del rango 94%-96%
    pedido), y CUALQUIER estrategia más arriesgada tiene un RTP progresivamente menor (confirmado
    por simulación: ≈83.6% cobrando tras 2 aciertos, ≈69.7% tras 3, ≈51.8% tras 4, ≈28% tras 6) —
    ninguna estrategia posible del jugador supera nunca el ≈95.4% de RTP, así la casa siempre
    mantiene su margen sin importar cuándo decida cobrar el jugador.

    El cofre bonus y el pájaro dorado tienen una pequeña probabilidad anidada de activar el bonus
    NIDO DORADO (5 lanzamientos gratis garantizados que siguen subiendo el multiplicador) o la
    CORONA JACKPOT (salto de multiplicador enorme) respectivamente — ambos son variancia extra ya
    incluida en la calibración de RTP de arriba, mantenidos poco frecuentes para no desviar el
    margen de la casa. El multiplicador total de la ronda está topado en MAX_MULTIPLIER.
    """

    STAGES = [
        # (común, cristal, cofre, pájaro_dorado, fallo)
        (0.60, 0.20, 0.08, 0.05, 0.07),   # lanzamiento 1
        (0.45, 0.20, 0.07, 0.04, 0.24),   # lanzamiento 2
        (0.32, 0.17, 0.06, 0.03, 0.42),   # lanzamiento 3
        (0.22, 0.12, 0.04, 0.02, 0.60),   # lanzamiento 4+
    ]

    # Ganancia multiplicativa fija por tipo de bloque, escalada por profundidad (más riesgo,
    # más premio si se acierta) — ver docstring: NO se escala para ser invariante a la estrategia.
    GAINS = [
        {'comun': 0.001, 'cristal': 0.015, 'cofre': 0.03, 'dorado': 0.05},   # lanzamiento 1
        {'comun': 0.04,  'cristal': 0.16,  'cofre': 0.35, 'dorado': 0.70},   # lanzamiento 2
        {'comun': 0.13,  'cristal': 0.48,  'cofre': 0.95, 'dorado': 1.90},  # lanzamiento 3
        {'comun': 0.30,  'cristal': 0.95,  'cofre': 1.90, 'dorado': 3.80},  # lanzamiento 4+
    ]

    MAX_MULTIPLIER = Decimal('500')

    CHEST_BONUS_CHANCE = 0.05      # probabilidad de que un cofre sea especial -> activa Nido Dorado
    GOLDEN_CORONA_CHANCE = 0.02    # probabilidad de que un pájaro dorado sea la Corona Jackpot
    CORONA_FACTOR_RANGE = (8.0, 15.0)

    BONUS_FREE_THROWS = 5
    BONUS_GAIN_RANGE = (0.08, 0.20)
    BONUS_GOLDEN_CHANCE = 0.12
    BONUS_GOLDEN_EXTRA_GAIN = 0.25

    # Personajes usados solo para la animación del frontend (no afectan la matemática)
    BIRDS = ['rey', 'veloz', 'bomba', 'dorado']

    @staticmethod
    def _stage_for(throw_index: int) -> tuple:
        return GoldenSlingRushGame.STAGES[min(throw_index, len(GoldenSlingRushGame.STAGES) - 1)]

    @staticmethod
    def _gains_for(throw_index: int) -> Dict[str, float]:
        return GoldenSlingRushGame.GAINS[min(throw_index, len(GoldenSlingRushGame.GAINS) - 1)]

    @staticmethod
    def _pick_outcome(stage: tuple) -> str:
        comun, cristal, cofre, dorado, fallo = stage
        r = random.random()
        if r < comun:
            return 'comun'
        r -= comun
        if r < cristal:
            return 'cristal'
        r -= cristal
        if r < cofre:
            return 'cofre'
        r -= cofre
        if r < dorado:
            return 'dorado'
        return 'fallo'

    @staticmethod
    def _pick_bird(outcome: str, bonus_triggered: bool) -> str:
        """Elige qué personaje se usa en la animación de este lanzamiento (cosmético)"""
        if outcome == 'dorado' or outcome == 'corona' or bonus_triggered:
            return 'dorado'
        if outcome == 'fallo':
            return random.choice(['bomba', 'rey'])
        if outcome == 'cristal':
            return random.choice(['veloz', 'rey'])
        return random.choice(['rey', 'veloz', 'bomba'])

    @staticmethod
    def _run_bonus(multiplier: Decimal) -> Decimal:
        """Bonus Nido Dorado: 5 lanzamientos gratis garantizados que siguen subiendo el multiplicador"""
        for _ in range(GoldenSlingRushGame.BONUS_FREE_THROWS):
            gain = random.uniform(*GoldenSlingRushGame.BONUS_GAIN_RANGE)
            if random.random() < GoldenSlingRushGame.BONUS_GOLDEN_CHANCE:
                gain += GoldenSlingRushGame.BONUS_GOLDEN_EXTRA_GAIN
            multiplier *= Decimal(str(1 + gain))
            multiplier = min(multiplier, GoldenSlingRushGame.MAX_MULTIPLIER)
        return multiplier

    @staticmethod
    def start_round(bet: Decimal) -> Dict[str, Any]:
        """Crea el estado inicial de una ronda (se guarda en sesión, como Duck Rush / Panda Mines)"""
        return {
            'bet_amount': str(bet),
            'multiplier': '1.0',
            'throws_taken': 0,
            'hits': 0,
        }

    @staticmethod
    def throw(round_state: Dict) -> Dict[str, Any]:
        """Ejecuta un lanzamiento sobre la ronda activa. Modifica round_state in-place."""
        throw_index = round_state['throws_taken']
        stage = GoldenSlingRushGame._stage_for(throw_index)
        outcome = GoldenSlingRushGame._pick_outcome(stage)
        round_state['throws_taken'] += 1

        if outcome == 'fallo':
            bird = GoldenSlingRushGame._pick_bird(outcome, False)
            return {
                'bird': bird,
                'outcome': 'fallo',
                'hit': False,
                'game_over': True,
                'multiplier': float(Decimal(round_state['multiplier'])),
                'payout': 0.0,
            }

        multiplier = Decimal(round_state['multiplier'])
        gain = GoldenSlingRushGame._gains_for(throw_index)[outcome]
        bonus_triggered = False
        final_outcome = outcome

        if outcome == 'dorado' and random.random() < GoldenSlingRushGame.GOLDEN_CORONA_CHANCE:
            factor = random.uniform(*GoldenSlingRushGame.CORONA_FACTOR_RANGE)
            multiplier *= Decimal(str(factor))
            final_outcome = 'corona'
        else:
            multiplier *= Decimal(str(1 + gain))

        if outcome == 'cofre' and random.random() < GoldenSlingRushGame.CHEST_BONUS_CHANCE:
            multiplier = GoldenSlingRushGame._run_bonus(multiplier)
            bonus_triggered = True

        multiplier = min(multiplier, GoldenSlingRushGame.MAX_MULTIPLIER)
        round_state['multiplier'] = str(multiplier)
        round_state['hits'] += 1

        bird = GoldenSlingRushGame._pick_bird(final_outcome, bonus_triggered)
        bet = Decimal(round_state['bet_amount'])
        potential_payout = GameLogic.calculate_payout(bet, float(multiplier))

        return {
            'bird': bird,
            'outcome': final_outcome,
            'bonus_triggered': bonus_triggered,
            'hit': True,
            'game_over': False,
            'multiplier': float(round(multiplier, 4)),
            'potential_payout': float(potential_payout),
            'can_cash_out': round_state['hits'] > 0,
        }

    @staticmethod
    def cash_out(round_state: Dict) -> Dict[str, Any]:
        """Cobra la apuesta al multiplicador actual (0 si aún no hubo ningún acierto)"""
        bet = Decimal(round_state['bet_amount'])
        multiplier = Decimal(round_state['multiplier'])
        payout = GameLogic.calculate_payout(bet, float(multiplier)) if round_state['hits'] > 0 else Decimal('0')
        profit_loss = GameLogic.calculate_profit(payout, bet)
        return {
            'multiplier': float(round(multiplier, 4)),
            'payout': float(payout),
            'profit_loss': float(profit_loss),
            'hits': round_state['hits'],
        }


class RouletteGame:
    """
    Lógica de la Ruleta Europea (0-36, una sola casilla verde — no americana con doble cero).

    Los multiplicadores representan el RETORNO TOTAL (apuesta + ganancia), igual que en el resto
    de los juegos de esta plataforma. Con las probabilidades reales de la ruleta europea, TODAS
    las apuestas (número pleno, columna, docena, o apuestas simples como rojo/par) dan exactamente
    el mismo RTP: 36/37 ≈ 97.3% (margen de casa 2.7%) — es la elegancia matemática de la ruleta
    europea real la que garantiza que la casa nunca pierda a largo plazo, sin importar qué
    combinación de apuestas haga el jugador.
    """

    WHEEL_SIZE = 37  # 0-36
    RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    COLUMNS = {
        1: {1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34},
        2: {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35},
        3: {3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36},
    }
    DOZENS = {
        1: set(range(1, 13)),
        2: set(range(13, 25)),
        3: set(range(25, 37)),
    }

    @staticmethod
    def spin_wheel() -> int:
        """Gira la ruleta una sola vez y devuelve el número ganador (0-36)"""
        return random.randint(0, RouletteGame.WHEEL_SIZE - 1)

    @staticmethod
    def evaluate_bet(number: int, bet_type: str, bet_value) -> int:
        """
        Evalúa una apuesta contra un número ya girado (permite colocar múltiples apuestas
        simultáneas sobre el mismo giro, como en una mesa de ruleta real).
        bet_type: 'number' (bet_value=0-36), 'red', 'black', 'even', 'odd',
                  'range' (bet_value='1-18' o '19-36'), 'dozen' (bet_value=1/2/3),
                  'column' (bet_value=1/2/3)

        Devuelve el multiplicador de retorno total (0 si la apuesta no ganó).
        """
        is_red = number in RouletteGame.RED_NUMBERS

        if bet_type == 'number' and int(bet_value) == number:
            return 36  # 35:1 + apuesta devuelta
        if bet_type == 'red' and is_red:
            return 2
        if bet_type == 'black' and number != 0 and not is_red:
            return 2
        if bet_type == 'even' and number != 0 and number % 2 == 0:
            return 2
        if bet_type == 'odd' and number % 2 == 1:
            return 2
        if bet_type == 'range' and bet_value == '1-18' and 1 <= number <= 18:
            return 2
        if bet_type == 'range' and bet_value == '19-36' and 19 <= number <= 36:
            return 2
        if bet_type == 'dozen' and number in RouletteGame.DOZENS.get(int(bet_value), set()):
            return 3  # 2:1 + apuesta devuelta
        if bet_type == 'column' and number in RouletteGame.COLUMNS.get(int(bet_value), set()):
            return 3
        return 0

    @staticmethod
    def spin(bet: Decimal, bet_type: str, bet_value) -> Dict[str, Any]:
        """Ejecuta una tirada de ruleta con una única apuesta (usado para compatibilidad)"""

        number = RouletteGame.spin_wheel()
        is_red = number in RouletteGame.RED_NUMBERS
        multiplier = RouletteGame.evaluate_bet(number, bet_type, bet_value)
        won = multiplier > 0

        payout = GameLogic.calculate_payout(bet, multiplier) if won else Decimal('0')
        profit_loss = GameLogic.calculate_profit(payout, bet)

        return {
            'number': number,
            'color': 'red' if is_red else ('black' if number != 0 else 'green'),
            'multiplier': multiplier,
            'payout': float(payout),
            'profit_loss': float(profit_loss),
            'result': {
                'won': won,
                'bet_type': bet_type,
                'winning_number': number
            }
        }


class GoldenJetGame:
    """
    Golden Jet: juego tipo "Crash" (igual a Aviator/JetX). El multiplicador sube en tiempo real
    mientras el jet vuela, y el jugador puede retirar en cualquier momento antes de que explote.

    El punto secreto de explosión se genera con la misma fórmula estándar de la industria que
    usan Bustabit y los clones de Aviator: crash_point = (1 - margen) / (1 - U), con U uniforme
    en [0,1). Esto garantiza matemáticamente que el RTP sea EXACTO (1 - HOUSE_EDGE) sin importar
    en qué multiplicador decida retirarse el jugador (estrategia fija o en tiempo real) — la casa
    nunca corre riesgo de descontrol, igual que en Panda Mines.

    El punto de explosión nunca se revela al cliente hasta que ocurre: el servidor guarda la hora
    de inicio y el punto de explosión en sesión; el cliente solo anima un multiplicador creciente
    en base al tiempo transcurrido, y el servidor valida cualquier intento de retiro comparando
    el tiempo real transcurrido contra el punto de explosión secreto.
    """

    HOUSE_EDGE = Decimal('0.04')  # 4% de margen -> 96% RTP, estándar de la industria
    GROWTH_RATE = 0.16  # velocidad de crecimiento exponencial del multiplicador (por segundo)
    MAX_MULTIPLIER = Decimal('1000.00')  # techo de seguridad

    @staticmethod
    def generate_crash_point() -> Decimal:
        """Genera el punto secreto de explosión (nunca se revela al cliente hasta que ocurre)"""
        u = max(random.random(), 1e-9)
        raw = (Decimal('1') - GoldenJetGame.HOUSE_EDGE) / Decimal(str(1 - u))
        crash_point = max(Decimal('1.00'), min(raw, GoldenJetGame.MAX_MULTIPLIER))
        return crash_point.quantize(Decimal('0.01'))

    @staticmethod
    def multiplier_at(elapsed_seconds: float) -> Decimal:
        """Multiplicador exacto en un instante dado, según la curva de crecimiento del vuelo"""
        value = math.exp(GoldenJetGame.GROWTH_RATE * max(elapsed_seconds, 0))
        return Decimal(str(value)).quantize(Decimal('0.0001'))

    @staticmethod
    def crash_time_seconds(crash_point: Decimal) -> float:
        """Tiempo (segundos) en el que el jet llega exactamente al punto de explosión"""
        return math.log(float(crash_point)) / GoldenJetGame.GROWTH_RATE


class CyberRoulettGame:
    """Lógica de Cyber Roulette (versión futurista de ruleta)"""

    @staticmethod
    def spin(bet: Decimal) -> Dict[str, Any]:
        """Versión digital/futurista de ruleta"""

        # 8 sectores en una rueda futurista
        sectors = ['CYBER', 'NEON', 'PLASMA', 'QUANTUM', 'NEXUS', 'VOID', 'PULSE', 'FLUX']
        winning_sector = random.choice(sectors)

        # Multiplicador basado en rareza del sector
        sector_multipliers = {
            'CYBER': 1.5,
            'NEON': 2.0,
            'PLASMA': 2.5,
            'QUANTUM': 3.0,
            'NEXUS': 4.0,
            'VOID': 5.0,
            'PULSE': 6.0,
            'FLUX': 8.0
        }

        multiplier = sector_multipliers.get(winning_sector, 1)
        payout = GameLogic.calculate_payout(bet, multiplier)
        profit_loss = GameLogic.calculate_profit(payout, bet)

        return {
            'sector': winning_sector,
            'multiplier': multiplier,
            'payout': float(payout),
            'profit_loss': float(profit_loss),
            'result': {
                'won': True,
                'sector_hit': winning_sector,
                'power_level': multiplier
            }
        }


class PersonajesGame:
    """Lógica del juego Personajes (aventura con personajes)"""

    CHARACTERS = {
        'wizard': {'hp': 100, 'multiplier': 3.0, 'emoji': '🧙'},
        'knight': {'hp': 150, 'multiplier': 2.0, 'emoji': '⚔️'},
        'archer': {'hp': 80, 'multiplier': 2.5, 'emoji': '🏹'},
        'mage': {'hp': 60, 'multiplier': 4.0, 'emoji': '✨'},
        'rogue': {'hp': 70, 'multiplier': 3.5, 'emoji': '🗡️'},
    }

    ENEMIES = [
        {'name': 'Goblin', 'damage': 10},
        {'name': 'Orc', 'damage': 20},
        {'name': 'Dragon', 'damage': 40},
        {'name': 'Skeleton', 'damage': 15},
        {'name': 'Troll', 'damage': 30},
    ]

    @staticmethod
    def play(bet: Decimal, character: str) -> Dict[str, Any]:
        """Juega una batalla de personajes"""

        if character not in PersonajesGame.CHARACTERS:
            character = random.choice(list(PersonajesGame.CHARACTERS.keys()))

        char_data = PersonajesGame.CHARACTERS[character]
        enemy = random.choice(PersonajesGame.ENEMIES)

        # Simular batalla: cuántos turnos sobrevive
        turns_survived = 0
        hp = char_data['hp']

        while hp > 0:
            # 70% de probabilidad de ganar el turno
            if random.random() > 0.7:
                hp -= enemy['damage']
            else:
                turns_survived += 1

            if turns_survived > 10:  # Máximo 10 turnos
                break

        multiplier = char_data['multiplier'] * (1 + turns_survived * 0.5)
        payout = GameLogic.calculate_payout(bet, multiplier)
        profit_loss = GameLogic.calculate_profit(payout, bet)

        return {
            'character': character,
            'enemy': enemy['name'],
            'turns_survived': turns_survived,
            'multiplier': round(multiplier, 2),
            'payout': float(payout),
            'profit_loss': float(profit_loss),
            'result': {
                'won': turns_survived > 0,
                'character_used': character,
                'enemy_defeated': enemy['name']
            }
        }


# Factory para obtener la lógica correcta
GAME_FACTORIES = {
    'slots': SlotsGame.spin,
    'farm_fest': FarmFestGame.spin,
    'panda_mines': PandaMinesGame.reveal_cell,
    'duck_rush': DuckRushGame.shoot,
    'roulette': RouletteGame.spin,
    'golden_jet': GoldenJetGame.generate_crash_point,
    'cyber_rolett': CyberRoulettGame.spin,
    'personajes': PersonajesGame.play,
    'dragon_fruit': DragonFruitGame.spin,
    'totem_falls': TotemFallsGame.spin,
    'frozen_age': FrozenAgeGame.spin,
}
