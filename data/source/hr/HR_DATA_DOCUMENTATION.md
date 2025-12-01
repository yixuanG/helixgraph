# Adidas Germany Marketing Department - HR Data Documentation

## Overview
This dataset contains realistic employee data for Adidas Germany HQ marketing department, designed for Neo4j graph database integration.

**Generated on:** December 1, 2025  
**Location:** `data/source/hr/`  
**Total Employees:** 25 (focused on Senior+ with signing authority)

---

## Files Generated

### 1. `employees.csv` (25 records)
Core employee information with organizational hierarchy.

**Schema:**
```
- employee_id: string (Primary Key, format: EMP-XXXXX)
- first_name: string (German names)
- last_name: string (German surnames)
- email: string (format: firstname.lastname@adidas.com)
- job_title: string (from CMO to Senior Managers)
- department: string (Brand, Performance, Digital, Trade, Leadership)
- level: string (Executive, Senior, Mid-level)
- reports_to: string (employee_id of manager, empty for CMO)
- location: string (Herzogenaurach, Germany)
- hiring_date: date (YYYY-MM-DD, realistic 2-20 years tenure)
- signing_authority_eur: integer (€75K to €5M based on level)
- cost_center: string (format: MKT-XXX)
```

**Key Features:**
- Realistic German names (Müller, Schmidt, Werner, etc.)
- Complete organizational hierarchy from CMO to Senior Managers
- Signing authority levels for procurement approval workflows
- 4 main departments: Brand, Performance, Digital, Trade Marketing

### 2. `employee_campaign_roles.csv` (714 records)
Links employees to marketing campaigns with defined roles.

**Schema:**
```
- employee_id: string (Foreign Key → employees.employee_id)
- campaign_id: string (Foreign Key → campaigns_adidas_v3.csv)
- role: string (Campaign Lead, Budget Owner, Approver, etc.)
- responsibility: string (description of duties)
- allocation_percentage: integer (% time allocated to campaign)
```

**Relationship Logic:**
- **Campaign Lead:** Assigned based on channel expertise
  - Social Media experts → Social campaigns
  - Search experts → Google Ads campaigns
  - E-commerce experts → Amazon campaigns
- **Budget Owner:** Directors/Senior Managers with sufficient signing authority
- **Approver:** VPs/Senior Directors for campaigns >€1M

**Example Graph Queries:**
```cypher
// Find who manages a specific campaign
MATCH (e:Employee)-[r:MANAGES_CAMPAIGN]->(c:Campaign {id: 'adi_012025_006'})
RETURN e.first_name, e.last_name, r.role, r.responsibility

// Find all campaigns a person manages
MATCH (e:Employee {employee_id: 'EMP-10020'})-[r:MANAGES_CAMPAIGN]->(c:Campaign)
RETURN c.campaign_name, r.role, r.allocation_percentage
```

### 3. `employee_product_expertise.csv` (4 records)
Maps employees to Adidas product expertise.

**Schema:**
```
- employee_id: string (Foreign Key → employees.employee_id)
- product_sku: string (Foreign Key → adidas_products.json)
- expertise_level: string (Primary Owner, Specialist, Supporting)
- years_experience: integer (2-10 years)
```

**Relationship Logic:**
- Product Marketing Directors assigned to relevant product categories
- Footwear experts → Running/Football shoes
- Apparel experts → Jersey/Clothing products

---

## Organizational Structure

```
CMO (Tobias Wolf) - €5M signing authority
├── VP Brand Marketing (Katharina Werner) - €2M
│   ├── Senior Director Brand Strategy (Lukas Lehmann) - €750K
│   │   ├── Director Product Marketing - Footwear (Matthias Becker) - €400K
│   │   │   ├── Senior Marketing Manager - Running (Katrin Fuchs) - €150K
│   │   │   └── Senior Marketing Manager - Football (Barbara Köhler) - €150K
│   │   └── Director Product Marketing - Apparel (Andrea Schmitt) - €400K
│   └── Senior Director Creative (Wolfgang Hartmann) - €750K
│       ├── Senior Campaign Manager (Lukas Kaiser) - €200K
│       └── Senior Campaign Manager (Lukas Koch) - €200K
├── VP Performance Marketing (Daniel Neumann) - €2M
│   ├── Senior Director Paid Media (Anna Herrmann) - €1M
│   │   ├── Director Search Marketing (Laura Schwarz) - €600K
│   │   ├── Director Display & Programmatic (Bernd Zimmermann) - €500K
│   │   └── Senior Paid Social Manager (Jan Köhler) - €250K
│   └── Senior Director Marketing Analytics (Sebastian Meier) - €500K
│       └── Senior Marketing Analytics Manager (Sebastian Schröder) - €75K
├── VP Digital Marketing (Melanie Werner) - €2M
│   ├── Senior Director Social Media (Petra Lehmann) - €800K
│   │   ├── Director Influencer Marketing (Stefanie Koch) - €500K
│   │   └── Senior Content Manager (Katharina Meier) - €100K
│   └── Senior Director E-Commerce Marketing (Nina Meyer) - €800K
│       └── Senior E-Commerce Manager (Christina Maier) - €150K
└── VP Trade Marketing (Katharina Schwarz) - €1.5M
    └── Senior Director Retail Marketing (Claudia Köhler) - €600K
```

