"""The `seed` command: empty catalogue, refusing to overwrite, and --replace."""

import pytest
from sqlalchemy import select

from app.cli import SAMPLE_PRODUCTS, seed
from app.db.session import SessionLocal
from app.models.product import Product

SAMPLE_SLUGS = {slug for slug, *_ in SAMPLE_PRODUCTS}


def products():
    with SessionLocal() as db:
        return {p.slug: p.deleted_at for p in db.scalars(select(Product))}


def add_old_product():
    with SessionLocal() as db:
        db.add(
            Product(
                slug="old-polo",
                name="Old Polo",
                category="tops",
                price=100,
                stock_quantity=1,
                description="From the previous catalogue.",
                image_url="/old-polo.jpg",
            )
        )
        db.commit()


def test_seed_fills_an_empty_catalogue():
    seed()
    assert set(products()) == SAMPLE_SLUGS


def test_seed_refuses_when_the_catalogue_has_products():
    add_old_product()
    with pytest.raises(SystemExit):
        seed()
    assert set(products()) == {"old-polo"}


def test_seed_replace_deletes_other_products_and_adds_samples():
    add_old_product()
    seed(replace=True)
    rows = products()
    assert rows["old-polo"] is not None  # soft-deleted, so past orders keep it
    assert all(rows[slug] is None for slug in SAMPLE_SLUGS)


def test_seed_replace_twice_adds_nothing_new():
    seed(replace=True)
    seed(replace=True)
    assert set(products()) == SAMPLE_SLUGS
