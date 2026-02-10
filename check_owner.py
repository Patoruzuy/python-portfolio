from app import app, OwnerProfile
import json

with app.app_context():
    owner = OwnerProfile.query.first()
    if owner:
        print("Owner exists:", owner.name)
        print("Skills type:", type(owner.skills))
        print("Skills:", json.dumps(owner.skills, indent=2) if owner.skills else "NONE")
        if owner.skills:
            print("\nSkills structure:")
            for category in owner.skills:
                print(f"  - {category.get('category')}: {len(category.get('skills', []))} skills")
    else:
        print("NO OWNER FOUND")
