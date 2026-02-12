#!/usr/bin/env python3
"""
Auto-generate README documentation from infrastructure code
This script scans Terraform files, workflows, and configurations to create
comprehensive, always up-to-date documentation.
"""

import os
import re
import yaml
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class ReadmeGenerator:
    def __init__(self, project_root="eks-multi-service"):
        self.project_root = Path(project_root)
        self.terraform_root = self.project_root / "terraform"
        self.workflows_dir = self.project_root / ".github" / "workflows"
        self.data = defaultdict(dict)

    def scan_terraform_environments(self):
        """Scan all Terraform environment configurations"""
        envs = {}
        env_dir = self.terraform_root / "environments"

        if env_dir.exists():
            for env in env_dir.iterdir():
                if env.is_dir():
                    env_config = self._parse_tfvars(env / "terraform.tfvars")
                    envs[env.name] = env_config

        self.data['environments'] = envs
        return envs

    def scan_terraform_modules(self):
        """Scan all Terraform modules"""
        modules = {}
        modules_dir = self.terraform_root / "modules"

        if modules_dir.exists():
            for module in modules_dir.iterdir():
                if module.is_dir():
                    module_info = self._parse_module(module)
                    modules[module.name] = module_info

        self.data['modules'] = modules
        return modules

    def scan_workflows(self):
        """Scan GitHub Actions workflows"""
        workflows = {}

        if self.workflows_dir.exists():
            for workflow_file in self.workflows_dir.glob("*.yml"):
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow = yaml.safe_load(f)
                    workflows[workflow_file.stem] = {
                        'name': workflow.get('name', 'Unknown'),
                        'triggers': list(workflow.get('on', {}).keys()),
                        'jobs': list(workflow.get('jobs', {}).keys())
                    }

        self.data['workflows'] = workflows
        return workflows

    def _parse_tfvars(self, tfvars_file):
        """Parse terraform.tfvars file"""
        config = {}
        if not tfvars_file.exists():
            return config

        with open(tfvars_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # Parse simple key-value pairs
            for line in content.split('\n'):
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    config[key] = value

        return config

    def _parse_module(self, module_dir):
        """Parse Terraform module information"""
        info = {
            'variables': [],
            'outputs': [],
            'resources': []
        }

        # Parse variables
        variables_file = module_dir / "variables.tf"
        if variables_file.exists():
            info['variables'] = self._extract_variables(variables_file)

        # Parse outputs
        outputs_file = module_dir / "outputs.tf"
        if outputs_file.exists():
            info['outputs'] = self._extract_outputs(outputs_file)

        # Parse main.tf for resources
        main_file = module_dir / "main.tf"
        if main_file.exists():
            info['resources'] = self._extract_resources(main_file)

        return info

    def _extract_variables(self, file_path):
        """Extract variable definitions"""
        variables = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

            # Find variable blocks
            var_pattern = r'variable\s+"([^"]+)"\s*{([^}]+)}'
            matches = re.finditer(var_pattern, content, re.DOTALL)

            for match in matches:
                var_name = match.group(1)
                var_block = match.group(2)

                desc_match = re.search(
                    r'description\s*=\s*"([^"]+)"', var_block)
                type_match = re.search(r'type\s*=\s*(\w+)', var_block)
                default_match = re.search(r'default\s*=\s*([^\n]+)', var_block)

                variables.append({
                    'name': var_name,
                    'description': desc_match.group(1) if desc_match else '',
                    'type': type_match.group(1) if type_match else 'string',
                    'default': default_match.group(1).strip() if default_match else None
                })

        return variables

    def _extract_outputs(self, file_path):
        """Extract output definitions"""
        outputs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

            output_pattern = r'output\s+"([^"]+)"\s*{([^}]+)}'
            matches = re.finditer(output_pattern, content, re.DOTALL)

            for match in matches:
                output_name = match.group(1)
                output_block = match.group(2)

                desc_match = re.search(
                    r'description\s*=\s*"([^"]+)"', output_block)

                outputs.append({
                    'name': output_name,
                    'description': desc_match.group(1) if desc_match else ''
                })

        return outputs

    def _extract_resources(self, file_path):
        """Extract resource types from main.tf"""
        resources = set()
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

            resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"'
            matches = re.finditer(resource_pattern, content)

            for match in matches:
                resources.add(match.group(1))

        return sorted(list(resources))

    def calculate_estimated_cost(self, env_name, config):
        """Calculate estimated monthly cost"""
        cost = 0

        # NAT Gateway cost
        if config.get('enable_nat_gateway') == 'true':
            if config.get('single_nat_gateway') == 'true':
                cost += 32  # Single NAT Gateway
            else:
                azs = config.get('availability_zones', '[]')
                num_azs = len(eval(azs)) if azs.startswith('[') else 3
                cost += 32 * num_azs  # Multiple NAT Gateways

        return cost

    def generate_readme(self):
        """Generate complete README content"""
        # Scan all components
        self.scan_terraform_environments()
        self.scan_terraform_modules()
        self.scan_workflows()

        readme = []
        readme.append(self._generate_header())
        readme.append(self._generate_overview())
        readme.append(self._generate_quick_start())
        readme.append(self._generate_infrastructure_section())
        readme.append(self._generate_workflows_section())
        readme.append(self._generate_cost_section())
        readme.append(self._generate_modules_section())
        readme.append(self._generate_footer())

        return '\n\n'.join(readme)

    def _generate_header(self):
        return """# EKS Multi-Service Infrastructure

> **Auto-generated documentation** - Last updated: {date}

[![Terraform](https://img.shields.io/badge/Terraform-1.6+-purple)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-EKS-orange)](https://aws.amazon.com/eks/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

Production-ready, multi-environment Kubernetes infrastructure on AWS EKS with complete automation via GitHub Actions.""".format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        )

    def _generate_overview(self):
        envs = self.data['environments']
        modules = self.data['modules']
        workflows = self.data['workflows']

        return f"""## 📊 Infrastructure Overview

**Current Status:**
- **Environments:** {len(envs)} ({', '.join(envs.keys())})
- **Terraform Modules:** {len(modules)} ({', '.join(modules.keys())})
- **CI/CD Pipelines:** {len(workflows)} workflows
- **Cloud Provider:** AWS (us-east-1)
- **Orchestration:** Amazon EKS + Terraform"""

    def _generate_quick_start(self):
        return """## 🚀 Quick Start

### Prerequisites
```bash
# Required tools
terraform >= 1.6.0
kubectl >= 1.28.0
aws-cli >= 2.13.0
```

### Deploy Infrastructure

**Option 1: GitHub Actions (Recommended)**
```bash
# Push changes to main branch
git add .
git commit -m "Deploy infrastructure"
git push origin main
# Workflow automatically triggers for dev environment
```

**Option 2: Local Deployment**
```bash
cd eks-multi-service/terraform/environments/dev
terraform init
terraform plan
terraform apply
```

**Option 3: Manual Workflow Trigger**
- Go to: Actions → Terraform Staging/Prod
- Click "Run workflow"
- Select: plan or apply"""

    def _generate_infrastructure_section(self):
        envs = self.data['environments']

        section = ["## 🏗️ Infrastructure Environments\n"]

        for env_name, config in envs.items():
            cost = self.calculate_estimated_cost(env_name, config)

            section.append(f"### {env_name.upper()} Environment\n")
            section.append("**Configuration:**")
            section.append("```hcl")
            for key, value in sorted(config.items()):
                if not key.startswith('_'):
                    section.append(f"{key:30s} = {value}")
            section.append("```\n")

            if cost > 0:
                section.append(f"**Estimated Cost:** ~${cost}/month\n")

        return '\n'.join(section)

    def _generate_workflows_section(self):
        workflows = self.data['workflows']

        section = ["## ⚙️ CI/CD Workflows\n"]
        section.append("| Workflow | Trigger | Purpose |")
        section.append("|----------|---------|---------|")

        for workflow_name, workflow_info in workflows.items():
            name = workflow_info['name']
            triggers = ', '.join(workflow_info['triggers'])
            purpose = self._get_workflow_purpose(workflow_name)
            section.append(f"| {name} | {triggers} | {purpose} |")

        return '\n'.join(section)

    def _get_workflow_purpose(self, workflow_name):
        """Get workflow purpose description"""
        purposes = {
            'terraform-dev': 'Auto-deploy dev environment on push to main',
            'terraform-staging': 'Manual deployment to staging',
            'terraform-prod': 'Manual deployment to production',
            'update-readme': 'Auto-update documentation on changes'
        }
        return purposes.get(workflow_name, 'Infrastructure deployment')

    def _generate_cost_section(self):
        envs = self.data['environments']

        section = ["## 💰 Cost Breakdown\n"]
        section.append(
            "| Environment | NAT Gateway | Estimated Monthly Cost |")
        section.append(
            "|-------------|-------------|------------------------|")

        total_cost = 0
        for env_name, config in envs.items():
            nat_config = "Single NAT" if config.get(
                'single_nat_gateway') == 'true' else "Multi-AZ NAT"
            cost = self.calculate_estimated_cost(env_name, config)
            total_cost += cost
            section.append(f"| {env_name} | {nat_config} | ~${cost} |")

        section.append(f"| **Total** | | **~${total_cost}** |")
        section.append("")
        section.append(
            "*Note: Costs include VPC infrastructure only. EKS cluster, databases, and compute costs not included.*")

        return '\n'.join(section)

    def _generate_modules_section(self):
        modules = self.data['modules']

        section = ["## 📦 Terraform Modules\n"]

        for module_name, module_info in modules.items():
            section.append(f"### {module_name.upper()} Module\n")

            if module_info['resources']:
                section.append("**Creates:**")
                for resource in module_info['resources']:
                    resource_name = resource.replace(
                        'aws_', '').replace('_', ' ').title()
                    section.append(f"- {resource_name}")
                section.append("")

            if module_info['variables']:
                section.append("<details>")
                section.append("<summary>📥 Input Variables</summary>\n")
                section.append("| Variable | Type | Description | Default |")
                section.append("|----------|------|-------------|---------|")
                for var in module_info['variables'][:10]:  # Show first 10
                    default = str(var.get('default', '-'))[:20]
                    section.append(
                        f"| `{var['name']}` | {var['type']} | {var['description']} | {default} |")
                section.append("</details>\n")

            if module_info['outputs']:
                section.append("<details>")
                section.append("<summary>📤 Outputs</summary>\n")
                section.append("| Output | Description |")
                section.append("|--------|-------------|")
                for output in module_info['outputs']:
                    section.append(
                        f"| `{output['name']}` | {output['description']} |")
                section.append("</details>\n")

        return '\n'.join(section)

    def _generate_footer(self):
        return """## 📚 Additional Documentation

- [Terraform Modules](terraform/modules/README.md)
- [Deployment Guide](docs/deployment-guide.md)
- [Troubleshooting](docs/troubleshooting.md)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- AWS EKS team for comprehensive documentation
- Terraform community for infrastructure patterns
- GitHub Actions for CI/CD automation

---

**🤖 This README is automatically generated.** To update, modify infrastructure code and push to main branch."""

    def save_readme(self, output_path=None):
        """Generate and save README"""
        if output_path is None:
            output_path = self.project_root / "README.md"

        content = self.generate_readme()

        # FIX: Specify UTF-8 encoding for Windows compatibility
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ README generated: {output_path}")
        print(
            f"✓ Documentation updated at {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    generator = ReadmeGenerator()
    generator.save_readme()
