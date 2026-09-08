"""Invoke the pinned Synthea jar into ``seed/raw/`` (deterministic).

Dev-time only. The jar is ~192 MiB and is **not** committed or vendored;
download it once::

    curl -L -o synthea.jar \\
      https://github.com/synthetichealth/synthea/releases/download/v4.0.0/synthea-with-dependencies.jar

Then::

    SYNTHEA_JAR=synthea.jar python -m seed.scripts.run_synthea

``JAVA_BIN`` overrides the ``java`` on PATH. The checksum of the jar is
verified against ``common.SYNTHEA_JAR_SHA256`` before it runs.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

from seed.scripts import common


def _verify_jar(jar: Path) -> None:
    if not jar.is_file():
        sys.exit(f"SYNTHEA_JAR not found: {jar}")
    size = jar.stat().st_size
    if size != common.SYNTHEA_JAR_SIZE:
        sys.exit(
            f"jar size {size} != pinned {common.SYNTHEA_JAR_SIZE}; wrong release?"
        )
    digest = hashlib.sha256(jar.read_bytes()).hexdigest()
    if digest != common.SYNTHEA_JAR_SHA256:
        sys.exit(f"jar sha256 {digest} != pinned {common.SYNTHEA_JAR_SHA256}")
    print(f"synthea jar verified: {common.SYNTHEA_VERSION} ({digest[:12]}...)")


def run() -> Path:
    jar = Path(os.environ.get("SYNTHEA_JAR", "synthea-with-dependencies.jar"))
    _verify_jar(jar)
    java = os.environ.get("JAVA_BIN", "java")

    if common.RAW_DIR.exists():
        shutil.rmtree(common.RAW_DIR)
    common.RAW_DIR.mkdir(parents=True)

    cmd = [
        java,
        "-jar",
        str(jar),
        "-s",
        str(common.SYNTHEA_PATIENT_SEED),
        "-cs",
        str(common.SYNTHEA_CLINICIAN_SEED),
        "-p",
        str(common.SYNTHEA_POPULATION),
        "-r",
        "20260101",  # fixed reference date -> deterministic ages
        "--exporter.baseDirectory",
        str(common.RAW_DIR),
        "--exporter.csv.export",
        "true",
        "--exporter.fhir.export",
        "false",
        "--exporter.hospital.fhir.export",
        "false",
        "--exporter.practitioner.fhir.export",
        "false",
        "--exporter.metadata.export",
        "false",
        "--generate.only_alive_patients",
        "true",
        common.SYNTHEA_LOCATION,
    ]
    print("running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    csv_dir = common.RAW_DIR / "csv"
    if not (csv_dir / "patients.csv").is_file():
        sys.exit("synthea produced no csv/patients.csv")
    print(f"synthea output: {csv_dir}")
    return csv_dir


if __name__ == "__main__":
    run()
