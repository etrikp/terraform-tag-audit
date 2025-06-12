import os
import sys
from utils import parse_hcl_file, find_provider_default_tags, find_resources_missing_tags
from rich.console import Console
from rich.table import Table

console = Console()

def main(path="."):
    if not os.path.exists(path):
        console.print(f"[bold red]Path not found:[/bold red] {path}")
        sys.exit(1)

    provider_tags = {}
    all_resources = []
    untagged_resources = []

    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith((".tf", ".hcl")):
                full_path = os.path.join(root, file)
                data = parse_hcl_file(full_path)
                if not data:
                    continue

                # Detect provider-level default_tags
                provider_tags.update(find_provider_default_tags(data))

                # Collect resources and check tags
                resources = find_resources_missing_tags(data, provider_tags)
                if resources:
                    untagged_resources.extend([(full_path, r) for r in resources])
                all_resources.extend(resources)

    table = Table(title="Untagged Resources Report")

    table.add_column("File", style="cyan")
    table.add_column("Resource Type", style="magenta")
    table.add_column("Resource Name", style="green")

    for file_path, res in untagged_resources:
        table.add_row(file_path, res["type"], res["name"])

    if untagged_resources:
        console.print(table)
        console.print(f"[bold red]{len(untagged_resources)}[/bold red] resource(s) are missing required tags.")
        sys.exit(1)
    else:
        console.print("[bold green]All resources have required tags.[/bold green]")

if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else "."
    main(path_arg)

