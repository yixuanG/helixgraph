# HR-Marketing Data Integration Guide

## 📋 Overview

This document describes the integration between HR employee data and Marketing campaign/product data, enabling comprehensive cross-domain analysis and insights.

---

## 🔗 Data Relationships

### **Current Integration Status**

| Relationship | Source File | Status | Records |
|--------------|-------------|--------|---------|
| Employee → Campaign | `employee_campaign_roles.csv` | ✅ Complete | 82 |
| Employee → Product | `employee_product_expertise.csv` | ✅ Complete | 91 |
| Employee → Channel | `employee_channel_expertise.csv` | ✅ **NEW** | 25 |
| Employee → Team | `employee_team_membership.csv` | ✅ **NEW** | 29 |

---

## 📊 New Data Files

### 1. **employee_channel_expertise.csv**

**Purpose:** Maps employees to their channel and media platform expertise

**Fields:**
```
- employee_id: Employee identifier (FK to employees.csv)
- channel: Channel type (e.g., SEM, SOCIAL, DISPLAY)
- media_platform: Specific platform (e.g., Google, Instagram, Criteo)
- expertise_level: Expert / Advanced / Intermediate / Beginner
- years_experience: Years of experience with this channel/platform
- certifications: Professional certifications (if any)
```

**Sample Data:**
```csv
EMP-10015,SEM,Google,Expert,8,Google Ads Certified
EMP-10009,SOCIAL,Instagram,Expert,10,Meta Blueprint Certified
EMP-10016,DISPLAY,Criteo,Expert,6,Criteo Platform Expert
```

**Links to Marketing Data:**
- `channels_v4.json` - Channel definitions
- `campaigns_adidas_v5.csv` - Campaign channel and media_platform fields

**Use Cases:**
1. **Campaign Staffing:** Find the best person for a Google SEM campaign
2. **Skill Gap Analysis:** Identify missing channel expertise
3. **Training Needs:** Plan certification programs
4. **Workload Balancing:** Distribute campaigns based on channel expertise

**Example Queries:**
```cypher
// Find all Google SEM experts
MATCH (e:Employee)-[r:HAS_CHANNEL_EXPERTISE]->(ch:Channel)
WHERE r.media_platform = 'Google' 
  AND ch.name = 'SEM'
  AND r.expertise_level = 'Expert'
RETURN e.name, r.certifications, r.years_experience

// Find campaigns without an expert assigned
MATCH (c:Campaign {channel: 'SOCIAL', media_platform: 'TikTok'})
WHERE NOT EXISTS {
  MATCH (c)<-[:LEADS]-(e:Employee)-[r:HAS_CHANNEL_EXPERTISE]->()
  WHERE r.media_platform = 'TikTok' 
    AND r.expertise_level IN ['Expert', 'Advanced']
}
RETURN c.campaign_id, c.campaign_name
```

---

### 2. **employee_team_membership.csv**

**Purpose:** Defines employee membership in marketing teams

**Fields:**
```
- employee_id: Employee identifier
- team: Short team code (e.g., Brand Offline, Digital Performance)
- team_full_name: Full team name
- role_in_team: Employee's role within the team
- start_date: When they joined the team
- is_team_lead: Boolean indicating team leadership
- status: active / inactive / on-leave
```

**Sample Data:**
```csv
EMP-10001,Brand Marketing,Brand Marketing,VP Brand Marketing,2008-06-28,true,active
EMP-10006,Brand Offline,Brand Offline,Creative Lead,2015-12-01,true,active
EMP-10007,Digital Performance,Digital Performance,Team Lead,2018-07-20,true,active
```

**Links to Marketing Data:**
- `campaigns_adidas_v5.csv` - Campaign team field

**Use Cases:**
1. **Team Structure:** Visualize team hierarchy and composition
2. **Campaign Ownership:** Link campaigns to responsible teams
3. **Team Performance:** Analyze team-level campaign metrics
4. **Resource Planning:** Understand team capacity and allocation

**Example Queries:**
```cypher
// Get all members of Digital Performance team
MATCH (e:Employee)-[m:MEMBER_OF]->(t:Team {name: 'Digital Performance'})
RETURN e.name, m.role_in_team, m.is_team_lead
ORDER BY m.is_team_lead DESC, e.level

// Find team leads for each team
MATCH (e:Employee)-[m:MEMBER_OF {is_team_lead: true}]->(t:Team)
RETURN t.name as team, e.name as team_lead, e.email

// Campaign count by team
MATCH (c:Campaign)
MATCH (e:Employee)-[:LEADS]->(c)
MATCH (e)-[:MEMBER_OF]->(t:Team)
WHERE c.team = t.name
RETURN t.name, count(DISTINCT c) as campaign_count
ORDER BY campaign_count DESC
```

---

## 🎯 Integration Benefits

### **1. Cross-Domain Insights**

