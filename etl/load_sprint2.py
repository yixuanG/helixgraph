
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from neo4j import GraphDatabase
from rag.config import get_config

class Neo4jLoader:
    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters)
            return [record for record in result]

    # ----------------------------------------------------------
    #  EXISTING SECTIONS ( NON-MARKETING KG )
    # ----------------------------------------------------------

    def load_suppliers(self, file_path):
        df = pd.read_csv(file_path)
        df.rename(columns={
            'vendorCode': 'id',
            'legalName': 'name',
            'category_L1': 'category',
            'riskScore': 'risk_score',
            'paymentTerms': 'payment_terms',
            'lastAnnualRevenue': 'last_annual_revenue'
        }, inplace=True)
        for _, row in df.iterrows():
            self.run_query(
                """
                CREATE (s:Supplier {
                    id: $id,
                    name: $name,
                    category: $category,
                    risk_score: $risk_score,
                    country: $country,
                    payment_terms: $payment_terms,
                    last_annual_revenue: $last_annual_revenue
                })
                """,
                row.to_dict()
            )

    def load_pos(self, file_path):
        df = pd.read_csv(file_path)
        df.rename(columns={
            'orderNumber': 'id',
            'supplierVendorCode': 'supplier_id',
            'orderTotalValue': 'amount',
            'dateIssued': 'date',
            'orderStatus': 'status'
        }, inplace=True)
        df['campaign_id'] = df['description'].str.extract(r"Campaign ID: (\S+)")
        if 'productSku' not in df.columns:
            df['productSku'] = None
        else:
            df['productSku'] = df['productSku'].where(pd.notnull(df['productSku']), None)

        for _, row in df.iterrows():
            self.run_query(
                """
                CREATE (p:PO {
                    id: $id,
                    supplier_id: $supplier_id,
                    amount: $amount,
                    date: $date,
                    status: $status,
                    category: $category,
                    campaign_id: $campaign_id,
                    description: $description,
                    product_sku: $productSku,
                    quantity: $quantity
                })
                """,
                row.to_dict()
            )

    def load_products_procurement(self, file_path):
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            self.run_query(
                """
                CREATE (p:Product {
                    sku: $sku,
                    name: $name,
                    description: $description,
                    unit_of_measure: $unitOfMeasure,
                    is_critical: $isCritical,
                    category: $category_L4
                })
                """,
                row.to_dict()
            )

    def load_invoices(self, file_path):
        df = pd.read_csv(file_path)
        df.rename(columns={'invoiceNumber': 'id'}, inplace=True)
        for _, row in df.iterrows():
            self.run_query(
                """
                CREATE (i:Invoice {
                    id: $id,
                    po_id: $po_id,
                    amount: $amount,
                    issue_date: $issue_date,
                    due_date: $due_date,
                    paid_date: $paid_date,
                    status: $status
                })
                """,
                row.to_dict()
            )

    def load_campaign_po_links(self, file_path):
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            self.run_query(
                """
                MATCH (c:Campaign {id: $campaign_id})
                MATCH (p:PO {id: $po_id})
                CREATE (c)-[:FUNDED]->(p)
                """,
                row.to_dict()
            )

    # ----------------------------------------------------------
    #  NEW SECTION — MARKETING KG
    # ----------------------------------------------------------

    # === (1) Campaign Loader ===
    def load_marketing_campaigns(self, file_path):
        df = pd.read_csv(file_path)

        # Clean column names
        df.columns = df.columns.str.strip()

        for _, row in df.iterrows():
            self.run_query(
                """
                MERGE (c:Campaign {id: $campaign_id})
                SET 
                    c.campaign_name = $campaign_name,
                    c.company = $company,
                    c.team = $team,
                    c.market = $market,
                    c.hero_product = $hero_product,
                    c.product_line = $product_line,
                    c.objective = $objective,
                    c.month = $month,
                    c.start_date = $start_date,
                    c.end_date = $end_date,
                    c.status = $status,
                    c.currency = $currency,
                    c.budget = toFloat($budget),
                    c.actual_spend = toFloat($actual_spend),
                    c.channel = $channel,
                    c.media_platform = $media_platform,
                    c.retargeting = $Retargeting,
                    c.billing_type = $billing_type,
                    c.billing_unit_cost = toFloat($billing_unit_cost),
                    c.impressions = toFloat($impressions),
                    c.clicks = toFloat($clicks),
                    c.ctr = toFloat($ctr),
                    c.views = toFloat($views),
                    c.vtr = toFloat($vtr),
                    c.sessions = toFloat($sessions),
                    c.conversions = toFloat($conversions),
                    c.conversion_rate = toFloat($conversion_rate),
                    c.aov = toFloat($aov),
                    c.reach = toFloat($reach),
                    c.grp = toFloat($grp),
                    c.frequency = toFloat($frequency),
                    c.revenue = toFloat($revenue),
                    c.roas = toFloat($roas)
                """,
                row.to_dict()
            )

            # Create AdGroup node
            self.run_query(
                """
                MERGE (g:AdGroup {id: $ad_group_id})
                MERGE (c:Campaign {id: $campaign_id})
                MERGE (c)-[:HAS_ADGROUP]->(g)
                """,
                row.to_dict()
            )

    # === (2) Marketing Product Loader ===
    def load_marketing_products(self, file_path):
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()

        for _, row in df.iterrows():
            self.run_query(
                """
                MERGE (p:Product {sku_id: $SKU_id})
                SET
                    p.product_id = $product_id,
                    p.product_name = $product_name,
                    p.category_level_1 = $category_level_1,
                    p.category_level_2 = $category_level_2,
                    p.brand = $brand,
                    p.sku_name = $SKU_name,
                    p.size = $size,
                    p.color = $color,
                    p.other_features = $other_features,
                    p.rrp = toFloat($RRP)
                """,
                row.to_dict()
            )

    # === (3) Order Loader ===
    def load_marketing_orders(self, file_path):
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()

        for _, row in df.iterrows():
            self.run_query(
                """
                MERGE (o:Order {order_id: $order_id})
                SET
                    o.order_date = $order_date,
                    o.month = $month,
                    o.sku_id = $sku_id,
                    o.sku_name = $sku_name,
                    o.rrp = toFloat($rrp),
                    o.asp = toFloat($asp),
                    o.no_of_transactions = toFloat($no_of_transactions),
                    o.revenue = toFloat($revenue),
                    o.customer_id = $customer_id
                """,
                row.to_dict()
            )

            # Link Order → Product
            self.run_query(
                """
                MATCH (o:Order {order_id: $order_id})
                MATCH (p:Product {sku_id: $sku_id})
                MERGE (o)-[:CONTAINS_PRODUCT]->(p)
                """,
                row.to_dict()
            )

            # Link Order → AdGroup
            self.run_query(
                """
                MATCH (o:Order {order_id: $order_id})
                MATCH (g:AdGroup {id: $ad_group_id})
                MERGE (g)-[:GENERATED]->(o)
                """,
                row.to_dict()
            )

    # ----------------------------------------------------------
    # RELATIONSHIPS FOR MARKETING
    # ----------------------------------------------------------

    def create_marketing_relationships(self):
        # Campaign → Product (via hero_product)
        self.run_query("""
            MATCH (c:Campaign), (p:Product)
            WHERE c.hero_product = p.product_name
            MERGE (c)-[:PROMOTES]->(p)
        """)

        # Campaign → Channel node
        self.run_query("""
            MATCH (c:Campaign)
            MERGE (ch:Channel {name: c.channel})
            MERGE (c)-[:USES_CHANNEL]->(ch)
        """)

        # Channel → Platform
        self.run_query("""
            MATCH (c:Campaign)
            MATCH (ch:Channel {name: c.channel})
            MERGE (pf:Platform {name: c.media_platform})
            MERGE (ch)-[:ON_PLATFORM]->(pf)
        """)

    # ----------------------------------------------------------
    # CLEAN + MAIN PIPELINE
    # ----------------------------------------------------------

    def clean_database(self):
        print("Cleaning database…")
        self.run_query("MATCH (n) DETACH DELETE n")

