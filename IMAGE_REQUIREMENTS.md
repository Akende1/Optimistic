# 📸 Profile Picture Requirements

**Optimistic Marketplace - Image Guidelines**

---

## 👥 Buyer Profile Pictures

### Status: **OPTIONAL** ⚪

**Where Used:**
- Profile page header
- Product review display (next to review text)
- Order history (small avatar)
- Wishlist items (micro avatar)
- Account dropdown menu

**Specifications:**
- **Minimum Size:** 200x200px
- **Recommended:** 400x400px
- **Aspect Ratio:** 1:1 (square)
- **Format:** PNG, JPG/JPEG
- **Max File Size:** 2 MB
- **Content:** Clear headshot or personal logo

**Default Behavior:**
If buyer doesn't upload a profile picture, show:
- Generic avatar icon (material-icons: `account_circle`)
- User's initials in colored circle (e.g., "JB" for John Banda)
- Gravatar (if email matches)

**Implementation:**
```python
# apps/accounts/models.py
class User(AbstractUser):
    profile_picture = models.ImageField(
        upload_to='users/profiles/',
        null=True,
        blank=True,  # NOT REQUIRED
        help_text='Profile picture for user account'
    )
```

**Frontend Display:**
```javascript
// Show profile picture or fallback to initials
const profileImageUrl = user.profile_picture || generateInitialsAvatar(user.first_name, user.last_name);

function generateInitialsAvatar(firstName, lastName) {
    const initials = (firstName[0] + lastName[0]).toUpperCase();
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'];
    const color = colors[initials.charCodeAt(0) % colors.length];
    
    // Return data URL with colored circle + white text
    return `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <circle cx="50" cy="50" r="50" fill="${color}"/>
        <text x="50" y="50" font-size="40" fill="white" text-anchor="middle" dy=".35em">${initials}</text>
    </svg>`;
}
```

---

## 🏪 Seller Store Images

### Status: **REQUIRED** ✅

Sellers **MUST** upload both images before KYC submission can be completed.

### 1. Store Profile Image (Logo/Avatar)

**Where Used:**
- Product listing cards (seller badge)
- Store page header (circle avatar)
- Order confirmation (seller info)
- Search results (next to store name)
- Featured sellers section
- Admin seller list

**Specifications:**
- **Minimum Size:** 400x400px
- **Recommended:** 800x800px
- **Aspect Ratio:** 1:1 (square)
- **Format:** PNG (preferred for transparency), JPG
- **Max File Size:** 2 MB
- **Content:** 
  - Store logo (if business has one)
  - Product photo (if single-product store)
  - Professional headshot (if personal brand)
  - **NO:** Generic icons, blurry images, text-only

**Implementation:**
```python
# apps/sellers/models.py
class Seller(models.Model):
    profile_image = models.ImageField(
        upload_to='sellers/profiles/',
        blank=True,  # Allows gradual data collection
        null=True,
        help_text="Store/seller profile picture"
    )
```

**Validation (Admin Review):**
Admin should reject seller verification if:
- ❌ Profile image is missing
- ❌ Image is blurry or low quality
- ❌ Image contains inappropriate content
- ❌ Image is a generic placeholder icon

### 2. Store Banner Image (Cover Photo)

**Where Used:**
- Store page header (full-width banner)
- Featured sellers carousel
- Seller directory cards
- Promotional emails/notifications

**Specifications:**
- **Minimum Size:** 1200x300px
- **Recommended:** 1920x480px
- **Aspect Ratio:** 4:1 or 16:4 (widescreen)
- **Format:** PNG, JPG
- **Max File Size:** 3 MB
- **Content:**
  - Products showcase (multiple products arranged)
  - Store interior/exterior photo
  - Brand imagery with text overlay
  - Seasonal promotions banner
  - **NO:** Stretched images, pixelated graphics, inappropriate content

**Implementation:**
```python
# apps/sellers/models.py
class Seller(models.Model):
    banner_image = models.ImageField(
        upload_to='sellers/banners/',
        blank=True,  # Allows gradual data collection
        null=True,
        help_text="Store banner/cover image"
    )
```

**Validation (Admin Review):**
Admin should reject seller verification if:
- ❌ Banner image is missing
- ❌ Image is distorted or stretched
- ❌ Text is unreadable or too small
- ❌ Image violates content policy

---

## 🎨 Image Upload UI/UX

### Buyer Registration Page

