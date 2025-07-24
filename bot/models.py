# File: reffbot/bot/models.py

from django.db import models

# Tabel: Users
class Users(models.Model):
    id = models.BigIntegerField(primary_key=True)  # Telegram ID
    fullname = models.TextField(null=True, blank=True)
    username = models.TextField(null=True, blank=True)
    ref_by = models.BigIntegerField(null=True, blank=True)
    joined_at = models.TextField(null=True, blank=True)
    bonus_balance = models.FloatField(default=0)
    total_bonus = models.FloatField(default=0)
    team_reset_at = models.TextField(null=True, blank=True)


    def __str__(self):
        return f"{self.fullname} ({self.id})"


# Tabel: Withdrawals
class Withdrawals(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    usdt = models.FloatField(default=0)
    trx = models.FloatField(default=0)
    bdt = models.FloatField(default=0)
    pkr = models.FloatField(default=0)
    idr = models.FloatField(default=0)
    date = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Withdraw #{self.id} - User {self.user_id}"


# Tabel: Referral_earnings
class ReferralEarnings(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="earnings")
    from_user_id = models.BigIntegerField()
    amount = models.FloatField()
    level = models.IntegerField()
    date = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    currency = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user_id} <- {self.from_user_id} | Level {self.level}"


# Tabel: Withdraw_requests
class WithdrawRequests(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    amount = models.FloatField()
    currency = models.TextField()
    status = models.TextField()
    card_name = models.TextField(null=True, blank=True)

    created_at = models.TextField()
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"WD Req #{self.id} - {self.currency} {self.amount}"


# Tabel: Settings
class Settings(models.Model):
    key = models.TextField(primary_key=True)
    value = models.TextField()

    def __str__(self):
        return self.key