```cypher
// Complete campaign context: Employee + Team + Channel + Product
MATCH (emp:Employee)-[:LEADS]->(c:Campaign)
MATCH (emp)-[:MEMBER_OF]->(team:Team)
MATCH (emp)-[ch_exp:HAS_CHANNEL_EXPERTISE]->(channel:Channel)
MATCH (emp)-[prod_exp:HAS_PRODUCT_EXPERTISE]->(prod:Product)
WHERE c.channel = channel.name 
  AND c.hero_product = prod.name
RETURN emp.name,
       team.name,
       c.campaign_name,
       channel.name,
       ch_exp.expertise_level as channel_expertise,
       prod_exp.expertise_level as product_expertise,
       c.budget,
       c.roas
```

### **2. Skills-Based Campaign Assignment**

```cypher
// Find best-fit employee for a new Instagram campaign promoting Adizero SL
MATCH (e:Employee)
MATCH (e)-[ch:HAS_CHANNEL_EXPERTISE {media_platform: 'Instagram'}]->()
MATCH (e)-[pr:HAS_PRODUCT_EXPERTISE {hero_product: 'Adizero SL'}]->()
WHERE ch.expertise_level IN ['Expert', 'Advanced']
  AND pr.expertise_level IN ['Primary Owner', 'Specialist']
RETURN e.name, 
       ch.expertise_level,
       ch.certifications,
       pr.expertise_level,
       pr.years_experience
ORDER BY ch.years_experience DESC, pr.years_experience DESC
LIMIT 5
```

### **3. Workload Analysis**

```cypher
// Employee workload by channel
MATCH (e:Employee)-[:LEADS]->(c:Campaign)
MATCH (e)-[ch:HAS_CHANNEL_EXPERTISE]->()
WHERE c.channel = ch.channel
RETURN e.name,
       ch.channel,
       ch.expertise_level,
       count(c) as campaigns,
       sum(c.budget) as total_budget,
       avg(c.allocation_percentage) as avg_allocation
ORDER BY total_budget DESC
```

### **4. Team Performance Dashboard**

```cypher
// Team-level KPIs
MATCH (t:Team)<-[:MEMBER_OF]-(e:Employee)-[:LEADS]->(c:Campaign)
WHERE c.status = 'completed'
RETURN t.name as team,
       count(DISTINCT e) as team_size,
       count(c) as campaigns_delivered,
       sum(c.revenue) as total_revenue,
       avg(c.roas) as avg_roas,
       sum(c.conversions) as total_conversions
ORDER BY total_revenue DESC
```

---

## 📈 Recommended Future Enhancements

### **Phase 2: Medium Priority**

1. **employee_kpi_responsibility.csv**
   - Link employees to KPI ownership
   - Connect to `kpi_definitions_v0.9.json`

2. **employee_market_coverage.csv**
   - Define market/region responsibility
   - Support for multi-market campaigns

3. **employee_budget_authority.csv**
   - Detailed budget approval workflows
   - Campaign spend authorization levels

### **Phase 3: Nice to Have**

4. **employee_vendor_contacts.csv**
   - Media platform vendor relationships
   - Account manager assignments

---

## 🔄 Data Maintenance

### **Update Frequency**

| File | Update Frequency | Trigger |
|------|------------------|---------|
| employee_channel_expertise | Quarterly | New certifications, skill development |
| employee_team_membership | As needed | Organizational changes, promotions |
| employee_campaign_roles | Per campaign | Campaign launch/completion |
| employee_product_expertise | Bi-annually | Product portfolio changes |

### **Data Quality Checks**

```cypher
// Check for employees leading campaigns without channel expertise
MATCH (e:Employee)-[:LEADS]->(c:Campaign)
WHERE NOT EXISTS {
  MATCH (e)-[ch:HAS_CHANNEL_EXPERTISE]->()
  WHERE ch.channel = c.channel
}
RETURN e.name, c.campaign_name, c.channel

// Check for team leads not marked in team membership
MATCH (e:Employee {level: 'Senior'})
MATCH (e)-[m:MEMBER_OF]->(t:Team)
WHERE e.job_title CONTAINS 'Director' 
  AND m.is_team_lead = false
RETURN e.name, e.job_title, t.name

// Find campaigns with no assigned employee
MATCH (c:Campaign)
WHERE NOT EXISTS {
  MATCH (c)<-[:LEADS]-(:Employee)
}
RETURN c.campaign_id, c.campaign_name, c.team
```

---

## 📚 Related Documentation

- **HR_DATA_DOCUMENTATION.md** - HR data structure
- **campaigns_adidas_v5.csv** - Campaign data schema
- **channels_v4.json** - Channel definitions
- **kpi_definitions_v0.9.json** - KPI dictionary

---

## 🎯 Summary

**Current Status:**
- ✅ 4 HR-Marketing integration files
- ✅ 227 total relationship mappings
- ✅ Covers Employee → Campaign, Product, Channel, Team

**Key Benefits:**
1. **Skills-based staffing** - Match expertise to campaign needs
2. **Team visibility** - Clear team structure and ownership
3. **Performance analysis** - Link individual/team performance to outcomes
4. **Resource optimization** - Workload balancing and capacity planning

**Next Steps:**
1. Import new data files to Neo4j
2. Create integration queries and dashboards
3. Plan Phase 2 enhancements (KPI, Market coverage)
4. Set up data quality monitoring

---

**Last Updated:** 2025-12-03  
**Version:** 1.0  
**Author:** Data Integration Team
