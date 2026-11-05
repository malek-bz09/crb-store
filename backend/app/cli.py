"""Command-line tasks.

    uv run python -m app.cli create-admin --email you@shop.dz --name "Your Name" [--role staff]
    uv run python -m app.cli seed     # add the sample products to an empty catalogue
    uv run python -m app.cli seed --replace   # delete every other product, add missing sample ones
"""

import argparse
import sys
from decimal import Decimal
from getpass import getpass

from sqlalchemy import func, select, update

from app.db.session import SessionLocal
from app.models.product import Product
from app.services.auth import save_admin

# The shop's starting catalogue. Photos are in frontend/public/<slug>.jpg
# (sources and licences in frontend/public/CREDITS.md).
SAMPLE_PRODUCTS = [
    ("crb-home-jersey", "CRB Home Jersey 26/27", "tops", "8900", None, 25,
     "The red home shirt in a light, breathable match fabric with a ribbed crew neck."),
    ("crb-away-jersey", "CRB Away Jersey 26/27", "tops", "8900", None, 20,
     "The white away shirt with red trim on the collar and cuffs."),
    ("crb-supporters-tee", "Supporters Tee – Red", "tops", "3500", None, 40,
     "Soft cotton everyday tee in club red, for match days and every other day."),
    ("crb-supporters-hoodie", "Supporters Hoodie – Red", "tops", "6900", "7900", 15,
     "Heavyweight brushed-fleece hoodie in club red with a roomy hood."),
    ("crb-retro-stripe-knit", "Retro Stripe Knit Sweater", "tops", "5900", None, 8,
     "Loose-fit knit sweater with old-school terrace stripes on cream."),
    ("crb-training-joggers", "Training Joggers – Red", "bottoms", "4900", None, 18,
     "Tapered fleece joggers with an elastic waist and cuffed ankles."),
    ("crb-match-shorts", "Training Shorts – Black", "bottoms", "2900", "3500", 22,
     "Lightweight training shorts with an elastic drawcord waist."),
    ("crb-red-knit-beanie", "Red Knit Beanie", "hats", "1900", None, 30,
     "Chunky ribbed beanie in club red with a fold-up cuff."),
    ("crb-burgundy-beanie", "Winter Beanie – Burgundy", "hats", "1900", None, 0,
     "Deep burgundy knit beanie for cold evenings in the stands."),
]


def seed(replace: bool = False) -> None:
    """Fills an empty catalogue. With replace=True, also works on a catalogue that
    has products: every product that isn't a sample one is deleted (the same soft
    delete as the admin, so past orders keep their items), and the missing sample
    products are added."""
    sample_slugs = [slug for slug, *_ in SAMPLE_PRODUCTS]
    with SessionLocal() as db:
        if not replace and db.scalar(select(Product.id).limit(1)) is not None:
            sys.exit("The catalogue already has products; nothing was added. "
                     "Use `seed --replace` to swap them for the sample ones.")
        removed = db.execute(
            update(Product)
            .where(Product.deleted_at.is_(None), Product.slug.not_in(sample_slugs))
            .values(deleted_at=func.now())
        ).rowcount
        # Slugs are unique even among deleted products, so skip any already in the table
        existing = set(db.scalars(select(Product.slug).where(Product.slug.in_(sample_slugs))))
        new = [row for row in SAMPLE_PRODUCTS if row[0] not in existing]
        db.add_all(
            Product(
                slug=slug, name=name, category=category, price=Decimal(price),
                compare_at_price=Decimal(old) if old else None, stock_quantity=stock,
                description=description, image_url=f"/{slug}.jpg",
            )
            for slug, name, category, price, old, stock, description in new
        )
        db.commit()
    print(f"Added {len(new)} sample products" + (f", deleted {removed} others." if removed else "."))


def create_admin(email: str, name: str, role: str) -> None:
    """Creates an account, or resets an existing one's name, role and password.
    The password is typed in (hidden), never passed on the command line where it
    would be saved in the shell history."""
    password = getpass("Password (at least 10 characters): ")
    if password != getpass("Repeat password: "):
        sys.exit("Passwords don't match.")
    with SessionLocal() as db:
        try:
            admin, created = save_admin(db, email=email, full_name=name, password=password, role=role)
        except ValueError as error:
            sys.exit(str(error))
    print(f"{'Created' if created else 'Updated'} {admin.role} account {admin.email}.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    seed_command = commands.add_parser("seed", help="add the sample products to an empty catalogue")
    seed_command.add_argument("--replace", action="store_true",
                              help="delete every non-sample product, then add the missing sample ones")
    new_admin = commands.add_parser("create-admin", help="add an admin account, or reset its password")
    new_admin.add_argument("--email", required=True)
    new_admin.add_argument("--name", required=True)
    new_admin.add_argument("--role", choices=["admin", "staff"], default="admin")
    args = parser.parse_args()
    if args.command == "seed":
        seed(replace=args.replace)
    elif args.command == "create-admin":
        create_admin(args.email, args.name, args.role)


if __name__ == "__main__":
    main()