```html
<!-- frontend/register.html -->
<div class="optional-section">
    <h3>Profile Picture (Optional)</h3>
    <p class="help-text">You can add this later in your profile settings</p>
    
    <div class="image-upload-widget">
        <input type="file" id="profile_picture" name="profile_picture" accept="image/png,image/jpeg" hidden>
        <label for="profile_picture" class="upload-button">
            <div class="preview-circle" id="preview-circle">
                <i class="material-icons">add_a_photo</i>
                <span>Upload Photo</span>
            </div>
        </label>
    </div>
    
    <button type="button" class="skip-button">Skip for now</button>
</div>

<script>
document.getElementById('profile_picture').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            const preview = document.getElementById('preview-circle');
            preview.style.backgroundImage = `url(${event.target.result})`;
            preview.innerHTML = '<i class="material-icons edit-icon">edit</i>';
        };
        reader.readAsDataURL(file);
    }
});
</script>
```

### Seller Registration Page

```html
<!-- frontend/seller-register.html (Tab 2: Store Setup) -->
<div class="required-images-section">
    <h3>Store Images <span class="required-badge">Required</span></h3>
    <p class="help-text">High-quality images help buyers trust your store</p>
    
    <!-- Profile Image -->
    <div class="image-upload-row">
        <label class="required">Store Profile Image (Logo)</label>
        <p class="specs">Square image, 400x400px minimum, PNG or JPG</p>
        
        <div class="image-upload-widget square">
            <input type="file" id="profile_image" name="profile_image" accept="image/*" required hidden>
            <label for="profile_image" class="upload-button">
                <div class="preview-square" id="profile-preview">
                    <i class="material-icons">store</i>
                    <span>Upload Logo</span>
                </div>
            </label>
        </div>
        <div class="upload-status" id="profile-status"></div>
    </div>
    
    <!-- Banner Image -->
    <div class="image-upload-row">
        <label class="required">Store Banner Image (Cover Photo)</label>
        <p class="specs">Widescreen image, 1200x300px minimum, PNG or JPG</p>
        
        <div class="image-upload-widget banner">
            <input type="file" id="banner_image" name="banner_image" accept="image/*" required hidden>
            <label for="banner_image" class="upload-button">
                <div class="preview-banner" id="banner-preview">
                    <i class="material-icons">image</i>
                    <span>Upload Banner</span>
                </div>
            </label>
        </div>
        <div class="upload-status" id="banner-status"></div>
    </div>
</div>

<script>
// Profile image preview
document.getElementById('profile_image').addEventListener('change', function(e) {
    handleImageUpload(e, 'profile-preview', 'profile-status', 'square');
});

// Banner image preview
document.getElementById('banner_image').addEventListener('change', function(e) {
    handleImageUpload(e, 'banner-preview', 'banner-status', 'banner');
});

function handleImageUpload(event, previewId, statusId, type) {
    const file = event.target.files[0];
    const statusElement = document.getElementById(statusId);
    
    // Validate file size
    if (file.size > 3 * 1024 * 1024) {  // 3MB
        statusElement.innerHTML = '❌ File too large (max 3MB)';
        statusElement.className = 'upload-status error';
        return;
    }
    
    // Validate dimensions
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            const preview = document.getElementById(previewId);
            
            if (type === 'square' && (img.width < 400 || img.height < 400)) {
                statusElement.innerHTML = '❌ Image too small (minimum 400x400px)';
                statusElement.className = 'upload-status error';
                return;
            }
            
            if (type === 'banner' && (img.width < 1200 || img.height < 300)) {
                statusElement.innerHTML = '❌ Image too small (minimum 1200x300px)';
                statusElement.className = 'upload-status error';
                return;
            }
            
            // Show preview
            preview.style.backgroundImage = `url(${e.target.result})`;
            preview.style.backgroundSize = 'cover';
            preview.innerHTML = '<i class="material-icons edit-icon">check_circle</i>';
            
            statusElement.innerHTML = '✅ Image ready';
            statusElement.className = 'upload-status success';
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}
</script>
```

---

## 🖼️ Image Processing Pipeline

### Backend (Django)

**Install Pillow for image processing:**
```powershell
pip install Pillow
```

**Create image validation & optimization:**
```python
# apps/common/validators.py
from django.core.exceptions import ValidationError
from PIL import Image

def validate_image_dimensions(image, min_width, min_height):
    """Validate image meets minimum dimensions."""
    img = Image.open(image)
    width, height = img.size
    
    if width < min_width or height < min_height:
        raise ValidationError(
            f'Image must be at least {min_width}x{min_height}px. '
            f'Uploaded image is {width}x{height}px.'
        )

def validate_profile_image(image):
    """Validate store profile image."""
    validate_image_dimensions(image, 400, 400)
    
def validate_banner_image(image):
    """Validate store banner image."""
    validate_image_dimensions(image, 1200, 300)

def optimize_image(image_path, max_width=2048):
    """Compress and resize image to optimize storage."""
    img = Image.open(image_path)
    
    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
    
    # Optimize and save
    img.save(image_path, optimize=True, quality=85)
```

