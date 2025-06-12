import hcl2

def parse_hcl_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return hcl2.load(f)
    except Exception:
        return None

def find_provider_default_tags(data):
    """
    Looks for provider blocks with default_tags
    """
    provider_tags = {}

    providers = data.get("provider", {})
    for provider_name, blocks in providers.items():
        if isinstance(blocks, list):
            for block in blocks:
                if "default_tags" in block:
                    provider_tags[provider_name] = block["default_tags"].get("tags", {})
    return provider_tags

def find_resources_missing_tags(data, provider_tags):
    """
    Finds resources that don't have tags and don't inherit them via provider
    """
    untagged = []

    resources = data.get("resource", {})
    for res_type, res_list in resources.items():
        for res_name, res_body in res_list.items():
            # AWS-only tag check for now
            if "tags" not in res_body:
                inherits = any(
                    prov for prov, tags in provider_tags.items()
                    if prov.startswith("aws") and tags
                )
                if not inherits:
                    untagged.append({
                        "type": res_type,
                        "name": res_name
                    })
    return untagged

