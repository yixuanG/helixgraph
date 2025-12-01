"""
Quick check of Neo4j database status
"""
import os
import certifi
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
os.environ['SSL_CERT_FILE'] = certifi.where()

def check_status():
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    print("=" * 80)
    print("🔍 Neo4j Database Status Check")
    print("=" * 80)
    print(f"\nConnecting to: {uri}")
    print(f"Database: {database}\n")
    
    with driver.session(database=database) as session:
        # Count all nodes
        print("📊 Node counts:")
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(*) as count
            ORDER BY count DESC
        """)
        total = 0
        for record in result:
            count = record['count']
            total += count
            print(f"   {record['label']}: {count}")
        print(f"\n   Total nodes: {total}")
        
        # Check Employee details
        print("\n👥 Employee sample (first 5):")
        result = session.run("""
            MATCH (e:Employee)
            RETURN e.id, e.name, e.role, e.department
            LIMIT 5
        """)
        for record in result:
            print(f"   {record['e.id']}: {record['e.name']} - {record['e.role']} ({record['e.department']})")
        
        # Check Skill details
        print("\n🎯 Skill sample (first 5):")
        result = session.run("""
            MATCH (s:Skill)
            RETURN s.id, s.name, s.category
            LIMIT 5
        """)
        for record in result:
            print(f"   {record['s.id']}: {record['s.name']} ({record['s.category']})")
        
        # Count relationships
        print("\n🔗 Relationship counts:")
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """)
        for record in result:
            print(f"   {record['type']}: {record['count']}")
    
    print("\n" + "=" * 80)
    driver.close()

if __name__ == "__main__":
    check_status()