def main():
    config = get_config()
    loader = Neo4jLoader(config.neo4j_uri, config.neo4j_user, config.neo4j_password, config.neo4j_database)

    loader.clean_database()

    data_path = "data/processed"

    # Procurement / Finance (existing)
    loader.load_suppliers(os.path.join(data_path, "procurement/suppliers.csv"))
    loader.load_products_procurement(os.path.join(data_path, "procurement/products.csv"))
    loader.load_pos(os.path.join(data_path, "procurement/pos.csv"))
    loader.load_invoices(os.path.join(data_path, "procurement/invoices.csv"))
    loader.load_campaign_po_links(os.path.join(data_path, "campaign_po_links.csv"))

    # Marketing (NEW)
    loader.load_marketing_campaigns(os.path.join(data_path, "marketing/campaigns_adidas_v5.csv"))
    loader.load_marketing_products(os.path.join(data_path, "marketing/products_v6.csv"))
    orders_path = "data/local/orders.csv"   # download the large file in your local repo 
    loader.load_marketing_orders(orders_path)
    
    # Alternative Loading
    # orders_url = "https://drive.google.com/uc?id=1NXCKHa1aQB9BqIPKdjJxKqQ0FCwuAaTF&export=download"
    # df = pd.read_csv(orders_url)


    # Relationships
    loader.create_relationships()
    loader.create_marketing_relationships()

    loader.close()
    print("KG load completed.")

if __name__ == "__main__":
    main()
