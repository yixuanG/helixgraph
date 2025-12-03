"""
Validate HR data against dictionary definitions

This script validates:
1. Expertise levels match dictionary
2. Teams exist in dictionary
3. Departments exist in dictionary
4. Job levels are valid
5. Employee roles are valid
6. No orphaned references

Usage:
    python scripts/validate_hr_data.py
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Paths
BASE_DIR = Path(__file__).parent.parent
HR_SOURCE_DIR = BASE_DIR / "data" / "source" / "hr"
HR_DICT_DIR = BASE_DIR / "data" / "dictionaries" / "hr"

class ValidationResult:
    """Store validation results"""
    def __init__(self, check_name: str):
        self.check_name = check_name
        self.errors = []
        self.warnings = []
        self.info = []
        
    def add_error(self, message: str):
        self.errors.append(message)
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def add_info(self, message: str):
        self.info.append(message)
    
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    def print_results(self):
        """Print validation results"""
        status = "✅" if self.is_valid() else "❌"
        print(f"\n{status} {self.check_name}")
        print("=" * 80)
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if self.info:
            print(f"\n💡 Info ({len(self.info)}):")
            for info in self.info:
                print(f"   - {info}")


class HRDataValidator:
    """Validate HR data against dictionaries"""
    
    def __init__(self):
        self.dictionaries = {}
        self.data_files = {}
        self.results = []
        
    def load_dictionaries(self):
        """Load all HR dictionaries"""
        print("📖 Loading dictionaries...")
        
        dict_files = {
            'expertise_levels': 'expertise_levels.json',
            'teams': 'teams.json',
            'departments': 'departments.json',
            'job_levels': 'job_levels.json',
            'employee_roles': 'employee_roles.json'
        }
        
        for key, filename in dict_files.items():
            file_path = HR_DICT_DIR / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.dictionaries[key] = json.load(f)
                print(f"   ✅ Loaded {filename}")
            else:
                print(f"   ⚠️  Missing {filename}")
    
    def load_data_files(self):
        """Load HR data files"""
        print("\n📂 Loading data files...")
        
        csv_files = {
            'employees': 'employees.csv',
            'employee_campaign_roles': 'employee_campaign_roles.csv',
            'employee_product_expertise': 'employee_product_expertise.csv',
            'employee_channel_expertise': 'employee_channel_expertise.csv',
            'employee_team_membership': 'employee_team_membership.csv'
        }
        
        for key, filename in csv_files.items():
            file_path = HR_SOURCE_DIR / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.data_files[key] = list(reader)
                print(f"   ✅ Loaded {filename} ({len(self.data_files[key])} records)")
            else:
                print(f"   ⚠️  Missing {filename}")
                self.data_files[key] = []
    
    def validate_expertise_levels(self) -> ValidationResult:
        """Validate expertise levels against dictionary"""
        result = ValidationResult("Expertise Levels Validation")
        
        # Get valid levels from dictionary
        valid_levels = set()
        if 'expertise_levels' in self.dictionaries:
            valid_levels = {level['name'] for level in self.dictionaries['expertise_levels']}
            valid_levels.update({level['code'] for level in self.dictionaries['expertise_levels']})
        
        result.add_info(f"Valid expertise levels: {', '.join(sorted(valid_levels))}")
        
        # Check channel expertise
        if 'employee_channel_expertise' in self.data_files:
            levels_found = set()
            for row in self.data_files['employee_channel_expertise']:
                level = row.get('expertise_level', '').strip()
                levels_found.add(level)
                if level and level not in valid_levels:
                    result.add_error(
                        f"Invalid expertise_level in employee_channel_expertise: "
                        f"'{level}' for {row.get('employee_id')}"
                    )
            result.add_info(f"Channel expertise levels used: {', '.join(sorted(levels_found))}")
        
        # Check product expertise
        if 'employee_product_expertise' in self.data_files:
            levels_found = set()
            for row in self.data_files['employee_product_expertise']:
                level = row.get('expertise_level', '').strip()
                levels_found.add(level)
                if level and level not in valid_levels:
                    result.add_error(
                        f"Invalid expertise_level in employee_product_expertise: "
                        f"'{level}' for {row.get('employee_id')}"
                    )
            result.add_info(f"Product expertise levels used: {', '.join(sorted(levels_found))}")
        
        return result
    
    def validate_teams(self) -> ValidationResult:
        """Validate teams against dictionary"""
        result = ValidationResult("Teams Validation")
        
        # Get valid teams from dictionary
        valid_teams = set()
        if 'teams' in self.dictionaries:
            valid_teams = {team['team_code'] for team in self.dictionaries['teams']}
            valid_teams.update({team['team_name'] for team in self.dictionaries['teams']})
        
        result.add_info(f"Valid teams: {', '.join(sorted(valid_teams))}")
        
        # Check team membership
        if 'employee_team_membership' in self.data_files:
            teams_found = set()
            for row in self.data_files['employee_team_membership']:
                team = row.get('team', '').strip()
                teams_found.add(team)
                if team and team not in valid_teams:
                    result.add_error(
                        f"Invalid team in employee_team_membership: "
                        f"'{team}' for {row.get('employee_id')}"
                    )
            result.add_info(f"Teams used: {', '.join(sorted(teams_found))}")
        
        return result
    
    def validate_departments(self) -> ValidationResult:
        """Validate departments against dictionary"""
        result = ValidationResult("Departments Validation")
        
        # Get valid departments from dictionary
        valid_departments = set()
        if 'departments' in self.dictionaries:
            valid_departments = {dept['department_code'] for dept in self.dictionaries['departments']}
            valid_departments.update({dept['department_name'] for dept in self.dictionaries['departments']})
        
        result.add_info(f"Valid departments: {', '.join(sorted(valid_departments))}")
        
        # Check employees
        if 'employees' in self.data_files:
            departments_found = set()
            for row in self.data_files['employees']:
                dept = row.get('department', '').strip()
                departments_found.add(dept)
                if dept and dept not in valid_departments:
                    result.add_warning(
                        f"Department not in dictionary: '{dept}' for {row.get('employee_id')}"
                    )
            result.add_info(f"Departments used: {', '.join(sorted(departments_found))}")
        
        return result
    
    def validate_job_levels(self) -> ValidationResult:
        """Validate job levels against dictionary"""
        result = ValidationResult("Job Levels Validation")
        
        # Get valid levels from dictionary
        valid_levels = set()
        if 'job_levels' in self.dictionaries:
            valid_levels = {level['level_code'] for level in self.dictionaries['job_levels']}
            valid_levels.update({level['level_name'] for level in self.dictionaries['job_levels']})
        
        result.add_info(f"Valid job levels: {', '.join(sorted(valid_levels))}")
        
        # Check employees
        if 'employees' in self.data_files:
            levels_found = set()
            for row in self.data_files['employees']:
                level = row.get('level', '').strip()
                levels_found.add(level)
                if level and level not in valid_levels:
                    result.add_warning(
                        f"Job level not in dictionary: '{level}' for {row.get('employee_id')}"
                    )
            result.add_info(f"Job levels used: {', '.join(sorted(levels_found))}")
        
        return result
    
    def validate_employee_roles(self) -> ValidationResult:
        """Validate employee roles against dictionary"""
        result = ValidationResult("Employee Roles Validation")
        
        # Get valid roles from dictionary
        valid_roles = set()
        if 'employee_roles' in self.dictionaries:
            valid_roles = {role['role_name'] for role in self.dictionaries['employee_roles']}
            valid_roles.update({role['role_code'] for role in self.dictionaries['employee_roles']})
        
        result.add_info(f"Valid roles: {', '.join(sorted(valid_roles))}")
        
        # Check campaign roles
        if 'employee_campaign_roles' in self.data_files:
            roles_found = set()
            for row in self.data_files['employee_campaign_roles']:
                role = row.get('role', '').strip()
                roles_found.add(role)
                if role and role not in valid_roles:
                    result.add_warning(
                        f"Role not in dictionary: '{role}' for {row.get('employee_id')}"
                    )
            result.add_info(f"Campaign roles used: {', '.join(sorted(roles_found))}")
        
        # Check team roles
        if 'employee_team_membership' in self.data_files:
            roles_found = set()
            for row in self.data_files['employee_team_membership']:
                role = row.get('role_in_team', '').strip()
                roles_found.add(role)
                # Team roles might be more flexible, so just info
                if role and role not in valid_roles:
                    result.add_info(
                        f"Team role not in standard dictionary: '{role}'"
                    )
        
        return result
    
    def validate_referential_integrity(self) -> ValidationResult:
        """Validate referential integrity across files"""
        result = ValidationResult("Referential Integrity")
        
        # Get all employee IDs
        employee_ids = set()
        if 'employees' in self.data_files:
            employee_ids = {row['employee_id'] for row in self.data_files['employees']}
            result.add_info(f"Total employees: {len(employee_ids)}")
        
        # Check campaign roles
        if 'employee_campaign_roles' in self.data_files:
            orphaned = set()
            for row in self.data_files['employee_campaign_roles']:
                emp_id = row.get('employee_id', '').strip()
                if emp_id and emp_id not in employee_ids:
                    orphaned.add(emp_id)
            
            if orphaned:
                result.add_error(
                    f"Orphaned employee IDs in campaign_roles: {', '.join(sorted(orphaned))}"
                )
            else:
                result.add_info("✓ All campaign role employee IDs are valid")
        
        # Check product expertise
        if 'employee_product_expertise' in self.data_files:
            orphaned = set()
            for row in self.data_files['employee_product_expertise']:
                emp_id = row.get('employee_id', '').strip()
                if emp_id and emp_id not in employee_ids:
                    orphaned.add(emp_id)
            
            if orphaned:
                result.add_error(
                    f"Orphaned employee IDs in product_expertise: {', '.join(sorted(orphaned))}"
                )
            else:
                result.add_info("✓ All product expertise employee IDs are valid")
        
        # Check channel expertise
        if 'employee_channel_expertise' in self.data_files:
            orphaned = set()
            for row in self.data_files['employee_channel_expertise']:
                emp_id = row.get('employee_id', '').strip()
                if emp_id and emp_id not in employee_ids:
                    orphaned.add(emp_id)
            
            if orphaned:
                result.add_error(
                    f"Orphaned employee IDs in channel_expertise: {', '.join(sorted(orphaned))}"
                )
            else:
                result.add_info("✓ All channel expertise employee IDs are valid")
        
        # Check team membership
        if 'employee_team_membership' in self.data_files:
            orphaned = set()
            for row in self.data_files['employee_team_membership']:
                emp_id = row.get('employee_id', '').strip()
                if emp_id and emp_id not in employee_ids:
                    orphaned.add(emp_id)
            
            if orphaned:
                result.add_error(
                    f"Orphaned employee IDs in team_membership: {', '.join(sorted(orphaned))}"
                )
            else:
                result.add_info("✓ All team membership employee IDs are valid")
        
        return result
    
    def validate_data_completeness(self) -> ValidationResult:
        """Check for data completeness"""
        result = ValidationResult("Data Completeness")
        
        # Check employees
        if 'employees' in self.data_files:
            employees = self.data_files['employees']
            total = len(employees)
            
            # Required fields
            required_fields = ['employee_id', 'first_name', 'last_name', 'email', 'job_title', 'department']
            for field in required_fields:
                missing = sum(1 for row in employees if not row.get(field, '').strip())
                if missing > 0:
                    result.add_error(f"Missing {field} in {missing}/{total} employee records")
            
            result.add_info(f"Validated {total} employee records")
        
        # Check coverage - employees without expertise
        if 'employees' in self.data_files:
            employee_ids = {row['employee_id'] for row in self.data_files['employees']}
            
            # Channel expertise coverage
            if 'employee_channel_expertise' in self.data_files:
                with_channel = {row['employee_id'] for row in self.data_files['employee_channel_expertise']}
                without_channel = employee_ids - with_channel
                coverage = len(with_channel) / len(employee_ids) * 100
                result.add_info(f"Channel expertise coverage: {coverage:.1f}% ({len(with_channel)}/{len(employee_ids)})")
                if without_channel:
                    result.add_warning(f"{len(without_channel)} employees without channel expertise")
            
            # Product expertise coverage
            if 'employee_product_expertise' in self.data_files:
                with_product = {row['employee_id'] for row in self.data_files['employee_product_expertise']}
                without_product = employee_ids - with_product
                coverage = len(with_product) / len(employee_ids) * 100
                result.add_info(f"Product expertise coverage: {coverage:.1f}% ({len(with_product)}/{len(employee_ids)})")
                if without_product:
                    result.add_warning(f"{len(without_product)} employees without product expertise")
            
            # Team membership coverage
            if 'employee_team_membership' in self.data_files:
                with_team = {row['employee_id'] for row in self.data_files['employee_team_membership']}
                without_team = employee_ids - with_team
                coverage = len(with_team) / len(employee_ids) * 100
                result.add_info(f"Team membership coverage: {coverage:.1f}% ({len(with_team)}/{len(employee_ids)})")
                if without_team:
                    result.add_warning(f"{len(without_team)} employees without team assignment")
        
        return result
    
    def run_all_validations(self):
        """Run all validation checks"""
        print("\n" + "=" * 80)
        print("🔍 HR Data Validation")
        print("=" * 80)
        
        # Load data
        self.load_dictionaries()
        self.load_data_files()
        
        # Run validations
        self.results = [
            self.validate_expertise_levels(),
            self.validate_teams(),
            self.validate_departments(),
            self.validate_job_levels(),
            self.validate_employee_roles(),
            self.validate_referential_integrity(),
            self.validate_data_completeness()
        ]
        
        # Print results
        for result in self.results:
            result.print_results()
        
        # Summary
        total_errors = sum(len(r.errors) for r in self.results)
        total_warnings = sum(len(r.warnings) for r in self.results)
        passed = sum(1 for r in self.results if r.is_valid())
        
        print("\n" + "=" * 80)
        print("📊 Validation Summary")
        print("=" * 80)
        print(f"✅ Passed: {passed}/{len(self.results)} checks")
        print(f"❌ Errors: {total_errors}")
        print(f"⚠️  Warnings: {total_warnings}")
        
        if total_errors == 0:
            print("\n🎉 All validations passed! Data is ready for import.")
            return True
        else:
            print("\n⚠️  Please fix errors before importing to Neo4j.")
            return False


def main():
    """Main function"""
    validator = HRDataValidator()
    success = validator.run_all_validations()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
