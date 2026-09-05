"""
Flipkart CSV CLI Importer (Refactored).

Now uses the shared app.ingestion engine for parsing and normalization.
The Flipkart canonical schema is recognized deterministically (no LLM call).

Usage:
    python scripts/import_flipkart_data.py [--merchant-id UUID] [--inventory-mode demo|zero]

Maintained for backward compatibility. All parsing logic lives in app/ingestion/.
"""
import os
import sys
import argparse
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.merchant import Merchant, User
from app.ingestion.importer import analyze_import, commit_import

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def parse_specs(spec_str: str) -> dict:
    """
    Kept for backward compatibility with existing tests.
    Delegates to the shared normalizer.
    """
    from app.ingestion.normalizer import normalize_specs
    return normalize_specs(spec_str)


def main():
    parser = argparse.ArgumentParser(description="Import Flipkart Dataset (uses shared ingestion engine)")
    parser.add_argument("--inventory-mode", choices=["demo", "zero"], default="zero",
                        help="demo: deterministic inventory, zero: 0 inventory")
    parser.add_argument("--merchant-id", type=str, help="UUID of the demo merchant")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.merchant_id:
            merchant = db.execute(select(Merchant).filter_by(id=args.merchant_id)).scalar_one_or_none()
        else:
            demo_user = db.execute(select(User).filter_by(email="merchant@demo.com")).scalar_one_or_none()
            if demo_user:
                merchant = db.execute(select(Merchant).filter_by(user_id=demo_user.id)).scalar_one_or_none()
            else:
                merchant = db.execute(select(Merchant)).scalars().first()

        if not merchant:
            logging.error("No merchant found. Run seed.py first.")
            sys.exit(1)

        logging.info(f"Using Merchant: {merchant.name} (ID: {merchant.id})")
        logging.info(f"Inventory Mode: {args.inventory_mode}")

        file_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "flipkart_com-ecommerce_sample.csv")
        if not os.path.exists(file_path):
            logging.error(f"Dataset not found at {file_path}")
            sys.exit(1)

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        logging.info(f"Analyzing CSV ({len(file_bytes)} bytes)...")

        analysis, error = analyze_import(
            file_bytes=file_bytes,
            merchant_id=merchant.id,
            use_category_filter=True,  # Flipkart: only target categories
            demo_inventory=(args.inventory_mode == "demo"),
        )

        if error:
            logging.error(f"Analysis failed: {error}")
            sys.exit(1)

        logging.info(f"Schema type: {analysis.schema_type}")
        logging.info(f"Total rows:  {analysis.total_rows}")
        logging.info(f"Valid rows:  {analysis.valid_row_count}")
        logging.info(f"Invalid rows:{analysis.invalid_row_count}")

        if analysis.valid_row_count == 0:
            logging.warning("No valid rows to import.")
            sys.exit(0)

        logging.info("Committing import to database...")
        result = commit_import(
            analysis=analysis,
            db=db,
            merchant_id=merchant.id,
            import_job_id=analysis.import_job_id,
        )

        logging.info("==================================================")
        logging.info("IMPORT SUMMARY")
        logging.info("==================================================")
        logging.info(f"Total analyzed:        {analysis.total_rows}")
        logging.info(f"Valid for import:      {analysis.valid_row_count}")
        logging.info(f"Invalid/Skipped:       {analysis.invalid_row_count}")
        logging.info(f"Newly inserted:        {result['inserted']}")
        logging.info(f"Already present:       {result['skipped_existing']}")
        logging.info(f"Failed:                {result['failed']}")
        logging.info("==================================================")

    except Exception as e:
        db.rollback()
        logging.error(f"Import failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
