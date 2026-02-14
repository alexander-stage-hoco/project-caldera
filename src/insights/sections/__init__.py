"""
Report sections for Caldera insights reports.
"""

from .base import BaseSection, SectionConfig, SectionData
from .executive_summary import ExecutiveSummarySection
from .repo_health import RepoHealthSection
from .file_hotspots import FileHotspotsSection
from .directory_analysis import DirectoryAnalysisSection
from .vulnerabilities import VulnerabilitiesSection
from .cross_tool import CrossToolSection
from .language_coverage import LanguageCoverageSection
from .distribution_insights import DistributionInsightsSection
from .roslyn_violations import RoslynViolationsSection
from .iac_misconfigs import IacMisconfigsSection
from .code_inequality import CodeInequalitySection
from .module_health import ModuleHealthSection
from .composite_risk import CompositeRiskSection
from .function_complexity import FunctionComplexitySection
from .coupling_analysis import CouplingAnalysisSection
from .authorship_risk import AuthorshipRiskSection
from .knowledge_risk import KnowledgeRiskSection
from .code_duplication import CodeDuplicationSection
from .dependency_health import DependencyHealthSection
from .license_compliance import LicenseComplianceSection
from .directory_structure import DirectoryStructureSection
from .blast_radius import BlastRadiusSection
from .code_size_hotspots import CodeSizeHotspotsSection
from .code_quality_rules import CodeQualityRulesSection
from .coverage_gap import CoverageGapSection
from .technical_debt_summary import TechnicalDebtSummarySection
from .coupling_debt import CouplingDebtSection
from .sonarqube_deep_dive import SonarQubeDeepDiveSection
from .secrets import SecretsSection
from .tool_readiness import ToolReadinessSection
from .tool_coverage_dashboard import ToolCoverageDashboardSection
from .component_inventory import ComponentInventorySection
from .import_dependencies import ImportDependenciesSection
from .circular_dependencies import CircularDependenciesSection

__all__ = [
    "BaseSection",
    "SectionConfig",
    "SectionData",
    "ExecutiveSummarySection",
    "RepoHealthSection",
    "FileHotspotsSection",
    "DirectoryAnalysisSection",
    "VulnerabilitiesSection",
    "CrossToolSection",
    "LanguageCoverageSection",
    "DistributionInsightsSection",
    "RoslynViolationsSection",
    "IacMisconfigsSection",
    "CodeInequalitySection",
    "ModuleHealthSection",
    "CompositeRiskSection",
    "FunctionComplexitySection",
    "CouplingAnalysisSection",
    "AuthorshipRiskSection",
    "KnowledgeRiskSection",
    "CodeDuplicationSection",
    "DependencyHealthSection",
    "LicenseComplianceSection",
    "DirectoryStructureSection",
    "BlastRadiusSection",
    "CodeSizeHotspotsSection",
    "CodeQualityRulesSection",
    "CoverageGapSection",
    "TechnicalDebtSummarySection",
    "CouplingDebtSection",
    "SonarQubeDeepDiveSection",
    "SecretsSection",
    "ToolReadinessSection",
    "ToolCoverageDashboardSection",
    "ComponentInventorySection",
    "ImportDependenciesSection",
    "CircularDependenciesSection",
]
