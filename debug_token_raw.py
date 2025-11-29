import os

def inspect_env():
    env_path = os.path.join('backend', '.env')
    if not os.path.exists(env_path):
        print(f"❌ {env_path} not found.")
        return

    print(f"Reading {env_path} in binary mode...")
    with open(env_path, 'rb') as f:
        content = f.read()
        print(f"Raw content: {content}")
        
    print("\nParsing line by line...")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("ACCESS_TOKEN"):
                print(f"Found ACCESS_TOKEN line: {repr(line)}")
                parts = line.split('=', 1)
                if len(parts) > 1:
                    token = parts[1].strip()
                    print(f"Parsed Token: {repr(token)}")
                    print(f"Token Length: {len(token)}")
                    if " " in token:
                        print("❌ WARNING: Token contains spaces!")
                    if "\t" in token:
                        print("❌ WARNING: Token contains tabs!")
                else:
                    print("❌ Could not split line.")

if __name__ == "__main__":
    inspect_env()
