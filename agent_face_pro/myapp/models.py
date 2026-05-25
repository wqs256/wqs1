from django.db import models


class UserSchedule(models.Model):
    id = models.AutoField(primary_key=True)
    user_phone = models.CharField(max_length=20, verbose_name='用户手机号')
    title = models.CharField(max_length=200, verbose_name='日程标题')
    content = models.TextField(blank=True, default='', verbose_name='日程内容')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    reminder_type = models.CharField(max_length=20, default='message', verbose_name='提醒方式')
    is_reminded = models.BooleanField(default=False, verbose_name='是否已提醒')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'user_schedule'
        verbose_name = '用户日程'
        verbose_name_plural = verbose_name


class UserExpense(models.Model):
    id = models.AutoField(primary_key=True)
    user_phone = models.CharField(max_length=20, verbose_name='用户手机号')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='金额')
    category = models.CharField(max_length=50, default='其他', verbose_name='分类')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    expense_date = models.DateField(verbose_name='消费日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'user_expense'
        verbose_name = '用户消费记录'
        verbose_name_plural = verbose_name


class TranslationRecord(models.Model):
    id = models.AutoField(primary_key=True)
    user_phone = models.CharField(max_length=20, verbose_name='用户手机号')
    source_text = models.TextField(verbose_name='原文')
    translated_text = models.TextField(verbose_name='译文')
    source_lang = models.CharField(max_length=10, default='zh', verbose_name='源语言')
    target_lang = models.CharField(max_length=10, default='en', verbose_name='目标语言')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'translation_record'
        verbose_name = '翻译记录'
        verbose_name_plural = verbose_name
