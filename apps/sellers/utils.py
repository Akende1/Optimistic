from typing import Any, Optional
from .models import Seller

def get_user_seller(user: Any) -> Optional[Seller]:
    """
    Helper to retrieve the Seller instance associated with a User.
    Used during product creation to ensure products are linked to the correct seller profile.
    """
    if not user or user.is_anonymous:
        return None
        
    try:
        return getattr(user, 'seller', None)
    except Exception:
        return None