from rest_framework import serializers

from .models import Author, Book, Game, Genre, Movie, Publisher, Show


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("name",)


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ("name",)


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("title", "price")


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ("first_name", "last_name")


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("title", "price", "publisher")


class ShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Show
        fields = ("title", "price", "publisher")


class EpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Show
        fields = ("title", "show")


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ("title", "price", "publisher")
