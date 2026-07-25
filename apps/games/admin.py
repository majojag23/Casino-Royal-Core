from django.contrib import admin
from .models import GameResult, GameSettings


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'game_type', 'bet_amount', 'payout', 'profit_loss', 'created_at')
    list_filter = ('game_type', 'created_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)


@admin.register(GameSettings)
class GameSettingsAdmin(admin.ModelAdmin):
    list_display = ('game_type', 'min_bet', 'max_bet', 'rtp', 'enabled')
    list_filter = ('enabled', 'game_type')
