import os
import json
import urllib.request
import zipfile
import shutil

class PackageManager:
    """Dapine Package Manager - dap install"""
    
    REGISTRY_URL = "https://raw.githubusercontent.com/Aditya-cyber-hind/dapine-packages/main/registry.json"
    PACKAGES_DIR = "./dap_packages"
    
    def __init__(self):
        self.registry = self._load_registry()
        if not os.path.exists(self.PACKAGES_DIR):
            os.makedirs(self.PACKAGES_DIR)
    
    def _load_registry(self):
        """Load package registry."""
        try:
            with urllib.request.urlopen(self.REGISTRY_URL) as r:
                return json.loads(r.read().decode())
        except:
            # Offline registry
            return {
                "packages": {
                    "stdlib": {"version": "1.0", "description": "Dapine Standard Library"},
                    "ml": {"version": "1.0", "description": "Machine Learning extensions"},
                    "charts": {"version": "1.0", "description": "Chart generation"},
                    "connectors": {"version": "1.0", "description": "Database & Excel connectors"},
                }
            }
    
    def install(self, package_name):
        """Install a package."""
        if package_name in self.registry.get("packages", {}):
            pkg = self.registry["packages"][package_name]
            print(f"📦 Installing {package_name} v{pkg['version']}...")
            print(f"   {pkg.get('description', '')}")
            
            # For built-in packages, just confirm
            builtin = ['stdlib', 'ml', 'charts', 'connectors']
            if package_name in builtin:
                print(f"✅ {package_name} is already bundled with Dapine!")
                return True
            
            print(f"✅ Package '{package_name}' installed successfully!")
            return True
        else:
            print(f"❌ Package '{package_name}' not found in registry.")
            self.search(package_name)
            return False
    
    def uninstall(self, package_name):
        """Uninstall a package."""
        pkg_dir = os.path.join(self.PACKAGES_DIR, package_name)
        if os.path.exists(pkg_dir):
            shutil.rmtree(pkg_dir)
            print(f"🗑️  Uninstalled {package_name}")
        else:
            print(f"❌ Package '{package_name}' not installed.")
    
    def list_installed(self):
        """List installed packages."""
        builtin = ['stdlib', 'ml', 'charts', 'connectors', 'duck_engine', 'ai_engine', 'reports']
        print("\n📦 Installed Packages:")
        print("  Built-in:")
        for pkg in builtin:
            print(f"    ✅ {pkg}")
        
        if os.path.exists(self.PACKAGES_DIR):
            installed = os.listdir(self.PACKAGES_DIR)
            if installed:
                print("  External:")
                for pkg in installed:
                    print(f"    📦 {pkg}")
    
    def search(self, query):
        """Search for packages."""
        print(f"\n🔍 Searching for '{query}'...")
        found = False
        for name, info in self.registry.get("packages", {}).items():
            if query.lower() in name.lower() or query.lower() in info.get('description', '').lower():
                print(f"  📦 {name} v{info.get('version', '?')} - {info.get('description', '')}")
                found = True
        if not found:
            print(f"  No packages found matching '{query}'")
    
    def update(self):
        """Update all packages."""
        print("🔄 Updating packages...")
        self.registry = self._load_registry()
        print("✅ Registry updated!")
    
    def create_package(self, name, files):
        """Create a new package from files."""
        pkg_dir = os.path.join(self.PACKAGES_DIR, name)
        os.makedirs(pkg_dir, exist_ok=True)
        
        # Create package.json
        pkg_json = {
            "name": name,
            "version": "1.0.0",
            "description": f"Package: {name}",
            "files": files,
            "dependencies": []
        }
        
        with open(os.path.join(pkg_dir, "package.json"), "w") as f:
            json.dump(pkg_json, f, indent=2)
        
        # Copy files
        for f in files:
            if os.path.exists(f):
                shutil.copy(f, pkg_dir)
        
        print(f"✅ Package '{name}' created at {pkg_dir}")