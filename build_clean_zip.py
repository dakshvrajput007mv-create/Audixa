import os
import zipfile

def create_clean_zip():
    zip_path = 'Audixa_Clean_Project.zip'
    if os.path.exists(zip_path):
        os.remove(zip_path)

    exclude_dirs = {'venv', '__pycache__', '.pytest_cache', '.git', 'test_data', 'uploads'}
    exclude_files = {'audixa.db'}

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk('.'):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            if 'venv' in root.replace('\\', '/').split('/'):
                continue
            
            for file in files:
                if file.endswith(('.pyc', '.zip', '.log')) or file.startswith('.') or file in exclude_files:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, '.')
                z.write(full_path, arcname=os.path.join('Audixa', rel_path))

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f'[Audixa] Clean Project Zip rebuilt successfully: {zip_path} ({size_mb:.2f} MB)')

if __name__ == '__main__':
    create_clean_zip()
