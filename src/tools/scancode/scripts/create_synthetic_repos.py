#!/usr/bin/env python3
"""Create synthetic repositories with various license configurations."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# License text templates
MIT_LICENSE = """MIT License

Copyright (c) 2024 Test Organization

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

APACHE_LICENSE = """                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity.

   Copyright 2024 Test Organization

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

GPL3_LICENSE = """                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

BSD3_LICENSE = """BSD 3-Clause License

Copyright (c) 2024, Test Organization
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

LGPL_LICENSE = """                   GNU LESSER GENERAL PUBLIC LICENSE
                       Version 2.1, February 1999

 Copyright (C) 1991, 1999 Free Software Foundation, Inc.
 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

[This is the first released version of the Lesser GPL.  It also counts
 as the successor of the GNU Library Public License, version 2, hence
 the version number 2.1.]

                            Preamble

  The licenses for most software are designed to take away your
freedom to share and change it.  By contrast, the GNU General Public
Licenses are intended to guarantee your freedom to share and change
free software--to make sure the software is free for all its users.

  This license, the Lesser General Public License, applies to some
specially designated software packages--typically libraries--of the
Free Software Foundation and other authors who decide to use it.
"""


@dataclass
class LicenseSpec:
    """Specification for a license file."""
    filename: str
    content: str
    spdx_id: str
    category: str  # permissive, copyleft, weak-copyleft, proprietary, unknown


@dataclass
class RepoSpec:
    """Specification for a synthetic repository."""
    name: str
    description: str
    licenses: list[LicenseSpec] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    expected_risk: str = "low"  # low, medium, high, critical


SYNTHETIC_REPOS = [
    RepoSpec(
        name="mit-only",
        description="Clean repository with MIT license only",
        licenses=[
            LicenseSpec("LICENSE", MIT_LICENSE, "MIT", "permissive"),
        ],
        files={
            "README.md": "# MIT Only Project\n\nThis project is licensed under MIT.\n",
            "src/main.py": '''"""Main module."""
# SPDX-License-Identifier: MIT


def main():
    """Entry point."""
    print("Hello, MIT World!")


if __name__ == "__main__":
    main()
''',
        },
        expected_risk="low",
    ),
    RepoSpec(
        name="gpl-mixed",
        description="Repository with GPL license (copyleft - commercial risk)",
        licenses=[
            LicenseSpec("LICENSE", GPL3_LICENSE, "GPL-3.0-only", "copyleft"),
            LicenseSpec("COPYING", GPL3_LICENSE, "GPL-3.0-only", "copyleft"),
        ],
        files={
            "README.md": "# GPL Project\n\nThis project is licensed under GPL v3.\n\n**WARNING**: Copyleft license - derivative works must also be GPL.\n",
            "src/main.py": '''"""Main module."""
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2024 Test Organization


def main():
    """Entry point."""
    print("Hello, GPL World!")


if __name__ == "__main__":
    main()
''',
            "src/lib/utils.py": '''"""Utility functions."""
# SPDX-License-Identifier: GPL-3.0-only


def helper():
    return "GPL helper"
''',
        },
        expected_risk="critical",
    ),
    RepoSpec(
        name="apache-bsd",
        description="Repository with Apache 2.0 and BSD licenses (both permissive)",
        licenses=[
            LicenseSpec("LICENSE", APACHE_LICENSE, "Apache-2.0", "permissive"),
            LicenseSpec("LICENSE.BSD", BSD3_LICENSE, "BSD-3-Clause", "permissive"),
        ],
        files={
            "README.md": "# Apache + BSD Project\n\nMain code is Apache 2.0, some components BSD-3.\n",
            "src/main.py": '''"""Main module."""
# SPDX-License-Identifier: Apache-2.0


def main():
    """Entry point."""
    print("Hello, Apache World!")


if __name__ == "__main__":
    main()
''',
            "vendor/third_party.py": '''"""Third-party code under BSD."""
# SPDX-License-Identifier: BSD-3-Clause


def vendor_function():
    return "BSD vendor code"
''',
        },
        expected_risk="low",
    ),
    RepoSpec(
        name="no-license",
        description="Repository with no license file (all rights reserved by default)",
        licenses=[],
        files={
            "README.md": "# No License Project\n\nNo license specified.\n",
            "src/main.py": '''"""Main module."""


def main():
    """Entry point."""
    print("Hello, No License World!")


if __name__ == "__main__":
    main()
''',
        },
        expected_risk="high",
    ),
    RepoSpec(
        name="multi-license",
        description="Repository with multiple licenses (MIT, Apache, LGPL)",
        licenses=[
            LicenseSpec("LICENSE", MIT_LICENSE, "MIT", "permissive"),
            LicenseSpec("LICENSE.Apache", APACHE_LICENSE, "Apache-2.0", "permissive"),
            LicenseSpec("LICENSE.LGPL", LGPL_LICENSE, "LGPL-2.1-only", "weak-copyleft"),
        ],
        files={
            "README.md": "# Multi-License Project\n\nDifferent components under different licenses.\n",
            "src/main.py": '''"""Main module - MIT licensed."""
# SPDX-License-Identifier: MIT


def main():
    """Entry point."""
    print("Hello, Multi-License World!")


if __name__ == "__main__":
    main()
''',
            "lib/apache_code.py": '''"""Apache 2.0 licensed code."""
# SPDX-License-Identifier: Apache-2.0


def apache_function():
    return "Apache code"
''',
            "lib/lgpl_code.py": '''"""LGPL 2.1 licensed code."""
# SPDX-License-Identifier: LGPL-2.1-only


def lgpl_function():
    return "LGPL code"
''',
        },
        expected_risk="medium",
    ),
]


def run_git(repo_path: Path, *args: str) -> None:
    """Run a git command in the repository."""
    subprocess.run(
        ["git", "-C", str(repo_path)] + list(args),
        check=True,
        capture_output=True,
    )


def create_repo(base_path: Path, spec: RepoSpec) -> None:
    """Create a synthetic repository from specification."""
    repo_path = base_path / spec.name

    # Clean up existing repo
    if repo_path.exists():
        shutil.rmtree(repo_path)

    repo_path.mkdir(parents=True)

    # Initialize git repo
    run_git(repo_path, "init")
    run_git(repo_path, "config", "user.email", "test@example.com")
    run_git(repo_path, "config", "user.name", "Test User")

    # Create license files
    for license_spec in spec.licenses:
        license_path = repo_path / license_spec.filename
        license_path.write_text(license_spec.content)

    # Create all other files
    for file_path, content in spec.files.items():
        full_path = repo_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    # Initial commit
    run_git(repo_path, "add", "-A")
    run_git(repo_path, "commit", "-m", "Initial commit")

    print(f"Created: {spec.name} - {spec.description}")
    print(f"  Licenses: {[l.spdx_id for l in spec.licenses] or ['none']}")
    print(f"  Risk level: {spec.expected_risk}")


def main() -> None:
    """Create all synthetic repositories."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent / "eval-repos" / "synthetic"

    print("Creating synthetic repositories for license analysis...")
    print(f"Output directory: {base_path}")
    print()

    for spec in SYNTHETIC_REPOS:
        create_repo(base_path, spec)

    print()
    print(f"Created {len(SYNTHETIC_REPOS)} synthetic repositories")

    # Summary by risk
    by_risk = {}
    for spec in SYNTHETIC_REPOS:
        by_risk.setdefault(spec.expected_risk, []).append(spec.name)

    print("\nBy risk level:")
    for risk in ["critical", "high", "medium", "low"]:
        if risk in by_risk:
            print(f"  {risk}: {', '.join(by_risk[risk])}")


if __name__ == "__main__":
    main()
