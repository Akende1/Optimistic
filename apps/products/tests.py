from types import SimpleNamespace

from django.test import SimpleTestCase

from .category_specs import get_category_attribute_schema, normalize_and_validate_attributes


class CategorySpecificationTests(SimpleTestCase):
    def test_gadget_category_uses_detailed_electronics_schema(self):
        category = SimpleNamespace(slug='gadgets', name='Gadgets and Phones')
        keys = {field['key'] for field in get_category_attribute_schema(category)}
        self.assertTrue({'device_type', 'processor', 'ram_gb', 'battery_capacity_mah', 'connectivity'} <= keys)

    def test_required_specs_and_types_are_validated(self):
        category = SimpleNamespace(slug='electronics', name='Electronics')
        normalized, errors = normalize_and_validate_attributes(category, {
            'device_type': 'Phone', 'brand': 'Example', 'model': 'X1',
            'condition': 'New', 'ram_gb': '8', 'screen_size_inches': '6.7',
        })
        self.assertEqual(errors, {})
        self.assertEqual(normalized['ram_gb'], 8)
        self.assertEqual(normalized['screen_size_inches'], 6.7)

        _, errors = normalize_and_validate_attributes(category, {'ram_gb': 'zero'})
        self.assertIn('device_type', errors)
        self.assertIn('brand', errors)
        self.assertIn('ram_gb', errors)

    def test_unknown_attributes_are_not_persisted(self):
        category = SimpleNamespace(slug='electronics', name='Electronics')
        normalized, errors = normalize_and_validate_attributes(category, {
            'device_type': 'Laptop', 'brand': 'Example', 'model': 'Pro',
            'condition': 'Used', 'untrusted_field': 'ignored',
        })
        self.assertEqual(errors, {})
        self.assertNotIn('untrusted_field', normalized)
