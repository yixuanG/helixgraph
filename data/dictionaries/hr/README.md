# HR Data Dictionaries

This folder contains standardized definitions and metadata for HR-related entities and attributes.

## 📁 Dictionary Files

### 1. **expertise_levels.json**
Defines the standardized expertise levels used across employee skill assessments.

**Levels:**
- **Primary Owner** (Level 1) - Full ownership and decision-making authority
- **Expert** (Level 2) - Advanced practitioner, can lead complex initiatives
- **Specialist** (Level 3) - Focused expertise in specific area
- **Advanced** (Level 4) - Working knowledge, growing expertise
- **Intermediate** (Level 5) - Foundational knowledge, guided execution
- **Supporting** (Level 6) - Awareness, ability to assist
- **Beginner** (Level 7) - Minimal experience, learning phase

**Usage:**
- `employee_channel_expertise.csv` - expertise_level field
- `employee_product_expertise.csv` - expertise_level field
- NER model training for SKILL entity recognition
- Performance reviews and skill assessments

---

### 2. **teams.json**
Defines the marketing team structure, hierarchy, and responsibilities.

**Team Hierarchy:**
```
Marketing Leadership (MKT-000)
├── Brand Marketing (MKT-100)
│   └── Brand Offline (MKT-110)
├── Performance Marketing (MKT-200)
│   └── Digital Performance (MKT-210)
├── Digital Marketing (MKT-300)
│   └── Digital Brand (MKT-310)
└── Trade Marketing (MKT-400)
    └── Retail Marketing (MKT-410)
```

**Fields:**
- team_id, team_code, team_name
- description, type, parent_team
- team_lead_role
- responsibilities, key_metrics
- channels (applicable channels)

**Usage:**
- `employee_team_membership.csv` - team field
- `campaigns_adidas_v5.csv` - team field mapping
- Organizational structure visualization
- Team performance analysis

---

### 3. **departments.json**
Defines departments and their functions within the organization.

**Departments:**
- **Marketing (MKT)** - Parent department
  - Brand Marketing (MKT-BRD)
  - Performance Marketing (MKT-PRF)
  - Digital Marketing (MKT-DIG)
  - Trade Marketing (MKT-TRD)

**Fields:**
- department_id, department_code, department_name
- description, parent_department
- head_role, cost_center_prefix
- functions, key_responsibilities
- typical_roles

**Usage:**
- `employees.csv` - department field
- Cost center allocation
- Budget planning and tracking
- Organizational reporting

---

### 4. **job_levels.json**
Defines job levels, seniority hierarchy, and associated attributes.

**Levels:**
1. **C-Level Executive** - Top executive leadership (CMO, CEO, etc.)
2. **Vice President (VP)** - Senior functional leadership
3. **Senior Director** - Senior domain management
4. **Director** - Specialty area management
5. **Senior Manager** - Experienced execution
6. **Manager** - Campaign/project execution
7. **Specialist** - Tactical execution

**Fields:**
- level_id, level_code, level_name
- seniority, typical_titles
- typical_experience_years
- reports_to, direct_reports
- key_responsibilities
- signing_authority_range
- skills_required

**Usage:**
- `employees.csv` - level field
- Signing authority validation
- Career progression planning
- Compensation benchmarking

---

### 5. **employee_roles.json**
Defines roles that employees can have in different contexts (campaigns, teams, channels, products).

**Role Types by Context:**

**Campaign Roles:**
- Campaign Lead - Primary campaign responsibility
- Campaign Support - Supporting campaign execution

**Team Roles:**
- Team Lead - Team leadership
- Team Member - Contributing member

**Channel Roles:**
- Channel Owner - Primary channel ownership
- Channel Specialist - Channel expertise

**Product Roles:**
- Product Owner - Product marketing ownership
- Product Specialist - Product expertise

**Functional Roles:**
- Creative Lead - Creative strategy and execution
- Analytics Lead - Analytics and insights

**Fields:**
- role_id, role_code, role_name
- context (Campaign/Team/Channel/Product)
- description, responsibilities
- typical_allocation_percentage
- decision_authority, accountability_level

**Usage:**
- `employee_campaign_roles.csv` - role field
- `employee_team_membership.csv` - role_in_team field
- Workload allocation analysis
- Responsibility clarity

---

## 🔗 Integration with Data Files

### HR Source Data
```
data/source/hr/
├── employees.csv                     → departments.json, job_levels.json
├── employee_campaign_roles.csv       → employee_roles.json
├── employee_product_expertise.csv    → expertise_levels.json
├── employee_channel_expertise.csv    → expertise_levels.json
└── employee_team_membership.csv      → teams.json, employee_roles.json
```

### Marketing Data
```
data/processed/marketing/
├── campaigns_adidas_v5.csv          → teams.json
└── products_v6.csv                  → (future: product_portfolio.json)

data/dictionaries/marketing/
├── channels_v4.json                 → employee_channel_expertise.csv
├── kpi_definitions_v0.9.json        → (future: employee_kpi_responsibility.csv)
└── objectives_dictionary_v0.9.json  → campaigns
```

---

## 📊 Data Validation

These dictionaries enable data quality checks:

```cypher
// Check if all expertise levels in data exist in dictionary
MATCH (e:Employee)-[r:HAS_CHANNEL_EXPERTISE]->()
WHERE NOT r.expertise_level IN [
  'Primary Owner', 'Expert', 'Specialist', 'Advanced', 
  'Intermediate', 'Supporting', 'Beginner'
]
RETURN DISTINCT r.expertise_level

// Check if all teams in data exist in dictionary
MATCH (e:Employee)-[m:MEMBER_OF]->(t:Team)
WITH collect(DISTINCT t.name) as data_teams
MATCH (dict:TeamDictionary)
WHERE NOT dict.team_code IN data_teams
RETURN dict.team_code as missing_team
```

---

## 🎯 NER Model Integration

These dictionaries support NER model entity recognition:

### Entity Types Supported:
- **ROLE** - Job titles and roles from job_levels.json and employee_roles.json
- **SKILL** - Expertise areas (channels, products, domains)
- **DEPARTMENT** - From departments.json
- **TEAM** - From teams.json

### Entity Extraction:
```python
# Example: Extract all job titles for NER training
import json

with open('data/dictionaries/hr/job_levels.json') as f:
    levels = json.load(f)

job_titles = []
for level in levels:
    job_titles.extend(level['typical_titles'])

# Use for NER annotation: ["Chief Marketing Officer (CMO)", "ROLE"]
```

---

## 🔄 Maintenance

### Update Frequency:
- **expertise_levels.json** - Annually (stable definitions)
- **teams.json** - Quarterly (organizational changes)
- **departments.json** - Annually (stable structure)
- **job_levels.json** - Annually (career framework updates)
- **employee_roles.json** - As needed (new role types)

### Version Control:
- All dictionaries should be versioned when significant changes occur
- Use semantic versioning in filenames when needed (e.g., `teams_v2.json`)
- Document changes in git commit messages

---

## 📚 Related Documentation

- **../HR_DATA_DOCUMENTATION.md** - HR data file documentation
- **../../docs/HR_MARKETING_DATA_INTEGRATION.md** - Integration guide
- **../../HR_MARKETING_INTEGRATION_SUMMARY.md** - Integration summary

---

**Last Updated:** 2025-12-03  
**Version:** 1.0  
**Maintained By:** HR & Data Team
