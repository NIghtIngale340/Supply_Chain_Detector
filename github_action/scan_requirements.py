import argparse
import json
import pathlib
import re
import time

import requests


def _parse_requirements(path: pathlib.Path) -> list[str]:
    packages: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#"):
            continue
        name = re.split(r"[<>=!~\[]", clean, maxsplit=1)[0].strip()
        if name:
            packages.append(name.lower())
    return packages


def _parse_package_json(path: pathlib.Path) -> list[str]:
    content = json.loads(path.read_text(encoding="utf-8"))
    deps = content.get("dependencies", {})
    dev_deps = content.get("devDependencies", {})
    return sorted({*deps.keys(), *dev_deps.keys()})


def discover_dependencies(root: pathlib.Path) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {"pypi": [], "npm": []}

    requirements_path = root / "requirements.txt"
    if requirements_path.exists():
        results["pypi"] = sorted(set(_parse_requirements(requirements_path)))

    package_json_path = root / "package.json"
    if package_json_path.exists():
        results["npm"] = sorted(set(_parse_package_json(package_json_path)))

    return results


def _submit_and_poll(api_base_url: str, name: str, registry: str, poll_timeout: int) -> dict:
    response = requests.post(
        f"{api_base_url}/analyze",
        json={"name": name, "registry": registry},
        timeout=15,
    )
    response.raise_for_status()
    job_id = response.json()["job_id"]

    deadline = time.time() + poll_timeout
    while time.time() < deadline:
        result_response = requests.get(f"{api_base_url}/results/{job_id}", timeout=15)
        result_response.raise_for_status()
        payload = result_response.json()
        if payload.get("status") == "completed":
            return payload.get("result", {})
        time.sleep(2)

    raise TimeoutError(f"Timed out waiting for {registry}:{name} (job={job_id})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--threshold", type=float, default=70.0)
    parser.add_argument("--poll-timeout", type=int, default=90)
    args = parser.parse_args()

    root = pathlib.Path("/github/workspace")
    if not root.exists():
        root = pathlib.Path.cwd()

    deps = discover_dependencies(root)
    findings: list[dict] = []

    for registry in ["pypi", "npm"]:
        for package in deps[registry]:
            result = _submit_and_poll(args.api_base_url, package, registry, args.poll_timeout)
            score = float(result.get("final_score", 0.0))
            findings.append({"registry": registry, "name": package, "score": score})
            print(f"{registry}:{package} -> {score}")

    high_risk = [item for item in findings if item["score"] >= args.threshold]
    if high_risk:
        print("Threshold exceeded:")
        for item in high_risk:
            print(f"- {item['registry']}:{item['name']} score={item['score']}")
        return 1

    print("All dependencies are below threshold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
