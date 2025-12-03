"""
Import HR data and dictionaries to Neo4j

This script imports:
1. HR dictionaries (expertise levels, teams, departments, job levels, roles)
2. HR employee data (employees, expertise, team membership, campaign roles)
3. Relationships between entities

Usage:
    python scripts/import_hr_to_neo4j.py [--clear]
    
Options:
    --clear: Clear existing HR data before import
"""

import json
import csv
import os
import sys
from pathlib import Path
import certifi
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables
load_dotenv()

# SSL Fix
os.environ['SSL_CERT_FILE'] = certifi.where()

# Paths
BASE_DIR = Path(__file__).parent.parent
HR_SOURCE_DIR = BASE_DIR / "data" / "source" / "hr"
HR_DICT_DIR = BASE_DIR / "data" / "dictionaries" / "hr"


class HRNeo4jImporter:
    """Import HR data to Neo4j"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        
    def close(self):
        """Close connection"""
        self.driver.close()
    
    def load_json(self, file_path: Path) -> List[Dict]:
        """Load JSON file"""
        if not file_path.exists():
            print(f"   ⚠️  File not found: {file_path.name}")
            return []
        
        print(f"   Loading: {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_csv(self, file_path: Path) -> List[Dict]:
        """Load CSV file"""
        if not file_path.exists():
            print(f"   ⚠️  File not found: {file_path.name}")
            return []
        
        print(f"   Loading: {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    
    def clear_hr_data(self):
        """Clear existing HR data"""
        print("\n🗑️  Clearing existing HR data...")
        
        queries = [
            "MATCH (n:Employee) DETACH DELETE n",
            "MATCH (n:ExpertiseLevel) DELETE n",
            "MATCH (n:Team) DELETE n",
            "MATCH (n:Department) DELETE n",
            "MATCH (n:JobLevel) DELETE n",
            "MATCH (n:EmployeeRole) DELETE n"
        ]
        
        with self.driver.session(database=self.database) as session:
            for query in queries:
                result = session.run(query)
                summary = result.consume()
                if summary.counters.nodes_deleted > 0 or summary.counters.relationships_deleted > 0:
                    print(f"   Deleted {summary.counters.nodes_deleted} nodes, "
                          f"{summary.counters.relationships_deleted} relationships")
    
    def create_indexes(self):
        """Create indexes for HR entities"""
        print("\n📊 Creating indexes...")
        
        indexes = [
            "CREATE INDEX employee_id IF NOT EXISTS FOR (e:Employee) ON (e.employee_id)",
            "CREATE INDEX employee_email IF NOT EXISTS FOR (e:Employee) ON (e.email)",
            "CREATE INDEX expertise_level_code IF NOT EXISTS FOR (l:ExpertiseLevel) ON (l.code)",
            "CREATE INDEX team_code IF NOT EXISTS FOR (t:Team) ON (t.team_code)",
            "CREATE INDEX department_code IF NOT EXISTS FOR (d:Department) ON (d.department_code)",
            "CREATE INDEX job_level_code IF NOT EXISTS FOR (l:JobLevel) ON (l.level_code)",
            "CREATE INDEX employee_role_code IF NOT EXISTS FOR (r:EmployeeRole) ON (r.role_code)"
        ]
        
        with self.driver.session(database=self.database) as session:
            for index in indexes:
                try:
                    session.run(index)
                    print(f"   ✅ Created index")
                except Exception as e:
                    print(f"   ⚠️  Index creation: {e}")
    
    def import_dictionaries(self):
        """Import dictionary data"""
        print("\n📖 Importing dictionaries...")
        
        # Import expertise levels
        expertise_levels = self.load_json(HR_DICT_DIR / "expertise_levels.json")
        if expertise_levels:
            query = """
            UNWIND $levels as level
            MERGE (l:ExpertiseLevel {code: level.code})
            SET l.name = level.name,
                l.level = level.level,
                l.description = level.description,
                l.requirements = level.requirements,
                l.responsibilities = level.responsibilities
            """
            with self.driver.session(database=self.database) as session:
                result = session.run(query, levels=expertise_levels)
                summary = result.consume()
                print(f"   ✅ Imported {len(expertise_levels)} expertise levels")
        
        # Import teams
        teams = self.load_json(HR_DICT_DIR / "teams.json")
        if teams:
            query = """
            UNWIND $teams as team
            MERGE (t:Team {team_code: team.team_code})
            SET t.team_id = team.team_id,
                t.team_name = team.team_name,
                t.department = team.department,
                t.description = team.description,
                t.type = team.type,
                t.parent_team = team.parent_team,
                t.team_lead_role = team.team_lead_role,
                t.responsibilities = team.responsibilities,
                t.key_metrics = team.key_metrics,
                t.channels = team.channels
            """
            with self.driver.session(database=self.database) as session:
                result = session.run(query, teams=teams)
                summary = result.consume()
                print(f"   ✅ Imported {len(teams)} teams")
            
            # Create team hierarchy relationships
            query_hierarchy = """
            MATCH (child:Team)
            WHERE child.parent_team IS NOT NULL
            MATCH (parent:Team {team_code: child.parent_team})
            MERGE (child)-[:BELONGS_TO]->(parent)
            """
            with self.driver.session(database=self.database) as session:
                result = session.run(query_hierarchy)
                summary = result.consume()
                print(f"   ✅ Created {summary.counters.relationships_created} team hierarchy relationships")
        
        # Import departments
        departments = self.load_json(HR_DICT_DIR / "departments.json")
        if departments:
            query = """
            UNWIND $departments as dept
            MERGE (d:Department {department_code: dept.department_code})
            SET d.department_id = dept.department_id,
                d.department_name = dept.department_name,
                d.full_name = dept.full_name,
                d.description = dept.description,
                d.parent_department = dept.parent_department,
                d.head_role = dept.head_role,
                d.cost_center_prefix = dept.cost_center_prefix,
                d.functions = dept.functions,
                d.key_responsibilities = dept.key_responsibilities
            """
            with self.driver.session(database=self.database) as session:
                result = session.run(query, departments=departments)
                summary = result.consume()
                print(f"   ✅ Imported {len(departments)} departments")
        
        # Import job levels
        job_levels = self.load_json(HR_DICT_DIR / "job_levels.json")
        if job_levels:
            query = """
            UNWIND $levels as level
            MERGE (l:JobLevel {level_code: level.level_code})
            SET l.level_id = level.level_id,
                l.level_name = level.level_name,
                l.description = level.description,
                l.seniority = level.seniority,
                l.typical_titles = level.typical_titles,
                l.typical_experience_years = level.typical_experience_years,
                l.reports_to = level.reports_to,
                l.direct_reports = level.direct_reports,
                l.key_responsibilities = level.key_responsibilities,
                l.signing_authority_min = level.signing_authority_range.min_eur,
                l.signing_authority_max = level.signing_authority_range.max_eur,
                l.skills_required = level.skills_required
            """
            with self.driver.session(database=self.database) as session:
                result = session.run(query, levels=job_levels)
                summary = result.consume()
                print(f"   ✅ Imported {len(job_levels)} job levels")
        
        # Import employee roles
        employee_roles = self.load_json(HR_DICT_DIR / "employee_roles.json")
        if employee_roles:
            query = """
            UNWIND $roles as role
            MERGE (r:EmployeeRole {role_code: role.role_code})
            SET r.role_id = role.role_id,
                r.role_name = role.role_name,
                r.context = role.context,
                r.description = role.description,
                r.responsibilities = role.responsibilities,
                r.typical_allocation_percentage = role.typical_allocation_percentage,
                r.decision_authority = role.decision_authority,
                r.accountability_level = role.accountability_level
            """
            with self.driver.session(database=self.database) as session:
                result = session.run(query, roles=employee_roles)
                summary = result.consume()
                print(f"   ✅ Imported {len(employee_roles)} employee roles")
    
    def import_employees(self):
        """Import employee data"""
        print("\n👥 Importing employees...")
        
        employees = self.load_csv(HR_SOURCE_DIR / "employees.csv")
        if not employees:
            return
        
        query = """
        UNWIND $employees as emp
        MERGE (e:Employee {employee_id: emp.employee_id})
        SET e.first_name = emp.first_name,
            e.last_name = emp.last_name,
            e.full_name = emp.first_name + ' ' + emp.last_name,
            e.email = emp.email,
            e.job_title = emp.job_title,
            e.department = emp.department,
            e.level = emp.level,
            e.reports_to = emp.reports_to,
            e.location = emp.location,
            e.hiring_date = emp.hiring_date,
            e.signing_authority_eur = toInteger(emp.signing_authority_eur),
            e.cost_center = emp.cost_center
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, employees=employees)
            summary = result.consume()
            print(f"   ✅ Imported {len(employees)} employees")
            print(f"      Nodes created: {summary.counters.nodes_created}")
            print(f"      Properties set: {summary.counters.properties_set}")
        
        # Create reporting relationships
        query_reports_to = """
        MATCH (e:Employee)
        WHERE e.reports_to IS NOT NULL AND e.reports_to <> ''
        MATCH (manager:Employee {employee_id: e.reports_to})
        MERGE (e)-[:REPORTS_TO]->(manager)
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query_reports_to)
            summary = result.consume()
            print(f"   ✅ Created {summary.counters.relationships_created} reporting relationships")
        
        # Link to departments
        query_departments = """
        MATCH (e:Employee)
        WHERE e.department IS NOT NULL
        MATCH (d:Department)
        WHERE d.department_code = e.department OR d.department_name = e.department
        MERGE (e)-[:WORKS_IN]->(d)
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query_departments)
            summary = result.consume()
            if summary.counters.relationships_created > 0:
                print(f"   ✅ Created {summary.counters.relationships_created} department relationships")
        
        # Link to job levels
        query_job_levels = """
        MATCH (e:Employee)
        WHERE e.level IS NOT NULL
        MATCH (l:JobLevel)
        WHERE l.level_code = e.level OR l.level_name = e.level
        MERGE (e)-[:HAS_JOB_LEVEL]->(l)
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query_job_levels)
            summary = result.consume()
            if summary.counters.relationships_created > 0:
                print(f"   ✅ Created {summary.counters.relationships_created} job level relationships")
    
    def import_channel_expertise(self):
        """Import employee channel expertise"""
        print("\n📺 Importing channel expertise...")
        
        expertise = self.load_csv(HR_SOURCE_DIR / "employee_channel_expertise.csv")
        if not expertise:
            return
        
        query = """
        UNWIND $expertise as exp
        MATCH (e:Employee {employee_id: exp.employee_id})
        MERGE (e)-[r:HAS_CHANNEL_EXPERTISE {
            channel: exp.channel,
            media_platform: exp.media_platform
        }]->(ch:Channel {name: exp.channel})
        ON CREATE SET
            ch.type = CASE 
                WHEN exp.channel IN ['TV', 'OOH', 'DOOH'] THEN 'Offline'
                ELSE 'Digital'
            END
        SET r.expertise_level = exp.expertise_level,
            r.years_experience = toInteger(exp.years_experience),
            r.certifications = exp.certifications
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, expertise=expertise)
            summary = result.consume()
            print(f"   ✅ Imported {len(expertise)} channel expertise records")
            print(f"      Relationships created: {summary.counters.relationships_created}")
    
    def import_product_expertise(self):
        """Import employee product expertise"""
        print("\n📦 Importing product expertise...")
        
        expertise = self.load_csv(HR_SOURCE_DIR / "employee_product_expertise.csv")
        if not expertise:
            return
        
        query = """
        UNWIND $expertise as exp
        MATCH (e:Employee {employee_id: exp.employee_id})
        MERGE (p:Product {name: exp.hero_product})
        MERGE (e)-[r:HAS_PRODUCT_EXPERTISE]->(p)
        SET r.expertise_level = exp.expertise_level,
            r.years_experience = toInteger(exp.years_experience)
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, expertise=expertise)
            summary = result.consume()
            print(f"   ✅ Imported {len(expertise)} product expertise records")
            print(f"      Relationships created: {summary.counters.relationships_created}")
    
    def import_team_membership(self):
        """Import employee team membership"""
        print("\n👨‍👩‍👧‍👦 Importing team membership...")
        
        memberships = self.load_csv(HR_SOURCE_DIR / "employee_team_membership.csv")
        if not memberships:
            return
        
        query = """
        UNWIND $memberships as mem
        MATCH (e:Employee {employee_id: mem.employee_id})
        MATCH (t:Team)
        WHERE t.team_code = mem.team OR t.team_name = mem.team
        MERGE (e)-[r:MEMBER_OF]->(t)
        SET r.role_in_team = mem.role_in_team,
            r.start_date = mem.start_date,
            r.is_team_lead = CASE WHEN mem.is_team_lead = 'true' THEN true ELSE false END,
            r.status = mem.status
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, memberships=memberships)
            summary = result.consume()
            print(f"   ✅ Imported {len(memberships)} team membership records")
            print(f"      Relationships created: {summary.counters.relationships_created}")
    
    def import_campaign_roles(self):
        """Import employee campaign roles"""
        print("\n🎯 Importing campaign roles...")
        
        roles = self.load_csv(HR_SOURCE_DIR / "employee_campaign_roles.csv")
        if not roles:
            return
        
        query = """
        UNWIND $roles as role
        MATCH (e:Employee {employee_id: role.employee_id})
        MERGE (c:Campaign {campaign_id: role.campaign_id})
        MERGE (e)-[r:LEADS]->(c)
        SET r.role = role.role,
            r.responsibility = role.responsibility,
            r.allocation_percentage = toInteger(role.allocation_percentage)
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, roles=roles)
            summary = result.consume()
            print(f"   ✅ Imported {len(roles)} campaign role records")
            print(f"      Relationships created: {summary.counters.relationships_created}")
    
    def verify_import(self):
        """Verify the import"""
        print("\n✅ Verifying import...")
        
        queries = {
            "Employees": "MATCH (e:Employee) RETURN count(e) as count",
            "Departments": "MATCH (d:Department) RETURN count(d) as count",
            "Teams": "MATCH (t:Team) RETURN count(t) as count",
            "Job Levels": "MATCH (l:JobLevel) RETURN count(l) as count",
            "Expertise Levels": "MATCH (l:ExpertiseLevel) RETURN count(l) as count",
            "Employee Roles": "MATCH (r:EmployeeRole) RETURN count(r) as count",
            "Channels": "MATCH (c:Channel) RETURN count(c) as count",
            "Products": "MATCH (p:Product) RETURN count(p) as count",
            "Campaigns": "MATCH (c:Campaign) RETURN count(c) as count",
            "Reporting Relationships": "MATCH ()-[r:REPORTS_TO]->() RETURN count(r) as count",
            "Team Memberships": "MATCH ()-[r:MEMBER_OF]->() RETURN count(r) as count",
            "Channel Expertise": "MATCH ()-[r:HAS_CHANNEL_EXPERTISE]->() RETURN count(r) as count",
            "Product Expertise": "MATCH ()-[r:HAS_PRODUCT_EXPERTISE]->() RETURN count(r) as count",
            "Campaign Leads": "MATCH ()-[r:LEADS]->() RETURN count(r) as count"
        }
        
        with self.driver.session(database=self.database) as session:
            for name, query in queries.items():
                result = session.run(query)
                count = result.single()['count']
                print(f"   {name}: {count}")
    
    def import_all(self, clear_first: bool = False):
        """Import all HR data"""
        print("\n" + "=" * 80)
        print("🚀 HR Data Import to Neo4j")
        print("=" * 80)
        
        try:
            # Clear if requested
            if clear_first:
                self.clear_hr_data()
            
            # Create indexes
            self.create_indexes()
            
            # Import dictionaries first
            self.import_dictionaries()
            
            # Import employee data
            self.import_employees()
            self.import_channel_expertise()
            self.import_product_expertise()
            self.import_team_membership()
            self.import_campaign_roles()
            
            # Verify
            self.verify_import()
            
            print("\n" + "=" * 80)
            print("✅ Import Complete!")
            print("=" * 80)
            print("\n💡 Next steps:")
            print("   1. Visit Neo4j Browser: https://console.neo4j.io")
            print("   2. Run validation queries")
            print("   3. Explore the HR knowledge graph")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Import failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function"""
    # Check for --clear flag
    clear_first = '--clear' in sys.argv
    
    # Get Neo4j credentials
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not all([uri, user, password]):
        print("❌ Missing Neo4j credentials in .env file")
        print("   Required: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        return 1
    
    # Run import
    importer = HRNeo4jImporter(uri, user, password, database)
    try:
        success = importer.import_all(clear_first=clear_first)
        return 0 if success else 1
    finally:
        importer.close()


if __name__ == "__main__":
    exit(main())
