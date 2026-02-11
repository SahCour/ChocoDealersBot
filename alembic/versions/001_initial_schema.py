"""Initial database schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-02-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing enum types if they exist (from previous failed migrations)
    op.execute("""
        DROP TYPE IF EXISTS transactionactiontype CASCADE;
        DROP TYPE IF EXISTS actiontype CASCADE;
        DROP TYPE IF EXISTS syncstatus CASCADE;
        DROP TYPE IF EXISTS synctype CASCADE;
        DROP TYPE IF EXISTS purchasestatus CASCADE;
        DROP TYPE IF EXISTS productionstatus CASCADE;
        DROP TYPE IF EXISTS paymentmethod CASCADE;
        DROP TYPE IF EXISTS salesource CASCADE;
        DROP TYPE IF EXISTS ingredientunit CASCADE;
        DROP TYPE IF EXISTS ingredientcategory CASCADE;
        DROP TYPE IF EXISTS productcategory CASCADE;
        DROP TYPE IF EXISTS userstatus CASCADE;
        DROP TYPE IF EXISTS userrole CASCADE;
    """)

    # Create enum types
    op.execute("""
        CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'STAFF');
        CREATE TYPE userstatus AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED');
        CREATE TYPE productcategory AS ENUM (
            'OUR_CHOCOLATE', 'CHOCOLATE_INGREDIENTS', 'CHINESE_TEA', 'BEVERAGES_COFFEE',
            'SHOP_MERCHANDISE', 'HOUSEHOLD_ITEMS', 'CHOCOLATE_PACKAGING', 'OTHER_PACKAGING',
            'PRINTING_MATERIALS', 'AI_EXPENSES', 'EQUIPMENT_MATERIALS'
        );
        CREATE TYPE ingredientcategory AS ENUM (
            'CACAO_BASE', 'NUTS_SEEDS', 'DAIRY_ALT', 'COFFEE', 'TEA', 'PACKAGING', 'SPICES', 'OTHER'
        );
        CREATE TYPE ingredientunit AS ENUM ('kg', 'L', 'pc', 'btl');
        CREATE TYPE salesource AS ENUM ('TELEGRAM_BOT', 'SQUARE_POS', 'MANUAL');
        CREATE TYPE paymentmethod AS ENUM ('CASH', 'CARD', 'BANK_TRANSFER', 'CRYPTO', 'OTHER');
        CREATE TYPE productionstatus AS ENUM ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
        CREATE TYPE purchasestatus AS ENUM ('ORDERED', 'RECEIVED', 'CANCELLED');
        CREATE TYPE synctype AS ENUM ('INVENTORY', 'SALES', 'PRODUCTS', 'FULL');
        CREATE TYPE syncstatus AS ENUM ('SUCCESS', 'FAILED', 'IN_PROGRESS');
        CREATE TYPE actiontype AS ENUM (
            'CREATE', 'UPDATE', 'DELETE', 'SALE', 'PRODUCTION', 'PURCHASE', 'INVENTORY_ADJUST', 'SYNC'
        );
        CREATE TYPE transactionactiontype AS ENUM ('ADD', 'CONSUME', 'CORRECTION');
    """)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(255)),
        sa.Column('first_name', sa.String(255)),
        sa.Column('last_name', sa.String(255)),
        sa.Column('role', postgresql.ENUM('ADMIN', 'MANAGER', 'STAFF', name='userrole'), nullable=False),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED', name='userstatus'), nullable=False),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'])
    op.create_unique_constraint('uq_users_telegram_id', 'users', ['telegram_id'])

    # Create role_permissions table
    op.create_table(
        'role_permissions',
        sa.Column('role', postgresql.ENUM('ADMIN', 'MANAGER', 'STAFF', name='userrole'), primary_key=True),
        sa.Column('permissions', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sku', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', postgresql.ENUM(
            'OUR_CHOCOLATE', 'CHOCOLATE_INGREDIENTS', 'CHINESE_TEA', 'BEVERAGES_COFFEE',
            'SHOP_MERCHANDISE', 'HOUSEHOLD_ITEMS', 'CHOCOLATE_PACKAGING', 'OTHER_PACKAGING',
            'PRINTING_MATERIALS', 'AI_EXPENSES', 'EQUIPMENT_MATERIALS',
            name='productcategory'
        ), nullable=False),
        sa.Column('weight_g', sa.DECIMAL(8, 2)),
        sa.Column('cocoa_percent', sa.String(20)),
        sa.Column('retail_price_thb', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('cogs_thb', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('square_item_id', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('notes', sa.Text()),
        sa.Column('grammovka', sa.Integer()),
        sa.Column('unit_type', sa.String(50)),
        sa.Column('quantity_per_package', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_products_sku', 'products', ['sku'])
    op.create_index('ix_products_category', 'products', ['category'])
    op.create_unique_constraint('uq_products_sku', 'products', ['sku'])

    # Create ingredients table
    op.create_table(
        'ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', postgresql.ENUM(
            'CACAO_BASE', 'NUTS_SEEDS', 'DAIRY_ALT', 'COFFEE', 'TEA', 'PACKAGING', 'SPICES', 'OTHER',
            name='ingredientcategory'
        ), nullable=False),
        sa.Column('price_per_unit_thb', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('unit', postgresql.ENUM('kg', 'L', 'pc', 'btl', name='ingredientunit'), nullable=False),
        sa.Column('supplier', sa.String(255)),
        sa.Column('notes', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_ingredients_code', 'ingredients', ['code'])
    op.create_unique_constraint('uq_ingredients_code', 'ingredients', ['code'])

    # Create inventory_products table
    op.create_table(
        'inventory_products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_stock_level', sa.Integer(), server_default='10'),
        sa.Column('max_stock_level', sa.Integer(), server_default='100'),
        sa.Column('location', sa.String(255), server_default='Main Warehouse'),
        sa.Column('last_count_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.CheckConstraint('quantity >= 0', name='positive_quantity'),
    )

    # Create inventory_ingredients table
    op.create_table(
        'inventory_ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ingredient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity_kg', sa.DECIMAL(12, 3), nullable=False, server_default='0'),
        sa.Column('min_stock_level_kg', sa.DECIMAL(12, 3), server_default='1'),
        sa.Column('max_stock_level_kg', sa.DECIMAL(12, 3), server_default='50'),
        sa.Column('location', sa.String(255), server_default='Main Warehouse'),
        sa.Column('expiry_date', sa.Date()),
        sa.Column('last_count_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='CASCADE'),
        sa.CheckConstraint('quantity_kg >= 0', name='positive_quantity_ing'),
    )

    # Create sales table
    op.create_table(
        'sales',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price_thb', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('discount_thb', sa.DECIMAL(10, 2), server_default='0'),
        sa.Column('final_price_thb', sa.DECIMAL(10, 2)),
        sa.Column('source', postgresql.ENUM('TELEGRAM_BOT', 'SQUARE_POS', 'MANUAL', name='salesource'), nullable=False),
        sa.Column('payment_method', postgresql.ENUM('CASH', 'CARD', 'BANK_TRANSFER', 'CRYPTO', 'OTHER', name='paymentmethod')),
        sa.Column('square_transaction_id', sa.String(255)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('customer_name', sa.String(255)),
        sa.Column('customer_telegram_id', sa.BigInteger()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.CheckConstraint('quantity > 0', name='positive_quantity_sale'),
    )
    op.create_index('ix_sales_created_at', 'sales', ['created_at'])

    # Create production table
    op.create_table(
        'production',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_number', sa.String(100)),
        sa.Column('quantity_produced', sa.Integer(), nullable=False),
        sa.Column('production_date', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('status', postgresql.ENUM('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='productionstatus'), nullable=False),
        sa.Column('cost_materials_thb', sa.DECIMAL(10, 2)),
        sa.Column('cost_labor_thb', sa.DECIMAL(10, 2)),
        sa.Column('total_cost_thb', sa.DECIMAL(10, 2)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.CheckConstraint('quantity_produced > 0', name='positive_quantity_prod'),
    )
    op.create_index('ix_production_status', 'production', ['status'])
    op.create_unique_constraint('uq_production_batch_number', 'production', ['batch_number'])

    # Create production_ingredients_used table
    op.create_table(
        'production_ingredients_used',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('production_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ingredient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity_used_kg', sa.DECIMAL(12, 3), nullable=False),
        sa.Column('cost_thb', sa.DECIMAL(10, 2)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['production_id'], ['production.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
    )

    # Create purchases table
    op.create_table(
        'purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ingredient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity_kg', sa.DECIMAL(12, 3), nullable=False),
        sa.Column('unit_price_thb', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('supplier', sa.String(255)),
        sa.Column('purchase_date', sa.Date(), nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('expected_delivery_date', sa.Date()),
        sa.Column('status', postgresql.ENUM('ORDERED', 'RECEIVED', 'CANCELLED', name='purchasestatus'), nullable=False),
        sa.Column('invoice_number', sa.String(100)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('received_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.CheckConstraint('quantity_kg > 0', name='positive_quantity_purch'),
    )
    op.create_index('ix_purchases_status', 'purchases', ['status'])

    # Create square_sync_log table
    op.create_table(
        'square_sync_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sync_type', postgresql.ENUM('INVENTORY', 'SALES', 'PRODUCTS', 'FULL', name='synctype'), nullable=False),
        sa.Column('sync_status', postgresql.ENUM('SUCCESS', 'FAILED', 'IN_PROGRESS', name='syncstatus'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('records_synced', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('triggered_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id']),
    )

    # Create sheets_sync_log table
    op.create_table(
        'sheets_sync_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sheet_name', sa.String(255), nullable=False),
        sa.Column('sync_direction', sa.String(20)),
        sa.Column('sync_status', postgresql.ENUM('SUCCESS', 'FAILED', 'IN_PROGRESS', name='syncstatus'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('records_synced', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('triggered_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id']),
    )

    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('action', postgresql.ENUM(
            'CREATE', 'UPDATE', 'DELETE', 'SALE', 'PRODUCTION', 'PURCHASE', 'INVENTORY_ADJUST', 'SYNC',
            name='actiontype'
        ), nullable=False),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True)),
        sa.Column('old_data', postgresql.JSONB()),
        sa.Column('new_data', postgresql.JSONB()),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])

    # Create transaction_logs table
    op.create_table(
        'transaction_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('user_name', sa.String(255), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('category', postgresql.ENUM(
            'OUR_CHOCOLATE', 'CHOCOLATE_INGREDIENTS', 'CHINESE_TEA', 'BEVERAGES_COFFEE',
            'SHOP_MERCHANDISE', 'HOUSEHOLD_ITEMS', 'CHOCOLATE_PACKAGING', 'OTHER_PACKAGING',
            'PRINTING_MATERIALS', 'AI_EXPENSES', 'EQUIPMENT_MATERIALS',
            name='productcategory'
        ), nullable=False),
        sa.Column('action_type', postgresql.ENUM('ADD', 'CONSUME', 'CORRECTION', name='transactionactiontype'), nullable=False),
        sa.Column('quantity_original', sa.Float(), nullable=False),
        sa.Column('quantity_unit', sa.String(50), nullable=False),
        sa.Column('quantity_grams', sa.Integer(), nullable=False),
        sa.Column('quantity_display', sa.String(100)),
        sa.Column('notes', sa.Text()),
        sa.Column('source', sa.String(50), server_default='telegram_bot'),
        sa.Column('admin_flag', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_transaction_logs_telegram_user_id', 'transaction_logs', ['telegram_user_id'])
    op.create_index('ix_transaction_logs_product_id', 'transaction_logs', ['product_id'])
    op.create_index('ix_transaction_logs_action_type', 'transaction_logs', ['action_type'])
    op.create_index('ix_transaction_logs_created_at', 'transaction_logs', ['created_at'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('transaction_logs')
    op.drop_table('audit_log')
    op.drop_table('sheets_sync_log')
    op.drop_table('square_sync_log')
    op.drop_table('purchases')
    op.drop_table('production_ingredients_used')
    op.drop_table('production')
    op.drop_table('sales')
    op.drop_table('inventory_ingredients')
    op.drop_table('inventory_products')
    op.drop_table('ingredients')
    op.drop_table('products')
    op.drop_table('role_permissions')
    op.drop_table('users')

    # Drop enum types
    op.execute("""
        DROP TYPE IF EXISTS transactionactiontype;
        DROP TYPE IF EXISTS actiontype;
        DROP TYPE IF EXISTS syncstatus;
        DROP TYPE IF EXISTS synctype;
        DROP TYPE IF EXISTS purchasestatus;
        DROP TYPE IF EXISTS productionstatus;
        DROP TYPE IF EXISTS paymentmethod;
        DROP TYPE IF EXISTS salesource;
        DROP TYPE IF EXISTS ingredientunit;
        DROP TYPE IF EXISTS ingredientcategory;
        DROP TYPE IF EXISTS productcategory;
        DROP TYPE IF EXISTS userstatus;
        DROP TYPE IF EXISTS userrole;
    """)
