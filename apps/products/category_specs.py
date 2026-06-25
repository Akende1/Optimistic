from __future__ import annotations

from decimal import Decimal, InvalidOperation


CATEGORY_ATTRIBUTE_SCHEMAS = {
    'electronics': [
        {
            'key': 'device_type',
            'label': 'Device Type',
            'type': 'select',
            'required': True,
            'options': ['Laptop', 'Desktop', 'Tablet', 'Phone', 'Accessory'],
        },
        {
            'key': 'brand',
            'label': 'Brand',
            'type': 'text',
            'required': True,
        },
        {
            'key': 'model',
            'label': 'Model',
            'type': 'text',
            'required': True,
        },
        {
            'key': 'ram_gb',
            'label': 'RAM (GB)',
            'type': 'number',
            'required': False,
            'min': 1,
        },
        {
            'key': 'storage_gb',
            'label': 'Storage (GB)',
            'type': 'number',
            'required': False,
            'min': 16,
        },
        {
            'key': 'condition',
            'label': 'Condition',
            'type': 'select',
            'required': True,
            'options': ['New', 'Like New', 'Used', 'Refurbished'],
        },
        {
            'key': 'warranty_months',
            'label': 'Warranty (Months)',
            'type': 'number',
            'required': False,
            'min': 0,
        },
    ],
    'fashion': [
        {
            'key': 'gender',
            'label': 'Gender',
            'type': 'select',
            'required': True,
            'options': ['Men', 'Women', 'Unisex', 'Kids'],
        },
        {
            'key': 'size',
            'label': 'Size',
            'type': 'text',
            'required': True,
        },
        {
            'key': 'color',
            'label': 'Color',
            'type': 'text',
            'required': True,
        },
        {
            'key': 'material',
            'label': 'Material',
            'type': 'text',
            'required': False,
        },
    ],
    'food': [
        {
            'key': 'weight_or_volume',
            'label': 'Weight / Volume',
            'type': 'text',
            'required': True,
        },
        {
            'key': 'expiry_date',
            'label': 'Expiry Date',
            'type': 'date',
            'required': True,
        },
        {
            'key': 'is_perishable',
            'label': 'Perishable Item',
            'type': 'boolean',
            'required': False,
        },
        {
            'key': 'origin',
            'label': 'Origin',
            'type': 'text',
            'required': False,
        },
    ],
    'home-garden': [
        {
            'key': 'material',
            'label': 'Material',
            'type': 'text',
            'required': True,
        },
        {
            'key': 'dimensions_cm',
            'label': 'Dimensions (cm)',
            'type': 'text',
            'required': False,
        },
        {
            'key': 'color',
            'label': 'Color',
            'type': 'text',
            'required': False,
        },
    ],
}


def get_category_attribute_schema(category):
    if not category:
        return []

    slug = (getattr(category, 'slug', '') or '').lower()
    name = (getattr(category, 'name', '') or '').lower().strip()

    if slug in CATEGORY_ATTRIBUTE_SCHEMAS:
        return CATEGORY_ATTRIBUTE_SCHEMAS[slug]

    if 'home' in name or 'garden' in name:
        return CATEGORY_ATTRIBUTE_SCHEMAS.get('home-garden', [])

    return CATEGORY_ATTRIBUTE_SCHEMAS.get(name, [])


def normalize_and_validate_attributes(category, attributes):
    schema = get_category_attribute_schema(category)
    if not schema:
        return {}, {}

    data = attributes or {}
    if not isinstance(data, dict):
        return {}, {'attributes': 'Attributes must be a key/value object.'}

    normalized = {}
    errors = {}

    for field in schema:
        key = field['key']
        label = field.get('label', key)
        field_type = field.get('type', 'text')
        required = field.get('required', False)
        value = data.get(key)

        if field_type == 'boolean':
            if value in [True, 'true', 'True', 1, '1', 'yes', 'on']:
                normalized[key] = True
            else:
                normalized[key] = False
            continue

        if value is None or str(value).strip() == '':
            if required:
                errors[key] = f'{label} is required.'
            continue

        if field_type == 'number':
            try:
                parsed = Decimal(str(value))
            except (InvalidOperation, ValueError):
                errors[key] = f'{label} must be a valid number.'
                continue

            min_value = field.get('min')
            if min_value is not None and parsed < Decimal(str(min_value)):
                errors[key] = f'{label} must be at least {min_value}.'
                continue

            # Emit int where possible to keep output clean.
            normalized[key] = int(parsed) if parsed == parsed.to_integral_value() else float(parsed)
            continue

        if field_type == 'select':
            options = field.get('options', [])
            value_str = str(value).strip()
            if options and value_str not in options:
                errors[key] = f'{label} must be one of: {", ".join(options)}.'
                continue
            normalized[key] = value_str
            continue

        normalized[key] = str(value).strip()

    return normalized, errors
