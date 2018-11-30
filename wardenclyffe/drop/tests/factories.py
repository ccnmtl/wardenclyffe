from __future__ import unicode_literals

import factory
from ..models import DropBucket
from wardenclyffe.main.tests.factories import CollectionFactory, UserFactory


class DropBucketFactory(factory.DjangoModelFactory):
    class Meta:
        model = DropBucket

    name = "test drop bucket"
    description = "test dropbucket description"
    bucket_id = "test-bucket-id"
    collection = factory.SubFactory(CollectionFactory)
    user = factory.SubFactory(UserFactory)
