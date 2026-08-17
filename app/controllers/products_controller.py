from flask import request

from app.extensions import db
from app.models.product import Product
from app.utils.decorators import success_response, error_response, get_current_user


def get_products():
    """
    Get all marketplace products. Supports pagination and search.
    Query params: ?page=1&per_page=20&search=tomato
    ---
    tags: [Marketplace]
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search")

    query = Product.query.filter_by(is_active=True)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response(
        {
            "items": [p.to_dict() for p in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        }
    )


def get_product_detail(product_id):
    """
    Get details of a single product.
    ---
    tags: [Marketplace]
    """
    product = Product.query.get(product_id)
    if not product:
        return error_response("Product not found", 404)
    return success_response(product.to_dict())


def get_products_by_category(name):
    """
    Get products filtered by category.
    ---
    tags: [Marketplace]
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Product.query.filter_by(category=name, is_active=True)
    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response(
        {
            "items": [p.to_dict() for p in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        }
    )


def add_product():
    """
    Add a new product to the marketplace.
    ---
    tags: [Marketplace]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    category = data.get("category")
    price = data.get("price")

    if not name or not category or price is None:
        return error_response("name, category and price are required", 400)

    product = Product(
        owner_id=user.id,
        name=name,
        description=data.get("description"),
        category=category,
        price=price,
        unit=data.get("unit", "kg"),
        quantity_available=data.get("quantity_available", 0),
        image_url=data.get("image_url"),
        location=data.get("location", user.farm_location),
    )
    db.session.add(product)
    db.session.commit()

    return success_response(product.to_dict(), message="Product added successfully", status_code=201)


def update_product(product_id):
    """
    Update a product. Only the owner or an admin may update it.
    ---
    tags: [Marketplace]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    product = Product.query.get(product_id)
    if not product:
        return error_response("Product not found", 404)

    if product.owner_id != user.id and user.role != "admin":
        return error_response("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    for field in (
        "name", "description", "category", "price", "unit",
        "quantity_available", "image_url", "location", "is_active",
    ):
        if field in data:
            setattr(product, field, data[field])

    db.session.commit()
    return success_response(product.to_dict(), message="Product updated successfully")


def delete_product(product_id):
    """
    Delete a product. Only the owner or an admin may delete it.
    ---
    tags: [Marketplace]
    """
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    product = Product.query.get(product_id)
    if not product:
        return error_response("Product not found", 404)

    if product.owner_id != user.id and user.role != "admin":
        return error_response("Forbidden", 403)

    db.session.delete(product)
    db.session.commit()
    return success_response(message="Product deleted successfully")
