# Save this block as make_project.py and run it
import os

project_files = {
    "requirements.txt": """fastapi==0.111.0
uvicorn==0.30.1
psycopg2-binary==2.9.9
pydantic==2.7.4
python-dotenv==1.0.1""",

    ".env.example": "DATABASE_URL=postgresql://username:password@localhost:5432/your_database_name",
    
    ".env": "DATABASE_URL=your_actual_database_connection_string_here"
}

# The files logic mapped above will be cleanly spit out into a new directory
os.makedirs("product-browser", exist_ok=True)
for filename, content in project_files.items():
    with open(os.path.join("product-browser", filename), "w") as f:
        f.write(content)

print("Project base directory 'product-browser' generated successfully!")