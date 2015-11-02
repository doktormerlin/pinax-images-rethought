import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from imagekit.models import ImageSpecField
from imagekit.processors import SmartResize


def image_upload_to(instance, filename):
    instance.original_filename = filename
    uid = str(uuid.uuid4())
    ext = filename.split(".")[-1].lower()
    return "pinax-images/{}/{}.{}".format(instance.pk, uid, ext)


class ImageSet(models.Model):
    primary_image = models.ForeignKey("Image", null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="image_sets")
    created_at = models.DateTimeField(default=timezone.now)

    def image_data(self):
        return {
            "pk": self.pk,
            "primaryImage": self.primary_image.data() if self.primary_image else {},
            "images": [image.data() for image in self.images.all()],
            "upload_url": reverse("images_set_upload", args=[self.pk])
        }


class Image(models.Model):
    image_set = models.ForeignKey(ImageSet, related_name="images")
    image = models.ImageField(upload_to=image_upload_to)
    original_filename = models.CharField(max_length=500)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="images")
    created_at = models.DateTimeField(default=timezone.now)

    list_thumbnail = ImageSpecField(source="image", processors=[SmartResize(35, 35)], format="JPEG", options={"quality": 75})
    small_thumbnail = ImageSpecField(source="image", processors=[SmartResize(100, 100)], format="JPEG", options={"quality": 75})
    medium_thumbnail = ImageSpecField(source="image", processors=[SmartResize(400, 400)], format="JPEG", options={"quality": 75})

    def __unicode__(self):
        return self.original_filename

    def toggle_primary(self):
        if self.image_set.primary_image == self:
            self.image_set.primary_image = None
        else:
            self.image_set.primary_image = self
        self.image_set.save()

    def data(self):
        return {
            "pk": self.pk,
            "is_primary": self == self.image_set.primary_image,
            "medium_thumbnail": self.medium_thumbnail.url,
            "small_thumbnail": self.small_thumbnail.url,
            "list_thumbnail": self.list_thumbnail.url,
            "filename": self.original_filename,
            "delete_url": reverse("images_delete", args=[self.pk]),
            "make_primary_url": reverse("images_make_primary", args=[self.pk])
        }