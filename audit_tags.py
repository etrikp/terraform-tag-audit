import os
import sys
import argparse
import json
import logging
from utils import parse_hcl_file, find_provider_default_tags, find_resources_missing_tags
from rich.console import Console
from rich.table import Table

console = Console()
logger = logging.getLogger("tag-audit")


def configure_logging(debug: bool):
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)


def main(path: str, json_output: bool, warn_only: bool, filter_provider: str, filter_resource: str):
    provider_tags = {}
    all_resources = []
    untagged_resources = []

    logger.info(f"Scanning directory: {path}")
    for root, dirs, files in os.walk(path):
        # Exclude hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for file in files:
            if file.endswith((".tf", ".hcl")):
                full_path = os.path.join(root, file)
                logger.debug(f"Parsing file: {full_path}")
                data = parse_hcl_file(full_path)
                if not data:
                    logger.warning(f"Failed to parse: {full_path}")
                    continue

                provider_tags.update(find_provider_default_tags(data))

                resources = find_resources_missing_tags(
                    data,
                    provider_tags,
                    filter_provider=filter_provider,
                    filter_resource=filter_resource,
                )
                if resources:
                    untagged_resources.extend([(full_path, r) for r in resources])
                all_resources.extend(resources)

    if json_output:
        report = [
            {"file": f, "type": r["type"], "name": r["name"]}
            for f, r in untagged_resources
        ]
        print(json.dumps(report, indent=2))
    else:
        table = Table(title="Untagged Resources Report")
        table.add_column("File", style="cyan")
        table.add_column("Resource Type", style="magenta")
        table.add_column("Resource Name", style="green")

        for file_path, res in untagged_resources:
            table.add_row(file_path, res["type"], res["name"])

        if untagged_resources:
            console.print(table)

    if untagged_resources:
        msg = f"{len(untagged_resources)} resource(s) missing required tags."
        if warn_only:
            logger.warning(msg)
        else:
            logger.error(msg)
            sys.exit(1)
    else:
        logger.info("All resources have required tags.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit Terraform/Terragrunt resources for missing tags.")
    parser.add_argument("path", nargs="?", default=".", help="Path to directory (default: current)")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of table")
    parser.add_argument("--warn-only", action="store_true", help="Warn instead of exiting with error on tag violations")
    parser.add_argument("--filter-provider", help="Only include resources from this provider")
    parser.add_argument("--filter-resource", help="Only include this resource type")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    configure_logging(args.debug)
    main(args.path, args.json, args.warn_only, args.filter_provider, args.filter_resource)

