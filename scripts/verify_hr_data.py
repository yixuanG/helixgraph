"""
Verify HR data import quality
"""
import os
import certifi
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
os.environ['SSL_CERT_FILE'] = certifi.where()

def verify_hr_data():
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    print("=" * 80)
    print("🔍 HR Data Verification Report")
    print("=" * 80)
    
    with driver.session(database=database) as session:
        # 1. Skills with proficiency levels
        print("\n1️⃣ HAS_SKILL relationships breakdown:")
        result = session.run("""
            MATCH ()-[r:HAS_SKILL]->()
            RETURN 
                CASE WHEN r.proficiency_level IS NOT NULL THEN 'With Proficiency' 
                     ELSE 'Legacy (No Proficiency)' 
                END as type,
                count(r) as count
        """)
        for record in result:
            print(f"   {record['type']}: {record['count']}")
        
        # 2. Proficiency level distribution
        print("\n2️⃣ Proficiency level distribution (new data):")
        result = session.run("""
            MATCH ()-[r:HAS_SKILL]->()
            WHERE r.proficiency_level IS NOT NULL
            RETURN r.proficiency_level as level, count(r) as count
            ORDER BY count DESC
        """)
        for record in result:
            print(f"   {record['level']}: {record['count']}")
        
        # 3. Top skills by employee count
        print("\n3️⃣ Top 10 skills (with proficiency data):")
        result = session.run("""
            MATCH (s:Skill)<-[r:HAS_SKILL]-(e:Employee)
            WHERE r.proficiency_level IS NOT NULL
            RETURN s.name as skill, count(e) as employees,
                   avg(r.years_of_experience) as avg_years
            ORDER BY employees DESC
            LIMIT 10
        """)
        for record in result:
            print(f"   {record['skill']}: {record['employees']} employees "
                  f"(avg {record['avg_years']:.1f} years)")
        
        # 4. Python experts
        print("\n4️⃣ Python experts (Advanced/Expert level):")
        result = session.run("""
            MATCH (e:Employee)-[r:HAS_SKILL]->(s:Skill {name: 'Python'})
            WHERE r.proficiency_level IN ['Advanced', 'Expert']
            RETURN e.name, e.role, r.proficiency_level, r.years_of_experience
            ORDER BY r.years_of_experience DESC
            LIMIT 5
        """)
        for record in result:
            print(f"   {record['e.name']} ({record['e.role']}): "
                  f"{record['r.proficiency_level']}, {record['r.years_of_experience']} years")
        
        # 5. Manager hierarchy
        print("\n5️⃣ Top managers (by direct reports):")
        result = session.run("""
            MATCH (e:Employee)-[:REPORTS_TO]->(m:Employee)
            RETURN m.name as manager, m.role, count(e) as direct_reports
            ORDER BY direct_reports DESC
            LIMIT 5
        """)
        for record in result:
            print(f"   {record['manager']} ({record['m.role']}): "
                  f"{record['direct_reports']} direct reports")
        
        # 6. Department skills
        print("\n6️⃣ Skills by department (Marketing):")
        result = session.run("""
            MATCH (e:Employee {department: 'Marketing'})-[r:HAS_SKILL]->(s:Skill)
            WHERE r.proficiency_level IS NOT NULL
            RETURN s.name, count(e) as count
            ORDER BY count DESC
            LIMIT 5
        """)
        for record in result:
            print(f"   {record['s.name']}: {record['count']} employees")
    
    print("\n" + "=" * 80)
    print("✅ Verification Complete!")
    print("=" * 80)
    
    driver.close()

if __name__ == "__main__":
    verify_hr_data()
