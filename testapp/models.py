from uuid import uuid4

from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Author(models.Model):
    uuid = models.UUIDField(default=uuid4)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    title = models.CharField(max_length=255)
    price = models.IntegerField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.author}: {self.title}"


class Movie(models.Model):
    title = models.CharField(max_length=255)
    price = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.publisher}: {self.title}"


class Show(models.Model):
    title = models.CharField(max_length=255)
    price = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.publisher}: {self.title}"


class Episode(models.Model):
    title = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4)
    show = models.ForeignKey(Show, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.show.title}: {self.title}"


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Game(models.Model):
    title = models.CharField(max_length=255)
    price = models.IntegerField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.publisher}: {self.title}"
