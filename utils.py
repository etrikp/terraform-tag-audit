import hcl2

def parse_hcl_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return hcl2.load(f)
    except Exception:
        return None

def find_provider_default_tags(data):
    """
    Looks for provider blocks with default_tags.
    Supports both list and dict formats.
    """
    provider_tags = {}

    if "provider" in data:
        for provider_block in data["provider"]:
            for provider_name, provider_config in provider_block.items():
                if isinstance(provider_config, list):
                    for conf in provider_config:
                        if "default_tags" in conf:
                            tags = conf["default_tags"].get("tags", {})
                            if tags:
                                provider_tags[provider_name] = tags
                elif isinstance(provider_config, dict):
                    if "default_tags" in provider_config:
                        tags = provider_config["default_tags"].get("tags", {})
                        if tags:
                            provider_tags[provider_name] = tags
    return provider_tags

def find_resources_missing_tags(data, provider_tags):
    """
    Finds resources that don't have tags and don't inherit them via provider.
    Supports both list and dict formats.
    """
    untagged = []

    if "resource" in data:
        for resource_block in data["resource"]:
            for res_type, instances in resource_block.items():
                for res_name, res_config in instances.items():
                    has_tags = "tags" in res_config
                    inherits_tags = any(
                        prov for prov, tags in provider_tags.items()
                        if prov.startswith("aws") and tags
                    )
                    if not has_tags and not inherits_tags:
                        untagged.append({
                            "type": res_type,
                            "name": res_name
                        })

    return untagged

