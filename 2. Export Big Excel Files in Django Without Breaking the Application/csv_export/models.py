from django.db import models


class Example(models.Model):
    col_a = models.CharField(max_length=255)
    col_b = models.CharField(max_length=255)
    col_c = models.CharField(max_length=255)
    col_d = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.col_a} {self.col_b} {self.col_c} {self.col_d}'


class LightweightExample(models.Model):
    name = models.CharField(max_length=50)
    value = models.PositiveIntegerField()

    def __str__(self):
        return self.name
