
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from neo4j import GraphDatabase
from rag.config import get_config

class GraphValidator:
    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters)
            return [record for record in result]

    # -------------------------------------------
    # VALIDATION
    # -------------------------------------------
    def validate_graph(self):
        print("=== Starting Graph Validation (Procurement + Marketing) ===")

        # -------------------------------------------
        # 1. NODE COUNTS
        # -------------------------------------------
        print("\n--- Node Counts ---")
        labels = [
            "Supplier", "PO", "Invoice", "Product",
            "Campaign", "AdGroup", "Order",
            "Channel", "Platform"
        ]
        for label in labels:
            result = self.run_query(f"MATCH (n:{label}) RETURN count(n) AS count")
            print(f"{label}: {result[0]['count']}")

        # -------------------------------------------
        # 2. RELATIONSHIP COUNTS
        # -------------------------------------------
        print("\n--- Relationship Counts ---")
        rel_types = [
            "BILLED_BY", "INVOICES", "FUNDED", "ORDERS",
            "HAS_ADGROUP", "GENERATED", "CONTAINS_PRODUCT",
            "USES_CHANNEL", "ON_PLATFORM", "PROMOTES"
        ]
        for rel in rel_types:
            result = self.run_query(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS count")
            print(f"{rel}: {result[0]['count']}")

        # -------------------------------------------
        # 3. DANGLING RELATIONSHIPS (PROCUREMENT)
        # -------------------------------------------
        print("\n--- Procurement Orphan Checks ---")

        # PO without Supplier
        result = self.run_query("""
            MATCH (p:PO) 
            WHERE NOT (p)-[:BILLED_BY]->(:Supplier)
            RETURN count(p) AS count
        """)
        print(f"POs without Supplier: {result[0]['count']}")

        # Invoice without PO
        result = self.run_query("""
            MATCH (i:Invoice)
            WHERE NOT (i)-[:INVOICES]->(:PO)
            RETURN count(i) AS count
        """)
        print(f"Invoices without PO: {result[0]['count']}")

        # Funded POs without Campaign
        result = self.run_query("""
            MATCH (p:PO)
            WHERE (p)<-[:FUNDED]-() 
              AND NOT (p)<-[:FUNDED]-(:Campaign)
            RETURN count(p) AS count
        """)
        print(f"Funded POs without Campaign: {result[0]['count']}")

        # -------------------------------------------
        # 4. DANGLING RELATIONSHIPS (MARKETING)
        # -------------------------------------------
        print("\n--- Marketing Orphan Checks ---")

        # Campaign without AdGroup
        result = self.run_query("""
            MATCH (c:Campaign)
            WHERE NOT (c)-[:HAS_ADGROUP]->(:AdGroup)
            RETURN count(c) AS count
        """)
        print(f"Campaigns without AdGroup: {result[0]['count']}")

        # AdGroup without Campaign
        result = self.run_query("""
            MATCH (g:AdGroup)
            WHERE NOT ()-[:HAS_ADGROUP]->(g)
            RETURN count(g) AS count
        """)
        print(f"AdGroups without Campaign: {result[0]['count']}")

        # AdGroup without Order
        result = self.run_query("""
            MATCH (g:AdGroup)
            WHERE NOT (g)-[:GENERATED]->(:Order)
            RETURN count(g) AS count
        """)
        print(f"AdGroups without Orders: {result[0]['count']}")

        # Orders without Product
        result = self.run_query("""
            MATCH (o:Order)
            WHERE NOT (o)-[:CONTAINS_PRODUCT]->(:Product)
            RETURN count(o) AS count
        """)
        print(f"Orders without Product: {result[0]['count']}")

        # Campaign without Channel
        result = self.run_query("""
            MATCH (c:Campaign)
            WHERE NOT (c)-[:USES_CHANNEL]->(:Channel)
            RETURN count(c) AS count
        """)
        print(f"Campaigns without Channel: {result[0]['count']}")

        # Channel without Platform
        result = self.run_query("""
            MATCH (ch:Channel)
            WHERE NOT (ch)-[:ON_PLATFORM]->(:Platform)
            RETURN count(ch) AS count
        """)
        print(f"Channels without Platform: {result[0]['count']}")

        print("\n=== Graph Validation Complete ===")

def main():
    config = get_config()
    validator = GraphValidator(
        config.neo4j_uri, 
        config.neo4j_user, 
        config.neo4j_password, 
        config.neo4j_database
    )
    validator.validate_graph()
    validator.close()

if __name__ == "__main__":
    main()
