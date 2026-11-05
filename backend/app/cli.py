"""Command-line tasks.

    uv run python -m app.cli create-admin --email you@shop.dz --name "Your Name" [--role staff]
    uv run python -m app.cli seed     # add the sample products to an empty catalogue
"""

import argparse
import sys
from decimal import Decimal
from getpass import getpass

from sqlalchemy import select

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


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(Product.id).limit(1)) is not None:
            sys.exit("The catalogue already has products; nothing was added.")
        db.add_all(
            Product(
                slug=slug, name=name, category=category, price=Decimal(price),
                compare_at_price=Decimal(old) if old else None, stock_quantity=stock,
                description=description, image_url=f"/{slug}.jpg",
            )
            for slug, name, category, price, old, stock, description in SAMPLE_PRODUCTS
        )
        db.commit()
    print(f"Added {len(SAMPLE_PRODUCTS)} sample products.")


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
    commands.add_parser("seed", help="add the sample products to an empty catalogue")
    new_admin = commands.add_parser("create-admin", help="add an admin account, or reset its password")
    new_admin.add_argument("--email", required=True)
    new_admin.add_argument("--name", required=True)
    new_admin.add_argument("--role", choices=["admin", "staff"], default="admin")
    args = parser.parse_args()
    if args.command == "seed":
        seed()
    elif args.command == "create-admin":
        create_admin(args.email, args.name, args.role)


if __name__ == "__main__":
    main()
