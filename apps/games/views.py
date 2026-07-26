import time
import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from apps.games.models import GameResult, SlotsJackpot

User = get_user_model()
from apps.games.game_logic import (
    SlotsGame,
    FarmFestGame,
    PandaMinesGame,
    DuckRushGame,
    RouletteGame,
    GoldenJetGame,
    CyberRoulettGame,
    PersonajesGame,
    DragonFruitGame,
    TotemFallsGame,
    GoldenSlingRushGame,
    FrozenAgeGame
)
from apps.payments.models import Transaction
from apps.core.websocket_utils import WebSocketBroadcaster


class GameViewSet(viewsets.ViewSet):
    """Vistas para juegos con soporte WebSocket"""
    permission_classes = [IsAuthenticated]

    FREE_SPINS_SESSION_KEY = 'slots_free_spins_remaining'
    FREE_SPINS_BET_SESSION_KEY = 'slots_free_spins_bet'

    @action(detail=False, methods=['post'])
    def play_slots(self, request):
        """Jugar Slots"""
        user = request.user
        free_spins_remaining = request.session.get(self.FREE_SPINS_SESSION_KEY, 0)
        is_free_spin = free_spins_remaining > 0

        if is_free_spin:
            bet_amount = Decimal(str(request.session.get(self.FREE_SPINS_BET_SESSION_KEY, '1.0')))
        else:
            bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))

            if bet_amount <= 0:
                return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

            if user.balance + user.bonus_balance < bet_amount:
                return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if is_free_spin:
                free_spins_remaining -= 1
            else:
                if not user.place_bet(bet_amount):
                    return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
                user.record_wager(bet_amount)

            jackpot = SlotsJackpot.get_locked()
            result = SlotsGame.spin(bet_amount, jackpot.amount)
            jackpot.amount = Decimal(str(result['jackpot_pool']))
            jackpot.save()

            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))

            if payout > 0:
                user.credit_win(payout)

            free_spins_awarded = result.get('free_spins_awarded', 0)
            if free_spins_awarded > 0:
                free_spins_remaining += free_spins_awarded
                request.session[self.FREE_SPINS_BET_SESSION_KEY] = str(bet_amount)
            request.session[self.FREE_SPINS_SESSION_KEY] = free_spins_remaining

            GameResult.objects.create(
                user=user,
                game_type='slots',
                bet_amount=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                result=result
            )

            Transaction.objects.create(
                user=user,
                transaction_id=f"GAME-SLOTS-{user.id}-{timezone.now().timestamp()}",
                transaction_type='bet',
                amount=0.0 if is_free_spin else float(bet_amount),
                status='completed',
                metadata=result
            )

            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id,
                game_type='slots',
                bet=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                new_balance=user.balance
            )

        return Response({
            'status': 'win' if payout > 0 else 'loss',
            'game_result': result,
            'balance': float(user.balance),
            'is_free_spin': is_free_spin,
            'free_spins_awarded': free_spins_awarded,
            'free_spins_remaining': free_spins_remaining
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def slots_jackpot(self, request):
        """Consulta el pool actual del jackpot y los giros gratis pendientes de Neon Slots"""
        jackpot = SlotsJackpot.objects.filter(pk=1).first()
        amount = jackpot.amount if jackpot else SlotsJackpot.BASE_AMOUNT
        free_spins_remaining = request.session.get(self.FREE_SPINS_SESSION_KEY, 0)
        return Response({'jackpot_pool': float(amount), 'free_spins_remaining': free_spins_remaining})

    FARM_FREE_SPINS_SESSION_KEY = 'farm_fest_free_spins_remaining'
    FARM_FREE_SPINS_BET_SESSION_KEY = 'farm_fest_free_spins_bet'

    @action(detail=False, methods=['post'])
    def play_farm_fest(self, request):
        """Jugar Farm Fest Slots"""
        user = request.user
        free_spins_remaining = request.session.get(self.FARM_FREE_SPINS_SESSION_KEY, 0)
        is_free_spin = free_spins_remaining > 0

        if is_free_spin:
            bet_amount = Decimal(str(request.session.get(self.FARM_FREE_SPINS_BET_SESSION_KEY, '1.0')))
        else:
            bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))

            if bet_amount <= 0:
                return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

            if user.balance + user.bonus_balance < bet_amount:
                return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if is_free_spin:
                free_spins_remaining -= 1
            else:
                if not user.place_bet(bet_amount):
                    return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
                user.record_wager(bet_amount)

            result = FarmFestGame.spin(bet_amount)

            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))

            if payout > 0:
                user.credit_win(payout)

            free_spins_awarded = result.get('free_spins_awarded', 0)
            if free_spins_awarded > 0:
                free_spins_remaining += free_spins_awarded
                request.session[self.FARM_FREE_SPINS_BET_SESSION_KEY] = str(bet_amount)
            request.session[self.FARM_FREE_SPINS_SESSION_KEY] = free_spins_remaining

            GameResult.objects.create(
                user=user,
                game_type='farm_fest',
                bet_amount=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                result=result
            )

            Transaction.objects.create(
                user=user,
                transaction_id=f"GAME-FARMFEST-{user.id}-{timezone.now().timestamp()}",
                transaction_type='bet',
                amount=0.0 if is_free_spin else float(bet_amount),
                status='completed',
                metadata=result
            )

            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id,
                game_type='farm_fest',
                bet=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                new_balance=user.balance
            )

        return Response({
            'status': 'win' if payout > 0 else 'loss',
            'game_result': result,
            'balance': float(user.balance),
            'is_free_spin': is_free_spin,
            'free_spins_awarded': free_spins_awarded,
            'free_spins_remaining': free_spins_remaining
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def farm_fest_free_spins(self, request):
        """Consulta los giros gratis pendientes de Farm Fest Slots"""
        free_spins_remaining = request.session.get(self.FARM_FREE_SPINS_SESSION_KEY, 0)
        return Response({'free_spins_remaining': free_spins_remaining})

    @action(detail=False, methods=['post'])
    def play_panda_mines(self, request):
        """Inicia una partida de Panda Mines o revela una celda de la partida activa"""
        user = request.user
        grid_id = request.data.get('grid_id')

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)

            if not grid_id:
                bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))
                mine_count = int(request.data.get('mine_count', 5))

                if bet_amount <= 0:
                    return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)
                if not (PandaMinesGame.MIN_MINES <= mine_count <= PandaMinesGame.MAX_MINES):
                    return Response({'error': 'Cantidad de minas inválida'}, status=status.HTTP_400_BAD_REQUEST)

                if not user.place_bet(bet_amount):
                    return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
                user.record_wager(bet_amount)

                grid = PandaMinesGame.generate_grid(mine_count)
                grid['bet_amount'] = str(bet_amount)

                new_grid_id = uuid.uuid4().hex
                request.session[f'panda_mines_{new_grid_id}'] = grid

                next_multiplier = PandaMinesGame.calculate_multiplier(grid['mine_count'], 1, False)

                return Response({
                    'grid_id': new_grid_id,
                    'mine_count': grid['mine_count'],
                    'total_cells': PandaMinesGame.TOTAL_CELLS,
                    'next_multiplier': float(round(next_multiplier, 4)),
                    'balance': float(user.balance),
                    'action': 'grid_generated'
                }, status=status.HTTP_200_OK)

            session_key = f'panda_mines_{grid_id}'
            grid = request.session.get(session_key)
            if not grid:
                return Response({'error': 'No hay una partida activa con ese ID'}, status=status.HTTP_400_BAD_REQUEST)

            cell_id = int(request.data.get('cell_id'))
            bet_amount = Decimal(grid['bet_amount'])
            result = PandaMinesGame.reveal_cell(grid, cell_id)

            if result.get('hit_mine'):
                request.session.pop(session_key, None)
                profit_loss = -bet_amount
                GameResult.objects.create(
                    user=user, game_type='panda_mines', bet_amount=bet_amount,
                    payout=Decimal('0'), profit_loss=profit_loss, result=result
                )
                WebSocketBroadcaster.broadcast_game_result(
                    user_id=user.id, game_type='panda_mines', bet=bet_amount,
                    payout=Decimal('0'), profit_loss=profit_loss, new_balance=user.balance
                )
                return Response({
                    'status': 'loss',
                    'game_result': result,
                    'balance': float(user.balance)
                }, status=status.HTTP_200_OK)

            if result.get('auto_cashout'):
                cashout_result = PandaMinesGame.cash_out(grid, bet_amount)
                request.session.pop(session_key, None)
                payout = Decimal(str(cashout_result['payout']))
                profit_loss = Decimal(str(cashout_result['profit_loss']))
                user.credit_win(payout)

                combined_result = {**result, **cashout_result}
                GameResult.objects.create(
                    user=user, game_type='panda_mines', bet_amount=bet_amount,
                    payout=payout, profit_loss=profit_loss, result=combined_result
                )
                WebSocketBroadcaster.broadcast_game_result(
                    user_id=user.id, game_type='panda_mines', bet=bet_amount,
                    payout=payout, profit_loss=profit_loss, new_balance=user.balance
                )
                return Response({
                    'status': 'win',
                    'game_result': combined_result,
                    'balance': float(user.balance)
                }, status=status.HTTP_200_OK)

            request.session[session_key] = grid
            return Response({
                'status': 'playing',
                'game_result': result,
                'balance': float(user.balance)
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def cashout_panda_mines(self, request):
        """Cobra la partida activa de Panda Mines al multiplicador actual"""
        user = request.user
        grid_id = request.data.get('grid_id')
        session_key = f'panda_mines_{grid_id}'
        grid = request.session.get(session_key)

        if not grid:
            return Response({'error': 'No hay una partida activa con ese ID'}, status=status.HTTP_400_BAD_REQUEST)
        if not grid['revealed']:
            return Response({'error': 'Revela al menos una celda antes de retirar'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            bet_amount = Decimal(grid['bet_amount'])
            result = PandaMinesGame.cash_out(grid, bet_amount)
            request.session.pop(session_key, None)

            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))
            user.credit_win(payout)

            GameResult.objects.create(
                user=user, game_type='panda_mines', bet_amount=bet_amount,
                payout=payout, profit_loss=profit_loss, result=result
            )
            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id, game_type='panda_mines', bet=bet_amount,
                payout=payout, profit_loss=profit_loss, new_balance=user.balance
            )

        return Response({
            'status': 'win',
            'game_result': result,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def play_duck_rush(self, request):
        """Inicia una ronda de Duck Rush o dispara sobre la ronda activa"""
        user = request.user
        round_id = request.data.get('round_id')

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)

            if not round_id:
                bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))

                if bet_amount <= 0:
                    return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

                if not user.place_bet(bet_amount):
                    return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
                user.record_wager(bet_amount)

                round_state = DuckRushGame.start_round(bet_amount)
                new_round_id = uuid.uuid4().hex
                request.session[f'duck_rush_{new_round_id}'] = round_state

                return Response({
                    'round_id': new_round_id,
                    'shots_allowed': round_state['shots_allowed'],
                    'balance': float(user.balance),
                    'action': 'round_started'
                }, status=status.HTTP_200_OK)

            session_key = f'duck_rush_{round_id}'
            round_state = request.session.get(session_key)
            if not round_state:
                return Response({'error': 'No hay una ronda activa con ese ID'}, status=status.HTTP_400_BAD_REQUEST)

            bet_amount = Decimal(round_state['bet_amount'])
            result = DuckRushGame.shoot(round_state)

            if result.get('error'):
                return Response({'error': 'No quedan tiros disponibles'}, status=status.HTTP_400_BAD_REQUEST)

            if not result['hit']:
                request.session.pop(session_key, None)
                profit_loss = -bet_amount
                GameResult.objects.create(
                    user=user, game_type='duck_rush', bet_amount=bet_amount,
                    payout=Decimal('0'), profit_loss=profit_loss, result=result
                )
                WebSocketBroadcaster.broadcast_game_result(
                    user_id=user.id, game_type='duck_rush', bet=bet_amount,
                    payout=Decimal('0'), profit_loss=profit_loss, new_balance=user.balance
                )
                return Response({
                    'status': 'loss',
                    'game_result': result,
                    'balance': float(user.balance)
                }, status=status.HTTP_200_OK)

            request.session[session_key] = round_state
            return Response({
                'status': 'playing',
                'game_result': result,
                'balance': float(user.balance)
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def cashout_duck_rush(self, request):
        """Cobra la ronda activa de Duck Rush al multiplicador actual"""
        user = request.user
        round_id = request.data.get('round_id')
        session_key = f'duck_rush_{round_id}'
        round_state = request.session.get(session_key)

        if not round_state:
            return Response({'error': 'No hay una ronda activa con ese ID'}, status=status.HTTP_400_BAD_REQUEST)
        if round_state['hits'] <= 0:
            return Response({'error': 'Acertá al menos un pato antes de retirar'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            bet_amount = Decimal(round_state['bet_amount'])
            result = DuckRushGame.cash_out(round_state)
            request.session.pop(session_key, None)

            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))
            user.credit_win(payout)

            GameResult.objects.create(
                user=user, game_type='duck_rush', bet_amount=bet_amount,
                payout=payout, profit_loss=profit_loss, result=result
            )
            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id, game_type='duck_rush', bet=bet_amount,
                payout=payout, profit_loss=profit_loss, new_balance=user.balance
            )

        return Response({
            'status': 'win',
            'game_result': result,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def play_golden_sling_rush(self, request):
        """Inicia una ronda de Golden Sling Rush o lanza sobre la ronda activa"""
        user = request.user
        round_id = request.data.get('round_id')

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)

            if not round_id:
                bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))

                if bet_amount <= 0:
                    return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

                if not user.place_bet(bet_amount):
                    return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
                user.record_wager(bet_amount)

                round_state = GoldenSlingRushGame.start_round(bet_amount)
                new_round_id = uuid.uuid4().hex
                request.session[f'golden_sling_rush_{new_round_id}'] = round_state

                return Response({
                    'round_id': new_round_id,
                    'balance': float(user.balance),
                    'action': 'round_started'
                }, status=status.HTTP_200_OK)

            session_key = f'golden_sling_rush_{round_id}'
            round_state = request.session.get(session_key)
            if not round_state:
                return Response({'error': 'No hay una ronda activa con ese ID'}, status=status.HTTP_400_BAD_REQUEST)

            bet_amount = Decimal(round_state['bet_amount'])
            result = GoldenSlingRushGame.throw(round_state)

            if not result['hit']:
                request.session.pop(session_key, None)
                profit_loss = -bet_amount
                GameResult.objects.create(
                    user=user, game_type='golden_sling_rush', bet_amount=bet_amount,
                    payout=Decimal('0'), profit_loss=profit_loss, result=result
                )
                WebSocketBroadcaster.broadcast_game_result(
                    user_id=user.id, game_type='golden_sling_rush', bet=bet_amount,
                    payout=Decimal('0'), profit_loss=profit_loss, new_balance=user.balance
                )
                return Response({
                    'status': 'loss',
                    'game_result': result,
                    'balance': float(user.balance)
                }, status=status.HTTP_200_OK)

            request.session[session_key] = round_state
            return Response({
                'status': 'playing',
                'game_result': result,
                'balance': float(user.balance)
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def cashout_golden_sling_rush(self, request):
        """Cobra la ronda activa de Golden Sling Rush al multiplicador actual"""
        user = request.user
        round_id = request.data.get('round_id')
        session_key = f'golden_sling_rush_{round_id}'
        round_state = request.session.get(session_key)

        if not round_state:
            return Response({'error': 'No hay una ronda activa con ese ID'}, status=status.HTTP_400_BAD_REQUEST)
        if round_state['hits'] <= 0:
            return Response({'error': 'Lanzá al menos una vez antes de retirar'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            bet_amount = Decimal(round_state['bet_amount'])
            result = GoldenSlingRushGame.cash_out(round_state)
            request.session.pop(session_key, None)

            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))
            user.credit_win(payout)

            GameResult.objects.create(
                user=user, game_type='golden_sling_rush', bet_amount=bet_amount,
                payout=payout, profit_loss=profit_loss, result=result
            )
            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id, game_type='golden_sling_rush', bet=bet_amount,
                payout=payout, profit_loss=profit_loss, new_balance=user.balance
            )

        return Response({
            'status': 'win',
            'game_result': result,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def play_roulette(self, request):
        """
        Jugar Ruleta: acepta una lista de apuestas simultáneas sobre un mismo giro
        (bets: [{bet_type, bet_value, amount}, ...]), como en una mesa real.
        """
        user = request.user
        bets = request.data.get('bets')

        if not bets:
            bet_amount = request.data.get('bet_amount')
            if bet_amount is not None:
                bets = [{
                    'bet_type': request.data.get('bet_type', 'red'),
                    'bet_value': request.data.get('bet_value', 0),
                    'amount': bet_amount
                }]

        if not bets:
            return Response({'error': 'No hay apuestas colocadas'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            total_bet = sum(Decimal(str(b['amount'])) for b in bets)
        except (KeyError, TypeError, ValueError):
            return Response({'error': 'Apuestas inválidas'}, status=status.HTTP_400_BAD_REQUEST)

        if total_bet <= 0:
            return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if not user.place_bet(total_bet):
                return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
            user.record_wager(total_bet)

            number = RouletteGame.spin_wheel()
            is_red = number in RouletteGame.RED_NUMBERS
            color = 'red' if is_red else ('black' if number != 0 else 'green')

            total_payout = Decimal('0')
            bet_results = []
            for b in bets:
                amount = Decimal(str(b['amount']))
                multiplier = RouletteGame.evaluate_bet(number, b['bet_type'], b['bet_value'])
                payout = amount * multiplier if multiplier > 0 else Decimal('0')
                total_payout += payout
                bet_results.append({
                    'bet_type': b['bet_type'],
                    'bet_value': b['bet_value'],
                    'amount': float(amount),
                    'won': multiplier > 0,
                    'multiplier': multiplier,
                    'payout': float(payout)
                })

            profit_loss = total_payout - total_bet
            if total_payout > 0:
                user.credit_win(total_payout)

            result = {
                'number': number,
                'color': color,
                'bets': bet_results,
                'total_bet': float(total_bet),
                'payout': float(total_payout),
                'profit_loss': float(profit_loss),
                'result': {'won': total_payout > 0, 'winning_number': number}
            }

            GameResult.objects.create(
                user=user,
                game_type='roulette',
                bet_amount=total_bet,
                payout=total_payout,
                profit_loss=profit_loss,
                result=result
            )

            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id,
                game_type='roulette',
                bet=total_bet,
                payout=total_payout,
                profit_loss=profit_loss,
                new_balance=user.balance
            )

        return Response({
            'status': 'win' if total_payout > 0 else 'loss',
            'game_result': result,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def play_golden_jet(self, request):
        """Inicia un vuelo de Golden Jet: deduce la apuesta y genera el punto de explosión secreto"""
        user = request.user
        bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))

        if bet_amount <= 0:
            return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if not user.place_bet(bet_amount):
                return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
            user.record_wager(bet_amount)

            crash_point = GoldenJetGame.generate_crash_point()
            round_id = uuid.uuid4().hex
            request.session[f'golden_jet_{round_id}'] = {
                'bet_amount': str(bet_amount),
                'crash_point': str(crash_point),
                'start_time': time.time(),
            }

        return Response({
            'round_id': round_id,
            'growth_rate': GoldenJetGame.GROWTH_RATE,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def golden_jet_status(self, request):
        """Consulta si el vuelo ya explotó, sin revelar el punto de explosión mientras siga en curso"""
        round_id = request.data.get('round_id')
        session_key = f'golden_jet_{round_id}'
        round_data = request.session.get(session_key)
        if not round_data:
            return Response({'error': 'No hay un vuelo activo con ese ID'}, status=status.HTTP_400_BAD_REQUEST)

        crash_point = Decimal(round_data['crash_point'])
        crash_time = GoldenJetGame.crash_time_seconds(crash_point)
        elapsed = time.time() - round_data['start_time']

        if elapsed >= crash_time:
            user = request.user
            bet_amount = Decimal(round_data['bet_amount'])
            request.session.pop(session_key, None)
            result = {'crashed': True, 'final_multiplier': float(crash_point)}

            GameResult.objects.create(
                user=user, game_type='golden_jet', bet_amount=bet_amount,
                payout=Decimal('0'), profit_loss=-bet_amount, result=result
            )
            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id, game_type='golden_jet', bet=bet_amount,
                payout=Decimal('0'), profit_loss=-bet_amount, new_balance=user.balance
            )
            return Response({'crashed': True, 'final_multiplier': float(crash_point)})

        current_multiplier = GoldenJetGame.multiplier_at(elapsed)
        return Response({'crashed': False, 'current_multiplier': float(current_multiplier)})

    @action(detail=False, methods=['post'])
    def cashout_golden_jet(self, request):
        """Retira el vuelo activo al multiplicador del instante actual, si no ha explotado todavía"""
        user = request.user
        round_id = request.data.get('round_id')
        session_key = f'golden_jet_{round_id}'
        round_data = request.session.get(session_key)
        if not round_data:
            return Response({'error': 'No hay un vuelo activo con ese ID'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            crash_point = Decimal(round_data['crash_point'])
            bet_amount = Decimal(round_data['bet_amount'])
            crash_time = GoldenJetGame.crash_time_seconds(crash_point)
            elapsed = time.time() - round_data['start_time']
            request.session.pop(session_key, None)

            if elapsed >= crash_time:
                result = {'crashed': True, 'final_multiplier': float(crash_point)}
                GameResult.objects.create(
                    user=user, game_type='golden_jet', bet_amount=bet_amount,
                    payout=Decimal('0'), profit_loss=-bet_amount, result=result
                )
                WebSocketBroadcaster.broadcast_game_result(
                    user_id=user.id, game_type='golden_jet', bet=bet_amount,
                    payout=Decimal('0'), profit_loss=-bet_amount, new_balance=user.balance
                )
                return Response({
                    'status': 'loss', 'game_result': result, 'balance': float(user.balance)
                }, status=status.HTTP_200_OK)

            current_multiplier = GoldenJetGame.multiplier_at(elapsed)
            payout = (bet_amount * current_multiplier).quantize(Decimal('0.01'))
            profit_loss = payout - bet_amount
            user.credit_win(payout)

            result = {'crashed': False, 'final_multiplier': float(current_multiplier), 'payout': float(payout)}
            GameResult.objects.create(
                user=user, game_type='golden_jet', bet_amount=bet_amount,
                payout=payout, profit_loss=profit_loss, result=result
            )
            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id, game_type='golden_jet', bet=bet_amount,
                payout=payout, profit_loss=profit_loss, new_balance=user.balance
            )

        return Response({
            'status': 'win', 'game_result': result, 'balance': float(user.balance)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def play_cyber_rolett(self, request):
        """Jugar Cyber Rolett"""
        user = request.user
        bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))

        if bet_amount <= 0:
            return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if not user.place_bet(bet_amount):
                return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
            user.record_wager(bet_amount)

            result = CyberRoulettGame.spin(bet_amount)
            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))

            user.credit_win(payout)

            GameResult.objects.create(
                user=user,
                game_type='cyber_rolett',
                bet_amount=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                result=result
            )

            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id,
                game_type='cyber_rolett',
                bet=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                new_balance=user.balance
            )

        return Response({
            'status': 'win',
            'game_result': result,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def play_personajes(self, request):
        """Jugar Personajes"""
        user = request.user
        bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))
        character = request.data.get('character', 'wizard')

        if bet_amount <= 0:
            return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if not user.place_bet(bet_amount):
                return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
            user.record_wager(bet_amount)

            result = PersonajesGame.play(bet_amount, character)
            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))

            if payout > 0:
                user.credit_win(payout)

            GameResult.objects.create(
                user=user,
                game_type='personajes',
                bet_amount=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                result=result
            )

            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id,
                game_type='personajes',
                bet=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                new_balance=user.balance
            )

        return Response({
            'status': 'win' if result['result']['won'] else 'loss',
            'game_result': result,
            'balance': float(user.balance)
        }, status=status.HTTP_200_OK)

    DRAGON_FREE_SPINS_SESSION_KEY = 'dragon_fruit_free_spins_remaining'
    DRAGON_FREE_SPINS_BET_SESSION_KEY = 'dragon_fruit_free_spins_bet'

    @action(detail=False, methods=['post'])
    def play_dragon_fruit(self, request):
        """Jugar Dragon Fruit Bonanza"""
        user = request.user
        free_spins_remaining = request.session.get(self.DRAGON_FREE_SPINS_SESSION_KEY, 0)
        is_free_spin = free_spins_remaining > 0

        if is_free_spin:
            bet_amount = Decimal(str(request.session.get(self.DRAGON_FREE_SPINS_BET_SESSION_KEY, '1.0')))
        else:
            bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))

            if bet_amount <= 0:
                return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if is_free_spin:
                free_spins_remaining -= 1
            else:
                if not user.place_bet(bet_amount):
                    return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
                user.record_wager(bet_amount)

            result = DragonFruitGame.spin(bet_amount, free_mode=is_free_spin)

            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))

            if payout > 0:
                user.credit_win(payout)

            free_spins_awarded = result.get('free_spins_awarded', 0)
            if free_spins_awarded > 0:
                free_spins_remaining += free_spins_awarded
                request.session[self.DRAGON_FREE_SPINS_BET_SESSION_KEY] = str(bet_amount)
            request.session[self.DRAGON_FREE_SPINS_SESSION_KEY] = free_spins_remaining

            GameResult.objects.create(
                user=user,
                game_type='dragon_fruit',
                bet_amount=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                result=result
            )

            Transaction.objects.create(
                user=user,
                transaction_id=f"GAME-DRAGONFRUIT-{user.id}-{timezone.now().timestamp()}",
                transaction_type='bet',
                amount=0.0 if is_free_spin else float(bet_amount),
                status='completed',
                metadata=result
            )

            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id,
                game_type='dragon_fruit',
                bet=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                new_balance=user.balance
            )

        return Response({
            'status': 'win' if payout > 0 else 'loss',
            'game_result': result,
            'balance': float(user.balance),
            'is_free_spin': is_free_spin,
            'free_spins_awarded': free_spins_awarded,
            'free_spins_remaining': free_spins_remaining
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def dragon_fruit_free_spins(self, request):
        """Consulta los giros gratis pendientes de Dragon Fruit Bonanza"""
        free_spins_remaining = request.session.get(self.DRAGON_FREE_SPINS_SESSION_KEY, 0)
        return Response({'free_spins_remaining': free_spins_remaining})

    TOTEM_FREE_SPINS_SESSION_KEY = 'totem_falls_free_spins_remaining'
    TOTEM_FREE_SPINS_BET_SESSION_KEY = 'totem_falls_free_spins_bet'

    @action(detail=False, methods=['post'])
    def play_totem_falls(self, request):
        """Jugar Totem Falls Bonanza"""
        user = request.user
        free_spins_remaining = request.session.get(self.TOTEM_FREE_SPINS_SESSION_KEY, 0)
        is_free_spin = free_spins_remaining > 0

        if is_free_spin:
            bet_amount = Decimal(str(request.session.get(self.TOTEM_FREE_SPINS_BET_SESSION_KEY, '1.0')))
        else:
            bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))

            if bet_amount <= 0:
                return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if is_free_spin:
                free_spins_remaining -= 1
            else:
                if not user.place_bet(bet_amount):
                    return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
                user.record_wager(bet_amount)

            result = TotemFallsGame.spin(bet_amount)

            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))

            if payout > 0:
                user.credit_win(payout)

            free_spins_awarded = result.get('free_spins_awarded', 0)
            if free_spins_awarded > 0:
                free_spins_remaining += free_spins_awarded
                request.session[self.TOTEM_FREE_SPINS_BET_SESSION_KEY] = str(bet_amount)
            request.session[self.TOTEM_FREE_SPINS_SESSION_KEY] = free_spins_remaining

            GameResult.objects.create(
                user=user,
                game_type='totem_falls',
                bet_amount=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                result=result
            )

            Transaction.objects.create(
                user=user,
                transaction_id=f"GAME-TOTEMFALLS-{user.id}-{timezone.now().timestamp()}",
                transaction_type='bet',
                amount=0.0 if is_free_spin else float(bet_amount),
                status='completed',
                metadata=result
            )

            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id,
                game_type='totem_falls',
                bet=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                new_balance=user.balance
            )

        return Response({
            'status': 'win' if payout > 0 else 'loss',
            'game_result': result,
            'balance': float(user.balance),
            'is_free_spin': is_free_spin,
            'free_spins_awarded': free_spins_awarded,
            'free_spins_remaining': free_spins_remaining
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def totem_falls_free_spins(self, request):
        """Consulta los giros gratis pendientes de Totem Falls Bonanza"""
        free_spins_remaining = request.session.get(self.TOTEM_FREE_SPINS_SESSION_KEY, 0)
        return Response({'free_spins_remaining': free_spins_remaining})

    FROZEN_FREE_SPINS_SESSION_KEY = 'frozen_age_free_spins_remaining'
    FROZEN_FREE_SPINS_BET_SESSION_KEY = 'frozen_age_free_spins_bet'

    @action(detail=False, methods=['post'])
    def play_frozen_age(self, request):
        """Jugar Frozen Age"""
        user = request.user
        free_spins_remaining = request.session.get(self.FROZEN_FREE_SPINS_SESSION_KEY, 0)
        is_free_spin = free_spins_remaining > 0

        if is_free_spin:
            bet_amount = Decimal(str(request.session.get(self.FROZEN_FREE_SPINS_BET_SESSION_KEY, '1.0')))
        else:
            bet_amount = Decimal(str(request.data.get('bet_amount', '1.0')))

            if bet_amount <= 0:
                return Response({'error': 'Apuesta inválida'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user.pk)
            if is_free_spin:
                free_spins_remaining -= 1
            else:
                if not user.place_bet(bet_amount):
                    return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)
                user.record_wager(bet_amount)

            result = FrozenAgeGame.spin(bet_amount)

            payout = Decimal(str(result['payout']))
            profit_loss = Decimal(str(result['profit_loss']))

            if payout > 0:
                user.credit_win(payout)

            free_spins_awarded = result.get('free_spins_awarded', 0)
            if free_spins_awarded > 0:
                free_spins_remaining += free_spins_awarded
                request.session[self.FROZEN_FREE_SPINS_BET_SESSION_KEY] = str(bet_amount)
            request.session[self.FROZEN_FREE_SPINS_SESSION_KEY] = free_spins_remaining

            GameResult.objects.create(
                user=user,
                game_type='frozen_age',
                bet_amount=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                result=result
            )

            Transaction.objects.create(
                user=user,
                transaction_id=f"GAME-FROZENAGE-{user.id}-{timezone.now().timestamp()}",
                transaction_type='bet',
                amount=0.0 if is_free_spin else float(bet_amount),
                status='completed',
                metadata=result
            )

            WebSocketBroadcaster.broadcast_game_result(
                user_id=user.id,
                game_type='frozen_age',
                bet=bet_amount,
                payout=payout,
                profit_loss=profit_loss,
                new_balance=user.balance
            )

        return Response({
            'status': 'win' if payout > 0 else 'loss',
            'game_result': result,
            'balance': float(user.balance),
            'is_free_spin': is_free_spin,
            'free_spins_awarded': free_spins_awarded,
            'free_spins_remaining': free_spins_remaining
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def frozen_age_free_spins(self, request):
        """Consulta los giros gratis pendientes de Frozen Age"""
        free_spins_remaining = request.session.get(self.FROZEN_FREE_SPINS_SESSION_KEY, 0)
        return Response({'free_spins_remaining': free_spins_remaining})

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Obtener historial de juegos"""
        games = GameResult.objects.filter(user=request.user).order_by('-created_at')[:20]
        data = [
            {
                'id': g.id,
                'game': g.game_type,
                'bet': float(g.bet_amount),
                'payout': float(g.payout),
                'profit_loss': float(g.profit_loss),
                'created_at': g.created_at.isoformat()
            }
            for g in games
        ]
        return Response(data)
