import os
import httpx
from dotenv import load_dotenv

# Load .env explicitly
env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
load_dotenv(env_path, override=True)

def diagnose_token():
    ig_user_id = os.getenv("IG_USER_ID")
    access_token = os.getenv("ACCESS_TOKEN")
    
    print(f"IG_USER_ID: {ig_user_id}")
    print(f"ACCESS_TOKEN: {access_token[:10]}..." if access_token else "ACCESS_TOKEN: None")
    
    if not access_token:
        print("❌ No access token found.")
        return

    base_url = "https://graph.facebook.com/v18.0"
    
    # 1. Check Permissions
    print("\n1. Checking Token Permissions...")
    try:
        resp = httpx.get(f"{base_url}/me/permissions", params={"access_token": access_token})
        data = resp.json()
        if "data" in data:
            perms = [p["permission"] for p in data["data"] if p["status"] == "granted"]
            print(f"✅ Granted Permissions: {', '.join(perms)}")
        else:
            print(f"❌ Could not fetch permissions: {data}")
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")

    # 2. Check Access to IG Account
    print(f"\n2. Checking Access to IG Account ({ig_user_id})...")
    try:
        resp = httpx.get(f"{base_url}/{ig_user_id}", params={"fields": "id,username", "access_token": access_token})
        data = resp.json()
        if "id" in data:
            print(f"✅ Successfully accessed IG Account: {data.get('username')} ({data.get('id')})")
        else:
            print(f"❌ Cannot access IG Account. Response: {data}")
    except Exception as e:
        print(f"❌ Error checking IG account: {e}")

    # 3. Try to create a container (POST) with token in Query Params
    print(f"\n3. Attempting to create media container (Token in Query Params)...")
    public_image_url = "https://images.unsplash.com/photo-1575936123452-b67c3203c357?ixlib=rb-4.0.3&w=1000&q=80"
    
    try:
        create_url = f"{base_url}/{ig_user_id}/media"
        # Token in Query Params
        params = {"access_token": access_token}
        payload = {
            "image_url": public_image_url,
            "caption": "Test Post (Query Param Token) 🚀"
        }
        
        print(f"POST {create_url}")
        resp = httpx.post(create_url, params=params, json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            print("✅ SUCCESS! Token in query params works.")
        else:
            print("❌ Failed even with query params.")

    except Exception as e:
        print(f"❌ Error creating container: {e}")

if __name__ == "__main__":
    diagnose_token()
