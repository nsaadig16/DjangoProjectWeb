import random
import string
from django.core.files.base import ContentFile
import requests

def generate_avatar(user):

    # Random seed
    seed = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    style = "bottts" 
    
    # URL for DiceBear API
    url = f"https://api.dicebear.com/7.x/{style}/png?seed={seed}&backgroundColor=b6e3f4"
    
    try:
        # Get the avatar image
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Save the avatar to the user's profile
        if response.content:
            filename = f"avatar_{user.username}.png"
            user.profile.profile_image.save(filename, ContentFile(response.content), save=True)
            return True
        return False
    except requests.RequestException:
        return False