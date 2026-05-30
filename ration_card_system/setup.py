import os

def setup_project():
    """Setup the project structure"""
    
    # Create directories
    directories = [
        'static/css',
        'static/js',
        'static/images',
        'templates',
        'templates/admin'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create requirements.txt
    with open('requirements.txt', 'w') as f:
        f.write("""Flask==2.3.3
Flask-Session==0.5.0""")
    
    print("\nProject structure created successfully!")
    print("\nNext steps:")
    print("1. pip install -r requirements.txt")
    print("2. python app.py")
    print("3. Open http://localhost:5000")

if __name__ == '__main__':
    setup_project()