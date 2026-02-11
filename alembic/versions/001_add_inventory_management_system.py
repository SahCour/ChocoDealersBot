"""Add inventory management system with new categories and TransactionLog

Revision ID: 001_inventory_mgmt
Revises: 
Create Date: 2026-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_inventory_mgmt'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade database schema for inventory management system.

    Changes:
    1. Update ProductCategory enum with 11 new categories
    2. Add TransactionActionType enum
    3. Add grammovka, unit_type, quantity_per_package to products table
    4. Add is_admin column to users table
    5. Create transaction_logs table

    ⚠️ CRITICAL: This migration changes ProductCategory enum values.
    Choose ONE of the options below based on your database state.
    """

    # ============================================
    # OPTION 1: EMPTY/TEST DATABASE (RECOMMENDED FOR FIRST DEPLOY)
    # ============================================
    # Use this if you have no production data or can recreate products
    # ✅ DISABLED: Not needed for empty database (tables don't exist yet)

    # op.execute("DELETE FROM products CASCADE;")  # Disabled - not needed for fresh DB

    # ============================================
    # OPTION 2: PRODUCTION DATABASE WITH DATA
    # ============================================
    # Use this if you have existing products that need to be mapped
    # Uncomment and customize the CASE statement below to map old categories to new ones:

    # op.execute("""
    #     UPDATE products SET category = (
    #         CASE category::text
    #             WHEN 'TRUFFLE' THEN 'OUR_CHOCOLATE'
    #             WHEN 'BAR_SMALL' THEN 'OUR_CHOCOLATE'
    #             WHEN 'BAR_LARGE' THEN 'OUR_CHOCOLATE'
    #             WHEN 'ICE_CREAM' THEN 'OUR_CHOCOLATE'
    #             WHEN 'BONBON' THEN 'OUR_CHOCOLATE'
    #             WHEN 'OTHER' THEN 'SHOP_MERCHANDISE'
    #             ELSE 'SHOP_MERCHANDISE'
    #         END
    #     )::productcategory;
    # """)

    # ============================================
    # 1. Update ProductCategory enum (SAFE VERSION)
    # ============================================

    # Make category column nullable temporarily
    op.execute("ALTER TABLE products ALTER COLUMN category DROP NOT NULL;")

    # Create new enum type
    op.execute("""
        CREATE TYPE productcategory_new AS ENUM (
            'OUR_CHOCOLATE',
            'CHOCOLATE_INGREDIENTS',
            'CHINESE_TEA',
            'BEVERAGES_COFFEE',
            'SHOP_MERCHANDISE',
            'HOUSEHOLD_ITEMS',
            'CHOCOLATE_PACKAGING',
            'OTHER_PACKAGING',
            'PRINTING_MATERIALS',
            'AI_EXPENSES',
            'EQUIPMENT_MATERIALS'
        );
    """)

    # Add temporary column with new enum type
    op.execute("""
        ALTER TABLE products
        ADD COLUMN category_new productcategory_new;
    """)

    # Copy data (will be NULL if old values don't match new enum)
    # If you used OPTION 2 above, this will work
    # If you used OPTION 1 (DELETE), this will just be NULL (fine, we deleted all rows)
    op.execute("""
        UPDATE products
        SET category_new = category::text::productcategory_new
        WHERE category IS NOT NULL;
    """)

    # Drop old column and enum
    op.execute("ALTER TABLE products DROP COLUMN category;")
    op.execute("DROP TYPE productcategory;")

    # Rename new column and type
    op.execute("ALTER TABLE products RENAME COLUMN category_new TO category;")
    op.execute("ALTER TYPE productcategory_new RENAME TO productcategory;")

    # Restore NOT NULL constraint
    op.execute("ALTER TABLE products ALTER COLUMN category SET NOT NULL;")
    
    # 2. Create TransactionActionType enum
    op.execute("""
        CREATE TYPE transactionactiontype AS ENUM ('ADD', 'CONSUME', 'CORRECTION');
    """)
    
    # 3. Add new columns to products table
    op.add_column('products', sa.Column('grammovka', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('unit_type', sa.String(length=50), nullable=True))
    op.add_column('products', sa.Column('quantity_per_package', sa.Integer(), nullable=True))
    
    # 4. Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='false'))
    
    # 5. Create transaction_logs table
    op.create_table('transaction_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.Enum(
            'OUR_CHOCOLATE',
            'CHOCOLATE_INGREDIENTS',
            'CHINESE_TEA',
            'BEVERAGES_COFFEE',
            'SHOP_MERCHANDISE',
            'HOUSEHOLD_ITEMS',
            'CHOCOLATE_PACKAGING',
            'OTHER_PACKAGING',
            'PRINTING_MATERIALS',
            'AI_EXPENSES',
            'EQUIPMENT_MATERIALS',
            name='productcategory'
        ), nullable=False),
        sa.Column('action_type', sa.Enum('ADD', 'CONSUME', 'CORRECTION', name='transactionactiontype'), nullable=False),
        sa.Column('quantity_original', sa.Float(), nullable=False),
        sa.Column('quantity_unit', sa.String(length=50), nullable=False),
        sa.Column('quantity_grams', sa.Integer(), nullable=False),
        sa.Column('quantity_display', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True, server_default='telegram_bot'),
        sa.Column('admin_flag', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on transaction_logs
    op.create_index(op.f('ix_transaction_logs_telegram_user_id'), 'transaction_logs', ['telegram_user_id'], unique=False)
    op.create_index(op.f('ix_transaction_logs_product_id'), 'transaction_logs', ['product_id'], unique=False)
    op.create_index(op.f('ix_transaction_logs_action_type'), 'transaction_logs', ['action_type'], unique=False)
    op.create_index(op.f('ix_transaction_logs_created_at'), 'transaction_logs', ['created_at'], unique=False)


def downgrade() -> None:
    """
    Downgrade database schema (reverse all changes).
    """
    
    # Drop transaction_logs table
    op.drop_index(op.f('ix_transaction_logs_created_at'), table_name='transaction_logs')
    op.drop_index(op.f('ix_transaction_logs_action_type'), table_name='transaction_logs')
    op.drop_index(op.f('ix_transaction_logs_product_id'), table_name='transaction_logs')
    op.drop_index(op.f('ix_transaction_logs_telegram_user_id'), table_name='transaction_logs')
    op.drop_table('transaction_logs')
    
    # Drop TransactionActionType enum
    op.execute('DROP TYPE transactionactiontype;')
    
    # Remove columns from users table
    op.drop_column('users', 'is_admin')
    
    # Remove columns from products table
    op.drop_column('products', 'quantity_per_package')
    op.drop_column('products', 'unit_type')
    op.drop_column('products', 'grammovka')
    
    # Restore old ProductCategory enum (if needed for rollback)
    # This is a simplified downgrade - in production you'd need to handle existing data
    op.execute("""
        ALTER TYPE productcategory RENAME TO productcategory_new;
    """)
    
    op.execute("""
        CREATE TYPE productcategory AS ENUM (
            'ICE_CREAM',
            'TRUFFLE',
            'BAR_SMALL',
            'BAR_LARGE',
            'BEAN_TO_BAR',
            'SYMPHONY',
            'DESSERT',
            'HALVA',
            'BONBON',
            'OTHER',
            'SET'
        );
    """)
    
    # This will fail if products have new category values
    # In production, you'd need to migrate the data first
    op.execute("""
        ALTER TABLE products 
        ALTER COLUMN category TYPE productcategory 
        USING 'OTHER'::productcategory;
    """)
    
    op.execute('DROP TYPE productcategory_new;')
