from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Book
from .permissions import AuthorPermission, BookPermission
from .serializers import (
    AuthorSerializer,
    BookSerializer,
    EpisodeSerializer,
    GameSerializer,
    GenreSerializer,
    MovieSerializer,
    ShowSerializer,
)


class BookAPIView(RetrieveAPIView):
    queryset = Book.objects.all()
    authentication_classes = (SessionAuthentication,)
    permission_classes = (BookPermission,)
    serializer_class = BookSerializer


class AuthorAPIView(RetrieveAPIView):
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    authentication_classes = ()
    permission_classes = (AuthorPermission,)
    serializer_class = AuthorSerializer


class PublisherAPIView(RetrieveAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = AuthorSerializer


class GenreAPIView(ListAPIView):
    serializer_class = GenreSerializer


class MovieViewSet(ModelViewSet):
    serializer_class = MovieSerializer


class ShowAPIView(RetrieveAPIView):
    serializer_class = ShowSerializer


class EpisodeAPIView(RetrieveAPIView):
    serializer_class = EpisodeSerializer

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {
            "uuid": self.kwargs["episode_uuid"],
            "show": self.kwargs["show_pk"],
        }
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj


class ComicAPIView(RetrieveAPIView):
    def get_serializer_class(self):
        raise NotImplementedError


class GameAPIView(RetrieveAPIView):
    serializer_class = GameSerializer


class GenericAPIView(APIView):
    pass


class ViewWithoutLookupField(RetrieveAPIView):
    lookup_field = None


class ViewWithLookupKwarg(RetrieveAPIView):
    lookup_field = "pk"
    lookup_url_kwarg = "id"