**Total Headcount by Level:**
- Executive: 1 (CMO)
- Senior: 16 (VPs, Senior Directors, Directors)
- Mid-level: 8 (Senior Managers)

---

## Neo4j Graph Database Integration

### Recommended Node Structure

```cypher
// Create Employee nodes
LOAD CSV WITH HEADERS FROM 'file:///employees.csv' AS row
CREATE (e:Employee {
  employee_id: row.employee_id,
  first_name: row.first_name,
  last_name: row.last_name,
  email: row.email,
  job_title: row.job_title,
  department: row.department,
  level: row.level,
  location: row.location,
  hiring_date: date(row.hiring_date),
  signing_authority_eur: toInteger(row.signing_authority_eur),
  cost_center: row.cost_center
});

// Create reporting relationships (REPORTS_TO)
LOAD CSV WITH HEADERS FROM 'file:///employees.csv' AS row
MATCH (e:Employee {employee_id: row.employee_id})
MATCH (m:Employee {employee_id: row.reports_to})
WHERE row.reports_to <> ''
CREATE (e)-[:REPORTS_TO]->(m);

// Create employee-campaign relationships
LOAD CSV WITH HEADERS FROM 'file:///employee_campaign_roles.csv' AS row
MATCH (e:Employee {employee_id: row.employee_id})
MATCH (c:Campaign {id: row.campaign_id})
CREATE (e)-[:MANAGES_CAMPAIGN {
  role: row.role,
  responsibility: row.responsibility,
  allocation_percentage: toInteger(row.allocation_percentage)
}]->(c);

// Create employee-product expertise
LOAD CSV WITH HEADERS FROM 'file:///employee_product_expertise.csv' AS row
MATCH (e:Employee {employee_id: row.employee_id})
MATCH (p:Product {sku: row.product_sku})
CREATE (e)-[:EXPERT_IN {
  expertise_level: row.expertise_level,
  years_experience: toInteger(row.years_experience)
}]->(p);
```

### Graph Relationships

**Node Types:**
- `Employee` - Marketing department staff

**Relationship Types:**
1. `REPORTS_TO` (Employee → Employee)
   - Properties: none
   - Purpose: Organizational hierarchy

2. `MANAGES_CAMPAIGN` (Employee → Campaign)
   - Properties: role, responsibility, allocation_percentage
   - Purpose: Campaign ownership and involvement

3. `EXPERT_IN` (Employee → Product)
   - Properties: expertise_level, years_experience
   - Purpose: Product category expertise

4. `APPROVES_PO` (Employee → PO) *[Future]*
   - Properties: approval_date, approval_amount
   - Purpose: Procurement authorization based on signing_authority

---

## Integration with Existing Data

### Links to Marketing Campaigns
The `employee_campaign_roles.csv` references campaign IDs from:
- **File:** `data/source/marketing/campaigns_adidas_v3.csv`
- **Matched:** 364 campaigns
- **Relationships:** 714 employee-campaign links

**Channel Expertise Mapping:**
- Paid Media Directors → Google Ads, Bing Ads, Display campaigns
- Social Media Directors → Meta, TikTok, LinkedIn campaigns
- E-Commerce Managers → Amazon, Marketplace campaigns

### Links to Products
The `employee_product_expertise.csv` references product SKUs from:
- **File:** `data/source/marketing/adidas_products.json`
- **Product experts:** Product Marketing Directors and Category Managers

### Links to Procurement (Future)
Employees with `signing_authority_eur` can approve Purchase Orders:
```cypher
// Find who can approve a €500K PO
MATCH (e:Employee)
WHERE e.signing_authority_eur >= 500000
RETURN e.first_name, e.last_name, e.job_title, e.signing_authority_eur
ORDER BY e.signing_authority_eur DESC
```

