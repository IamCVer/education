# app/models/qa_history_model.py
"""
定义问答历史记录相关的数据库模型 (Tortoise-ORM)。
"""
from tortoise import fields
from tortoise.models import Model


class QAHistory(Model):
    """
    问答历史记录表模型。
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="qa_history")
    question_text = fields.TextField()
    answer_text = fields.TextField()
    sources = fields.JSONField() # 用于存储答案的来源信息
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "qa_history"

    def __str__(self):
        return f"Q: {self.question_text[:30]}..."