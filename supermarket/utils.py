import os

ALLOWED_PRODUCT_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_PRODUCT_IMAGE_CONTENT_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
}
MAX_PRODUCT_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_product_image(image_file):
    """Return (is_valid, error_message). Passes when image_file is None."""
    if not image_file:
        return True, None

    extension = os.path.splitext(image_file.name)[1].lower()
    if extension not in ALLOWED_PRODUCT_IMAGE_EXTENSIONS:
        return False, 'Only JPG, JPEG, PNG, and WEBP image formats are allowed.'

    content_type = getattr(image_file, 'content_type', '')
    if content_type and content_type not in ALLOWED_PRODUCT_IMAGE_CONTENT_TYPES:
        return False, 'Invalid image file type. Please upload a JPG, JPEG, PNG, or WEBP file.'

    if image_file.size > MAX_PRODUCT_IMAGE_SIZE:
        return False, 'Image file is too large. Maximum size is 5 MB.'

    return True, None


def remove_product_image(product):
    """Delete the product image file from storage if it exists."""
    if product.image:
        product.image.delete(save=False)
        product.image = None
