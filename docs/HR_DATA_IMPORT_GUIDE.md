# HR Data Import Guide

Complete guide for validating and importing HR data to Neo4j.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Data Validation](#data-validation)
3. [Neo4j Import](#neo4j-import)
4. [Verification Queries](#verification-queries)
5. [Troubleshooting](#troubleshooting)

---

## 🎯 Prerequisites

### 1. **Environment Setup**

Ensure your `.env` file contains Neo4j credentials:

```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

### 2. **Required Data Files**

**HR Source Data** (`data/source/hr/`):
```
✅ employees.csv
✅ employee_campaign_roles.csv
✅ employee_product_expertise.csv
✅ employee_channel_expertise.csv
✅ employee_team_membership.csv
```

**HR Dictionaries** (`data/dictionaries/hr/`):
```
✅ expertise_levels.json
✅ teams.json
✅ departments.json
✅ job_levels.json
✅ employee_roles.json
```

### 3. **Python Dependencies**

```bash
pip install neo4j python-dotenv certifi
```

---

## 🔍 Data Validation

### Step 1: Run Validation Script

Before importing to Neo4j, validate your data:

```bash
python scripts/validate_hr_data.py
```

### What It Checks:

#### **1. Expertise Levels Validation**
- ✅ All expertise levels match dictionary definitions
- ✅ No invalid or misspelled levels

#### **2. Teams Validation**
- ✅ All teams exist in dictionary
- ✅ Team codes are consistent

#### **3. Departments Validation**
- ✅ All departments exist in dictionary
- ✅ Department codes match

#### **4. Job Levels Validation**
- ✅ All job levels are valid
- ✅ Level codes are consistent

#### **5. Employee Roles Validation**
- ✅ All roles match dictionary
- ✅ Role codes are valid

#### **6. Referential Integrity**
- ✅ No orphaned employee IDs
- ✅ All foreign keys are valid

#### **7. Data Completeness**
- ✅ Required fields are populated
- ✅ Coverage statistics (expertise, teams, etc.)

### Sample Output:

```
================================================================================
🔍 HR Data Validation
================================================================================

📖 Loading dictionaries...
   ✅ Loaded expertise_levels.json
   ✅ Loaded teams.json
   ✅ Loaded departments.json
   ✅ Loaded job_levels.json
   ✅ Loaded employee_roles.json

📂 Loading data files...
   ✅ Loaded employees.csv (27 records)
   ✅ Loaded employee_campaign_roles.csv (82 records)
   ✅ Loaded employee_product_expertise.csv (91 records)
   ✅ Loaded employee_channel_expertise.csv (25 records)
   ✅ Loaded employee_team_membership.csv (29 records)

✅ Expertise Levels Validation
================================================================================

💡 Info (3):
   - Valid expertise levels: Advanced, Beginner, Expert, Intermediate, Primary Owner, Specialist, Supporting
   - Channel expertise levels used: Advanced, Expert, Intermediate
   - Product expertise levels used: Primary Owner, Specialist, Supporting

✅ Teams Validation
================================================================================

💡 Info (2):
   - Valid teams: Brand Marketing, Brand Offline, Digital Brand, Digital Marketing, ...
   - Teams used: Brand Marketing, Brand Offline, Digital Brand, ...

...

================================================================================
📊 Validation Summary
================================================================================
✅ Passed: 7/7 checks
❌ Errors: 0
⚠️  Warnings: 2

🎉 All validations passed! Data is ready for import.
```

### Fix Errors Before Import

If validation fails:
1. Review error messages
2. Fix data files
3. Re-run validation
4. Continue when validation passes

---

## 🚀 Neo4j Import

### Step 1: Run Import Script

```bash
# First time import
python scripts/import_hr_to_neo4j.py

# Clear existing data and re-import
python scripts/import_hr_to_neo4j.py --clear
```

### Import Process:

#### **Phase 1: Setup** (5-10 seconds)
```
📊 Creating indexes...
   ✅ Created index for Employee.employee_id
   ✅ Created index for Employee.email
   ✅ Created index for Team.team_code
   ...
```

#### **Phase 2: Dictionary Import** (10-15 seconds)
```
📖 Importing dictionaries...
   ✅ Imported 7 expertise levels
   ✅ Imported 9 teams
   ✅ Created 4 team hierarchy relationships
   ✅ Imported 5 departments
   ✅ Imported 7 job levels
   ✅ Imported 10 employee roles
```

#### **Phase 3: Employee Data** (15-20 seconds)
```
👥 Importing employees...
   ✅ Imported 27 employees
      Nodes created: 27
      Properties set: 297
   ✅ Created 26 reporting relationships
   ✅ Created 27 department relationships
   ✅ Created 27 job level relationships
```

#### **Phase 4: Relationships** (20-30 seconds)
```
📺 Importing channel expertise...
   ✅ Imported 25 channel expertise records
      Relationships created: 25

📦 Importing product expertise...
   ✅ Imported 91 product expertise records
      Relationships created: 91

👨‍👩‍👧‍👦 Importing team membership...
   ✅ Imported 29 team membership records
      Relationships created: 29

🎯 Importing campaign roles...
   ✅ Imported 82 campaign role records
      Relationships created: 82
```

#### **Phase 5: Verification**
```
✅ Verifying import...
   Employees: 27
   Departments: 5
   Teams: 9
   Job Levels: 7
   Expertise Levels: 7
   Employee Roles: 10
   Channels: 9
   Products: 15
   Campaigns: 45
   Reporting Relationships: 26
   Team Memberships: 29
   Channel Expertise: 25
   Product Expertise: 91
   Campaign Leads: 82
```

### Sample Output:

```
================================================================================
🚀 HR Data Import to Neo4j
================================================================================

📊 Creating indexes...
   ✅ Created index
   ✅ Created index
   ...

📖 Importing dictionaries...
   Loading: expertise_levels.json
   ✅ Imported 7 expertise levels
   ...

👥 Importing employees...
   Loading: employees.csv
   ✅ Imported 27 employees
   ...

================================================================================
✅ Import Complete!
================================================================================

💡 Next steps:
   1. Visit Neo4j Browser: https://console.neo4j.io
   2. Run validation queries
   3. Explore the HR knowledge graph
```

---

## 🔎 Verification Queries

After import, run these queries in Neo4j Browser to verify data:

### 1. **Check Employee Count**

```cypher
MATCH (e:Employee)
RETURN count(e) as total_employees
```

Expected: 27 employees

---

### 2. **View Sample Employee with All Relationships**

```cypher
MATCH (e:Employee {employee_id: 'EMP-10001'})
OPTIONAL MATCH (e)-[r1:REPORTS_TO]->(manager)
OPTIONAL MATCH (e)-[r2:WORKS_IN]->(dept)
OPTIONAL MATCH (e)-[r3:HAS_JOB_LEVEL]->(level)
OPTIONAL MATCH (e)-[r4:MEMBER_OF]->(team)
OPTIONAL MATCH (e)-[r5:HAS_CHANNEL_EXPERTISE]->(channel)
OPTIONAL MATCH (e)-[r6:HAS_PRODUCT_EXPERTISE]->(product)
OPTIONAL MATCH (e)-[r7:LEADS]->(campaign)
RETURN e, manager, dept, level, 
       collect(DISTINCT team) as teams,
       collect(DISTINCT channel) as channels,
       collect(DISTINCT product) as products,
       count(DISTINCT campaign) as campaigns_count
```

---

### 3. **Team Structure**

```cypher
MATCH (t:Team)
OPTIONAL MATCH (t)-[:BELONGS_TO]->(parent:Team)
OPTIONAL MATCH (e:Employee)-[:MEMBER_OF]->(t)
RETURN t.team_name as team,
       parent.team_name as parent_team,
       count(DISTINCT e) as team_size
ORDER BY parent_team, team
```

Expected: Hierarchical team structure with member counts

---

### 4. **Channel Expertise Distribution**

```cypher
MATCH (e:Employee)-[r:HAS_CHANNEL_EXPERTISE]->(c:Channel)
RETURN c.name as channel,
       r.expertise_level as level,
       count(e) as employees
ORDER BY channel, level
```

---

### 5. **Employees Without Team Assignment**

```cypher
MATCH (e:Employee)
WHERE NOT EXISTS {
  MATCH (e)-[:MEMBER_OF]->(:Team)
}
RETURN e.employee_id, e.full_name, e.job_title
```

Expected: Empty result (all employees should have team)

---

### 6. **Campaign Coverage by Employee**

```cypher
MATCH (e:Employee)-[r:LEADS]->(c:Campaign)
RETURN e.full_name,
       count(c) as campaigns,
       sum(r.allocation_percentage) as total_allocation
ORDER BY total_allocation DESC
LIMIT 10
```

---

### 7. **Top Channel Experts**

```cypher
MATCH (e:Employee)-[r:HAS_CHANNEL_EXPERTISE]->(c:Channel)
WHERE r.expertise_level = 'Expert'
RETURN e.full_name,
       collect(c.name + ' (' + r.media_platform + ')') as channels,
       collect(r.certifications) as certifications
```

---

### 8. **Team Lead Assignment**

```cypher
MATCH (e:Employee)-[m:MEMBER_OF {is_team_lead: true}]->(t:Team)
RETURN t.team_name as team,
       e.full_name as team_lead,
       e.job_title
ORDER BY t.team_name
```

---

### 9. **Complete HR Graph Sample**

```cypher
MATCH path = (e:Employee {employee_id: 'EMP-10007'})-[*1..2]-()
RETURN path
LIMIT 100
```

Visualize the complete graph structure for one employee.

---

## 🐛 Troubleshooting

### Issue 1: Connection Error

**Error:**
```
❌ Missing Neo4j credentials in .env file
```

**Solution:**
Check `.env` file contains:
```bash
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
```

---

### Issue 2: Validation Errors

**Error:**
```
❌ Invalid expertise_level: 'Exper' for EMP-10015
```

**Solution:**
1. Check the error message
2. Fix the data file
3. Re-run validation
4. Continue when validation passes

---

### Issue 3: Orphaned References

**Error:**
```
❌ Orphaned employee IDs in channel_expertise: EMP-99999
```

**Solution:**
- Ensure employee ID exists in `employees.csv`
- Fix or remove the orphaned record

---

### Issue 4: Missing Dictionary Files

**Warning:**
```
⚠️  Missing expertise_levels.json
```

**Solution:**
Ensure all dictionary files exist in `data/dictionaries/hr/`

---

### Issue 5: Import Fails Midway

**Error:**
```
❌ Import failed: ...
```

**Solution:**
1. Check the error message
2. Fix the issue
3. Re-run import with `--clear` flag:
   ```bash
   python scripts/import_hr_to_neo4j.py --clear
   ```

---

## 📊 Data Model

### Node Types

```
Employee
├── Properties: employee_id, full_name, email, job_title, department, level
│
Department
├── Properties: department_code, department_name, description
│
Team
├── Properties: team_code, team_name, description, type
│
JobLevel
├── Properties: level_code, level_name, seniority
│
ExpertiseLevel
├── Properties: code, name, level, description
│
EmployeeRole
├── Properties: role_code, role_name, context
│
Channel
├── Properties: name, type
│
Product
├── Properties: name
│
Campaign
└── Properties: campaign_id, campaign_name
```

### Relationship Types

```
Employee -[:REPORTS_TO]-> Employee
Employee -[:WORKS_IN]-> Department
Employee -[:HAS_JOB_LEVEL]-> JobLevel
Employee -[:MEMBER_OF]-> Team
Employee -[:HAS_CHANNEL_EXPERTISE]-> Channel
Employee -[:HAS_PRODUCT_EXPERTISE]-> Product
Employee -[:LEADS]-> Campaign
Team -[:BELONGS_TO]-> Team (parent)
```

---

## 🎯 Next Steps

After successful import:

1. **✅ Run Verification Queries** - Ensure data is correct
2. **✅ Create Dashboard Queries** - Build analytics queries
3. **✅ Update API** - Connect FastAPI to new HR data
4. **✅ Document Queries** - Save useful queries for team
5. **✅ Set Up Monitoring** - Track data quality over time

---

## 📚 Related Documentation

- **validate_hr_data.py** - Validation script
- **import_hr_to_neo4j.py** - Import script
- **HR_DATA_DOCUMENTATION.md** - HR data structure
- **HR_MARKETING_DATA_INTEGRATION.md** - Integration guide
- **LABEL_STRATEGY.md** - Domain labels and metadata

---

**Last Updated:** 2025-12-03  
**Version:** 1.0  
**Maintained By:** Data Engineering Team
