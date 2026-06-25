"""
Common Mixins - Reusable logic for serializers and views.
"""

from typing import Any, cast


class ImageURLMixin:
    """
    Mixin to provide absolute URLs for image fields in serializers.
    Ensures images are accessible via full URLs in the frontend.
    """
    def get_image_url(self, image_field):
        """
        Helper to convert an ImageField to an absolute URL using the request context.
        """
        if not image_field:
            return None
            
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(image_field.url)
        return image_field.url


class SchemaDriftMixin:
    """
    Handles dynamic attributes stored in JSONField by flattening them 
    into the serialized output. Essential for marketplace products with 
    varied specifications (e.g., RAM for electronics vs. Size for fashion).
    """
    def to_representation(self, instance):
        representation = cast(Any, super()).to_representation(instance)
        # If the instance has an 'attributes' JSONField, flatten it into the root
        attributes = getattr(instance, 'attributes', {})
        if isinstance(attributes, dict):
            for key, value in attributes.items():
                # Safeguard: Don't overwrite hardcoded model fields
                if key not in representation:
                    representation[key] = value
        return representation

    def check_field_available(self, model, field_name: str) -> bool:
        """Check if a field exists on a model class or instance."""
        return hasattr(model, field_name)

    def get_safe_field(self, instance: Any, field_name: str, default: Any = None) -> Any:
        """Safely retrieve an attribute from an instance, falling back to a default."""
        return getattr(instance, field_name, default)