---

## Use Cases for Graph Queries

### 1. Campaign Approval Workflow
```cypher
// Who needs to approve a €2M campaign?
MATCH (e:Employee)
WHERE e.signing_authority_eur >= 2000000
RETURN e.job_title, e.first_name, e.last_name, e.email
ORDER BY e.signing_authority_eur ASC
LIMIT 1
```

### 2. Find Campaign Lead
```cypher
// Who is leading campaign X?
MATCH (e:Employee)-[r:MANAGES_CAMPAIGN {role: 'Campaign Lead'}]->(c:Campaign {id: 'adi_012025_006'})
RETURN e.first_name + ' ' + e.last_name AS campaign_lead, e.email
```

### 3. Department Budget Capacity
```cypher
// Total signing authority by department
MATCH (e:Employee)
RETURN e.department, SUM(e.signing_authority_eur) AS total_authority
ORDER BY total_authority DESC
```

### 4. Find Manager Chain
```cypher
// Get reporting chain for an employee
MATCH path = (e:Employee {employee_id: 'EMP-10020'})-[:REPORTS_TO*]->(cmo:Employee)
WHERE cmo.job_title CONTAINS 'CMO'
RETURN [node IN nodes(path) | node.job_title] AS reporting_chain
```

### 5. Campaign Workload
```cypher
// Find employees with >200% allocation (overworked)
MATCH (e:Employee)-[r:MANAGES_CAMPAIGN]->(c:Campaign)
WITH e, SUM(r.allocation_percentage) AS total_allocation
WHERE total_allocation > 200
RETURN e.first_name, e.last_name, e.job_title, total_allocation
ORDER BY total_allocation DESC
```

### 6. Cross-Domain Query Example
```cypher
// Find suppliers used by campaigns managed by a specific employee
MATCH (e:Employee {employee_id: 'EMP-10020'})-[:MANAGES_CAMPAIGN]->(c:Campaign)
MATCH (c)-[:FUNDED]->(po:PO)-[:BILLED_BY]->(s:Supplier)
RETURN DISTINCT s.name, COUNT(po) AS num_pos, SUM(po.amount) AS total_spend
ORDER BY total_spend DESC
```

---

## Data Quality Notes

### Realistic German Context
- ✅ German first names and surnames from common German naming conventions
- ✅ All employees based in Herzogenaurach (Adidas HQ location)
- ✅ Corporate email format matching Adidas standard
- ✅ Realistic hire dates (2-20 years tenure distribution)

### Signing Authority Levels
Based on typical German corporate authorization limits:
- **CMO:** €5M (Board-level decisions)
- **VPs:** €1.5M - €2M (Strategic campaigns)
- **Senior Directors:** €500K - €1M (Major initiatives)
- **Directors:** €400K - €600K (Departmental budgets)
- **Senior Managers:** €75K - €250K (Tactical execution)

### Department Distribution
- Brand Marketing: 36% (9 employees) - Largest team
- Performance Marketing: 28% (7 employees)
- Digital Marketing: 24% (6 employees)
- Trade Marketing: 8% (2 employees)
- Marketing Leadership: 4% (1 employee - CMO)

---

## Next Steps

### 1. Load into Neo4j
Use the Cypher scripts above or create an ETL script:
```bash
python etl/load_hr_data.py
```

### 2. Create Indexes
```cypher
CREATE INDEX employee_id_index FOR (e:Employee) ON (e.employee_id);
CREATE INDEX employee_email_index FOR (e:Employee) ON (e.email);
CREATE INDEX employee_department_index FOR (e:Employee) ON (e.department);
```

### 3. Validate Relationships
```cypher
// Check all employees have a manager (except CMO)
MATCH (e:Employee)
WHERE NOT (e)-[:REPORTS_TO]->() AND NOT e.job_title CONTAINS 'CMO'
RETURN e.employee_id, e.job_title
```

### 4. Build Approval Workflows
Create logic to route PO approvals based on:
- Campaign budget vs. employee signing authority
- Department alignment
- Reporting hierarchy

---

## Contact & Maintenance

**Generator Script:** `data/raw/hr_data_generator.py`  
**Regenerate Data:** `cd data/raw && python hr_data_generator.py`

**Notes:**
- Data is randomized on each generation
- Campaign relationships based on actual campaign data
- Adjust ORG_STRUCTURE in generator script to modify org chart
- Add more CHANNEL_EXPERTISE mappings for better campaign matching

---

**Version:** 1.0  
**Last Updated:** December 1, 2025  
**Author:** HR Data Generator Script
