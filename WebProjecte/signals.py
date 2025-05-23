from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Profile

@receiver(pre_save, sender=Profile)
def delete_old_profile_image(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = Profile.objects.get(pk=instance.pk)
    except Profile.DoesNotExist:
        return

    old_image = old_instance.profile_image
    new_image = instance.profile_image

    if old_image and old_image != new_image:
        try:
            old_image.storage.delete(old_image.name)
        except Exception:
            # Opcional: loguear error o pasar
            pass

@receiver(post_delete, sender=Profile)
def delete_profile_image_file(sender, instance, **kwargs):
    if instance.profile_image:
        try:
            instance.profile_image.storage.delete(instance.profile_image.name)
        except Exception:
            pass
