import hcl2


def parse_hcl_file(file_path):
    """
    Parses an HCL (.tf or .hcl) file and returns the data as a list of blocks.
    Returns None on error.
    """
    try:
        with open(file_path, 'r') as f:
            return hcl2.load(f)
    except Exception:
        return None


def find_provider_default_tags(blocks):
    """
    Extracts any default tags set at the provider level.
    Supports multiple providers and multiple configurations per provider.
    Returns a dict of provider name -> default tags dict.
    """
    provider_tags = {}

    if not isinstance(blocks, list):
        return provider_tags

    for block in blocks:
        if not isinstance(block, dict) or "provider" not in block:
            continue

        provider_block = block["provider"]
        if not isinstance(provider_block, dict):
            continue

        for provider_name, provider_config in provider_block.items():
            if isinstance(provider_config, list):
                for conf in provider_config:
                    if isinstance(conf, dict) and "default_tags" in conf:
                        tags = conf["default_tags"].get("tags", {})
                        if tags:
                            provider_tags[provider_name] = tags
            elif isinstance(provider_config, dict):
                if "default_tags" in provider_config:
                    tags = provider_config["default_tags"].get("tags", {})
                    if tags:
                        provider_tags[provider_name] = tags

    return provider_tags


def find_resources_missing_tags(blocks, provider_tags, filter_provider=None, filter_resource=None):
    """
    Finds resources that:
      - Do not have a 'tags' block, or the 'tags' block is empty
      - And do not inherit from a provider with default_tags
    Returns a list of dicts with keys: 'type' and 'name'
    """
    untagged = []

    if not isinstance(blocks, list):
        return untagged

    for block in blocks:
        if not isinstance(block, dict) or "resource" not in block:
            continue

        resource_block = block["resource"]
        if not isinstance(resource_block, dict):
            continue

        for res_type, instances in resource_block.items():
            if filter_resource and res_type != filter_resource:
                continue
            if not isinstance(instances, dict):
                continue

            for res_name, res_config in instances.items():
                if not isinstance(res_config, dict):
                    continue

                # Skip if provider filter doesn't match
                if filter_provider and not res_type.startswith(filter_provider):
                    continue

                # Explicit tags defined?
                has_tags = "tags" in res_config and bool(res_config["tags"])

                # Inherits from provider with default tags?
                inherits_tags = bool(provider_tags)

                if not has_tags and not inherits_tags:
                    untagged.append({
                        "type": res_type,
                        "name": res_name
                    })

    return untagged

