"""
Import HR data with new structure including employee-skill mappings

New data structure:
- hr_employees.json: Employee information
- hr_skills.json: Skill catalog
- hr_employee_skills.json: Employee-Skill mappings with proficiency levels
- hr_teams.json: Team information (optional)

Usage:
    python scripts/import_hr_data.py
"""
import json
import os
from pathlib import Path
import certifi
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SSL Fix
os.environ['SSL_CERT_FILE'] = certifi.where()

# Use Google Drive data path
DATA_SOURCE_DIR = Path(__file__).parent.parent / "data" / "source" / "hr"

def load_json(file_path: Path):
    """Load JSON file"""
    print(f"   Loading: {file_path.name}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

class HRDataImporter:
    """Import HR data to Neo4j"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        
    def close(self):
        """Close connection"""
        self.driver.close()
    
    def create_indexes(self):
        """Create indexes for HR entities"""
        print("\n📊 Creating indexes...")
        
        indexes = [
            "CREATE INDEX employee_id IF NOT EXISTS FOR (e:Employee) ON (e.id)",
            "CREATE INDEX skill_id IF NOT EXISTS FOR (s:Skill) ON (s.id)",
            "CREATE INDEX skill_name IF NOT EXISTS FOR (s:Skill) ON (s.name)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for idx in indexes:
                session.run(idx)
        
        print("✅ Indexes created")
    
    def import_employees(self):
        """Import employees from hr_employees.json"""
        print("\n👥 Importing Employees...")
        
        employees_file = DATA_SOURCE_DIR / "hr_employees.json"
        employees = load_json(employees_file)
        
        # Process employee data
        processed_employees = []
        for emp in employees:
            full_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            if not full_name:
                full_name = emp.get('name', 'Unknown')
            
            processed_employees.append({
                'id': emp.get('employee_id', ''),
                'name': full_name,
                'first_name': emp.get('first_name', ''),
                'last_name': emp.get('last_name', ''),
                'email': emp.get('email', ''),
                'phone': emp.get('phone', ''),
                'hire_date': emp.get('hire_date', ''),
                'role': emp.get('job_title', ''),
                'department': emp.get('department', ''),
                'manager_id': emp.get('manager_id', ''),
                'salary': float(emp.get('salary', 0)),
                'location': emp.get('location', '')
            })
        
        query = """
        UNWIND $employees as emp
        MERGE (e:Employee {id: emp.id})
        ON CREATE SET
            e.name = emp.name,
            e.first_name = emp.first_name,
            e.last_name = emp.last_name,
            e.email = emp.email,
            e.phone = emp.phone,
            e.hire_date = date(emp.hire_date),
            e.role = emp.role,
            e.department = emp.department,
            e.manager_id = emp.manager_id,
            e.salary = emp.salary,
            e.location = emp.location
        ON MATCH SET
            e.name = emp.name,
            e.first_name = emp.first_name,
            e.last_name = emp.last_name,
            e.email = emp.email,
            e.phone = emp.phone,
            e.hire_date = date(emp.hire_date),
            e.role = emp.role,
            e.department = emp.department,
            e.manager_id = emp.manager_id,
            e.salary = emp.salary,
            e.location = emp.location
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, employees=processed_employees)
            summary = result.consume()
        
        print(f"✅ Processed {len(employees)} employees")
        print(f"   Nodes created: {summary.counters.nodes_created}")
        print(f"   Properties set: {summary.counters.properties_set}")
    
    def import_skills(self):
        """Import skills from hr_skills.json"""
        print("\n🎯 Importing Skills...")
        
        skills_file = DATA_SOURCE_DIR / "hr_skills.json"
        skills = load_json(skills_file)
        
        query = """
        UNWIND $skills as skill
        MERGE (s:Skill {id: skill.skill_id})
        ON CREATE SET
            s.name = skill.name,
            s.category = skill.category,
            s.description = coalesce(skill.description, '')
        ON MATCH SET
            s.name = skill.name,
            s.category = skill.category,
            s.description = coalesce(skill.description, '')
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, skills=skills)
            summary = result.consume()
        
        print(f"✅ Processed {len(skills)} skills")
        print(f"   Nodes created: {summary.counters.nodes_created}")
        print(f"   Properties set: {summary.counters.properties_set}")
    
    def import_employee_skills(self):
        """Import employee-skill relationships from hr_employee_skills.json"""
        print("\n🔗 Importing Employee-Skill Relationships...")
        
        mappings_file = DATA_SOURCE_DIR / "hr_employee_skills.json"
        mappings = load_json(mappings_file)
        
        print(f"   Total mappings to process: {len(mappings)}")
        
        # Batch process in chunks of 500
        batch_size = 500
        total_created = 0
        
        query = """
        UNWIND $mappings as mapping
        MATCH (e:Employee {id: mapping.employee_id})
        MATCH (s:Skill {id: mapping.skill_id})
        MERGE (e)-[r:HAS_SKILL]->(s)
        ON CREATE SET
            r.proficiency_level = mapping.proficiency_level,
            r.years_of_experience = toFloat(mapping.years_of_experience)
        ON MATCH SET
            r.proficiency_level = mapping.proficiency_level,
            r.years_of_experience = toFloat(mapping.years_of_experience)
        """
        
        with self.driver.session(database=self.database) as session:
            for i in range(0, len(mappings), batch_size):
                batch = mappings[i:i+batch_size]
                result = session.run(query, mappings=batch)
                summary = result.consume()
                created = summary.counters.relationships_created
                total_created += created
                
                if (i + batch_size) % 1000 == 0:
                    print(f"   Progress: {i + batch_size}/{len(mappings)} mappings processed...")
        
        print(f"✅ Processed {len(mappings)} employee-skill mappings")
        print(f"   Relationships created: {total_created}")
        print(f"   Relationships updated: {len(mappings) - total_created}")
    
    def create_manager_relationships(self):
        """Create REPORTS_TO relationships between employees and managers"""
        print("\n🔗 Creating Manager Relationships...")
        
        query = """
        MATCH (e:Employee)
        WHERE e.manager_id IS NOT NULL AND e.manager_id <> ''
        MATCH (m:Employee {id: e.manager_id})
        MERGE (e)-[:REPORTS_TO]->(m)
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            summary = result.consume()
        
        print(f"✅ Created {summary.counters.relationships_created} REPORTS_TO relationships")
    
    def verify_import(self):
        """Verify imported data"""
        print("\n🔍 Verifying import...")
        
        with self.driver.session(database=self.database) as session:
            # Count nodes
            result = session.run("MATCH (n) WHERE n:Employee OR n:Skill RETURN labels(n)[0] as type, count(*) as count")
            
            print(f"\n📊 Import Summary:")
            for record in result:
                print(f"   {record['type']}: {record['count']}")
            
            # Count relationships
            result = session.run("""
                MATCH ()-[r]->()
                WHERE type(r) IN ['HAS_SKILL', 'REPORTS_TO']
                RETURN type(r) as type, count(r) as count
            """)
            
            print(f"\n   Relationships:")
            for record in result:
                print(f"   {record['type']}: {record['count']}")
            
            # Sample data
            result = session.run("""
                MATCH (e:Employee)-[r:HAS_SKILL]->(s:Skill)
                RETURN e.name as employee, 
                       s.name as skill,
                       r.proficiency_level as level,
                       r.years_of_experience as years
                LIMIT 5
            """)
            
            print(f"\n   Sample Employee-Skill data:")
            for record in result:
                print(f"   - {record['employee']}: {record['skill']} ({record['level']}, {record['years']} years)")
    
    def import_all(self):
        """Import all HR data"""
        print("=" * 80)
        print("🚀 HR Data Import Starting...")
        print(f"📂 Data source: {DATA_SOURCE_DIR}")
        print("=" * 80)
        
        try:
            # Create indexes
            self.create_indexes()
            
            # Import entities
            self.import_employees()
            self.import_skills()
            
            # Create relationships
            self.import_employee_skills()
            self.create_manager_relationships()
            
            # Verify
            self.verify_import()
            
            print("\n" + "=" * 80)
            print("✅ HR Data Import Complete!")
            print("=" * 80)
            print("\n💡 Next steps:")
            print("   1. Test queries in Neo4j Browser")
            print("   2. Campaign team gap analysis now uses real skill data!")
            print("   3. Explore skill proficiency levels and experience")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Import failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main import function"""
    
    # Get Neo4j credentials from environment
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not all([uri, username, password]):
        print("❌ Error: Neo4j credentials not found")
        print("\nPlease ensure .env contains:")
        print("  NEO4J_URI=...")
        print("  NEO4J_USERNAME=...")
        print("  NEO4J_PASSWORD=...")
        return
    
    print(f"\n🔌 Connecting to Neo4j...")
    print(f"   URI: {uri}")
    print(f"   Database: {database}")
    
    # Create importer
    importer = HRDataImporter(uri, username, password, database)
    
    try:
        # Test connection
        print("\n🔄 Testing connection...")
        importer.driver.verify_connectivity()
        print("✅ Connection successful!")
        
        # Import data
        success = importer.import_all()
        
        if success:
            print("\n🎉 All HR data imported successfully!")
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        importer.close()

if __name__ == "__main__":
    main()
