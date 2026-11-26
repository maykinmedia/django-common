import factory

from testapp.models import Author, Book, Episode, Genre, Movie, Publisher, Show


class GenreFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")  # pyright:ignore[reportPrivateImportUsage]

    class Meta:  # pyright:ignore[reportIncompatibleVariableOverride]
        model = Genre


class AuthorFactory(factory.django.DjangoModelFactory):
    first_name = factory.Faker("first_name")  # pyright:ignore[reportPrivateImportUsage]
    last_name = factory.Faker("last_name")  # pyright:ignore[reportPrivateImportUsage]

    class Meta:  # pyright:ignore[reportIncompatibleVariableOverride]
        model = Author


class PublisherFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")  # pyright:ignore[reportPrivateImportUsage]

    class Meta:  # pyright:ignore[reportIncompatibleVariableOverride]
        model = Publisher


class BookFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("name")  # pyright:ignore[reportPrivateImportUsage]
    price = factory.Faker("pyint")  # pyright:ignore[reportPrivateImportUsage]
    author = factory.SubFactory(AuthorFactory)  # pyright:ignore[reportPrivateImportUsage]
    publisher = factory.SubFactory(PublisherFactory)  # pyright:ignore[reportPrivateImportUsage]

    class Meta:  # pyright:ignore[reportIncompatibleVariableOverride]
        model = Book


class MovieFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("name")  # pyright:ignore[reportPrivateImportUsage]
    price = factory.Faker("pyint")  # pyright:ignore[reportPrivateImportUsage]
    publisher = factory.SubFactory(PublisherFactory)  # pyright:ignore[reportPrivateImportUsage]

    class Meta:  # pyright:ignore[reportIncompatibleVariableOverride]
        model = Movie


class ShowFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("name")  # pyright:ignore[reportPrivateImportUsage]
    price = factory.Faker("pyint")  # pyright:ignore[reportPrivateImportUsage]
    publisher = factory.SubFactory(PublisherFactory)  # pyright:ignore[reportPrivateImportUsage]

    class Meta:  # pyright:ignore[reportIncompatibleVariableOverride]
        model = Show


class EpisodeFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("name")  # pyright:ignore[reportPrivateImportUsage]
    show = factory.SubFactory(ShowFactory)  # pyright:ignore[reportPrivateImportUsage]

    class Meta:  # pyright:ignore[reportIncompatibleVariableOverride]
        model = Episode