**Apply validators to models:**
```python
# apps/sellers/models.py
from apps.common.validators import validate_profile_image, validate_banner_image

class Seller(models.Model):
    profile_image = models.ImageField(
        upload_to='sellers/profiles/',
        validators=[validate_profile_image],
        help_text="Store logo (400x400px minimum)"
    )
    
    banner_image = models.ImageField(
        upload_to='sellers/banners/',
        validators=[validate_banner_image],
        help_text="Store banner (1200x300px minimum)"
    )
```

**Post-processing signal:**
```python
# apps/sellers/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Seller
from apps.common.validators import optimize_image

@receiver(post_save, sender=Seller)
def optimize_seller_images(sender, instance, **kwargs):
    """Optimize images after upload."""
    if instance.profile_image:
        optimize_image(instance.profile_image.path)
    if instance.banner_image:
        optimize_image(instance.banner_image.path)
```

---

## 🔍 Admin Review Checklist

When reviewing seller verification, admin should check:

### Profile Image:
- ✅ Image is uploaded
- ✅ Image is clear and in focus
- ✅ Image represents the store/brand
- ✅ Image is appropriate (no offensive content)
- ✅ Image is not a generic placeholder

### Banner Image:
- ✅ Image is uploaded
- ✅ Image is high quality (not pixelated)
- ✅ Image is properly sized (not stretched)
- ✅ Text (if any) is readable
- ✅ Image is appropriate and professional

**Rejection Reasons:**
```
❌ Profile image missing
❌ Banner image missing
❌ Low quality/blurry images
❌ Generic placeholder images used
❌ Inappropriate or offensive content
❌ Images do not represent the business
```

---

## 📱 Mobile Optimization

### Responsive Image Display

```css
/* Buyer profile picture (circular) */
.user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #e0e0e0;
}

.user-avatar-large {
    width: 120px;
    height: 120px;
}

/* Seller profile image */
.seller-logo {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.seller-logo-large {
    width: 150px;
    height: 150px;
}

/* Seller banner */
.seller-banner {
    width: 100%;
    height: 200px;
    object-fit: cover;
    border-radius: 12px;
}

@media (min-width: 768px) {
    .seller-banner {
        height: 300px;
    }
}

@media (min-width: 1200px) {
    .seller-banner {
        height: 400px;
    }
}
```

---

## 🚀 Implementation Checklist

### Buyer Profile Pictures (Optional)
- [ ] Add `profile_picture` field to User model ✅ (Already done)
- [ ] Create optional upload widget in registration form
- [ ] Create "Skip for now" button
- [ ] Add edit profile picture in settings
- [ ] Implement fallback initials avatar
- [ ] Display profile picture in reviews, orders

### Seller Store Images (Required)
- [ ] Add `profile_image` and `banner_image` to Seller model ✅ (Already done)
- [ ] Create image upload widgets in seller registration
- [ ] Add image validation (dimensions, file size)
- [ ] Implement image optimization (compression)
- [ ] Show previews before upload
- [ ] Block KYC submission if images missing
- [ ] Admin review interface shows both images
- [ ] Display store images in:
  - [ ] Product listings
  - [ ] Store page
  - [ ] Search results
  - [ ] Featured sellers

### Image Storage (Production)
- [ ] Configure S3 bucket for media files
- [ ] Set up CloudFront/CDN for fast delivery
- [ ] Implement image thumbnails (multiple sizes)
- [ ] Add lazy loading for performance

---

## 📊 Success Metrics

Track these after implementation:

| Metric | Target | Timeframe |
|--------|--------|-----------|
| Buyers with profile pictures | >35% | 1 month |
| Sellers with complete image profiles | 100% | Always (required) |
| Image upload success rate | >95% | Ongoing |
| Average image load time | <1 second | Ongoing |
| Image rejection rate (admin) | <5% | Ongoing |

---

## 🎯 Quick Summary

✅ **Buyer Profile Pictures**: Optional, fallback to initials  
✅ **Seller Profile Images**: Required, enforced at KYC  
✅ **Seller Banner Images**: Required, enforced at KYC  
✅ **Models Updated**: All fields already in database schema  
✅ **Next Steps**: Build upload UI + admin review interface

---

**The trust starts with a face (or logo). Make it count! 📸**

---

**Last Updated**: February 27, 2026  
**Status**: Ready for Implementation
