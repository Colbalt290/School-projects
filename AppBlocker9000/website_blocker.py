import os

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts" if os.name == "nt" else "/etc/hosts"

def block_site(domain: str):
    # Strip protocols and ensure we have the base root domain
    clean_domain = domain.lower().replace("https://", "").replace("http://", "").strip("/")
    root_domain = clean_domain[4:] if clean_domain.startswith("www.") else clean_domain
    
    # Always target both the root and the www prefix
    domains_to_block = [root_domain, f"www.{root_domain}"]

    try:
        with open(HOSTS_PATH, "r+") as file:
            content = file.read()
            for d in domains_to_block:
                entry_v4 = f"127.0.0.1 {d}"
                entry_v6 = f"::1 {d}"
                
                if entry_v4 not in content:
                    file.write(f"{entry_v4}\n")
                if entry_v6 not in content:
                    file.write(f"{entry_v6}\n")
    except PermissionError:
        print("Permission denied: File modification requires Administrator/root privileges.")

def unblock_site(domain: str):
    clean_domain = domain.lower().replace("https://", "").replace("http://", "").strip("/")
    root_domain = clean_domain[4:] if clean_domain.startswith("www.") else clean_domain
    domains_to_remove = [root_domain, f"www.{root_domain}"]

    try:
        with open(HOSTS_PATH, "r") as file:
            lines = file.readlines()

        with open(HOSTS_PATH, "w") as file:
            for line in lines:
                if not any(d in line for d in domains_to_remove):
                    file.write(line)
    except PermissionError:
        print("Permission denied: File modification requires Administrator/root privileges.")